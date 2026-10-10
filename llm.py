"""LLM 决策引擎（R2/F2）

调用 OpenAI 兼容接口（OpenRouter）让 LLM 分析市场并输出结构化决策。
- 输入为市场文本块（见 panta.market_to_prompt_block）
- 输出 JSON: {decision, confidence, reason, suggested_usdc}
- 强制 timeout 60s + max_retries=1（免费模型不稳定）
- 解析失败或超时返回 HOLD（不崩循环）
"""
from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError

import config

log = logging.getLogger("pantapilot.llm")

SYSTEM_PROMPT = """You are an expert analyst for prediction markets. You will be given a prediction market (sports, esports, or similar) with its current YES and NO prices.

Rules:
- Recommend BUY_YES or BUY_NO ONLY when you have a SPECIFIC, articulable reason the market is mispriced (e.g. the implied probability clearly diverges from your independent estimate of the true probability).
- Prefer markets that resolve in the near term.
- If you are not confident or do not understand the market, output HOLD.
- Keep any single trade small (a few USDC at most).
- Confidence is a number 0-1 expressing how sure you are about your edge.

Output ONLY a JSON object with no extra text, exactly this shape:
{"decision": "BUY_YES"|"BUY_NO"|"HOLD", "confidence": 0.0, "reason": "short reason", "suggested_usdc": -socialcost}"""


class LLMDecisionEngine:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.base_url = base_url or config.LLM_BASE_URL
        self.api_key = api_key if api_key is not None else config.LLM_API_KEY
        self.model = model or config.LLM_MODEL
        self.timeout = timeout if timeout is not None else config.LLM_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else config.LLM_MAX_RETRIES
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key or "sk-dummy",
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    def analyze(self, market_text: str, user_hint: str = "") -> dict[str, Any]:
        """返回标准化决策字典，失败时返回 HOLD 安全默认。"""
        default = {
            "decision": "HOLD",
            "confidence": 0.0,
            "reason": "LLM analysis failed",
            "suggested_usdc": 0.0,
        }
        if not self.api_key:
            log.warning("LLM_API_KEY 未配置，返回 HOLD")
            return default
        try:
            content = self._call(market_text, user_hint)
            parsed = _parse_json(content)
            if parsed is None:
                return default
            return _normalize(parsed)
        except (APITimeoutError, APIConnectionError, RateLimitError, Exception) as exc:  # noqa: BLE001
            log.warning("LLM 调用失败(%s): %s", type(exc).__name__, exc)
            return default

    def _call(self, market_text: str, user_hint: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": market_text + (f"\n\n{user_hint}" if user_hint else "")},
        ]
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


def _parse_json(content: str) -> dict[str, Any] | None:
    content = content.strip()
    # 去掉可能包裹的 ```json ... ```
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # 尝试提取第一个 { ... } 块
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _normalize(parsed: dict[str, Any]) -> dict[str, Any]:
    decision = str(parsed.get("decision", "HOLD")).upper()
    if decision not in ("BUY_YES", "BUY_NO", "HOLD"):
        decision = "HOLD"
    try:
        confidence = float(parsed.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    try:
        suggested = float(parsed.get("suggested_usdc", 0.0))
    except (TypeError, ValueError):
        suggested = 0.0
    if suggested < 0:
        suggested = 0.0
    return {
        "decision": decision,
        "confidence": confidence,
        "reason": str(parsed.get("reason", "")),
        "suggested_usdc": suggested,
    }