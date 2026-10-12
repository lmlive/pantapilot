# PantaPilot — Submission Checklist (copy-paste reference)

> Generated 2026-10-12. Everything below is verified against the live repo/API, not assumed.
> Use this to fill the Colosseum main-competition form and the Superteam Earn listing.

---

## 0. TL;DR — what is still on you

| # | Item | Status | Who |
|---|---|---|---|
| 1 | Demo video | ✅ **Done** — `docs/demo.mp4`, 93s, 1.25 MB, public | — |
| 2 | Repo public | ✅ **Done** — verified anonymous 200 | — |
| 3 | Colosseum main-competition registration | ❌ **NOT DONE** — needs your login | **You** |
| 4 | SUBMISSION.md fixes (traction / wording / links) | ✅ Done | — |
| 5 | Impact potential → productization roadmap | ✅ Done | — |

**The only blocking item is #3.** You must register/submit on Colosseum yourself; it needs
your account and email verification. Earn alone does not count (double submission required).

---

## 1. Canonical facts (use these exact strings)

| Field | Value |
|---|---|
| Project name | **PantaPilot** |
| One-line pitch | Autonomous 4-agent trading desk that finds and acts on mispriced Panta prediction markets |
| GitHub (public) | `https://github.com/lmlive/pantapilot` |
| Demo video | `https://github.com/lmlive/pantapilot/blob/master/docs/demo.mp4` |
| Raw video (direct) | `https://raw.githubusercontent.com/lmlive/pantapilot/master/docs/demo.mp4` |
| Dashboard snapshot | `https://raw.githubusercontent.com/lmlive/pantapilot/master/docs/dashboard_full.png` |
| Track | Panta API Sidetrack ($5,000) · Colosseum Crypto World's Fair |
| Stack | Python, Panta REST API, Solana (solders/base58), OpenAI-compatible LLM, static HTML dashboard |
| License / cost to run | Runs free — paper mode by default, needs only a free OpenAI-compatible LLM key (we use `meituan/longcat-2.5-preview:free`) |

---

## 2. Paste-ready description (short)

> **PantaPilot — the four-agent trading desk for Panta prediction markets.**
>
> Most "AI trading" bots are one prompt and one guess. PantaPilot runs a desk: a **Scout**
> pulls live oracle + web intel, an **Estimator** independently prices the true probability,
> a **Decision** agent measures the gap against the market's implied odds, and a **Risk**
> agent holds veto power over caps and liquidity. Only consensus reaches Panta's 5-step
> non-custodial order chain — quote, build, sign, submit, verify — with zero mocks.
>
> Every step is logged to JSONL and rendered as an expandable evidence chain on a live
> dashboard, so a human can audit exactly *why* any order happened.
>
> **We report measurements, not a flattering graph.** Run `python backtest_real.py` and you
> will see our honest null result: Panta's venue currently has 1 tradeable market and its
> settled markets resolved within 1.8% of 50/50, so there is no mispricing history to
> claim profit from. The integration is real; the edge is not there yet — and we'd rather
> tell you that than fake a 100% win rate.

---

## 3. Paste-ready description (long / if a bigger field is offered)

> **The problem.** Short-horizon prediction markets (sports, esports, crypto milestones)
> reprice faster than any human can watch. Retail traders cannot monitor dozens of markets
> all day, so mispricings appear and vanish before anyone acts.
>
> **What we built.** PantaPilot is an autonomous monitoring-and-decision desk with four
> specialised roles that deliberate before any order:
>
> 1. **Scout** — gathers grounded intel from the market's own oracle sources first, then
>    falls back to live web search. Fail-safe: empty intel never crashes the loop.
> 2. **Estimator** — independently assesses the true probability of the outcome, with an
>    explicit uncertainty label, deliberately *before* seeing the trade decision.
> 3. **Decision** — compares market-implied probability against the model's estimate and
>    only proposes a trade when the gap is material and articulable.
> 4. **Risk** — absolute veto over per-trade caps (`MAX_TRADE_USDC`), liquidity, and
>    rationale quality. A veto forces `HOLD`.
>
> Consensus then flows through Panta's real 5-step order chain against the production API
> (`https://live-api.panta.market/api/v1`). `DRY_RUN=true` (the default) runs the entire
> path up to the unsigned transaction and stops — so anyone can reproduce the full
> pipeline with no wallet and no capital at risk.
>
> **Why it is more than a demo.** The hard part of an autonomous agent is not placing an
> order; it is the deliberation and the audit trail that make a human willing to trust it.
> That part is built: every agent step is persisted to JSONL and surfaced as an expandable
> evidence chain on the dashboard. Phase 1 of our roadmap turns that decision core into a
> **Telegram signal bot** that pushes a verdict card the moment an edge appears, followed by
> a persistent multi-market worker and then opt-in delegated execution under user-set caps.
> Signal delivery is distribution — and distribution is what turns this repo into a product.

---

## 4. Video script (already rendered — use if you re-record with your own voice)

File: `docs/demo.mp4` (93s, 1920×1080, silent, subtitled). Scene map:

| Time | Scene |
|---|---|
| 0:00–0:06 | Title: PantaPilot, the four-role pipeline |
| 0:06–0:28 | **Terminal run** — the real captured output, lines printing in order with a scrolling window and cursor. It is a faithful re-drawing of `demo_capture/run_transcript.txt`, not a screen recording. |
| 0:28–0:40 | Pipeline diagram: why four roles beat one prompt |
| 0:40–0:54 | **Evidence chain**, verbatim from `demo_capture/run.jsonl` |
| 0:54–1:09 | Live dashboard: pipeline cards + market grid |
| 1:09–1:21 | "What is real today" — including the honest null backtest |
| 1:21–1:33 | Productization roadmap (Telegram bot → worker → delegated execution) |

Volunteer line to say in a live pitch: *"We found the venue has no mispricing history yet,
so we're reporting that instead of a fake ROI — here's the script that proves it."*

---

## 5. Colosseum main-competition submission — your steps

1. Go to the Colosseum Crypto World's Fair site and **log in / register** (needs your email).
2. Open your project and **create the submission** for the Crypto World's Fair hackathon.
3. Paste from §1–§3 above:
   - Project name, one-line pitch, long description.
   - GitHub URL, demo video URL.
4. **Select the Panta sidetrack** as the track/bounty you are entering.
5. Confirm the submission is **submitted**, not just saved as a draft — drafts do not count.
6. Capture the confirmation screen / URL as proof.

> I cannot do steps 1–6 for you: they require your account credentials and email
> verification, and I have no Colosseum access. Everything you need to paste is in §1–§3.

## 6. Superteam Earn submission — your steps

1. Open the Panta API Sidetrack listing on Superteam Earn.
2. Submit with the same §1–§3 material.
3. Verify the listing shows your submission as **submitted**.

**Both platforms are required.** Submitting only Earn does not count.

---

## 7. Reproducibility commands (for judges)

```bash
git clone https://github.com/lmlive/pantapilot.git
cd pantapilot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add any OpenAI-compatible LLM key; PANTA_API_KEY optional for paper mode

python main.py                # live scan -> 4-agent desk -> logs/ + dashboard
python backtest_real.py       # the honest null backtest (real settled markets)
python -m unittest test_agents.py   # 14 offline tests, no network
```

## 8. Known limitations to state honestly if asked

- **Venue liquidity is the binding constraint.** As of 2026-10-12 (evening): 99 markets, exactly
  1 tradeable (`primary`), 7 `secondary`, 92 resolved. The tradeable market carried 8.35 USDC of
  volume. Settled markets we could measure resolved within 1.8% of 50/50. No claimable edge yet.
- **Panta renames its status values and changes counts without notice.** During 2026-10-12 alone the
  tradeable count went 1 → 2 → 1, `primary` became `open` and back, and the secondary count swung
  from 97 to 7. `panta.py` normalises all of it (`_PRIMARY_ALIASES`), so the scanner survives — but
  never quote a venue count without its date.
- **The Estimator can be confidently wrong, and nothing downstream catches it.** Measured on one
  market and one model: 0.51, 0.55, then 0.98 across three runs, with self-reported confidence
  *rising* as the estimate got worse (0.98 at confidence 0.95, uncertainty "low"). The 0.98 run
  produced a `BUY_YES`; Risk approved it, because Risk checks caps and liquidity rather than
  re-deriving the estimate. State this if asked — do not claim the roles "verify" the estimate.
- **The LLM is a free-tier model.** Occasional failed calls are expected; the pipeline
  degrades to single-agent analysis and the dashboard labels the Estimator `unavailable`
  rather than inventing a number.
- **`lastYesPrice` is the last traded price,** not the price at decision time — so
  `backtest_real.py` measures strategy *selection*, not realised P&L.
- **No capital has been deployed.** Everything you see ran in paper mode.
