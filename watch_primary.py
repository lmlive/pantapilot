"""Watch Panta for a newly tradeable primary market.

Context: the venue had 0 primary markets on the evening of 2026-10-12, which
blocks recording the demo (main.py only analyses primary markets, correctly -
they are the only tradeable ones). Rather than editing that filter, wait for the
venue to list one.

This polls read-only, prints a transition line the first time a market appears,
and exits 0 on success so it can be chained. It never places or builds an order.

Usage:
    .venv/bin/python watch_primary.py              # poll every 60s, run until found
    .venv/bin/python watch_primary.py --once       # single check, exit 0/1
    .venv/bin/python watch_primary.py --interval 30 --timeout 3600
"""
from __future__ import annotations

import argparse
import sys
import time

import config  # noqa: F401  (loads .env)
from panta import PantaClient


def snapshot() -> list[dict]:
    return PantaClient().primary_markets()


def venue_summary() -> str:
    """One line describing what the venue holds right now.

    A bare "0 primary markets" is ambiguous - it reads the same whether the venue
    is about to list one or has nothing but settled markets. Showing the breakdown
    makes it obvious which situation you are waiting on.
    """
    try:
        mk = PantaClient().list_markets()
    except Exception as exc:  # noqa: BLE001
        return f"(market list unavailable: {type(exc).__name__})"
    if not mk:
        return "(venue returned no markets)"
    import collections

    counts = collections.Counter(str(m.get("status")) for m in mk)
    parts = ", ".join(f"{v} {k}" for k, v in counts.most_common())
    return f"{len(mk)} markets total ({parts})"


def describe(markets: list[dict]) -> str:
    lines = []
    for m in markets:
        yes = m.get("yesPrice")
        vol = m.get("volumeUsdc")
        lines.append(f"    - {str(m.get('title'))[:62]}")
        lines.append(f"      yes={yes} vol={vol} status={m.get('status')}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60, help="seconds between polls")
    ap.add_argument("--timeout", type=int, default=0, help="give up after N seconds (0 = forever)")
    ap.add_argument("--once", action="store_true", help="check once and exit")
    args = ap.parse_args()

    started = time.monotonic()
    attempt = 0

    while True:
        attempt += 1
        stamp = time.strftime("%H:%M:%S")
        try:
            markets = snapshot()
        except Exception as exc:  # noqa: BLE001
            print(f"[{stamp}] poll failed: {type(exc).__name__}: {str(exc)[:120]}", flush=True)
            markets = []

        if markets:
            print(f"[{stamp}] FOUND {len(markets)} tradeable primary market(s):", flush=True)
            print(describe(markets), flush=True)
            print(flush=True)
            print("Ready to record. Start the run with:", flush=True)
            print("  cd /data/hack/pantapilot && DRY_RUN=true .venv/bin/python main.py", flush=True)
            return 0

        print(f"[{stamp}] attempt {attempt}: 0 primary markets | {venue_summary()}", flush=True)

        if args.once:
            return 1

        if args.timeout and (time.monotonic() - started) >= args.timeout:
            print(f"gave up after {args.timeout}s with no primary market", flush=True)
            return 1

        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
