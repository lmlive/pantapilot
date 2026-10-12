"""Measure real pixel change between sampled frames.

Grayscale PNGs avoid JPEG noise. A frame that differs from the next only in the
text cursor produces a tiny changed-pixel fraction; a frame with new terminal
output produces a large one. That separates "idle but alive" from "still".
"""
from __future__ import annotations

import glob
import os

from PIL import Image, ImageChops

files = sorted(glob.glob("sec/t*.png"), key=lambda p: int(os.path.basename(p)[1:-4]))
if len(files) < 2:
    raise SystemExit("need at least 2 frames")

prev = None
prev_name = None
print(f"{'pair':>16}  {'changed %':>9}  {'max delta':>9}  verdict")
for path in files:
    img = Image.open(path).convert("L")
    name = os.path.basename(path)[1:-4]
    if prev is not None:
        diff = ImageChops.difference(prev, img)
        hist = diff.histogram()
        total = img.width * img.height
        changed = sum(hist[8:])  # ignore sub-8 differences: encode + cursor blink
        pct = changed / total * 100
        mx = max(i for i, c in enumerate(hist) if c)
        verdict = "STATIC" if pct < 0.5 else ("minor" if pct < 3 else "CHANGED")
        print(f"{prev_name+'->'+name:>16}  {pct:>8.2f}%  {mx:>9}  {verdict}")
    prev = img
    prev_name = name
