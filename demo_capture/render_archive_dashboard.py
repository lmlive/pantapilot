"""Render the dashboard from an archived log, without touching the live one.

Workflow:
  1. point LOG_FILE at the archive
  2. render
  3. restore LOG_FILE to the live path

Used to build the dashboard shots for the demo video from the same run that the
terminal recording captured. Read-only with respect to market data (it fetches
the venue list for the market cards but places no orders).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # repo root, not demo_capture/
ARCHIVE = BASE / "logs" / "pre-recording-20261012-201344.jsonl"
LIVE = BASE / "logs" / "pantapilot.jsonl"
SHOT = BASE / "dashboard" / "_archive_index.html"


def main() -> int:
    if not ARCHIVE.exists():
        print(f"missing archive: {ARCHIVE}")
        return 1

    # Render into a copy of the archive so the original is never mutated.
    scratch = BASE / "logs" / "_render_scratch.jsonl"
    shutil.copyfile(ARCHIVE, scratch)

    os.environ["LOG_FILE"] = str(scratch)
    for mod in [m for m in list(sys.modules) if m in ("config", "logger", "dashboard", "panta")]:
        del sys.modules[mod]
    sys.path.insert(0, str(BASE))

    import config  # noqa: E402
    import dashboard  # noqa: E402
    from logger import JsonlLogger  # noqa: E402
    from panta import PantaClient  # noqa: E402

    print(f"LOG_FILE in effect: {config.LOG_FILE}")

    logger = JsonlLogger()
    records = logger.read_all()
    analyses = [r for r in records if r.get("event") == "analysis"]
    holds = [r for r in analyses if (r.get("decision") or {}).get("decision") == "HOLD"]
    buys = [
        r for r in analyses
        if (r.get("decision") or {}).get("decision") in ("BUY_YES", "BUY_NO")
    ]
    trades = [r for r in records if r.get("event") in ("trade_dry_run", "trade_live")]

    stats = {
        "markets": len({r.get("marketId") for r in analyses if r.get("marketId")}),
        "analyzed": len(analyses),
        "buy_signals": len(buys),
        "holds": len(holds),
        "trades": len(trades),
    }
    print(f"stats: {stats}")

    try:
        markets = PantaClient().primary_markets()
    except Exception as exc:  # noqa: BLE001
        print(f"market fetch failed ({type(exc).__name__}); rendering without cards")
        markets = []

    dashboard.render_dashboard(logger, stats, markets=markets)

    rendered = BASE / "dashboard" / "index.html"
    if rendered.exists():
        shutil.copyfile(rendered, SHOT)
        print(f"dashboard rendered -> {SHOT.relative_to(BASE)}")
    else:
        print("render produced no dashboard/index.html")
        return 1

    scratch.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
