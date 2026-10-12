"""Build the 90-second demo video from real run artifacts.

Scenes (ffmpeg, no external editor):
  1. Title card
  2. LIVE terminal run        (progressive replay of demo_capture/run_transcript.txt:
                               lines print in order with a scrolling window + cursor.
                               This is a faithful re-drawing of the captured run, NOT a
                               screen recording -- the content is verbatim run output.)
  3. 4-agent pipeline diagram (the actual Scout->Estimator->Decision->Risk flow)
  4. Decision evidence chain  (real JSONL record fields)
  5. Dashboard                (docs/dashboard.png)
  6. Productization roadmap
  7. Closing card

Output: docs/demo.mp4  (1920x1080, H.264, silent)

Usage:  .venv/bin/python build_demo_video.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

BASE = Path(__file__).resolve().parent
WORK = BASE / "demo_capture" / "video"
DOCS = BASE / "docs"
WORK.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(exist_ok=True)

W, H, FPS = 1920, 1080, 30
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG = "0x0f1220"
FG = "0xe8eaf0"
ACCENT = "0x3498db"
GREEN = "0x2ecc71"
GREY = "0x8899aa"
ORANGE = "0xe67e22"


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd[:8])}...\n{proc.stderr[-2000:]}")


TEXTDIR = WORK / "_text"
_TXT_N = [0]


def esc(s: str) -> str:
    """Escape text for ffmpeg drawtext."""
    return (s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
             .replace("%", "\\%").replace(",", "\\,"))


def textfile(text: str) -> str:
    """Write text to a numbered file and return the path for drawtext=textfile=.

    Using textfile avoids the quoting/escaping minefield of inline drawtext text
    (apostrophes in "World's Fair" break an inline graph).
    """
    TEXTDIR.mkdir(parents=True, exist_ok=True)
    _TXT_N[0] += 1
    p = TEXTDIR / f"t{_TXT_N[0]:05d}.txt"
    # A literal '%' and trailing newline must be handled; write exactly the text.
    p.write_text(text, encoding="utf-8")
    return p.as_posix()


def drawtext(text: str, *, font: str = SANS, size: int = 32, color: str = FG,
             x: str = "80", y: str = "80", alpha: str = "1") -> str:
    tf = textfile(text)
    return (f"drawtext=fontfile={font}:textfile={tf}:fontsize={size}:"
            f"fontcolor={color}:x={x}:y={y}:alpha={alpha}")


def card(out: Path, lines: list[tuple[str, str, int, str]], seconds: float = 4.0,
         right: str | None = None, spacing: int = 70) -> None:
    """Render a static card. lines = [(text, color, size, font)].

    `spacing` controls the vertical step; raise it for cards with large type so
    lines do not overlap.
    """
    filters = [f"color=c={BG}:s={W}x{H}:d={seconds}:r={FPS}[bg]"]
    cur = "bg"
    for i, (text, color, size, font) in enumerate(lines):
        nxt = f"v{i}"
        filters.append(
            f"[{cur}]{drawtext(text, font=font, size=size, color=color, x='90', y=str(120 + i*spacing))}[{nxt}]"
        )
        cur = nxt
    if right:
        filters.append(f"[{cur}]{drawtext(right, size=26, color=GREY, x='90', y='980')}[vout]")
        cur = "vout"
    fc = ";".join(filters)
    run(["ffmpeg", "-y", "-filter_complex", fc, "-map", f"[{cur}]",
         "-t", str(seconds), "-pix_fmt", "yuv420p", str(out)])


def _line_color(ln: str) -> str:
    if ln.startswith("  Panta") or "trade_dry_run" in ln:
        return GREEN
    if "!!" in ln:
        return "0xe74c3c"
    if ln.startswith("=") or ln.startswith(" PantaPilot") or ln.startswith(" SUMMARY"):
        return ACCENT
    if ln.strip().startswith(("Scout", "Estimator", "Decision", "Risk", "Benchmark")):
        return "0xf1c40f"
    return FG


LINE_H = 30          # row pitch in px
TEXT_TOP = 132       # y of the first transcript row
MAX_ROWS = 28        # rows visible before the view scrolls
LEAD_IN = 1.2        # seconds of empty terminal before the first line


def terminal_scene(out: Path, lines: list[str], seconds: float) -> None:
    """Render the transcript as a progressive, scrolling terminal.

    This is a re-drawing of the real captured run rather than a screen recording:
    each line appears in turn (top to bottom), the text scrolls up once it fills
    the window, and a cursor blinks at the write head. Nothing is invented -- the
    content is exactly `lines`, taken from demo_capture/run_transcript.txt.
    """
    lines = lines or ["(no output)"]
    total = len(lines)
    reveal = max(seconds - LEAD_IN, 0.5)
    per_line = reveal / total

    clips: list[Path] = []

    # Lead-in: an empty terminal with a blinking cursor at the write head.
    lead = WORK / "term_lead.mp4"
    _terminal_frame(lead, [], dur=LEAD_IN)
    clips.append(lead)

    # One clip per revealed line. Only the first n lines are drawn, so text that
    # has not "printed" yet is genuinely absent rather than merely cropped away.
    for n in range(1, total + 1):
        first = max(0, n - MAX_ROWS)          # scroll once the window is full
        visible = lines[first:n]
        cursor_row = (n - 1) - first
        clip = WORK / f"term_n{n:03d}.mp4"
        _terminal_frame(clip, visible, dur=per_line, cursor_row=cursor_row,
                        show_cursor=(n < total))
        clips.append(clip)

    concat(out, clips)


def _terminal_frame(out: Path, visible: list[str], *, dur: float,
                    cursor_row: int = 0, show_cursor: bool = True) -> None:
    """Render one terminal state: window chrome + the `visible` lines only."""
    dur = max(dur, 0.05)
    filters = [
        f"color=c={BG}:s={W}x{H}:d=1:r={FPS}[bg]",
        f"[bg]drawbox=x=60:y=60:w={W-120}:h={H-140}:color=0x171a2b@1:t=fill[win]",
        f"[win]drawbox=x=60:y=60:w={W-120}:h=52:color=0x242a44@1:t=fill[bar]",
        f"[bar]drawbox=x=96:y=78:w=16:h=16:color=0xe74c3c@1:t=fill[d1]",
        f"[d1]drawbox=x=122:y=78:w=16:h=16:color=0xf1c40f@1:t=fill[d2]",
        f"[d2]drawbox=x=148:y=78:w=16:h=16:color=0x2ecc71@1:t=fill[d3]",
    ]
    cur = "d3"
    for i, ln in enumerate(visible):
        nxt = f"t{i}"
        filters.append(
            f"[{cur}]{drawtext(ln[:118], font=MONO, size=22, color=_line_color(ln), x='90', y=str(TEXT_TOP + i*LINE_H))}[{nxt}]"
        )
        cur = nxt
    # Blinking cursor at the write head (t toggles because we emit real frames).
    if show_cursor:
        cy = TEXT_TOP + cursor_row * LINE_H + 2
        filters.append(
            f"[{cur}]drawbox=x=90:y={cy}:w=13:h=24:color=0xe8eaf0@1:t=fill:"
            f"enable='lt(mod(t,1.0),0.5)'[cur1]"
        )
        cur = "cur1"
    fc = ";".join(filters)
    run(["ffmpeg", "-y", "-filter_complex", fc, "-map", f"[{cur}]",
         "-t", f"{dur:.4f}", "-r", str(FPS), "-pix_fmt", "yuv420p",
         "-c:v", "libx264", str(out)])


def pipeline_scene(out: Path, seconds: float) -> None:
    """The four-agent pipeline, drawn as four labelled boxes with arrows."""
    boxes = [
        ("1  SCOUT", "Oracle + web intel", "2 sources", "0x3498db"),
        ("2  ESTIMATOR", "Independent P(TRUE)", "true_prob_yes", "0x9b59b6"),
        ("3  DECISION", "Market vs model", "edge = gap", "0xf1c40f"),
        ("4  RISK", "Veto + caps", "PASSED / VETO", "0xe74c3c"),
    ]
    bw, bh, gap = 380, 210, 60
    total = len(boxes) * bw + (len(boxes) - 1) * gap
    x0 = (W - total) // 2
    y0 = 380
    filters = [f"color=c={BG}:s={W}x{H}:d={seconds}:r={FPS}[bg]"]
    cur = "bg"
    step = 0
    for i, (title, sub, stat, col) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        n1, n2 = f"b{step}", f"b{step+1}"
        filters.append(f"[{cur}]drawbox=x={x}:y={y0}:w={bw}:h={bh}:color=0x171a2b@1:t=fill[{n1}]")
        filters.append(f"[{n1}]drawbox=x={x}:y={y0}:w={bw}:h=5:color={col}@1:t=fill[{n2}]")
        cur = n2
        step += 2
        for j, (txt, size, fnt, tcol) in enumerate(
            [(title, 30, SANS_B, col), (sub, 22, SANS, FG), (stat, 20, MONO, GREY)]
        ):
            n3 = f"b{step}"
            tx = x + 24
            ty = y0 + 40 + j * 54
            filters.append(
                f"[{cur}]{drawtext(txt, font=fnt, size=size, color=tcol, x=str(tx), y=str(ty))}[{n3}]"
            )
            cur = n3
            step += 1
        if i < len(boxes) - 1:
            ax = x + bw + 12
            n4 = f"b{step}"
            filters.append(
                f"[{cur}]{drawtext('->', font=SANS_B, size=44, color='0x44506b', x=str(ax), y=str(y0+80))}[{n4}]"
            )
            cur = n4
            step += 1
    # captions
    filters.append(f"[{cur}]{drawtext('Every market goes through all four roles before an order is allowed', font=SANS, size=32, color=FG, x='90', y='200')}[c1]")
    filters.append(f"[c1]{drawtext('No single prompt decides. Consensus is required.', font=SANS, size=26, color=GREY, x='90', y='260')}[c2]")
    filters.append(f"[c2]{drawtext('Scout -> Estimator -> Decision -> Risk  (live pipeline: scout>estimator>decision>risk)', font=MONO, size=24, color=ACCENT, x='90', y='860')}[c3]")
    filters.append(f"[c3]{drawtext('If any role fails, the desk degrades to single-agent analysis instead of crashing', font=SANS, size=24, color=ORANGE, x='90', y='920')}[vout]")
    cur = "vout"
    fc = ";".join(filters)
    run(["ffmpeg", "-y", "-filter_complex", fc, "-map", f"[{cur}]",
         "-t", str(seconds), "-pix_fmt", "yuv420p", str(out)])


def evidence_scene(out: Path, rec: dict, seconds: float) -> None:
    """Show the real evidence-chain fields from a captured JSONL record."""
    d = rec.get("decision", {})
    ev = d.get("evidence", {})
    est = ev.get("estimator") or {}
    intel = ev.get("intel") or {}
    risk = ev.get("risk") or {}
    # Keep this line short: a raw dict dump overflows the 1920px frame.
    est_line = (f"estimator   : true_prob_yes={est.get('true_prob_yes')}  "
                f"confidence={est.get('confidence')}  unc={est.get('uncertainty')}"
                if est else "estimator   : unavailable (call failed -> degraded)")
    lines = [
        ("DECISION EVIDENCE CHAIN  (verbatim from logs/pantapilot.jsonl)", ACCENT, 30, SANS_B),
        ("", FG, 10, SANS),
        (f"market      : {str(rec.get('title'))[:74]}", FG, 24, MONO),
        (f"marketId    : {rec.get('marketId')}", GREY, 20, MONO),
        (f"ts          : {rec.get('ts')}", GREY, 20, MONO),
        ("", FG, 10, SANS),
        (f"pipeline    : {ev.get('pipeline')}", GREEN, 24, MONO),
        (f"scout       : {len(intel.get('queries') or [])} queries, "
         f"oracle={'yes' if intel.get('oracle_head') else 'no'}, "
         f"web={'yes' if intel.get('search_head') else 'no'}", FG, 24, MONO),
        (est_line, FG, 22, MONO),
        (f"decision    : {d.get('decision')}  confidence={d.get('confidence')}", FG, 24, MONO),
        (f"risk        : approved={risk.get('approved')}  {str(risk.get('note'))[:46]}", FG, 22, MONO),
        ("", FG, 10, SANS),
        (f"reason      : {str(d.get('reason'))[:100]}", FG, 22, MONO),
    ]
    filters = [f"color=c={BG}:s={W}x{H}:d={seconds}:r={FPS}[bg]"]
    cur = "bg"
    for i, (txt, col, size, fnt) in enumerate(lines):
        nxt = f"e{i}"
        ty = 120 + i * 56
        filters.append(
            f"[{cur}]{drawtext(txt, font=fnt, size=size, color=col, x='90', y=str(ty))}[{nxt}]"
        )
        cur = nxt
    filters.append(
        f"[{cur}]{drawtext('This JSONL line is the audit trail judges can expand in the dashboard.', font=SANS, size=26, color=GREY, x='90', y='960')}[vout]"
    )
    cur = "vout"
    fc = ";".join(filters)
    run(["ffmpeg", "-y", "-filter_complex", fc, "-map", f"[{cur}]",
         "-t", str(seconds), "-pix_fmt", "yuv420p", str(out)])


def image_scene(out: Path, png: Path, seconds: float, caption: str,
                crop_top_frac: float = 0.0, crop_h_frac: float = 1.0) -> None:
    """Show a PNG with a caption strip at the bottom.

    A full-page dashboard screenshot is very tall; shown whole, its text is
    unreadable at 1080p. crop_top_frac/crop_h_frac select the readable band.
    """
    cap = textfile(caption)
    crop = ""
    if crop_h_frac < 1.0:
        # crop=w:h:x:y  -- width stays full; y is derived from the source height.
        crop = (f"crop=iw:ih*{crop_h_frac:.4f}:0:ih*{crop_top_frac:.4f},")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(png),
         "-t", f"{seconds}", "-r", str(FPS),
         "-vf", (crop + f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                 f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={BG},"
                 f"drawtext=fontfile={SANS}:textfile={cap}:fontsize=30:"
                 f"fontcolor={FG}:x=90:y={H-70}:box=1:boxcolor=0x0f1220@0.85:boxborderw=14"),
         "-pix_fmt", "yuv420p", "-c:v", "libx264", str(out)])


def concat(out: Path, clips: list[Path]) -> None:
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])


def main() -> int:
    clips: list[Path] = []

    # ---- Scene 1: title --------------------------------------------------
    s = WORK / "s1.mp4"
    card(s, [
        ("PantaPilot", FG, 96, SANS_B),
        ("", FG, 10, SANS),
        ("An autonomous 4-agent trading desk for Panta prediction markets", ACCENT, 38, SANS),
        ("", FG, 10, SANS),
        ("Scout  ->  Estimator  ->  Decision  ->  Risk", FG, 34, MONO),
        ("", FG, 10, SANS),
        ("Colosseum Crypto World's Fair  |  Panta API Sidetrack", GREY, 28, SANS),
    ], 6.0, right="Live Panta API  |  paper mode (DRY_RUN=true)", spacing=130)
    clips.append(s)

    # ---- Scene 2: terminal ----------------------------------------------
    transcript = (BASE / "demo_capture" / "run_transcript.txt")
    if transcript.exists() and transcript.read_text(encoding="utf-8").strip():
        lines = transcript.read_text(encoding="utf-8").rstrip().splitlines()
    else:
        # Rebuild from the JSONL if the tee'd transcript is missing.
        lines = ["$ .venv/bin/python run_demo_capture.py", ""]
        for raw in (BASE / "demo_capture" / "run.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(raw)
            if r.get("event") == "start":
                lines.append(f"[start] mode={r.get('mode')} markets={r.get('marketCount')}")
            elif r.get("event") == "analysis":
                dd = r["decision"]
                lines.append(f"[analysis] {str(r.get('title'))[:60]}")
                lines.append(f"           => {dd['decision']} confidence={dd['confidence']}")
                lines.append(f"           reason: {str(dd.get('reason'))[:88]}")
    s = WORK / "s2.mp4"
    terminal_scene(s, lines, 22.0)
    clips.append(s)

    # ---- Scene 3: pipeline ----------------------------------------------
    s = WORK / "s3.mp4"
    pipeline_scene(s, 12.0)
    clips.append(s)

    # ---- Scene 4: evidence chain ----------------------------------------
    s = WORK / "s4.mp4"
    rec = json.loads((BASE / "demo_capture" / "run.jsonl").read_text(encoding="utf-8")
                     .strip().splitlines()[-1])
    evidence_scene(s, rec, 14.0)
    clips.append(s)

    # ---- Scene 5: dashboard (two readable bands) ------------------------
    s = WORK / "s5a.mp4"
    image_scene(s, DOCS / "dashboard_full.png", 8.0,
                "Live dashboard - the 4-role pipeline card for a real decision",
                crop_top_frac=0.0, crop_h_frac=0.42)
    clips.append(s)
    s = WORK / "s5b.mp4"
    image_scene(s, DOCS / "dashboard_full.png", 7.0,
                "Every tracked market: status, YES/NO price bars, volume",
                crop_top_frac=0.40, crop_h_frac=0.45)
    clips.append(s)

    # ---- Scene 6: verdict / traction ------------------------------------
    s = WORK / "s6.mp4"
    card(s, [
        ("What is real today", FG, 56, SANS_B),
        ("", FG, 10, SANS),
        ("Live Panta API integration, zero mocks (5-step order chain)", GREEN, 30, SANS),
        ("4-role deliberation with a full JSONL audit trail", GREEN, 30, SANS),
        ("Honest null backtest: venue has no mispricing history yet", ORANGE, 30, SANS),
        ("Paper mode by default - no capital at risk", GREEN, 30, SANS),
        ("", FG, 10, SANS),
        ("We report the measurement, not a claimed P&L.", GREY, 30, SANS),
    ], 12.0)
    clips.append(s)

    # ---- Scene 7: roadmap -----------------------------------------------
    s = WORK / "s7.mp4"
    card(s, [
        ("Productization roadmap", FG, 56, SANS_B),
        ("", FG, 10, SANS),
        ("Phase 1  Telegram bot - push a signal card the moment an edge appears", ACCENT, 30, SANS),
        ("Phase 2  Persistent worker - all markets, per-category models, digests", ACCENT, 30, SANS),
        ("Phase 3  Delegated execution - user-set caps, risk veto enforced", ACCENT, 30, SANS),
        ("", FG, 10, SANS),
        ("The hard part is trust: deliberation + audit trail. That part is built.", GREEN, 30, SANS),
    ], 12.0, right="github.com/lmlive/pantapilot")
    clips.append(s)

    final = DOCS / "demo.mp4"
    concat(final, clips)

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(final)],
        capture_output=True, text=True).stdout.strip()
    size = final.stat().st_size
    print(f"\nbuilt {final.relative_to(BASE)}  duration={float(dur):.1f}s  "
          f"size={size/1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
