"""Turn the tall dashboard capture into a video segment that pans over it.

A single static frame reads as a screenshot; a slow pan makes it legible as a
product surface and lets the viewer follow from the stat cards down to the
decision cards. Held still at the start so the eye can land on the counters, then
panned, then held at the bottom conclusion.

Output matches the terminal segment (1488x764, 30fps, no audio) so the two
concatenate without a re-encode mismatch.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BUILD = BASE / "demo_capture" / "build2"
SHOT = BUILD / "dashboard_4k.png"
OUT = BUILD / "p2_dashboard.mp4"

W, H = 1488, 764
FPS = 30
HOLD_TOP = 3.0     # seconds held at the top
PAN = 7.0          # seconds spent panning
HOLD_BOTTOM = 4.0  # seconds held at the bottom


def main() -> int:
    if not SHOT.exists():
        print(f"missing {SHOT}")
        return 1

    # Source is 2x; scale first so the pan is expressed in output pixels.
    metrics = json.loads((BUILD / "dashboard_metrics.json").read_text())
    scrollable = max(0, int(metrics["scroll_height"]) - int(metrics["viewport"]))
    total = HOLD_TOP + PAN + HOLD_BOTTOM
    print(f"scrollable {scrollable}px over {PAN}s in a {total}s clip")

    # crop then offset; y goes 0 -> scrollable across the pan window.
    vf = (
        f"scale={W}:-2,crop={W}:{H}:0:'min({scrollable},"
        f"max(0,(t-{HOLD_TOP})/{PAN}*{scrollable}))',"
        f"fps={FPS},format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-loop", "1", "-i", str(SHOT),
        "-t", str(total),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-an", str(OUT),
    ]
    print("running ffmpeg...")
    subprocess.run(cmd, check=True)
    print(f"saved {OUT.name} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
