"""Assemble the final demo video: title card, terminal run, dashboard pan.

Structure (target well under the 3-minute cap):
  0:00-0:05  title card  - what this is, in one line
  0:05-0:09  caption over the terminal, explains what to watch
  ...        the recorded run, trimmed to where the decision lands
  ...        dashboard segment, panned, with a caption naming the surface
  end        closing card with the honest framing

All text is burned in because the source recordings are silent and the judges
watch muted. Every claim on screen is one the project can support: this is paper
mode, nothing is signed or broadcast, and no profit is asserted.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BUILD = BASE / "demo_capture" / "build2"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

W, H = 1488, 764
FPS = 30

TITLE_DUR = 5.0
CLOSE_DUR = 5.0
DIM = "0x0f1220"  # matches the dashboard's background


def textfile(path: Path, text: str) -> str:
    """Write narration to a file and return a drawtext textfile= reference.

    drawtext's inline text= needs several levels of escaping for ':' and ',' that
    are easy to get wrong (and the failure message is opaque). Passing the string
    through a file sidesteps the filtergraph parser entirely.
    """
    path.write_text(text, encoding="utf-8")
    return str(path)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def title_card(out: Path) -> None:
    """Opening card: name, one-line positioning, and the two hard guarantees."""
    lines = [
        ("PantaPilot", FONT, 86, 200, "white"),
        ("An autonomous prediction-market desk that is graded on restraint",
         FONT_REG, 32, 320, "0x9aa4c7"),
        ("4 agents - live Panta markets - paper mode (DRY_RUN)",
         FONT_REG, 30, 400, "0x6ee7b7"),
        ("No funds. No signature. Nothing broadcast.",
         FONT_REG, 26, 460, "0x8b93b0"),
    ]
    parts = [f"drawbox=x=0:y=0:w={W}:h={H}:color={DIM}:t=fill"]
    for i, (txt, font, size, y, color) in enumerate(lines):
        tf = textfile(BUILD / f"_title_{i}.txt", txt)
        parts.append(
            f"drawtext=fontfile={font}:textfile={tf}:fontcolor={color}:"
            f"fontsize={size}:x=(w-text_w)/2:y={y}"
        )
    parts.append("format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", f"color=c={DIM}:s={W}x{H}:r={FPS}",
         "-t", str(TITLE_DUR), "-vf", ",".join(parts),
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-an", str(out)])


def close_card(out: Path) -> None:
    lines = [
        ("What you just watched", FONT, 44, 170, "white"),
        ("Scout gathered evidence, the Estimator priced it independently,",
         FONT_REG, 28, 290, "0xc9d1ea"),
        ("Decision compared that to the market, and Risk could veto it.",
         FONT_REG, 28, 335, "0xc9d1ea"),
        ("The verdict was HOLD. Its value is that it can be trusted not to trade.",
         FONT_REG, 28, 420, "0x6ee7b7"),
        ("github.com/lmlive/pantapilot", FONT_REG, 26, 520, "0x8b93b0"),
    ]
    parts = [f"drawbox=x=0:y=0:w={W}:h={H}:color={DIM}:t=fill"]
    for i, (txt, font, size, y, color) in enumerate(lines):
        tf = textfile(BUILD / f"_close_{i}.txt", txt)
        parts.append(
            f"drawtext=fontfile={font}:textfile={tf}:fontcolor={color}:"
            f"fontsize={size}:x=(w-text_w)/2:y={y}"
        )
    parts.append("format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", f"color=c={DIM}:s={W}x{H}:r={FPS}",
         "-t", str(CLOSE_DUR), "-vf", ",".join(parts),
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-an", str(out)])


def caption(src: Path, out: Path, text: str, start: float, dur: float) -> None:
    """Burn a lower-third caption onto a segment between start and start+dur.

    Kept to the bottom 78px and semi-transparent so it never covers the content
    the viewer is meant to read - the dashboard's market cards sit low, and a
    taller bar clipped them.
    """
    end = start + dur
    tf = textfile(BUILD / f"_cap_{int(start)}.txt", text)
    vf = (
        f"drawbox=x=0:y=h-78:w={W}:h=78:color=black@0.78:t=fill:"
        f"enable='between(t,{start},{end})',"
        f"drawtext=fontfile={FONT_REG}:textfile={tf}:"
        f"fontcolor=white:fontsize=27:x=(w-text_w)/2:y=h-54:"
        f"enable='between(t,{start},{end})',"
        f"format=yuv420p"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-an", str(out)])


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    t_card = BUILD / "c1_title.mp4"
    t_body = BUILD / "c2_terminal.mp4"
    t_dash = BUILD / "c3_dashboard.mp4"
    t_close = BUILD / "c4_close.mp4"

    print("building title card...")
    title_card(t_card)

    print("adding caption to terminal segment...")
    caption(BUILD / "p1_terminal.mp4", t_body,
            "Live run: 4 agents on a real Panta market. Nothing is signed or broadcast.",
            0.3, 7.0)

    print("adding caption to dashboard segment...")
    caption(BUILD / "p2_dashboard.mp4", t_dash,
            "Every decision carries its evidence trail, stage by stage.",
            0.6, 5.0)

    print("building closing card...")
    close_card(t_close)

    print("concatenating...")
    run(["ffmpeg", "-v", "error", "-y",
         "-i", str(t_card), "-i", str(t_body), "-i", str(t_dash), "-i", str(t_close),
         "-filter_complex",
         "[0:v]fps=30,format=yuv420p[a];"
         "[1:v]fps=30,format=yuv420p[b];"
         "[2:v]fps=30,format=yuv420p[c];"
         "[3:v]fps=30,format=yuv420p[d];"
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
