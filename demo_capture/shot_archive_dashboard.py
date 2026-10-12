"""Screenshot the archive-rendered dashboard for the demo video.

Captures at 1600x900 so the result matches a 16:9 video frame, and also grabs a
cropped shot of the AI Decision Flow area for use as a detail insert.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "dashboard" / "_archive_index.html"
OUT = BASE / "demo_capture" / "build"


def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}; run render_archive_dashboard.py first")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    # Strip the auto-refresh meta so playback is deterministic.
    html = SRC.read_text(encoding="utf-8").replace('content="60"', 'content="3600"')
    tmp = OUT / "_norefresh.html"
    tmp.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 900},
                                device_scale_factor=2)
        page.goto(tmp.as_uri())
        page.wait_for_timeout(1500)

        full = OUT / "dashboard_full.png"
        page.screenshot(path=str(full), full_page=True)
        print(f"saved {full.name} ({full.stat().st_size} bytes)")

        hero = OUT / "dashboard_hero.png"
        page.screenshot(path=str(hero))
        print(f"saved {hero.name} ({hero.stat().st_size} bytes)")

        browser.close()

    tmp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
