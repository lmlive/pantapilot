"""Regenerate the dashboard HTML from the current JSONL log against the live
Panta market list, without placing any orders.

This is the same render path main.py uses, extracted so the dashboard can be
refreshed on demand for the demo recording.
"""
from __future__ import annotations

import logging
import sys

import config
from dashboard import render_dashboard
from logger import JsonlLogger
from panta import PantaClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def main() -> int:
    client = PantaClient()
    markets = client.primary_markets()
    logger = JsonlLogger()

    records = logger.read_all()
    analyses = [r for r in records if r.get("event") == "analysis"]
    holds = [r for r in analyses if (r.get("decision") or {}).get("decision") == "HOLD"]
    buys = [
        r for r in analyses
        if (r.get("decision") or {}).get("decision") in ("BUY_YES", "BUY_NO")
    ]

    stats = {
        "markets": len(markets),
        "analyzed": len(analyses),
        "buy_signals": len(buys),
        "holds": len(holds),
        "trades": 0,
    }
    print("stats:", stats)

    render_dashboard(logger, stats, markets=markets)
    print("dashboard rendered (DRY_RUN=%s)" % config.DRY_RUN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
