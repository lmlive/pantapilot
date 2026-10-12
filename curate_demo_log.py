"""Build a demo log containing ONLY entries backed by the live Panta API.

The dashboard reads logs/pantapilot.jsonl. That file accumulated entries from
three different sources over three days:

  * 2026-10-12  real runs against live-api.panta.market (BTC market)
  * 2026-10-11  hand-written sample markets that DO NOT exist on Panta
                (Premier League / NBA / Chess / CS2) - used as video filler
  * 2026-10-10  early smoke runs

Showing the synthetic ones next to real data would misrepresent the venue: a
judge who checks Panta finds exactly one tradeable market, not a sportsbook.

This script writes logs/pantapilot.jsonl containing only records whose market
id is present in the live API, and archives the original alongside it.

    python3 curate_demo_log.py            # dry run, prints what it would do
    python3 curate_demo_log.py --write    # actually rewrite the log
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import logging

from panta import PantaClient

logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

LOG = Path(__file__).with_name("logs") / "pantapilot.jsonl"


def load_records(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="rewrite the log in place")
    args = ap.parse_args()

    if not LOG.exists():
        print(f"no log at {LOG}")
        return 1

    client = PantaClient()
    live = client.primary_markets()
    live_ids = {
        str(m.get("marketId") or m.get("id") or "")
        for m in live
        if (m.get("marketId") or m.get("id"))
    }
    print(f"live Panta market ids ({len(live_ids)}): {sorted(live_ids)}")

    records = load_records(LOG)
    print(f"total records: {len(records)}")

    # Keep: non-analysis events from today, plus analyses whose market is real.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    kept: list[dict] = []
    dropped_titles: set[str] = set()
    fallback_count = 0
    full_pipeline_count = 0

    for r in records:
        ev = r.get("event")
        if ev == "analysis":
            mid = str(r.get("marketId") or "")
            if mid in live_ids:
                kept.append(r)
                pipeline = ((r.get("decision") or {}).get("evidence") or {}).get("pipeline")
                if pipeline == "fallback_single_agent":
                    fallback_count += 1
                elif pipeline == "scout>estimator>decision>risk":
                    full_pipeline_count += 1
            else:
                dropped_titles.add(str(r.get("title"))[:60])
            continue
        # start / trade events: keep only today's, so the demo shows one session
        if str(r.get("ts", "")).startswith(today):
            kept.append(r)

    print(f"keeping {len(kept)} records; dropping {len(dropped_titles)} synthetic markets:")
    for t in sorted(dropped_titles):
        print("   -", t)
    print()
    print(f"  full four-agent pipeline decisions : {full_pipeline_count}")
    print(f"  degraded single-agent decisions    : {fallback_count}")
    if fallback_count:
        print("  (degraded runs are kept and labelled; they must not be shown as consensus)")

    if not args.write:
        print("\n(dry run - pass --write to apply)")
        return 0

    backup = LOG.with_suffix(".jsonl.bak-"
                             + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
    shutil.copy2(LOG, backup)
    with LOG.open("w", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(kept)} records to {LOG}")
    print(f"original archived at {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
