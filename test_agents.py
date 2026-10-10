"""离线单元测试：Agent 团队流水线 / Scout 纯函数 / LLM 解析工具。

运行方式（标准库 unittest，无新依赖，绝不联网）：

    cd /data/hack/pantapilot && .venv/bin/python -m unittest test_agents.py -v

隔离策略（测试中不发起任何真实网络 / LLM 调用）：
- agents.gather_intel 被 monkeypatch 为返回空情报 dict（避免抓 oracle URL / Brave 搜索）；
- AgentTeam._ask 被 monkeypatch 为按 system prompt 关键词返回固定 dict（不打真实 LLM key）；
- 降级路径中 team.fallback.analyze 被 mock 为返回固定 HOLD dict（不打单 agent LLM key）。
"""
from __future__ import annotations

import unittest

import agents
import scout
from llm import _normalize, _parse_json


def _fake_intel(market, enable_search: bool = True, **kwargs):
    """gather_intel 的离线替身：返回空情报包（管道不应因此死亡）。"""
    return {"queries": [], "oracleData": "", "searchIntel": "", "meta": {}}


# 固定的各步 LLM 返回（真实 LLM 永远不会被调用）
FIXED_ESTIMATOR = {
    "true_prob_yes": 0.72,
    "confidence": 0.8,
    "key_evidence": "- test evidence",
    "uncertainty": "low",
}
FIXED_DECISION = {
    "decision": "BUY_YES",
    "confidence": 0.7,
    "reason": "estimator edge vs implied prob",
    "suggested_usdc": 2.0,
}
FIXED_RISK_APPROVED = {"final": "BUY_YES", "approved": True, "note": "ok"}
FIXED_RISK_VETO = {"final": "HOLD", "approved": False, "note": "weak"}

MARKET = {"status": "open", "volumeUsdc": 1000, "title": "Test market"}
MARKET_TEXT = "Test market: Will X happen? YES 0.45 / NO 0.55"


def _fixed_ask(system: str, user: str, *, risk=FIXED_RISK_APPROVED):
    """按 system prompt 关键词分发到对应固定返回（与 AgentTeam._ask 同签名，缺省 self）。"""
    low = system.lower()
    if "probability estimator" in low:
        return dict(FIXED_ESTIMATOR)
    if "prediction-market trader" in low:
        return dict(FIXED_DECISION)
    if "risk manager" in low:
        return dict(risk)
    raise AssertionError(f"unexpected system prompt: {system[:80]!r}")


class _AskPatchedTestCase(unittest.TestCase):
    """基类：setUp 记录原始 _ask/gather_intel，teardown 必然还原（不影响其它测试）。"""

    def setUp(self):
        self._orig_ask = agents.AgentTeam._ask
        self._orig_gather = agents.gather_intel
        agents.gather_intel = _fake_intel  # 隔离：绝不真实抓 oracle/Brave

    def tearDown(self):
        agents.AgentTeam._ask = self._orig_ask
        agents.gather_intel = self._orig_gather

    def make_team(self) -> agents.AgentTeam:
        return agents.AgentTeam()


# ---------------------------------------------------------------------------
# 1) 各步固定 JSON：流程正确、pipeline 正确
# ---------------------------------------------------------------------------
class TestPipelineHappyPath(_AskPatchedTestCase):
    def test_full_pipeline_decision_buy_yes(self):
        agents.AgentTeam._ask = lambda self, system, user: _fixed_ask(system, user)
        team = self.make_team()

        result = team.analyze(MARKET, MARKET_TEXT, enable_search=False)

        self.assertEqual(result["decision"], "BUY_YES")
        self.assertAlmostEqual(result["confidence"], 0.7)
        self.assertEqual(result["evidence"]["pipeline"], "scout>estimator>decision>risk")
        # 证据链：estimator 与 risk 的原始返回被保留
        self.assertEqual(result["evidence"]["estimator"], FIXED_ESTIMATOR)
        self.assertEqual(result["evidence"]["risk"], FIXED_RISK_APPROVED)
        # _slim_intel 截断后的 intel 结构存在（空情报也不致死）
        self.assertIn("oracle_head", result["evidence"]["intel"])

    def test_risk_approved_keeps_decision(self):
        agents.AgentTeam._ask = lambda self, system, user: _fixed_ask(system, user)
        team = self.make_team()

        result = team.analyze(MARKET, MARKET_TEXT, enable_search=True)

        self.assertEqual(result["decision"], "BUY_YES")
        self.assertNotIn("[risk veto]", result["reason"])
        self.assertEqual(result["evidence"]["pipeline"], "scout>estimator>decision>risk")


# ---------------------------------------------------------------------------
# 2) risk veto：approved=false 把 BUY_YES 改成 HOLD，reason 带 [risk veto]
# ---------------------------------------------------------------------------
class TestRiskVeto(_AskPatchedTestCase):
    def test_veto_downgrades_buy_to_hold(self):
        agents.AgentTeam._ask = lambda self, system, user: _fixed_ask(
            system, user, risk=FIXED_RISK_VETO
        )
        team = self.make_team()

        result = team.analyze(MARKET, MARKET_TEXT)

        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("[risk veto]", result["reason"])
        self.assertIn("weak", result["reason"])  # veto note 被保留
        self.assertEqual(result["evidence"]["pipeline"], "scout>estimator>decision>risk")
        self.assertEqual(result["evidence"]["risk"], FIXED_RISK_VETO)


# ---------------------------------------------------------------------------
# 3) 降级：_ask 全部返回 None → fallback_single_agent（mock fallback.analyze 隔离网络）
# ---------------------------------------------------------------------------
class TestFallback(_AskPatchedTestCase):
    def test_all_none_falls_back_to_single_agent(self):
        agents.AgentTeam._ask = lambda self, system, user: None
        team = self.make_team()
        # mock 单 agent 兜底，绝不打真实 LLM key
        team.fallback.analyze = lambda market_text, user_hint="": {
            "decision": "HOLD",
            "confidence": 0.0,
            "reason": "LLM analysis failed",
            "suggested_usdc": 0.0,
        }

        result = team.analyze(MARKET, MARKET_TEXT)

        self.assertEqual(result["evidence"]["pipeline"], "fallback_single_agent")
        self.assertEqual(result["decision"], "HOLD")
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["suggested_usdc"], 0.0)
        # 降级返回仍带 intel 截断（日志/看板兼容）
        self.assertIn("intel", result["evidence"])

    def test_estimator_none_decision_ok_still_runs_risk(self):
        # est=None 时 Decision 仍执行（intel 文本直喂），管道不死
        def partial_ask(self, system, user):
            low = system.lower()
            if "probability estimator" in low:
                return None
            return _fixed_ask(system, user)

        agents.AgentTeam._ask = partial_ask
        team = self.make_team()

        result = team.analyze(MARKET, MARKET_TEXT)

        self.assertEqual(result["decision"], "BUY_YES")
        self.assertIsNone(result["evidence"]["estimator"])
        self.assertEqual(result["evidence"]["pipeline"], "scout>estimator>decision>risk")


# ---------------------------------------------------------------------------
# 4) scout 纯函数
# ---------------------------------------------------------------------------
class TestScoutPureFunctions(unittest.TestCase):
    def test_build_queries_from_title(self):
        queries = scout._build_queries("Haaland 8+ points, GW6", "sports")
        self.assertIsInstance(queries, list)
        self.assertGreater(len(queries), 0)
        self.assertTrue(all(isinstance(q, str) and q for q in queries))

    def test_build_queries_short_title_returns_empty(self):
        self.assertEqual(scout._build_queries("", "sports"), [])
        self.assertEqual(scout._build_queries("hi", "sports"), [])
        self.assertEqual(scout._build_queries("ab", ""), [])

    def test_summarize_empty_intel(self):
        text = scout.summarize_for_prompt({})
        self.assertIn("(No external intel", text)

    def test_summarize_with_oracle_data_mentions_oracle(self):
        text = scout.summarize_for_prompt({"oracleData": "Haaland: 9 pts at 60'"})
        self.assertIn("ORACLE", text)
        self.assertIn("Haaland: 9 pts at 60'", text)


# ---------------------------------------------------------------------------
# 5) 兼容：_parse_json / _normalize
# ---------------------------------------------------------------------------
class TestLLMHelpers(unittest.TestCase):
    def test_parse_json_fenced_block(self):
        parsed = _parse_json('```json\n{"decision": "HOLD", "confidence": 0.5}\n```')
        self.assertEqual(parsed, {"decision": "HOLD", "confidence": 0.5})

    def test_parse_json_plain_text_returns_none(self):
        self.assertIsNone(_parse_json("I am not confident about this market at all."))

    def test_parse_json_embedded_object(self):
        parsed = _parse_json('Sure! Here you go: {"decision": "BUY_NO", "confidence": 0.6}')
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["decision"], "BUY_NO")

    def test_normalize_clips_confidence(self):
        out = _normalize({"decision": "BUY_YES", "confidence": 3.5, "reason": "edge"})
        self.assertEqual(out["confidence"], 1.0)
        out = _normalize({"decision": "BUY_YES", "confidence": -2.0, "reason": "edge"})
        self.assertEqual(out["confidence"], 0.0)

    def test_normalize_invalid_decision_becomes_hold(self):
        out = _normalize({"decision": "MAYBE", "confidence": 0.5, "reason": "?"})
        self.assertEqual(out["decision"], "HOLD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
