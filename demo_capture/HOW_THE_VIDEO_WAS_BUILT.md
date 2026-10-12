# Demo video — how the submitted file was built

**Deliverable:** `demo_capture/video/pantapilot_demo.mp4` (also copied to `pantapilot_demo_final.mp4`
in the workspace root) — **1:58, 1488×764, 30fps, silent, 4.3 MB**.

## What the judges asked for

> "YouTube, Loom, or Vimeo. Up to 3 minutes. Should show the live product, not a slide deck, not a
> code walkthrough."

The constraint that shaped everything: **the source recording showed only a terminal.** That reads as
a code walkthrough, so the dashboard — the actual product surface — had to be added.

## Source material

| File | Duration | Verdict |
|---|---|---|
| `demo.mp4` (first attempt) | 4:15 | **Rejected.** Over the limit, and 143s (56%) of it was a frozen terminal. |
| `demo2.mp4` (final recording) | 2:12 | **Used.** Under the limit, but the last ~38s were still static. |

Both were silent (`mean_volume: -91.0 dB`), so every claim had to be burned in as text.

## How the static tail was found

The first attempt to locate it failed three ways and is worth recording so nobody repeats it:

- **md5 of extracted frames** — every frame differs because the terminal cursor blinks.
- **Per-frame byte size** — a blinking cursor keeps average frame size near 23 KB throughout, so a
  frozen screen looks identical to a busy one.
- **Adding `ssim`/`psnr` filters** — produced no output with these inputs.

What worked was **visual comparison**: stack the same region from several timestamps and read them.
Four frames at 110s/150s/190s/230s were character-for-character identical, differing only in cursor
position. Do that first next time; it takes one command.

## Assembly

```
# 1. trim the terminal segment to where the decision lands
ffmpeg -i demo2.mp4 -t 94 -an -c:v libx264 -crf 20 build2/p1_terminal.mp4

# 2. render + screenshot the dashboard from the same run's log
.venv/bin/python render_now.py
.venv/bin/python demo_capture/make_dashboard_clip.py

# 3. pan over the tall dashboard capture
.venv/bin/python demo_capture/pan_dashboard.py

# 4. burn in title, captions, closing card; concatenate
.venv/bin/python demo_capture/assemble_demo.py
```

**Structure of the result:**

| Time | Content |
|---|---|
| 0:00–0:05 | Title card — name, positioning, `paper mode (DRY_RUN)` |
| 0:05–1:39 | The live run, captioned |
| 1:39–1:53 | Dashboard, panning from stat cards to market cards |
| 1:53–1:58 | Closing card |

## Two traps in the ffmpeg work

**`drawtext` inline `text=` cannot take `:` or `,`.** They are the filtergraph's own separators, and
escaping them correctly needs several backslash levels ("No option name near ..." is the only clue
you get). **Use `textfile=` instead** — write the string to a file and reference it. That is what
`assemble_demo.py` does for every piece of text.

**Concatenate only after normalising.** The title cards render at a different pixel format than the
clips; without an explicit `fps=30,format=yuv420p` on every input before `concat`, the join fails
with an opaque filter error.

## Honesty constraints honoured on screen

The burned-in text was checked against the same rules as the written submission:

- It says **paper mode (DRY_RUN)** and **"Nothing is signed or broadcast"** — no trade has ever been
  broadcast, and the video must not imply otherwise.
- It claims **no profit, ROI, or win rate**. The verdict shown is `HOLD`.
- The closing line is the honest framing, not a pitch: *"The verdict was HOLD. Its value is that it
  can be trusted not to trade."*
- It does **not** claim the four roles verify each other's numbers. Risk checks caps and liquidity;
  it does not re-derive the Estimator's probability. See `SUBMISSION.md`.
