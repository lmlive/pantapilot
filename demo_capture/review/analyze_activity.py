"""Find where demo.mp4 stops showing activity.

ffprobe emits `pts_time,pkt_size` per frame. A static screen compresses to almost
nothing, so a sustained collapse in average frame size marks the point where the
recording became a still image. Used to decide the trim point for the 3-minute
submission limit.
"""
from __future__ import annotations

import collections
import csv

BUCKET = 10  # seconds

buckets: dict[int, list[int]] = collections.defaultdict(list)
total = 0
with open("frames.csv") as fh:
    for row in csv.reader(fh):
        if len(row) != 2:
            continue
        try:
            t = float(row[0])
            size = int(row[1])
        except ValueError:
            continue
        buckets[int(t // BUCKET) * BUCKET].append(size)
        total += 1

print(f"frames parsed: {total}")
print()
print(f"{'window':>12}  {'avg bytes':>10}  {'frames':>7}  activity")
for k in sorted(buckets):
    v = buckets[k]
    avg = sum(v) / len(v)
    bar = "#" * int(min(avg / 400, 45))
    print(f"{k:>6}-{k + BUCKET:<5}  {avg:>10.0f}  {len(v):>7}  {bar}")

# The last window whose average is above a usable threshold is the end of content.
vals = {k: sum(v) / len(v) for k, v in buckets.items()}
if vals:
    peak = max(vals.values())
    threshold = peak * 0.15  # 15% of the busiest window
    active = [k for k, a in sorted(vals.items()) if a >= threshold]
    print()
    print(f"busiest window avg : {peak:.0f} bytes")
    print(f"activity threshold : {threshold:.0f} bytes")
    if active:
        last = active[-1]
        print(f"last ACTIVE window : {last}s - {last + BUCKET}s")
        print(f"=> content ends around {last + BUCKET}s; trim there")
