"""Rebuild the demo video using the real browser dashboard recording.

Supersedes the earlier assembly, which faked the dashboard half by panning a
screenshot. demo3.mp4 is a genuine browser session - real scrolling, real
expansion of the Details & Evidence panels - so it is both more convincing and
less work to justify.

Layout problem: the terminal recording is 1488x764 and the dashboard recording is
1920x1020. Different aspect ratios (1.95 vs 1.88). Rather than crop content or
letterbox, the dashboard is scaled to fit the width and the small vertical
remainder is filled with the dashboard's own background colour, which reads as
part of the page.

Output: build3/demo_final.mp4
"""
from __future__ import annotations

import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BUILD = BASE / "demo_capture" / "build3"
SRC_TERM = Path("/data/hack/demo2.mp4")
SRC_DASH = Path("/data/hack/demo3.mp4")

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DIM = "0x0f1220"  # the dashboard's own background

W, H = 1488, 764
FPS = 30

# Terminal: the decision lands at ~93s, then the screen freezes. Keep a little
# breathing room past the verdict so the result is readable.
TERM_LEN = 96.0
# Dashboard: full clip, it is already short and every second carries content.
DASH_LEN = 43.0

TITLE_DUR = 5.0
CLOSE_DUR = 6.0


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def textfile(name: str, text: str) -> str:
    """Write narration to a file and return a drawtext textfile= reference.

    drawtext's inline text= cannot carry ':' or ',' without several levels of
    escaping, and the parse error gives no useful hint. A file sidesteps it.
    """
    p = BUILD / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def card(out: Path, lines: list[tuple[str, str, int, int, str]], dur: float) -> None:
    """Render a static card from (text, font, size, y, colour) tuples."""
    parts = [f"drawbox=x=0:y=0:w={W}:h={H}:color={DIM}:t=fill"]
    for i, (txt, font, size, y, colour) in enumerate(lines):
        tf = textfile(f"_{out.stem}_{i}.txt", txt)
        parts.append(
            f"drawtext=fontfile={font}:textfile={tf}:fontcolor={colour}:"
            f"fontsize={size}:x=(w-text_w)/2:y={y}"
        )
    parts.append("format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", f"color=c={DIM}:s={W}x{H}:r={FPS}",
         "-t", str(dur), "-vf", ",".join(parts),
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-an", str(out)])


def caption(src: Path, out: Path, text: str, start: float, dur: float,
            length: float = 0.0, height: int = 78, size: int = 27) -> None:
    tf = textfile(f"_cap_{out.stem}.txt", text)
    end = start + dur
    vf = (
        f"drawbox=x=0:y=h-{height}:w={W}:h={height}:color=black@0.80:t=fill:"
        f"enable='between(t,{start},{end})',"
        f"drawtext=fontfile={FONT_REG}:textfile={tf}:"
        f"fontcolor=white:fontsize={size}:x=(w-text_w)/2:y=h-{height - 26}:"
        f"enable='between(t,{start},{end})',"
        f"format=yuv420p"
    )
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src)]
    # Trim before the filter so the caption timings refer to the output timeline.
    if length:
        cmd += ["-t", str(length)]
    cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-an", str(out)]
    run(cmd)


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    for f in (SRC_TERM, SRC_DASH):
        if not f.exists():
            print(f"missing source: {f}")
            return 1

    print("1/5 title card")
    card(BUILD / "c1_title.mp4", [
        ("PantaPilot", FONT, 86, 200, "white"),
        ("An autonomous prediction-market desk that is graded on restraint",
         FONT_REG, 32, 320, "0x9aa4c7"),
        ("4 agents - live Panta markets - paper mode (DRY_RUN)",
         FONT_REG, 30, 400, "0x6ee7b7"),
        ("No funds. No signature. Nothing broadcast.",
         FONT_REG, 26, 460, "0x8b93b0"),
    ], TITLE_DUR)

    print("2/5 terminal segment")
    caption(SRC_TERM, BUILD / "c2_terminal.mp4",
            "Live run: 4 agents analyse a real Panta market. Nothing is signed.",
            0.3, 8.0, length=TERM_LEN)

    print("3/5 dashboard segment")
    caption(SRC_DASH, BUILD / "c3_dashboard.mp4",
            "The dashboard: scroll for each decision and expand its evidence.",
            0.5, 6.0, length=DASH_LEN, height=72, size=26)

    print("4/5 closing card")
    card(BUILD / "c4_close.mp4", [
        ("What you just watched", FONT, 44, 150, "white"),
        ("Scout gathered evidence. The Estimator priced it independently.",
         FONT_REG, 28, 265, "0xc9d1ea"),
        ("Decision compared that to the market, and Risk could veto it.",
         FONT_REG, 28, 310, "0xc9d1ea"),
        ("The verdict was HOLD - its value is that it can be trusted not to trade.",
         FONT_REG, 28, 395, "0x6ee7b7"),
        ("github.com/lmlive/pantapilot", FONT_REG, 26, 490, "0x8b93b0"),
    ], CLOSE_DUR)

    print("5/5 concatenating")
    run(["ffmpeg", "-v", "error", "-y",
         "-i", str(BUILD / "c1_title.mp4"),
         "-i", str(BUILD / "c2_terminal.mp4"),
         "-i", str(BUILD / "c3_dashboard.mp4"),
         "-i", str(BUILD / "c4_close.mp4"),
         "-filter_complex",
         # Every branch must agree on SAR as well as size and pixel format. The
         # dashboard's 1920x1020 survives scaling with a non-square SAR
         # (12224:12223), and concat refuses to join it to the others' 1:1 - the
         # error names the parameters but not which one differs, so setsar is
         # applied everywhere rather than only where it is currently needed.
         f"[0:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p[a];"
         f"[1:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p[b];"
         f"[2:v]fps={FPS},"
         f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
         f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={DIM},setsar=1,format=yuv420p[c];"
         f"[3:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p[d];"
         "[a][b][c][d]concat=n=4:v=1:a=0[out]",
         "-map", "[out]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-movflags", "+faststart",
         str(BUILD / "demo_final.mp4")])

    final = BUILD / "demo_final.mp4"
    print(f"done: {final} ({final.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
