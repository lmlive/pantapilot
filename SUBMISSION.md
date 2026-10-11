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
- **Decisive Action:** Fine-tuned confidence thresholds (`MIN_CONFIDENCE=0.5`) and proactive edge discovery ensure live demonstrations showcase real, high-conviction `BUY` executions rather than passive `HOLD` stalls.

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

- **PAPER Mode by Default:** `DRY_RUN=true` out of the box stops at unsigned transaction building, letting anyone test safely without burning real funds.
- **Strict Risk Guardrails:** Per-trade USDC limit (`MAX_TRADE_USDC=5.0`), illiquidity vetoes, and zero unauthenticated broadcasts.
- **Self-Healing Network Layer:** Automated proxy environment normalization (`clean_no_proxy()`) guaranteeing robust HTTP connectivity in sandboxed developer environments.
- **Fast Demo Execution:** Intelligent curation sorts for high-volume, oracle-backed markets, condensing execution cycles to 3–5 high-impact opportunities ideal for 90-second video presentations.

---

## 📊 Judging Criteria Matrix

| Criterion | How PantaPilot Delivers |
|---|---|
| **Panta API Integration** | **Complete 5-Step Order Chain.** Quotes, builds, signs, submits, and verifies against live Panta endpoints—zero mocks. |
| **Technical Excellence** | **4-Role Agent Architecture.** Scout, Estimator, Decision, and Risk running structured prompts, graceful fallbacks, and real-time state synchronization. |
| **Product / UX** | **Cyber-Terminal Dashboard.** Auto-refreshing web dashboard with horizontal pipeline flow cards, price bars, and real-time trade logs. |
| **Originality** | **Deliberative AI Desk.** Moves beyond naive single-prompt predictors to multi-agent checks-and-balances with quantifiable margin-of-safety gating. |
| **Impact & Viability** | **24/7 Market Maker & Liquidity Provider.** Constantly patrols rapid sports/esports markets where human attention lags, capturing mispriced micro-windows. |

---

## 🏁 Quickstart

```bash
# Clone and enter repo
cd pantapilot

# Configure your environment
cp .env.example .env
# Edit .env with your PANTA_API_KEY and LLM_API_KEY (defaults to free OpenRouter model)

# Run in safe PAPER mode (evaluates 3-5 curated markets, triggers pipeline)
python main.py

# Open the live dashboard
open dashboard/index.html
```

---

*Powered by **Panta** & Solana.*
