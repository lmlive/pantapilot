# PantaPilot

> AI prediction-market trading agent — Colosseum Crypto World's Fair hackathon · Panta API Sidetrack ($5,000)

**🎬 Demo video (90s): [`docs/demo.mp4`](docs/demo.mp4)** — a real live-API run: terminal, four-agent pipeline, the decision evidence chain, and the dashboard.

**📄 Full submission write-up: [`SUBMISSION.md`](SUBMISSION.md)**
**📋 Submission checklist & paste-ready text: [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md)**

**PantaPilot** scans Panta's prediction markets around the clock, uses an LLM to find mispriced events, and places small trades when it detects a real edge. The core loop:

**Scan markets → gather intel → estimate probability → find edge → risk check → place order on edge → log decision → render dashboard**

> **Honest status:** the integration is real and runs against the production Panta API, but the
> venue currently has **1 tradeable market** and almost no mispricing history — so the strategy
> correctly returns `HOLD` and **we claim no trading profit**. See the Traction & Evidence section
> of [`SUBMISSION.md`](SUBMISSION.md), and run `python backtest_real.py` to reproduce the null result.

## Why

Short-horizon prediction markets (sports, esports, etc.) move faster than any human can watch. Retail users cannot monitor dozens of markets all day and catch mispriced odds. PantaPilot automates that with a multi-agent team: a Scout gathers live intel (official settlement feeds + web search), an Estimator independently estimates the true probability, a Decision agent compares it against the market's implied price, and a Risk manager holds veto power — acting only when there is a specific, articulable edge.

## Architecture

```
main.py         Orchestrator: scan → analyze → trade → log → dashboard loop
panta.py        Panta HTTP API client (markets + 5-step order chain)
agents.py       Multi-agent team: Estimator → Decision → Risk
scout.py        Scout: intel gathering (oracle sources + web search)
llm.py          Single-agent fallback (OpenAI-compatible / OpenRouter)
trader.py       Order execution (dry-run semi-chain + full live chain)
logger.py       JSONL event logging
dashboard.py    Static self-refreshing HTML dashboard (with evidence chain)
config.py       Config + safety guardrails
```

## Multi-Agent Trading Team

Instead of one static LLM call, each market goes through a trading-desk pipeline:

```
┌──────────────────────────────────────────────────────────┐
│ ① Scout (scout.py)                                       │
│    Gathers live intel: the market's official ORACLE      │
│    data sources first (settlement feeds like the FPL     │
│    API), then Brave Search snippets as fallback.         │
│    All fetches are fail-safe (empty intel on error).     │
├──────────────────────────────────────────────────────────┤
│ ② Estimator (agents.py)                                  │
│    Independently estimates the TRUE probability from     │
│    market fields + intel → {true_prob_yes, confidence,  │
│    key_evidence, uncertainty}                            │
├──────────────────────────────────────────────────────────┤
│ ③ Decision (agents.py)                                   │
│    Compares market implied probability vs. estimator's  │
│    estimate; trades ONLY on a material, articulable edge  │
│    → {decision, confidence, reason, suggested_usdc}      │
├──────────────────────────────────────────────────────────┤
│ ④ Risk (agents.py)                                       │
│    Veto power: rejects proposals with low confidence,    │
│    near-zero volume, or cap violations → forced HOLD    │
└──────────────────────────────────────────────────────────┘
```

- **Degradation:** if any agent step fails, the pipeline falls back to the single-agent static analysis (`evidence.pipeline = "fallback_single_agent"`) — the loop never dies.
- **Evidence chain:** every stage's output is logged to JSONL and rendered as an expandable "Evidence chain" block on the dashboard — the full audit trail of how a decision was reached.
- New env vars:

| Var | Default | Meaning |
|---|---|---|
| `AGENTS_ENABLED` | `true` | `false` reverts to single-agent static analysis |
| `SCOUT_SEARCH_ENABLED` | `true` | Enable Brave Search fallback when no oracle source exists |

## Quick Start

```bash
# 1. Set up env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure keys
cp .env.example .env   # fill in PANTA_API_KEY, LLM_API_KEY, wallet
chmod 600 .env

# 3. Run (DRY_RUN defaults to true — no real money)
python main.py

# 4. Open the dashboard
open dashboard/index.html   # auto-refreshes every 60s
```

## Safety Guardrails

- **`DRY_RUN=true` by default** — the bot only quotes and builds an unsigned transaction, then stops. It never signs or broadcasts. Set `DRY_RUN=false` only when you are ready for real money.
- **`MAX_TRADE_USDC`** caps each trade (default 5 USDC).
- Use a **dedicated small-funded keypair**, never your main wallet.
- Keys live in `.env` (chmod 600, gitignored). Revoke API keys after the event.

## Panta API integration

Fully real, non-mocked calls (live base URL `https://live-api.panta.market/api/v1`):

1. `POST /primaryorderquote/` — get a quote (`quoteId`, ~60s expiry)
2. `POST /primaryorderbuild/` — build unsigned transaction (before quote expires)
3. Local signing with `solders` + RPC broadcast
4. `POST /primaryordersubmit/`
5. `POST /primaryorderverify/`

`pk_test_` keys only see sandbox fake data — use an `env:"live"` key for real markets.

## Logs

JSONL at `logs/pantapilot.jsonl`, one event per line with `ts` (UTC ISO) and event type: `start / analysis / trade_start / trade_done / error / trade_dry_run`. Each `analysis` event carries the full `evidence` (pipeline name, estimator output, risk verdict, intel summary) — the dashboard and replay both read this file.

## Known pitfalls handled

- Cleans `no_proxy` entries containing `[` (avoids httpx `Invalid port: ':1]'`)
- Tolerant market-status parsing (case-insensitive + aliases)
- Handles `items` (not `results`) list field; `detail` prices may be null
- LLM timeout (60s) + 1 retry; free models are flaky — on failure it falls back to HOLD (or single-agent fallback in the multi-agent team)
- A single market failure never kills the loop
- Web intel fetches (oracle sources, Brave Search) are fail-safe: empty intel on any error

## Stack

Python · httpx · solders · base58 · openai (OpenRouter) · python-dotenv

LLM: OpenRouter `cohere/north-mini-code:free` (verified working).

---

Powered by **Panta**.