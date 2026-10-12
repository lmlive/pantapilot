"""Live demo capture: run the real pipeline and record the session for the demo video.

Writes a clean, verbatim transcript to demo_capture/run_transcript.txt
Dispatches per-market progress lines to stderr so the recording shows the
four-agent pipeline actually working (not a frozen log replay).

Usage:
    .venv/bin/python run_demo_capture.py 2>&1 | tee demo_capture/run_transcript.txt
"""
from __future__ import annotations

import io
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

OUT_DIR = BASE / "demo_capture"
OUT_DIR.mkdir(exist_ok=True)

import config  # noqa: E402  (imports after sys.path setup)
from dashboard import render_dashboard  # noqa: E402
from llm import LLMDecisionEngine  # noqa: E402
from logger import JsonlLogger  # noqa: E402
from main import select_demo_markets  # noqa: E402
from agents import AgentTeam  # noqa: E402
from panta import PantaClient, market_to_prompt_block  # noqa: E402
from trader import Trader  # noqa: E402

# Separate, dated log file so the recording is self-contained and reproducible.
RUN_LOG = OUT_DIR / "run.jsonl"
if RUN_LOG.exists():
    RUN_LOG.unlink()

config.LOG_FILE = RUN_LOG


def narrate(msg: str) -> None:
    """Progress line for the on-camera terminal (stderr, unbuffered)."""
    print(msg, file=sys.stderr, flush=True)


def main() -> int:
    narrate("=" * 78)
    narrate(" PantaPilot — LIVE RUN  |  4-Agent Trading Desk on Panta Prediction Markets")
    narrate(f" mode=DRY_RUN(paper)  max_trade={config.MAX_TRADE_USDC} USDC  "
            f"min_confidence={config.MIN_CONFIDENCE}")
    narrate("=" * 78)

    client = PantaClient()
    logger = JsonlLogger(RUN_LOG)
    llm = LLMDecisionEngine()
    trader = Trader(client, logger)
    team = AgentTeam() if config.AGENTS_ENABLED else None

    # ---- 1. Market scan (real Panta API) --------------------------------
    narrate("\n[1/3] Scanning live Panta markets ...")
    try:
        markets = client.primary_markets()
    except Exception as exc:  # noqa: BLE001 - demo must not die
        narrate(f"  !! market scan failed: {exc}")
        return 1

    narrate(f"  -> {len(markets)} primary (tradeable) markets returned by Panta API")
    picked = select_demo_markets(markets, config.DEMO_MARKET_LIMIT)
    narrate(f"  -> curated {len(picked)} high-signal markets for this session")

    logger.start(mode="PAPER", market_count=len(picked))

    # ---- 2. Four-agent pipeline -----------------------------------------
    narrate("\n[2/3] Running Scout -> Estimator -> Decision -> Risk on each market")
    stats = {"markets": len(picked), "analyzed": 0, "buy_signals": 0, "holds": 0, "trades": 0}

    for i, m in enumerate(picked, 1):
        title = str(m.get("title") or "")[:70]
        narrate(f"\n  [{i}/{len(picked)}] {title}")
        try:
            text = market_to_prompt_block(m)
            narrate("        Scout    : gathering oracle + web intel ...")
            if team is not None:
                decision = team.analyze(m, text, enable_search=config.SCOUT_SEARCH_ENABLED)
            else:
                decision = llm.analyze(text)
        except Exception as exc:  # noqa: BLE001 - single market failure must not break loop
            narrate(f"        !! analysis error: {exc}")
            continue

        stats["analyzed"] += 1
        dec = decision.get("decision", "HOLD")
        conf = float(decision.get("confidence") or 0.0)
        ev = decision.get("evidence") or {}
        est = ev.get("estimator") or {}
        bm = ev.get("benchmark") or {}
        risk = ev.get("risk") or {}
        if est:
            narrate(f"        Estimator: true_prob_yes={est.get('true_prob_yes')} "
                    f"(confidence {est.get('confidence')})")
        if bm:
            narrate(f"        Benchmark: market {bm.get('market_implied')} vs model "
                    f"{bm.get('estimator_prob')}  edge={bm.get('gap_pct')}")
        narrate(f"        Decision : {dec}  (confidence {conf:.2f})")
        if risk:
            narrate(f"        Risk     : approved={risk.get('approved')} -- "
                    f"{str(risk.get('note') or '')[:80]}")

        if dec in ("BUY_YES", "BUY_NO"):
            stats["buy_signals"] += 1
        else:
            stats["holds"] += 1

        logger.analysis(m.get("marketId", ""), m.get("title", ""), decision)
        narrate(f"        => {dec}  (confidence {conf:.2f})")

        if dec in ("BUY_YES", "BUY_NO") and conf >= config.MIN_CONFIDENCE:
            try:
                res = trader.execute(m, decision)
                if res.get("ok"):
                    stats["trades"] += 1
                    narrate(f"        Panta    : quote -> build OK, stage={res.get('stage')} "
                            f"(paper mode: not broadcast)")
            except Exception as exc:  # noqa: BLE001
                narrate(f"        !! order path error (handled): {exc}")

    # ---- 3. Dashboard ---------------------------------------------------
    narrate("\n[3/3] Rendering dashboard ...")
    buf = io.StringIO()
    with redirect_stdout(buf):
        render_dashboard(logger, stats, markets=picked)
    narrate(f"  -> dashboard/index.html  ({stats['analyzed']} decisions, "
            f"{stats['buy_signals']} BUY signals, {stats['holds']} HOLD)")

    narrate("\n" + "=" * 78)
    narrate(f" SUMMARY  markets={stats['markets']}  analyzed={stats['analyzed']}  "
            f"buy={stats['buy_signals']}  hold={stats['holds']}  trades={stats['trades']}")
    narrate(f" log={RUN_LOG.name}   paper mode: no funds at risk")
    narrate("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
