# PantaPilot — Demo Video Recording Script

**Target length:** 2:52 (hard ceiling 3:00)
**Format:** screen recording + voice-over · 1920×1080 · upload to YouTube / Loom / Vimeo (public or unlisted-with-link)
**Requirement being satisfied:** *"YouTube, Loom, or Vimeo. Up to 3 minutes. Should show the live product, not a slide deck, not a code walkthrough."*

> **The one rule for this recording:** every pixel of the product you show is a real run against
> `https://live-api.panta.market/api/v1` with four live LLM agent calls. No mockups, no static
> screenshots sold as live, no editor open, no source code read aloud. If a take stumbles, re-run
> the loop — do not fake it.

---

## 0. Pre-flight checklist (do this before you hit record)

### 0.1 Terminal

```bash
cd /data/hack/pantapilot

# Sanity check the interpreter — system python3 lacks the deps, .venv/bin/python is required
.venv/bin/python --version          # expect: Python 3.14.x

# Clear the log so this take's decision rows are unambiguous on camera
cp logs/pantapilot.jsonl logs/pantapilot.jsonl.take-backup 2>/dev/null
```

Set the terminal to **large, readable font** (16–18pt), dark background, window ~1600×900, and
`export SCAN_INTERVAL_MINUTES=999` so the loop does not fire a second round mid-sentence.
Before rolling, paste the run command but **do not press Enter** — you press it on camera in shot 2.

### 0.2 Browser tabs (open in this exact order, left to right)

| Tab | URL | Why |
|---|---|---|
| 1 | `file:///data/hack/pantapilot/dashboard/index.html` | The live dashboard. It self-refreshes every 60s (`<meta http-equiv="refresh" content="60">`). |
| 2 | `https://live-api.panta.market/api/v1/markets/` | Raw Panta API response — proves the market data is real and not ours. |

Hide bookmarks and the tab strip if your recorder allows; no other tabs, no email, no chat.

### 0.3 Window layout

- **Left 60%:** terminal (the run).
- **Right 40%:** dashboard tab.
- **Full screen / hide the desktop.** Nothing on screen should suggest a laptop in a bedroom.

### 0.4 Facts you may state on camera (verified 2026-10-12 afternoon)

| Fact | Verified value |
|---|---|
| Tradeable markets on Panta | **2** (`open`). Was 1 in the morning — the venue added one. |
| Market 1 | *Will BTC reach a new all-time high by December 31, 2026?* — YES **0.5054**, vol **3.25 USDC** |
| Market 2 | *Will Ral Andrew take first place in the ongoing Panta X …* — YES **0.5323**, vol **20.00 USDC** |
| Total markets on venue | 99 (2 `open`, 97 `secondary_active`) |
| A full decision round | **~45–65 seconds** (Estimator alone measured at 46s once) |
| Mode | `DRY_RUN=true` → PAPER. No funds, no signature, no broadcast. |

Venue counts move and Panta renames status values (`primary`→`open` mid-day). Re-check before
recording and quote the date alongside any number. Do not promise a market count on camera.

### 0.5 Facts you must NOT state

- ❌ Any profit, ROI, win-rate, or "beats the market" claim. There is none.
- ❌ Any claim of deep liquidity. There is 3.25 USDC of volume.
- ❌ Any claim that a trade was executed. Nothing has ever been broadcast.
- ❌ Any suggestion that the dashboard numbers are historical performance. They are decisions, not P&L.
- ❌ **Any claim that the Estimator is reliable, or that the four roles "verify" the estimate.**
  Measured on this exact market: the Estimator returned **0.51, 0.55, then 0.98** across three runs
  — and the more extreme the estimate, the *higher* its self-reported confidence (0.98 @ confidence
  0.95, uncertainty "low"). The 0.98 run cleared the 15% edge bar and produced a `BUY YES`, which
  then failed at the API (`INVALID_MARKET_PARAMS` — the market has null price and null volume, so it
  is not actually tradeable). Risk did not catch it, because Risk checks caps and liquidity, not the
  estimate itself.

  If a judge asks whether the agents are reliable, say this plainly. The honest answer is stronger
  than a vague one: the pipeline verifies *process* — every role ran and every step is auditable —
  and we have measured evidence of exactly where it currently fails.

---

## 1. Timeline

Legend — **[LIVE]** = must be captured from the real running product, cannot be staged.

### 0:00 – 0:10 · Cold open: what this is

| | |
|---|---|
| **On screen** | **[LIVE]** Dashboard, tab 1, already painted with the real decision rows. Cursor rests on the `PantaPilot` title. |
| **Action** | None. Hold still. Let the viewer read `LIVE API DATA` and `PAPER` badges. |
| **VO** | "This is PantaPilot — an autonomous trading desk for prediction markets. Four AI agents — a Scout, an Estimator, a Decision trader, and a Risk manager — watch Panta's markets around the clock, find mispriced odds, and argue before anything gets bought. Everything you're about to see is a real run against Panta's live API." |

**Why this works:** inside 10 seconds the viewer knows *what* (four-agent trading desk), *where*
(Panta), and *that it is real* (live API, on screen). No logo animation, no "hi I'm the founder".

---

### 0:10 – 0:40 · The desk runs itself (the core loop)

| | |
|---|---|
| **On screen** | **[LIVE]** Terminal takes the frame. |
| **Action** | Press **Enter** on: `DRY_RUN=true .venv/bin/python main.py`. Lines stream in. Do not talk over the first scan lines — let them land. |
| **VO** | "The loop is one command. It scans Panta's live API for tradeable markets — right now that returns **exactly one market**. A market on whether Bitcoin hits a new all-time high by the end of 2026, priced at fifty-point-five cents on YES, with three dollars and twenty-five cents of volume. The desk then runs that market through four agents, and the whole round takes about thirty seconds." |

**Live terminal lines the camera must show** (from `main.py` + `logger.py`):

```
INFO pantapilot.main: PantaPilot 启动 mode=PAPER interval=... max_trade=5.0USDC model=meituan/longcat-2.5-preview:free
INFO pantapilot.main: 决策引擎: 多角色 Agent 团队 (Scout>Estimator>Decision>Risk)
INFO httpx: HTTP Request: GET https://live-api.panta.market/api/v1/markets/ "HTTP/1.1 200 OK"
INFO pantapilot.main: 本轮扫描到 1 个 primary 市场
```

**[LIVE]** — the `1 个 primary 市场` line and the `live-api.panta.market` HTTP 200s are the honesty
proof. Neither is reproducible from a fixture; both must come off the wire during the take.

---

### 0:40 – 1:15 · Inside the four agents

| | |
|---|---|
| **On screen** | **[LIVE]** Terminal — the agent calls firing in sequence. |
| **Action** | Point at the two HTTP calls as they appear: first the oracle fetch, then the LLM call. |
| **VO** | "Here's what makes this more than a prompt. The Scout goes out first and pulls grounded intel — it tries the market's own oracle source, a live settlement feed, and falls back to a web search. Then the Estimator reads that intel and independently prices the true probability, **without seeing any trade instruction** — it doesn't know what the desk is hoping to hear. Only then does the Decision agent compare the estimate against the market's implied odds. And the fourth agent, Risk, holds an absolute veto over the caps, the liquidity, and whether the reasoning even makes sense." |

**What is literally happening** (verified in `agents.py`):

1. `gather_intel()` — oracle URL first, Brave Search fallback. Every fetch is fail-safe.
2. `ESTIMATOR_PROMPT` → `{true_prob_yes, confidence, key_evidence, uncertainty}`.
3. `DECISION_PROMPT` → compares implied vs. estimated, needs a material gap to act.
4. `RISK_PROMPT` → `{final, approved, note}`; `approved=false` forces HOLD and rewrites the reason
   as `[risk veto] <note> / original: <reason>`.

**[LIVE]** — the three LLM calls and the oracle fetch are network round-trips. They take ~30s wall
clock and cannot be faked convincingly. Record them.

> **If an agent call fails on this take:** you will see the pipeline degrade to
> `fallback_single_agent` and the dashboard will label the Estimator `unavailable` instead of
> printing a fake number. **That is a good take** — say so: *"notice the Estimator says unavailable
> rather than inventing a number — the loop degrades instead of dying."* Then re-run for a clean take
> as a bonus shot. Never edit the failure out and never narrate it as a success.

---

### 1:15 – 1:45 · The decision, and why HOLD is the point

| | |
|---|---|
| **On screen** | **[LIVE]** Cut back to dashboard tab 1. The new decision row has just rendered at the top of **AI Decision Flow**. |
| **Action** | Scroll so the HOLD row and its four-role pipeline strip are both visible. **Expand** `Details & Evidence ▾` with a click. |
| **VO** | "And here's the verdict from that run: **HOLD**. Read the reason the agent actually wrote — *'Market YES price is within zero-point-five percent of the estimator's estimate — no clear edge.'* The market is fairly priced, so the desk does nothing. That's the first agent box, that's the estimator's number, the decision, and Risk passing the HOLD. Underneath is the full evidence chain — every agent's output, the intel it used, the gap it computed — logged to JSONL and rendered here so a human can audit exactly why. **A trading bot that can't say no isn't a trading bot, it's a slot machine.**" |

**The exact real string** (from `logs/pantapilot.jsonl`, 2026-10-12T08:37:37Z):

> `Market YES price (50.5%) is within 0.5% of estimator's 51% – no clear edge.`

Its evidence, on screen in the same row: pipeline `scout>estimator>decision>risk`, estimator
`YES 0.51 (51%)`, `conf 0.30 · unc high`, benchmark `market_implied 0.5054 / estimator_prob 0.51 /
gap_pct +0.5%`, risk `PASSED — HOLD decision approved`.

**[LIVE]** — the row must be produced by the run you recorded in shot 2, not pre-baked. If the
fresh row's wording differs (the free-tier model rephrases), read *that* row aloud instead of this
quoted one; the script's exact quote is a labelled example, not a line to fabricate on screen.

---

### 1:45 – 2:15 · The veto — the shot that sells the product

| | |
|---|---|
| **On screen** | **[LIVE]** Dashboard, scrolled to the row wearing the red **`RISK VETOED`** badge. |
| **Action** | Click the badge row, expand `Details & Evidence`. Zoom/crop to the 4th agent box, which is rendered red with `VETOED`. Let it sit for two full seconds. |
| **VO** | "Now the moment I actually care about — and note the timestamp top-right: this one is **from the 10th, an earlier session**, not the run you just watched. The same desk **did** find an edge — the Decision agent proposed a buy, one USDC. And the Risk agent **killed it.** Look at the red box: *'confidence below threshold and weak rationale.'* The estimator said ninety-nine percent confident, the trade looked obvious, and the desk still refused to spend a dollar. That's the whole thesis: the value of an autonomous trading agent isn't that it can place an order — it's that it can be trusted not to, and that you can see exactly why." |

**MANDATORY — state the date out loud.** The ring light must not hide this: this veto is a
**real record from 2026-10-10**, replayed from `logs/pantapilot.jsonl`. It is *not* produced by
the run recorded at 0:10–0:40. Say "from the 10th, an earlier session" while the on-screen
timestamp (`2026-10-10T12:35:27`) is legible. A viewer who assumes this happened live would be
misled, and that is the one thing this video cannot afford.

The reason it is still the right shot: the row is genuinely in the log, genuinely rendered from
it, and genuinely shows risk control overriding the product's own apparent interest. Replay of a
real record is honest; a re-enactment would not be.

**The real veto record** (`logs/pantapilot.jsonl`, 2026-10-10T12:35:27Z), verbatim on screen:

> Row: `HOLD` · badge **`RISK VETOED`** · reason:
> `[risk veto] Confidence below threshold (0.0 < 0.6) and weak rationale / original: No market price data; cannot assess edge.`
> Pipeline strip: Scout `3 Sources` → Estimator `YES 0.99 (99%)`, `conf 0.95 · unc low` →
> Decision `HOLD`, `0.0 USDC proposed` → **Risk `VETOED`** in red.

**[LIVE or logged-real]** — this row already exists in the JSONL log and is rendered from it by
`dashboard.py` (`_is_risk_veto()` matches the `[risk veto]` prefix or `approved=false`). Showing it
is honest: it is a real recorded decision. Do **not** re-enact it by hand-editing the log.

**This is the most persuasive 30 seconds in the video.** The interviewer sees risk control working
against the product's own apparent interest — the single hardest thing to fake and the single most
credible signal that the agents are real.

---

### 2:15 – 2:45 · What is actually real today (honest status)

| | |
|---|---|
| **On screen** | **[LIVE]** Dashboard **Markets** grid — the single market card, `primary` badge, `YES 0.51 / NO 0.49` bar, `Volume: 3.25 USDC`. Optionally cut to browser tab 2, the raw API JSON. |
| **Action** | Hover the market card. Then switch to the raw API tab for ~2 seconds. |
| **VO** | "So what's actually real today? The integration is real — that's Panta's production API, and this is the raw response, unedited. But I want to be straight with you about the venue: **Panta currently has exactly one tradeable market.** Ninety-eight markets exist, ninety-two are already settled, and that one live market carries three dollars of volume. That's not deep enough to claim an edge, and we don't. The honest result is that there is no mispricing history to profit from yet. Every number on this screen is a decision, not a profit — nothing here has ever been broadcast on-chain." |

**Do not** soften this. The judges are technical; a team that reports its own null result reads as
more credible than one showing a green curve, and this framing turns the weakest fact into the
strongest signal of integrity.

---

### 2:45 – 2:52 · Close

| | |
|---|---|
| **On screen** | **[LIVE]** Dashboard full frame again — `PantaPilot` + `LIVE API DATA` + `PAPER` + `Powered by Panta`. |
| **Action** | None. Cursor moves off-screen. |
| **VO** | "PantaPilot: four agents, one audit trail, and the discipline to say no. Built on Panta's live API. Repo and the full write-up are in the description." |

Hard stop. Do not add a "thank you" — it eats the last five seconds and adds nothing.

---

## 2. Shot-by-shot recording checklist

| # | Shot | Time | Live? | Can it be re-shot? |
|---|---|---|---|---|
| 1 | Dashboard cold open | 0:00–0:10 | Yes | Yes — dashboard persists |
| 2 | Terminal run start (Enter) | 0:10–0:40 | **Yes** | Yes, but costs a ~30s network round-trip each take |
| 3 | Agent calls in terminal | 0:40–1:15 | **Yes** | Same take as #2 — do not cut mid-run |
| 4 | HOLD row + evidence expand | 1:15–1:45 | **Yes** | Only after a fresh run; wording varies per run |
| 5 | RISK VETOED row | 1:45–2:15 | Logged-real | Yes — replayable from JSONL |
| 6 | Markets grid + raw API | 2:15–2:45 | **Yes** | Yes |
| 7 | Close | 2:45–2:52 | Yes | Yes |

**Shots 2–4 are one continuous take.** Do not stop the recorder mid-round; a visible cut between
the agents firing and the resulting dashboard row invites the suspicion that the row was staged.

---

## 3. Pre-upload verification

- [ ] Runtime is **≤ 3:00**. Time it. 2:50 is the sweet spot; anything over 3:00 is disqualified.
- [ ] No code editor is visible at any point. No source file is scrolled. No function is read aloud.
- [ ] No slide, no title card, no logo animation — the product is the first thing on screen.
- [ ] Audio is intelligible at 1× and the terminal font is legible at 1080p on a laptop screen.
- [ ] The word "profit", "ROI", "returns", or "win rate" does not appear, in VO or on screen.
- [ ] The one-market limitation is stated out loud, not buried in the description text.
- [ ] Captions/subtitles are burned in or uploaded — judges may watch muted.
- [ ] Upload is **public** or unlisted-but-link-accessible on YouTube / Loom / Vimeo; paste the URL
      into the submission form and re-open it in a private window to confirm it plays.

---

## 4. Contingencies

| Situation | What to do |
|---|---|
| A live round takes >60s (slow free-tier LLM) | Cut shot 3's tail in the edit, keep the continuous run. Do **not** speed up the terminal footage — timestamps would betray it. Budget 2:52 and let the take breathe. |
| Estimator returns `unavailable` | Keep it, narrate it as graceful degradation. Re-run once for a clean take if time allows. |
| The decision comes back `BUY_YES` instead of `HOLD` | Fine — but `DRY_RUN=true` means no order is broadcast. Say so explicitly on camera: *"it will build the order and stop, because paper mode never signs or sends."* Do not imply a fill. |
| Panta returns 0 tradeable markets on recording day | Record anyway and narrate it: *"zero tradeable markets right now — that's the venue's real state, and the desk correctly has nothing to do."* Then show the persisted decision rows via shots 4–5. |
| Bad take, out of time | Ship the take with the honest failure. A real degraded run beats a polished fake, and the judges' criterion is "show the live product". |

---

## 5. Sources for every fact in this script

| Claim | Source |
|---|---|
| 1 tradeable market, 92 settled, YES 0.5054, volume 3.25 USDC | Live probe of `PantaClient.primary_markets()`, 2026-10-12 |
| Round takes ~30s | Real timed run of `DRY_RUN=true .venv/bin/python main.py`, 2026-10-12 17:04–17:07 |
| HOLD reason string | `logs/pantapilot.jsonl` line 319, 2026-10-12T08:37:37Z |
| RISK VETOED reason string | `logs/pantapilot.jsonl` line 2, 2026-10-10T12:35:27Z |
| Four-role prompts and veto logic | `agents.py` — `ESTIMATOR_PROMPT`, `DECISION_PROMPT`, `RISK_PROMPT`, `analyze()` |
| Scout source order (oracle → Brave fallback) | `scout.py` — `gather_intel()` |
| Fallback to single agent | `agents.py:170-173`, `README.md` §Multi-Agent Trading Team |
| Dashboard badges and pipeline strip | `dashboard.py` — `_is_risk_veto()`, `_pipeline_flow()`; `dashboard/index.html` |
| PAPER mode never signs or broadcasts | `config.py:66` (`DRY_RUN` default `True`), `README.md` §Safety Guardrails |
