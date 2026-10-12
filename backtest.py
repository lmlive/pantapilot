"""Illustrative walkthrough on a SAMPLE portfolio — NOT traction evidence (P2 回测统计).

⚠️  READ THIS BEFORE CITING ANY NUMBER FROM THIS FILE.
The list below is hand-authored: each entry's `oracleOutcome` was written by hand to
match its own `decision`, and no Panta API call is made anywhere in this module
(`PantaClient` is imported but unused). It therefore trivially reports a 100% win rate
and is NOT a measurement of the strategy.

For the honest, data-backed version that pulls real settled markets from the live Panta
API and reports the real (currently null) result, run:

    .venv/bin/python backtest_real.py

Keep this file only as a readable illustration of how a settled market maps to a P&L.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import config
from panta import PantaClient, normalize_status

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("pantapilot.backtest")

# 典型历史样本基准数据（用于离线演示与基准验证）
SAMPLE_RESOLVED_MARKETS = [
    {
        "marketId": "hist-cs2-navi-faze",
        "title": "CS2 Major Final: NAVI vs FaZe - NAVI Wins?",
        "initialYesPrice": 0.42,
        "initialNoPrice": 0.58,
        "volumeUsdc": 14200.0,
        "oracleOutcome": "YES",  # 实际 NAVI 获胜
        "scoutIntel": "NAVI in top form, 14-game win streak on Mirage; FaZe playing with recent roster sub.",
        "trueProbYes": 0.65,
        "decision": "BUY_YES",
        "confidence": 0.78,
    },
    {
        "marketId": "hist-nba-celtics-heat",
        "title": "NBA Eastern Finals G7: Celtics vs Heat - Celtics Win?",
        "initialYesPrice": 0.68,
        "initialNoPrice": 0.32,
        "volumeUsdc": 28900.0,
        "oracleOutcome": "YES",  # 实际 Celtics 获胜
        "scoutIntel": "Starting lineup healthy at home; implied probability 68% fairly matches 70% model estimate.",
        "trueProbYes": 0.70,
        "decision": "HOLD",  # 价差仅 2%，不足 15%，纪律性放弃
        "confidence": 0.45,
    },
    {
        "marketId": "hist-dota2-ti-gl",
        "title": "Dota 2 TI Semifinal: Team Spirit vs Gaimin Gladiators - Spirit Wins?",
        "initialYesPrice": 0.35,
        "initialNoPrice": 0.65,
        "volumeUsdc": 9600.0,
        "oracleOutcome": "YES",  # 实际 Spirit 获胜
        "scoutIntel": "Official patch notes favor late-game drafts where Spirit maintains 88% winrate this season.",
        "trueProbYes": 0.58,
        "decision": "BUY_YES",
        "confidence": 0.74,
    },
    {
        "marketId": "hist-premier-league-mci",
        "title": "Premier League: Man City vs Arsenal - Arsenal Wins?",
        "initialYesPrice": 0.55,
        "initialNoPrice": 0.45,
        "volumeUsdc": 35000.0,
        "oracleOutcome": "NO",  # 实际 City 获胜（Arsenal 输）
        "scoutIntel": "Arsenal key defender injured in pre-match warm-up; implied YES price 55% heavily overvalued.",
        "trueProbYes": 0.32,
        "decision": "BUY_NO",  # 发现高估，做空 BUY_NO
        "confidence": 0.82,
    },
]


def run_backtest(markets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = markets or SAMPLE_RESOLVED_MARKETS
    total = len(items)
    trades = 0
    wins = 0
    losses = 0
    holds = 0
    total_invested_usdc = 0.0
    total_return_usdc = 0.0

    print("=" * 68)
    print(" 📊 PantaPilot Historical Backtest & Mispricing Capture Report")
    print("=" * 68)

    for m in items:
        m_id = m.get("marketId", "")
        title = m.get("title", "")
        init_yes = float(m.get("initialYesPrice", 0.5))
        est_prob = float(m.get("trueProbYes", 0.5))
        outcome = m.get("oracleOutcome", "UNKNOWN")
        dec = m.get("decision", "HOLD")
        conf = float(m.get("confidence", 0.0))
        edge = (est_prob - init_yes) * 100

        print(f"\n[Market] {title}")
        print(f"  • Odds Implied: {init_yes*100:.1f}% | Agent Estimate: {est_prob*100:.1f}% | Edge: {edge:+.1f}%")
        print(f"  • Decision: {dec} (Conf {conf:.2f}) | Resolved Outcome: {outcome}")

        if dec in ("BUY_YES", "BUY_NO"):
            trades += 1
            bet_size = 2.0  # 默认 2 USDC
            total_invested_usdc += bet_size

            # 计算收益
            is_win = (dec == "BUY_YES" and outcome == "YES") or (dec == "BUY_NO" and outcome == "NO")
            if is_win:
                wins += 1
                price_paid = init_yes if dec == "BUY_YES" else (1.0 - init_yes)
                payout = bet_size / price_paid if price_paid > 0 else bet_size
                net_profit = payout - bet_size
                total_return_usdc += payout
                print(f"  ➔ RESULT: WIN (+{net_profit:.2f} USDC, ROI +{net_profit/bet_size*100:.1f}%)")
            else:
                losses += 1
                print(f"  ➔ RESULT: LOSS (-{bet_size:.2f} USDC)")
        else:
            holds += 1
            print("  ➔ RESULT: PASS (No sufficient edge, disciplined preservation)")

    net_pnl = total_return_usdc - total_invested_usdc
    win_rate = (wins / trades * 100) if trades > 0 else 0.0
    roi = (net_pnl / total_invested_usdc * 100) if total_invested_usdc > 0 else 0.0

    summary = {
        "total_markets": total,
        "trades_executed": trades,
        "holds": holds,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(win_rate, 1),
        "total_invested_usdc": round(total_invested_usdc, 2),
        "net_pnl_usdc": round(net_pnl, 2),
        "roi_pct": round(roi, 1),
    }

    print("\n" + "=" * 68)
    print(f" 🏆 SUMMARY: {wins} Wins / {losses} Losses | Win Rate: {win_rate:.1f}%")
    print(f" 💰 Total Bet: {total_invested_usdc:.2f} USDC | Net Profit: {net_pnl:+.2f} USDC | ROI: {roi:+.1f}%")
    print("=" * 68)
    return summary


if __name__ == "__main__":
    run_backtest()
