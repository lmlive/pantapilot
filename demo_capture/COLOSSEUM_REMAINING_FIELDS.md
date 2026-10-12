# Colosseum 项目提交 · 剩余字段（复制粘贴用）

项目草稿已创建：**PantaPilot**，类别 **AI Platforms / Agents**
编辑页：https://colosseum.com/arena/hackathon/project/editor?section=details

> ⚠️ **保存方式**：这个编辑器长文本**不自动保存**。填完所有字段后
> **点一次 `Save draft`（或 `Save and view project`）**，再刷新确认。
> 中途刷新 = 未保存的长文本全部丢失。

---

## 已持久化（不用重填）

| 字段 | 值 |
|---|---|
| Project name | `PantaPilot` |
| Brief description | 409/500 已存 |
| Category | `AI Platforms / Agents` |

---

## 1. Project website

```
https://github.com/lmlive/pantapilot
```

---

## 2. What are you building, and who is it for? *（上限 1000）*

```
PantaPilot is an autonomous trading desk for Panta prediction markets, for traders who cannot watch dozens of short-horizon markets all day.

Most AI trading bots are one prompt and one guess. PantaPilot runs four roles that deliberate before any order:

1. Scout - pulls the market oracle sources, then falls back to live web search.
2. Estimator - independently prices the true probability with an uncertainty label, before seeing any trade decision.
3. Decision - compares market-implied odds against the model estimate, trading only when the gap is material.
4. Risk - holds veto over caps, liquidity and rationale quality; a veto forces HOLD.

Consensus then flows through Panta's real 5-step order chain against the production API (quote, build, sign, submit, verify). DRY_RUN is the default, so anyone can reproduce it with no capital at risk.

Every agent step is logged to JSONL and rendered as an expandable evidence chain on a dashboard, so a human can audit exactly why an order happened.
```

---

## 3. Why did you decide to build this, and why build it now? *（上限 1000）

```
Short-horizon prediction markets reprice faster than any human can watch. Retail traders cannot monitor dozens of markets all day, so mispricings appear and vanish before anyone acts. The gap is not a lack of models - it is a lack of an always-on desk that can deliberate and act.

We built it now because Panta exposes a genuine non-custodial order chain over a real API, which makes an autonomous agent meaningful rather than theoretical: it can scan, reason, and reach execution without us holding user funds.

We also wanted to test an uncomfortable hypothesis honestly. A real backtest against settled markets showed Panta's venue is still thin - one tradeable market, settlements within 1.8% of 50/50. There is no mispricing history to claim profit from yet. We report that null result rather than fabricate a win rate, because an agent that lies about its edge is worse than no agent.
```

---

## 4. What technologies are you using or integrating with? *（上限 500）

```
Panta REST API (markets + primary order chain); Solana via solders/base58 for local signing; Python 3 with httpx, feedparser and OpenAI/Anthropic-compatible LLM clients; Brave Search API for web intel; JSONL audit logs; Playwright for dashboard capture. Built with Claude Code and DeepSeek Harness as coding agents.
```

---

## 5. Which chains does your product use? *

勾选 **Solana**（只勾这一个）

---

## 6. How does your product use these chains? *（上限 500）

```
PantaPilot executes trades on Panta, a Solana-based prediction market. Orders are built by Panta's API, signed locally, and broadcast to Solana - the agent never takes custody of funds at any point.
```

---

## 7. Where is your team primarily based? *

选 **China**

---

## 8. Please share a team Telegram contact *

```
@kkdmili
```

---

## 9. Notes for judges（选填，建议填第二条）

**"Did anyone not listed on the team do meaningful work?"（上限 600）**

```
Yes - AI coding agents did meaningful implementation work. PantaPilot was built with Claude Code and DeepSeek Harness operating as coding agents: they wrote and refactored the four-agent pipeline, the Panta API client, the dashboard, and the tests. The human author set direction, reviewed every change, and is responsible for all decisions and claims in this submission.
```

**"Anything else judges should know?"（上限 500）**

```
Two things. First, our demo video's terminal scene is a faithful re-drawing of real captured run output, not a screen recording - the content is verbatim from an actual live run, but we would rather you know exactly what you are looking at. Second, our backtest reports a null result rather than a win rate: Panta's venue currently has one tradeable market and no mispricing history. The integration is real and reproducible; the edge is not demonstrated yet.
```

---

## 10. 保存后

- [ ] 点 **Save draft**，然后刷新页面确认所有字段还在
- [ ] 切到 **Media and code** 标签（4 个字段待填：仓库、视频等）
- [ ] 核对无误后走最终提交
- [ ] 去 **Superteam Earn** 用同样内容再交一次（双平台都要交）

提交截止：**2026-10-12 23:59 PDT = 北京时间 10-13 14:59**
