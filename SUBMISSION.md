# PantaPilot — Submission

**Colosseum Crypto World's Fair · Panta API Sidetrack**

## What it is

PantaPilot is an autonomous AI trading agent for Panta's prediction markets. It continuously scans live markets, uses a free LLM to detect mispriced events, and places small trades when it finds a real, articulable edge. Every decision is logged and surfaced on a self-refreshing dashboard.

## Core loop

```
Scan markets → gather intel → estimate probability → find edge → risk check → place order on edge → log decision → render dashboard
```

## Why it stands out

- **Multi-agent team with live intel gathering.** Not a single static LLM call: a Scout gathers real intelligence (official oracle settlement feeds + web search), an Estimator independently estimates the true probability, a Decision agent compares it against the market's implied probability to find a specific edge, and a Risk manager holds veto power. The full evidence chain is logged and rendered — every decision is auditable.
- **Full, real Panta API integration.** All five steps of the order chain are real HTTP calls (quote → build → sign → submit → verify), not mocks.
- **Safety first.** DRY_RUN on by default, per-trade cap, dedicated small wallet, keys gitignored and revocable.
- **Visible product.** A live dashboard shows tracked markets, the AI decision stream, confidence bars, and price bars.

## Roadmap / impact

- **Now:** single-wallet, primary-market edge discovery.
- **Next:** secondary-market trading, agent debate/ensemble before committing, position & claim automation.

## Judging criteria coverage

| Criterion | Coverage |
|---|---|
| Panta API integration | Full live 5-step order chain, non-mocked |
| Technical implementation | Five-step chain + safety guardrails + fault tolerance |
| Product/UX | Self-refreshing dashboard with decision flow & price bars |
| Originality | Multi-agent team (Scout → Estimator → Decision → Risk) with live intel + evidence chain, not copy-trading |
| Impact potential | Extends to secondary markets, multi-agent debate |
| Traction | Decision log is the seed; live money trading is a bonus |

## Run it

See `README.md`. Default mode is **PAPER** (`DRY_RUN=true`) — no real money until you opt in.

## Links

- GitHub: (repository URL)
- Demo video: (link)

---

Powered by **Panta**.