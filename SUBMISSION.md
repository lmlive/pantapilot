# PantaPilot — Autonomous 4-Agent Trading Desk on Panta Prediction Markets

**Colosseum Crypto World's Fair · Panta API Sidetrack ($5,000)**

---

## 🚀 The 10-Second Pitch: A 4-Agent Trading Desk in Action

**Picture this: Four specialized AI agents sitting around a live trading desk, deliberating before every single on-chain order.**

Instead of relying on a fragile, hallucinating single-prompt LLM or passive copy-trading, **PantaPilot** deploys an autonomous collaborative team:

```
[ 🕵️ Scout ] ➔ [ 📊 Estimator ] ➔ [ 🎯 Decision ] ➔ [ 🛡️ Risk ] ➔ [ ⚡ Solana On-Chain ]
 Live Feeds &      Bayesian True      Spots Mispricing     Enforces Hard      5-Step Panta Order
  Web Intel       Probability (72%)    Edge (>15% Gap)       Cap & Veto        (Quote➔Build➔Sign)
```

1. **🕵️ Scout (Intel Recon):** Intercepts live oracle settlement feeds and live web signals, filtering noise into grounded market facts.
2. **📊 Estimator (Quant):** Independently assesses the *true probability* of the outcome, producing a calibrated forecast (e.g., YES @ 72%) with explicit uncertainty metrics.
3. **🎯 Decision (Trader):** Measures the disparity between the market's implied odds and the Estimator's probability. When an edge exceeds **15%**, it decisively issues a `BUY` proposal with target position sizing.
4. **🛡️ Risk (Risk Manager):** Holds absolute veto power—vetts volume liquidity, wallet caps (default ≤ 5 USDC), and rationale validity before stamping `PASSED`.

Only when the team reaches verified consensus does PantaPilot execute the live transaction through Panta's 5-step non-custodial order chain.

---

## 🎬 What Judges See in the Demo & Dashboard

- **Live Horizontal Pipeline View:** Every analyzed market features an intuitive four-step visual cards flow: `Scout (Intel Found) ➔ Estimator (Probability) ➔ Decision (Edge Disparity) ➔ Risk (Approved)`.
- **Benchmark Disparity Highlighting:** Clear mathematical contrast: *"Market Implied 45.0% vs Model Assessed 72.0% (Gap: +27.0% Edge)"*.
- **Auditable Evidence Chain:** Judges can expand any decision to inspect raw oracle feeds, Brave search queries, confidence scores, and risk audit logs.
- **Honest Decision Discipline:** A single trade only fires when an articulable edge clears the threshold (`MIN_CONFIDENCE=0.6` plus a >15% probability gap). Because the Strategy is deliberately conservative, a live scan can legitimately end in `HOLD` — that restraint is the product working as designed, not a stalled demo.

---

## 🛠️ Full Panta API & Solana Integration (Zero Mocks)

PantaPilot connects directly to the production Panta API (`https://live-api.panta.market/api/v1`) and Solana mainnet:

1. **Quote (`POST /primaryorderquote/`):** Obtains live pricing and share calculations for 60-second locks.
2. **Build (`POST /primaryorderbuild/`):** Generates base64 unsigned transactions strictly within slippage tolerance (100 bps).
3. **Local Sign & Broadcast:** Signs locally with dedicated ephemeral keypairs and broadcasts via Solana RPC.
4. **Submit (`POST /primaryordersubmit/`):** Registers transaction signatures back with Panta.
5. **Verify (`POST /primaryorderverify/`):** Validates on-chain settlement and fills.

---

## 🛡️ Safety & Production Engineering

- **Paper Mode Is the Default (Not a Limitation):** `DRY_RUN=true` ships out of the box and drives the full order path up to the unsigned transaction — quote, build — then stops. Anyone can run PantaPilot end-to-end against the live Panta API **without a funded wallet and without risking a cent**. Flip `DRY_RUN=false` with a dedicated small keypair to broadcast. So the demo video you are watching is a real live-API run in paper mode; no capital was deployed and no profit is claimed.
- **Strict Risk Guardrails:** Per-trade USDC limit (`MAX_TRADE_USDC=5.0`), illiquidity vetoes, and zero unauthenticated broadcasts.
- **Self-Healing Network Layer:** Automated proxy environment normalization (`clean_no_proxy()`) guaranteeing robust HTTP connectivity in sandboxed developer environments.
- **Fast Demo Execution:** Intelligent curation sorts for high-volume, oracle-backed markets, condensing execution cycles to a few high-impact opportunities ideal for 90-second video presentations.

---

## 📊 Judging Criteria Matrix

| Criterion | How PantaPilot Delivers |
|---|---|
| **Panta API Integration** | **Complete 5-Step Order Chain.** Quotes, builds, signs, submits, and verifies against live Panta endpoints—zero mocks. |
| **Technical Excellence** | **4-Role Agent Architecture.** Scout, Estimator, Decision, and Risk running structured prompts, graceful fallbacks, and real-time state synchronization. Degrades to single-agent analysis rather than crashing if any step fails. |
| **Product / UX** | **Cyber-Terminal Dashboard.** Auto-refreshing web dashboard with horizontal pipeline flow cards, price bars, and real-time trade logs. |
| **Originality** | **Deliberative AI Desk.** Moves beyond naive single-prompt predictors to multi-agent checks-and-balances with quantifiable margin-of-safety gating. |
| **Impact & Viability** | **A monitoring desk that scales with the venue.** See the productization path below — the same four-agent loop generalizes to signal pushing, multi-venue coverage, and delegated execution. |

---

## 📈 Traction & Evidence (what is real, measured today)

We would rather show you the true numbers than a flattering graph.

**What we measured.** PantaPilot has been run repeatedly against the live Panta API
(`https://live-api.panta.market/api/v1`), writing a full JSONL audit trail — every scan,
every agent step, every decision. A captured sample run ships in the repo at
[`demo_capture/run.jsonl`](demo_capture/run.jsonl) (regenerate it with
`python run_demo_capture.py`; live runs write to the gitignored `logs/`).

**What the live venue currently looks like (sampled 2026-10-12).** Of 98 markets returned
by `/markets/`: **92 settled, 97 in `secondary`, and exactly 1 in `primary` (tradeable).**
That single primary market returned `yesPrice: null`, `noPrice: null` and zero volume.
A live scan therefore analyzes a very small opportunity set, and the Decision agent's
disciplined answer is often `HOLD`.

**We tried to backtest it, and we are reporting the null result.** `backtest_real.py`
pulls *real* settled markets (not hand-written samples) and evaluates the strategy's
own selection rule against the real pre-resolution price and the real outcome.

The count moves as markets settle, so run it yourself rather than trusting a number
transcribed here. A representative run on 2026-10-12 returned:

```
Settled markets with usable price+outcome: 8
Actionable (edge >= 15%, volume >= 10 USDC): 0
Max |entry - 0.50| observed: 0.018
```

Every settled market on the venue resolved near 50/50 with volumes in the tens of USDC.
**There is not enough mispricing history on Panta today to demonstrate a positive
historical edge, so we do not claim one.** (An earlier internal script reported a
100% win rate from a hard-coded sample list; we removed that claim — it was not data.)

**What this means for a judge.** The value here is not a claimed P&L. It is:
1. **A working, non-mock integration** proven against production endpoints.
2. **A measured market observation** — the real constraint on this strategy is *venue
   liquidity*, and we can state it precisely instead of guessing.
3. **A falsifiable harness** — `backtest_real.py` is the exact tool that will report a
   positive result the moment the venue has enough volume to produce one. It is honest
   by construction, which is what you want in an autonomous trading agent.

---

## 🛠️ Productization Roadmap (beyond the hackathon demo)

PantaPilot is not a one-off script; it is the decision core of a monitoring product.
Each step below reuses the same Scout ➔ Estimator ➔ Decision ➔ Risk loop.

**Phase 1 — Signal delivery (next, ~2 weeks).** The four-agent pipeline already produces a
structured, auditable verdict per market. The immediate next step is a **Telegram bot** that
pushes a signal card the moment the desk finds an edge — market, implied vs modelled
probability, the gap, the risk verdict, and a one-tap link to the market. This turns a
dashboard you must visit into an alert you receive, which is what a real trader wants.
The same JSON payload feeds Discord or a webhook, so the channel is a config choice.

**Phase 2 — Coverage and scheduling.** Run the desk as a persistent worker (systemd /
container) across every tradeable market, with per-category models (sports vs crypto vs
macro), a daily digest of passes *and* trades, and alerting when the venue's liquidity
crosses a usable threshold. Because the venue is thin today, the honest first product is
**monitoring + alerting**, not capital deployment.

**Phase 3 — Delegated execution.** For opted-in users, expose the same pipeline as a
one-click or auto-execute layer under hard, user-set caps (per-trade, per-day, per-market),
with the Risk agent's veto enforced on-chain rather than by convention. The paper-mode
default already makes this a safe trial: users watch real decisions against real markets
before enabling a single dollar.

**Why this is more than a demo.** The hard part of an autonomous agent is not placing an
order — it is the *deliberation and the audit trail* that make a human willing to trust it.
That part is built, logged, and rendered. Signal pushing is distribution, and distribution
is what turns this repository into a product.

---

## 🏁 Quickstart

```bash
# Clone and enter repo
git clone https://github.com/lmlive/pantapilot.git
cd pantapilot

# Set up a virtualenv and install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
# Edit .env with your PANTA_API_KEY and LLM_API_KEY (defaults to free OpenRouter model)

# Run in paper mode (scans live markets, runs the 4-agent desk, writes logs/, renders dashboard)
python main.py

# Open the rendered dashboard
open dashboard/index.html
```

**Verifying the integration without a wallet:** keep `DRY_RUN=true` (the default). The full
Scout ➔ Estimator ➔ Decision ➔ Risk loop runs against the live Panta API and drives the order
path through quote + build. Nothing is signed and nothing is broadcast.

**Reproduce the traction section:**

```bash
# Real settled markets, real outcomes — prints a null result today, by design.
python backtest_real.py
```

---

## 🔗 Links

| | |
|---|---|
| **GitHub repository** | https://github.com/lmlive/pantapilot |
| **Demo video (90s)** | [`docs/demo.mp4`](docs/demo.mp4) (also linked at the top of the README) |
| **Live dashboard snapshot** | [`docs/dashboard_full.png`](docs/dashboard_full.png) |
| **Decision audit log (sample)** | [`demo_capture/run.jsonl`](demo_capture/run.jsonl) — raw JSONL, one event per line |
| **Panta API reference used** | `https://live-api.panta.market/api/v1` (`/markets/`, `/primaryorderquote/`, `/primaryorderbuild/`, `/primaryordersubmit/`, `/primaryorderverify/`) |

---

*Powered by **Panta** & Solana.*
