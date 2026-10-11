"""交易员 Agent 团队（R2 升级版）

将单次静态 LLM 调用升级为多角色协作流水线：

  Scout (scout.py)   → 搜集情报（oracle 官方源 + web 搜索）
  Estimator 概率估算师 → 基于市场信息 + 情报，独立估算真实概率
  Decision 交易决策员  → 对比隐含概率 vs 估算概率，找价差，决定 BUY/HOLD
  Risk 风控经理        → 复核仓位与市场状态，最终放行

每个角色是一次专用 system prompt 的 LLM 调用（与单 agent 成本可控）。
任一环节失败自动降级（回退到单 agent 静态分析），主循环不死。
"""
from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

import config
from llm import _normalize, _parse_json
from scout import gather_intel, summarize_for_prompt

log = logging.getLogger("pantapilot.agents")

# ---------------------------------------------------------------------------
# 各 Agent 的 system prompt
# ---------------------------------------------------------------------------
ESTIMATOR_PROMPT = """You are a quantitative probability estimator for prediction markets.

You receive:
1. The market's structured fields (title, prices, volume, resolution time).
2. Live intelligence gathered from the web (news, official data sources).

Your ONLY job is to estimate the TRUE probability that the event happens (the YES outcome).
- Use the intelligence evidence as your primary basis.
- Be explicit about what evidence supports your estimate.
- If intelligence is absent or insufficient, give a wide uncertainty and lower confidence.

Output ONLY a JSON object:
{"true_prob_yes": 0.0, "confidence": 0.0, "key_evidence": "1-3 bullet points", "uncertainty": "low|medium|high"}"""

DECISION_PROMPT = """You are a disciplined prediction-market trader. You receive:
1. Current market prices (YES/NO) and volume.
2. An independent probability estimate from your estimator agent.

Your job is to find mispricing: compare the market's implied YES probability against the estimator's true_prob_yes estimate.
- Rule: When the gap between market price and estimated true probability is >15%, be decisive and recommend BUY_YES (if undervalued) or BUY_NO (if overvalued). Do NOT hesitate or default to HOLD when a clear edge exists!
- If the estimated true probability is significantly higher than market YES price (gap > +15%), recommend BUY_YES.
- If the estimated true probability is significantly lower than market YES price (gap < -15%), recommend BUY_NO.
- Output HOLD ONLY when the market is fairly priced (gap < 10%) or there is severe conflicting ambiguity.
- Keep any single trade small (a few USDC at most, e.g. 1.0 to 2.0 USDC).
- Confidence should be between 0.5 and 0.85 when a clear edge is identified.

Output ONLY a JSON object:
{"decision": "BUY_YES"|"BUY_NO"|"HOLD", "confidence": 0.0, "reason": "short reason highlighting the implied vs estimated gap", "suggested_usdc": 1.5}"""

RISK_PROMPT = """You are a risk manager reviewing a proposed trade before execution.

You receive the proposed decision, its confidence, the market's status/volume, and a per-trade cap.
- If the proposed decision is HOLD, approve it immediately.
- For BUY proposals: Approve if trade size is <= max_trade_usdc, confidence >= min_confidence, and the edge logic is sound.
- Veto (final = HOLD, approved = false) ONLY if: confidence is below threshold, market has zero volume/liquidity, amount exceeds cap, or the reasoning is irrational.
- Do NOT veto valid trades with clear edge and small sizes.

Output ONLY a JSON object:
{"final": "BUY_YES"|"BUY_NO"|"HOLD", "approved": true|false, "note": "short reason"}"""


class AgentTeam:
    """多角色 LLM 交易团队。每个角色独立超时/重试（沿用全局配置）。"""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.model = model or config.LLM_MODEL
        api_key = api_key if api_key is not None else config.LLM_API_KEY
        self.enabled = bool(api_key)
        self.client = OpenAI(
            base_url=base_url or config.LLM_BASE_URL,
            api_key=api_key or "sk-dummy",
            timeout=config.LLM_TIMEOUT_SECONDS,
            max_retries=config.LLM_MAX_RETRIES,
        )
        # 单 agent 兜底
        from llm import LLMDecisionEngine

        self.fallback = LLMDecisionEngine(base_url=base_url, api_key=api_key, model=model)

    # ------------------------------------------------------------------
    def _ask(self, system: str, user: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return _parse_json(resp.choices[0].message.content or "")
        except Exception as exc:  # noqa: BLE001
            log.warning("Agent 调用失败: %s", exc)
            return None

    # ------------------------------------------------------------------
    def analyze(self, market: dict[str, Any], market_text: str, enable_search: bool = True) -> dict[str, Any]:
        """完整流水线：Scout → Estimator → Decision → Risk。

        返回兼容旧格式的决策 dict，额外附 evidence（供日志/看板）。
        """
        # ① Scout：情报搜集
        intel = gather_intel(market, enable_search=enable_search)
        intel_text = summarize_for_prompt(intel)

        # ② Estimator：独立估算真实概率
        est_user = f"{market_text}\n\n---\n{intel_text}"
        est = self._ask(ESTIMATOR_PROMPT, est_user)

        # 提取市场隐含概率并计算基准对比（P2 对比基准）
        implied_yes: float | None = None
        for k in ("yesPrice", "primaryYesPrice"):
            v = market.get(k)
            if v not in (None, ""):
                try:
                    fval = float(v)
                    if 0.0 <= fval <= 1.0:
                        implied_yes = fval
                        break
                except (ValueError, TypeError):
                    pass

        benchmark: dict[str, Any] | None = None
        if est and isinstance(est, dict):
            try:
                est_prob = float(est.get("true_prob_yes", 0.0))
                if implied_yes is not None:
                    gap = est_prob - implied_yes
                    gap_pct = gap * 100
                    benchmark = {
                        "market_implied": round(implied_yes, 4),
                        "estimator_prob": round(est_prob, 4),
                        "gap": round(gap, 4),
                        "gap_pct": f"{gap_pct:+.1f}%",
                    }
            except (ValueError, TypeError):
                pass

        # ③ Decision：对比找 edge
        if est:
            benchmark_text = ""
            if benchmark:
                benchmark_text = (
                    f"BENCHMARK COMPARISON:\n"
                    f"- Market Implied YES Probability: {benchmark['market_implied']*100:.1f}%\n"
                    f"- Estimator Assessed YES Probability: {benchmark['estimator_prob']*100:.1f}%\n"
                    f"- Net Disparity (Gap): {benchmark['gap_pct']}\n\n"
                )
            dec_user = (
                f"{market_text}\n\n---\n"
                f"{benchmark_text}"
                f"ESTIMATOR'S INDEPENDENT ESTIMATE:\n"
                + json.dumps(est, ensure_ascii=False)
            )
        else:
            dec_user = f"{market_text}\n\n---\n{intel_text}"
        dec = self._ask(DECISION_PROMPT, dec_user)

        if dec is None:
            # 降级：单 agent 静态分析
            decision = self.fallback.analyze(market_text)
            return {**decision, "evidence": {"pipeline": "fallback_single_agent", "intel": _slim_intel(intel)}}

        decision = _normalize(dec)

        # ④ Risk：风控复核（低置信度/超上限时否决）
        risk_user = json.dumps(
            {
                "proposal": decision,
                "estimator": est,
                "benchmark": benchmark,
                "market_status": market.get("status"),
                "volume_usdc": market.get("volumeUsdc"),
                "max_trade_usdc": config.MAX_TRADE_USDC,
                "min_confidence": config.MIN_CONFIDENCE,
            },
            ensure_ascii=False,
        )
        risk = self._ask(RISK_PROMPT, risk_user)
        if risk and not risk.get("approved", True):
            original_reason = decision["reason"]
            decision["decision"] = "HOLD"
            decision["confidence"] = min(decision["confidence"], 0.5)
            decision["suggested_usdc"] = 0.0
            decision["reason"] = f"[risk veto] {risk.get('note', '')} / original: {original_reason}"

        return {
            **decision,
            "evidence": {
                "pipeline": "scout>estimator>decision>risk",
                "estimator": est,
                "risk": risk,
                "intel": _slim_intel(intel),
                "benchmark": benchmark,
            },
        }


def _slim_intel(intel: dict[str, Any]) -> dict[str, Any]:
    """日志友好截断（避免情报原文撑爆 JSONL）。"""
    return {
        "queries": intel.get("queries", []),
        "oracle_head": (intel.get("oracleData") or "")[:400],
        "search_head": (intel.get("searchIntel") or "")[:400],
        "meta": intel.get("meta", {}),
    }