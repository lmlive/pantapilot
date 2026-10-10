"""冒烟测试：在无真实 key 的情况下验证日志与看板渲染可用。"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from logger import JsonlLogger
from panta import normalize_status, market_to_prompt_block, _format_end_time

logger = JsonlLogger(Path(BASE) / "logs" / "smoke.jsonl")

# 清理旧文件
if logger.path.exists():
    logger.path.unlink()

# 写各 event
logger.start(mode="PAPER", market_count=3)
logger.analysis("m1", "Will team A win?", {"decision": "BUY_YES", "confidence": 0.72, "reason": "implied too low", "suggested_usdc": 3})
logger.analysis("m2", "Over/under goals", {"decision": "HOLD", "confidence": 0.4, "reason": "unclear", "suggested_usdc": 0})
logger.trade_dry_run("m1", "Will team A win?", {"quoteId": "q1"}, {"transaction": "dGVzdA=="})
logger.error("m3", "boom")

# 读回
recs = logger.read_all()
assert len(recs) == 5, f"expected 5 records, got {len(recs)}"
events = [r["event"] for r in recs]
assert events == ["start", "analysis", "analysis", "trade_dry_run", "error"], events
print("LOG_OK events=", events)

# normalize_status
assert normalize_status("primary") == "primary"
assert normalize_status("PRIMARY") == "primary"
assert normalize_status("Open") == "primary"
assert normalize_status("resolved") == "resolved"
assert normalize_status("CLOSED") == "resolved"
assert normalize_status("secondary") == "secondary"
print("STATUS_OK")

# _format_end_time
s = _format_end_time(1750000000)
assert s.endswith("UTC"), s
ms = _format_end_time(1750000000000)
assert ms.endswith("UTC"), ms
print("TIME_OK", s, ms)

# market_to_prompt_block
block = market_to_prompt_block({
    "title": "T", "description": "D" * 3000, "category": "Sports",
    "yesPrice": "0.5", "noPrice": "0.5", "volumeUsdc": "100",
    "endTime": 1750000000, "oracle": "pyth",
})
assert "Market: T" in block
assert len(block) < 2000  # description 被截断到 1200
print("PROMPT_OK")

# 渲染看板
import dashboard
dashboard.render_dashboard(logger, {"markets": 3, "analyzed": 2, "buy_signals": 1, "holds": 1})
html = (BASE / "dashboard" / "index.html").read_text(encoding="utf-8")
assert "Powered by" in html and "Panta" in html
assert "PantaPilot" in html
print("DASHBOARD_OK")

print("ALL_SMOKE_OK")