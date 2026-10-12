# Demo video — how the submitted file was built

**Deliverable:** `demo_capture/video/pantapilot_demo.mp4` (also copied to `pantapilot_demo_final.mp4`
in the workspace root) — **2:30, 1488×764, 30fps, silent, 6.3 MB**.

## What the judges asked for

> "YouTube, Loom, or Vimeo. Up to 3 minutes. Should show the live product, not a slide deck, not a
> code walkthrough."

Two constraints shaped everything: the 3-minute cap, and the fact that **a terminal recording alone
reads as a code walkthrough** — the dashboard is the actual product surface and had to appear.

## Source material

| File | Duration | Resolution | Verdict |
|---|---|---|---|
| `demo.mp4` (first attempt) | 4:15 | 1488×764 | **Rejected.** Over the limit; 143s (56%) was a frozen terminal. |
| `demo2.mp4` (terminal, used) | 2:12 | 1488×764 | **Used**, trimmed to 96s — the decision lands at ~93s and the screen freezes after. |
| `demo3.mp4` (dashboard, used) | 0:43 | 1920×1020 | **Used in full.** A real browser session: real scrolling, real expansion of the evidence panels. |

All three are silent (`mean_volume: -91.0 dB`), so every claim is burned in as text.

`demo3.mp4` superseded an earlier approach that faked the dashboard half by panning a screenshot. A
genuine browser recording is more convincing — it shows the URL bar, the scroll interaction, and the
`Details & Evidence` panels being opened.

## How the static tail was found

The first attempt to locate it failed three ways, which is worth recording so nobody repeats it:

- **md5 of extracted frames** — every frame differs because the terminal cursor blinks.
- **Per-frame byte size** — a blinking cursor keeps average frame size near 23 KB throughout, so a
  frozen screen looks identical to a busy one.
- **`ssim`/`psnr` filters** — produced no output with these inputs.

What worked was **visual comparison**: stack the same region from several timestamps and read them.
Four frames at 110s/150s/190s/230s were character-for-character identical, differing only in cursor
position. Do that first next time; it takes one command.

## Assembly

```
.venv/bin/python demo_capture/assemble_demo.py
```

Structure of the result:

| Time | Content |
|---|---|
| 0:00–0:05 | Title card — name, positioning, `paper mode (DRY_RUN)` |
| 0:05–1:41 | The live run, captioned |
| 1:41–2:24 | The real dashboard session, captioned |
| 2:24–2:30 | Closing card |

## Three ffmpeg traps, all hit in this task

**`drawtext` inline `text=` cannot take `:` or `,`.** They are the filtergraph's own separators, and
escaping them needs several backslash levels ("No option name near ..." is the only clue you get).
**Use `textfile=`** — write the string to a file and reference it. Every piece of text here does.

**Scale-then-pad needs `force_original_aspect_ratio=decrease`.** The dashboard is 1920×1020 and the
canvas 1488×764. Scaling by width gives 790px of height, and `pad()` refuses to shrink:
*"Padded dimensions cannot be smaller than input dimensions."*

**Every concat branch must agree on SAR, not just size and pixel format.** The dashboard survives
scaling with a non-square SAR (12224:12223) and `concat` rejects the join with
*"parameters (size 1488x764, SAR 12224:12223) do not match ... (1488x764, SAR 1:1)"*. Add
`setsar=1` to **all** branches.

## Honesty constraints honoured on screen

The burned-in text was checked against the same rules as the written submission:

- It says **paper mode (DRY_RUN)** and **"Nothing is signed"** — no trade has ever been broadcast.
- It claims **no profit, ROI, or win rate**. The verdict shown is `HOLD`.
- The closing line is the honest framing, not a pitch: *"The verdict was HOLD - its value is that it
  can be trusted not to trade."*
- It does **not** claim the four roles verify each other's numbers. Risk checks caps and liquidity;
  it does not re-derive the Estimator's probability. See `SUBMISSION.md`.
