"""Render the dashboard to a PNG for the demo video and the repo docs.

Usage:  .venv/bin/python capture_dashboard.py
Output: docs/dashboard.png  (and demo_capture/dashboard_full.png)
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from playwright.sync_api import sync_playwright  # noqa: E402

DASH = BASE / "dashboard" / "index.html"
DOCS = BASE / "docs"
DOCS.mkdir(exist_ok=True)


def main() -> int:
    if not DASH.exists():
        print(f"missing {DASH}; render the dashboard first")
        return 1

    # The dashboard auto-refreshes every 60s via <meta http-equiv="refresh">.
    # Strip it for the screenshot so capture is deterministic.
    html = DASH.read_text(encoding="utf-8")
    tmp = BASE / "demo_capture" / "_dashboard_norefresh.html"
    tmp.write_text(html.replace('content="60"', 'content="3600"'), encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000},
                                device_scale_factor=2)
        page.goto(tmp.as_uri())
        page.wait_for_timeout(1200)

        # Full-page capture (the dashboard is taller than one viewport).
        full = DOCS / "dashboard_full.png"
        page.screenshot(path=str(full), full_page=True)
        print(f"saved {full.relative_to(BASE)}")

        # Hero viewport capture for the video.
        hero = DOCS / "dashboard.png"
        page.screenshot(path=str(hero))
        print(f"saved {hero.relative_to(BASE)}")

        browser.close()

    try:
        tmp.unlink()
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
