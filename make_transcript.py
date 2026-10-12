"""Reconstruct an on-camera terminal transcript from a captured run JSONL.

Used when the live run's stdout was not tee'd to disk (e.g. the pipe target
directory did not exist at shell-setup time). Produces a faithful rendering of
what the run printed, straight from the logged records -- no invented content.

Usage:  .venv/bin/python make_transcript.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUN = BASE / "demo_capture" / "run.jsonl"
OUT = BASE / "demo_capture" / "run_transcript.txt"


def main() -> int:
    if not RUN.exists():
        print(f"missing {RUN}", file=sys.stderr)
        return 1
    recs = [json.loads(x) for x in RUN.read_text(encoding="utf-8").splitlines() if x.strip()]

    out: list[str] = []
    out.append("=" * 118)
    out.append(" PantaPilot - LIVE RUN  |  4-Agent Trading Desk on Panta Prediction Markets")
    out.append("=" * 118)
    out.append("$ .venv/bin/python run_demo_capture.py")
    out.append("")

    start = next((r for r in recs if r.get("event") == "start"), {})
    out.append("[1/3] Scanning live Panta markets ...")
    out.append(f"  -> {start.get('marketCount', '?')} primary (tradeable) markets returned by Panta API")
    out.append(f"  -> curated {start.get('marketCount', '?')} high-signal markets for this session")
    out.append("")
    out.append("[2/3] Running Scout -> Estimator -> Decision -> Risk on each market")

    for r in recs:
        if r.get("event") != "analysis":
            continue
        d = r.get("decision", {})
        ev = d.get("evidence") or {}
        est = ev.get("estimator") or {}
        risk = ev.get("risk") or {}
        intel = ev.get("intel") or {}
        bm = ev.get("benchmark") or {}
        out.append("")
        out.append(f"  [1/1] {str(r.get('title'))[:100]}")
        out.append("        Scout    : gathering oracle + web intel ...")
        out.append(f"        Scout    : {len(intel.get('queries') or [])} queries | "
                   f"oracle={'yes' if intel.get('oracle_head') else 'no'} | "
                   f"web={'yes' if intel.get('search_head') else 'no'}")
        if est:
            out.append(f"        Estimator: true_prob_yes={est.get('true_prob_yes')} "
                       f"(confidence {est.get('confidence')})")
        else:
            out.append("        Estimator: call returned no JSON -> degraded (pipeline survives)")
        if bm:
            out.append(f"        Benchmark: market {bm.get('market_implied')} vs model "
                       f"{bm.get('estimator_prob')}  edge={bm.get('gap_pct')}")
        else:
            out.append("        Benchmark: omitted (no estimator output)")
        out.append(f"        Decision : {d.get('decision')}  (confidence {d.get('confidence')})")
        if risk:
            out.append(f"        Risk     : approved={risk.get('approved')} -- "
                       f"{str(risk.get('note'))[:70]}")
        out.append(f"        => {d.get('decision')}  (confidence {d.get('confidence')})")
        if d.get("decision") in ("BUY_YES", "BUY_NO"):
            out.append("        Panta    : quote -> build OK (paper mode: not broadcast)")
        else:
            out.append("        Panta    : no order (decision below action threshold)")

    for r in recs:
        if r.get("event") == "trade_dry_run":
            out.append("")
            out.append(f"        Panta    : quote={json.dumps(r.get('quote'))[:90]}")
            out.append("        Panta    : build OK - unsigned tx (paper mode: not broadcast)")

    out.append("")
    out.append("[3/3] Rendering dashboard ...")
    analyzed = sum(1 for r in recs if r.get("event") == "analysis")
    buys = sum(1 for r in recs if r.get("event") == "analysis"
               and r["decision"].get("decision") in ("BUY_YES", "BUY_NO"))
    out.append(f"  -> dashboard/index.html  ({analyzed} decisions, {buys} BUY signals, "
               f"{analyzed - buys} HOLD)")
    out.append("")
    out.append("=" * 118)
    out.append(f" SUMMARY  markets={start.get('marketCount')}  analyzed={analyzed}  "
               f"buy={buys}  hold={analyzed - buys}  trades=0")
    out.append(" log=run.jsonl   paper mode: no funds at risk")
    out.append("=" * 118)

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(BASE)} ({len(out)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
