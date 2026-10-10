"""Lead 验收：证据链渲染（含 XSS 转义与旧日志兼容）。"""
from __future__ import annotations

import html as html_mod
from pathlib import Path

import dashboard
from logger import JsonlLogger

PIPELINE = "scout>estimator>decision>risk"
PIPELINE_ESCAPED = html_mod.escape(PIPELINE)

log_p = Path("logs/evidence_check.jsonl")
log_p.unlink(missing_ok=True)
lg = JsonlLogger(log_p)

lg.start("PAPER", 1)
lg.analysis(
    "m1",
    "Test market",
    {
        "decision": "HOLD",
        "confidence": 0.0,
        "reason": "[risk veto] low volume / original: no edge",
        "suggested_usdc": 0.0,
        "evidence": {
            "pipeline": PIPELINE,
            "estimator": {
                "true_prob_yes": 0.6,
                "confidence": 0.4,
                "key_evidence": "oracle says <b>hot</b>",
                "uncertainty": "medium",
            },
            "risk": {"final": "HOLD", "approved": False, "note": "low volume"},
            "intel": {
                "queries": ["test q"],
                "oracle_head": "<script>alert(1)</script>head",
                "search_head": "",
                "meta": {},
            },
        },
    },
)
lg.analysis("m2", "Old format", {"decision": "BUY_YES", "confidence": 0.7, "reason": "legacy", "suggested_usdc": 2})

dashboard.render_dashboard(lg, {"markets": 1, "analyzed": 2, "buy_signals": 1, "holds": 1})
html = Path("dashboard/index.html").read_text(encoding="utf-8")

checks = {
    "ev- class": 'class="ev"' in html or "ev-pipe" in html,
    "est YES 0.60": "YES 0.60" in html,
    "pipeline shown (html-escaped)": PIPELINE_ESCAPED in html,
    "pipeline raw not injected": PIPELINE not in html,
    "RISK VETO badge": "RISK VETO" in html,
    "key_evidence present": "key_evidence" in html,
    "b tag escaped": "<b>hot</b>" not in html,
    "script escaped": "<script>alert(1)</script>" not in html,
    "legacy renders": "Old format" in html,
    "Powered by Panta": "Powered by" in html and "Panta" in html,
    "meta refresh 60": 'http-equiv="refresh" content="60"' in html,
}
for k, v in checks.items():
    print(("PASS" if v else "FAIL"), k)
print("ALL_PASS" if all(checks.values()) else "HAS_FAILURE")

log_p.unlink(missing_ok=True)
