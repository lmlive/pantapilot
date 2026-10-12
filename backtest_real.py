"""Real-market backtest (honest traction evidence).

Earlier `backtest.py` iterated a hand-authored SAMPLE_RESOLVED_MARKETS list whose
outcomes were written to match its own decisions, producing a 100% win rate. That
is not evidence. This module instead pulls REAL settled markets from the live Panta
API and evaluates the strategy against them.

What the Panta API actually exposes for a settled market (verified 2026-10-12):
  - yesPrice / noPrice          -> settlement payoff (1 or 0), NOT the entry odds
  - lastYesPrice                -> the real last traded YES price before resolution
  - priceSource = 'resolved_outcome'
  - totalYesVolume/totalNoVolume -> real traded volume per side

So "what would the strategy have done" is answerable at the level of:
  entry price (lastYesPrice) + realised outcome (yesPrice==1 ? YES : NO).

Honest limitations (reported in the output, not hidden):
  * lastYesPrice is the LAST price, not the price at any earlier decision time.
    A live agent decides earlier, so this is an upper-bound-quality proxy, not a
    tick-accurate simulation.
  * The strategy is applied as a fixed threshold rule over the market's own
    informational state; it is NOT a re-run of the LLM at historical time T
    (the LLM was not running then and no historical price series is exposed).
    This measures whether the edge-threshold discipline would have selected
    favourable markets -- it is NOT a claim of realised trading profit.

Usage:  .venv/bin/python backtest_real.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import config  # noqa: E402
from panta import PantaClient  # noqa: E402

# Strategy parameters (mirror the live guardrails).
MIN_VOLUME_USDC = 10.0
BET_USDC = 2.0


def _f(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def collect_resolved(client: PantaClient, limit: int | None = None) -> list[dict[str, Any]]:
    """Pull settled markets and extract the real pre-resolution odds + outcome."""
    rows: list[dict[str, Any]] = []
    for m in client.list_markets():
        if not m.get("resolved"):
            continue
        mid = m.get("marketId")
        title = (m.get("title") or "").strip()
        if not mid or not title:
            continue  # untitled/draft markets carry no signal
        # Detail is authoritative for lastYesPrice.
        try:
            detail = client.market_detail(mid)
        except Exception:  # noqa: BLE001
            continue
        entry = _f(detail.get("lastYesPrice"))
        settle_yes = _f(detail.get("yesPrice"))
        # NOTE: for settled markets the LIST endpoint reports volumeUsdc=0.00 while
        # market_detail carries the true traded volume in totalVolumeUsdc.
        vol = _f(detail.get("totalVolumeUsdc"))
        if vol is None:
            vol = _f(detail.get("volumeUsdc")) or 0.0
        if entry is None or settle_yes is None:
            continue
        # lastYesPrice arrives either as 0-1 decimal or as integer-scaled 1e9.
        if entry > 1.0:
            entry = entry / 1e9
        if not (0.0 < entry < 1.0):
            continue
        rows.append(
            {
                "marketId": mid,
                "title": title,
                "category": detail.get("category"),
                "entry_yes": entry,
                "outcome": "YES" if settle_yes >= 0.5 else "NO",
                "volume_usdc": vol,
                "oracle": detail.get("oracle"),
            }
        )
        if limit and len(rows) >= limit:
            break
    return rows


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the live strategy's selection rule to settled markets.

    Rule (matches the Decision prompt in agents.py): trade only when the gap between
    market price and fair value is > 15%; otherwise HOLD. Here the live
    'mispricing' proxy is the deviation of entry_yes from 0.5, and a volume floor
    mirrors the Risk agent's liquidity veto.
    """
    trades: list[dict[str, Any]] = []
    passes: list[dict[str, Any]] = []
    for r in rows:
        entry = r["entry_yes"]
        deviation = abs(entry - 0.5)
        if r["volume_usdc"] < MIN_VOLUME_USDC:
            passes.append({**r, "pass_reason": "illiquid"})
            continue
        if deviation < 0.10:
            passes.append({**r, "pass_reason": "no_material_edge"})
            continue  # no material edge -> disciplined pass (HOLD)
        # Fade the deviation: if price is rich (entry>0.5) the model's edge is on NO.
        side = "NO" if entry > 0.5 else "YES"
        price_paid = (1.0 - entry) if side == "NO" else entry
        won = r["outcome"] == side
        shares = BET_USDC / price_paid if price_paid > 0 else 0.0
        payout = shares if won else 0.0
        trades.append(
            {
                **r,
                "side": side,
                "price_paid": round(price_paid, 4),
                "won": won,
                "pnl_usdc": round(payout - BET_USDC, 4),
            }
        )

    n = len(trades)
    wins = sum(1 for t in trades if t["won"])
    invested = BET_USDC * n
    pnl = sum(t["pnl_usdc"] for t in trades)
    devs = [abs(r["entry_yes"] - 0.5) for r in rows]
    return {
        "settled_markets_seen": len(rows),
        "actionable_trades": n,
        "skipped_no_edge_or_illiquid": len(rows) - n,
        "wins": wins,
        "losses": n - wins,
        "win_rate_pct": round(wins / n * 100, 1) if n else 0.0,
        "invested_usdc": round(invested, 2),
        "net_pnl_usdc": round(pnl, 2),
        "roi_pct": round(pnl / invested * 100, 1) if invested else 0.0,
        "max_entry_deviation_from_050": round(max(devs), 4) if devs else None,
        "trades": trades,
        "passes": passes,
    }


def main() -> int:
    print("=" * 78)
    print(" PantaPilot — Real-Market Backtest (live Panta API, no hand-authored data)")
    print("=" * 78)

    client = PantaClient()
    try:
        rows = collect_resolved(client)
    finally:
        client.close()

    print(f"\nSettled markets with usable price+outcome: {len(rows)}")
    if not rows:
        print("No usable settled markets returned by the API right now.")
        return 0

    res = evaluate(rows)
    print(f"Actionable (edge >= 0.10, volume >= {MIN_VOLUME_USDC} USDC): "
          f"{res['actionable_trades']}")
    print(f"Disciplined passes: {res['skipped_no_edge_or_illiquid']}\n")

    for t in res["trades"][:15]:
        mark = "WIN " if t["won"] else "LOSS"
        print(f"  [{mark}] {t['title'][:48]:48s} entry={t['entry_yes']:.3f} "
              f"side={t['side']:3s} vol={t['volume_usdc']:8.2f} pnl={t['pnl_usdc']:+.2f}")

    if not res["trades"]:
        print("  (no market cleared the edge + liquidity bar)")
        print(f"\n  Observed settled markets (entry = last traded YES price):")
        for p in sorted(res["passes"], key=lambda x: -x["volume_usdc"])[:12]:
            dev = abs(p["entry_yes"] - 0.5)
            print(f"    entry={p['entry_yes']:.4f} dev={dev:.4f} "
                  f"vol={p['volume_usdc']:8.2f} out={p['outcome']:3s} "
                  f"({p['pass_reason']}) {p['title'][:36]}")

    print("\n" + "=" * 78)
    print(f" Win Rate: {res['win_rate_pct']}%  ({res['wins']}W / {res['losses']}L)")
    print(f" Invested: {res['invested_usdc']} USDC   Net PnL: {res['net_pnl_usdc']:+.2f} USDC"
          f"   ROI: {res['roi_pct']:+.1f}%")
    print(f" Max |entry - 0.50| observed: {res['max_entry_deviation_from_050']}")
    print("=" * 78)
    print("\nCAVEATS (state these to judges; do not present this as realised profit):")
    print("  * entry = lastYesPrice (last traded price), not the price at decision time.")
    print("  * strategy applied as a fixed threshold rule, not a historical LLM re-run.")
    print("  * settled outcome is binary; no fees/slippage modelled beyond price paid.")

    out = BASE / "demo_capture" / "backtest_real.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
