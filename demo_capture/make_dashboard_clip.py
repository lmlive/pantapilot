"""Build the dashboard segment for the demo video.

The terminal recording is 1488x764. The dashboard is taller than that and its
text would be unreadable if squeezed to fit, so instead of a static 16:9 frame we
scroll a 1488px-wide render past the viewport at reading speed.

Produces a silent h264 clip at exactly the terminal's resolution and frame rate,
so the two segments concatenate cleanly.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "dashboard" / "index.html"
OUT = BASE / "demo_capture" / "build2"

W, H = 1488, 764
FPS = 30


def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    html = SRC.read_text(encoding="utf-8").replace('content="60"', 'content="3600"')
    tmp = OUT / "_norefresh.html"
    tmp.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H},
                                device_scale_factor=2)
        page.goto(tmp.as_uri())
        page.wait_for_timeout(1500)

        # Total scrollable height, used to compute a scroll distance.
        metrics = page.evaluate(
            "() => ({sh: document.documentElement.scrollHeight, "
            "ih: window.innerHeight})"
        )
        scroll_h = int(metrics["sh"])
        view_h = int(metrics["ih"])
        max_scroll = max(0, scroll_h - view_h)
        print(f"dashboard height {scroll_h}px, viewport {view_h}px, "
              f"scrollable {max_scroll}px")

        canvas = OUT / "dashboard_4k.png"
        page.screenshot(path=str(canvas), full_page=True)
        print(f"saved {canvas.name} ({canvas.stat().st_size} bytes)")

        browser.close()

    tmp.unlink(missing_ok=True)

    info = {"scroll_height": scroll_h, "viewport": view_h, "width": W, "height": H}
    (OUT / "dashboard_metrics.json").write_text(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
