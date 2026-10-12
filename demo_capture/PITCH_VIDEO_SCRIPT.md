# PantaPilot — Pitch Video Script (≤ 2:00)

**Purpose:** the *pitch* video, separate from the demo video. Judges said: *"introduce yourselves, tell us what you're building, and tell us why you're the people to build it. Nothing fancy required... Up to 2 minutes."* So this is **one person talking to camera**, no screen share. The demo video carries the product footage; this one carries the thinking.

**Runtime:** ~2:00 at 155 wpm. English body = **313 words** (verified by script, not estimated).

**Recording setup:** record on Loom or OBS, upload to YouTube, mark **Public** before submitting. Quiet room, one lamp, camera at eye level. No intro animation, no music — a plain talking head matches the tone we're claiming. Look at the lens on every bolded line.

---

## The script

### 0:00 – 0:20 · WHO

Hi, I'm Liming — a full-stack engineer in Changsha, China, ten years shipping software.

**Most of that work has been where being wrong is expensive**: pharmacy ERP, chain-store POS, CRM, heavily regulated integrations — systems where an audit trail isn't a feature, it's the requirement.

**I take complex systems from first conversation to production on my own.**

### 0:20 – 1:00 · WHAT

I'm building **PantaPilot — an autonomous trading desk for Panta's prediction markets.**

Four AI agents deliberate before any order goes out. **Scout** gathers the market's oracle sources and live web signals. **Estimator** independently prices the true probability. **Decision** compares that to the market's implied odds and moves only on a material gap. **Risk** holds veto power over caps, liquidity and rationale.

Surviving orders run through **Panta's real five-step order chain against the production API.** Every step is logged as an evidence chain, so **a human can audit exactly why an order happened.**

### 1:00 – 1:35 · WHY ME (part 1 — engineering)

Why me? **Ten years building systems where the audit trail matters more than the demo.** Regulated integrations teach you to design the failure path first: the API returns null, the network dies mid-order. PantaPilot applies that habit to an agent — it degrades to a safe HOLD instead of crashing, and paper mode lets anyone reproduce it without risking a cent.

And plainly: **I built this with AI coding agents — Claude Code and DeepSeek Harness.** I set the direction and stand behind every claim here.

### 1:35 – 1:55 · WHY ME (part 2 — the honest part) · **the line that matters**

And the honest part. We ran a real backtest against settled markets on the venue. **The result was zero — eight settled markets, no actionable edge, every one resolving within 1.8% of fifty-fifty.** We thought we had a win rate from a sample list. It wasn't real data, so we deleted it.

**An agent that inflates its edge is worse than no agent at all.** That habit is why I'm the right person to build this — and why you should trust it when it trades.


---

## Total word count

| Segment | Words | Target time |
|---|---|---|
| 0:00–0:20 Who | 55 | 0:20 |
| 0:20–1:00 What | 91 | 0:40 |
| 1:00–1:35 Why you (engineering + AI agents) | 84 | 0:35 |
| 1:35–1:55 Why you (honest null result) | 83 | 0:25 |
| **Total English body** | **313** | **~2:00** |

> **Pace check (measured, not estimated):** 313 words across the four segments. That lands at **~2:00 at 155 wpm** — a normal, unhurried pitch pace. If you speak slower than that, use the cut list below to shed 15–20 words; do **not** cut the null-result segment or the AI-agent disclosure, they are the two things judges will remember.

---

## Recording notes

1. **One take, no scripts on screen.** The bolded lines are your eye-line anchors. Everything else can be paraphrased — judges are scoring how you think, not whether you memorized it.
2. **Do not cut the null-result segment.** It is the entire differentiation. That's the part where you're telling them something nobody else's pitch says.
3. **Say the AI-agent disclosure out loud**, and keep your tone matter-of-fact. Owned, it reads as confidence; hidden, it reads as a gap.
4. **No product footage here.** If you're tempted to show the dashboard, that's the demo video's job — mixing them weakens both.
5. **Upload Public.** An unlisted pitch video is a submission that gets marked incomplete.

**If you're running long, cut in this order:** (1) "CRM, heavily regulated integrations" → keep only "pharmacy ERP and chain-store POS"; (2) "the API returns null, the network dies mid-order" → keep one example; (3) "and live web signals" in the Scout line. Each is ~5 seconds and none carries a judge-facing claim.

---

## 中文对照版

### 0:00 – 0:20 · 你是谁

你好，我是 Liming。我是一名全栈工程师，base 在长沙，写软件大概十年了。

**这十年里，我大部分时间都在"出错代价很高"的地方干活**：医药 ERP、连锁门店 POS、CRM，以及强监管的第三方接口对接——这类系统里，审计留痕不是加分项，而是硬性要求。

**我能独立把一个复杂系统从第一次沟通一路做到上线。**

### 0:20 – 1:00 · 你在做什么

我在做的是 **PantaPilot——一个跑在 Panta 预测市场上的自主交易台。**

四个 AI 智能体在任何一笔订单发出前都会先议事。**Scout** 去抓这个市场的预言机数据源和实时网络信号；**Estimator** 独立估出真实概率；**Decision** 把它和市场隐含赔率做比较，只有出现实质性价差才行动；**Risk** 握有一票否决权，管住额度、流动性和理由质量。

活下来的订单会走 **Panta 真实的五步下单链路，全部打生产 API**。每一步输出都会落日志、形成证据链，**人类可以复盘一笔订单到底为什么发生。**

### 1:00 – 1:35 · 为什么是你（工程能力）

为什么是我？**我在"审计留痕比演示效果更重要"的系统里干了十年。** 强监管的对接教会我先把失败路径设计好：接口返回 null 怎么办、下单到一半网络断了怎么办。PantaPilot 就是把这个习惯用在了智能体上——某一环挂了会安全降级成 HOLD，而不是整个崩掉；默认纸面模式，任何人不用花一分钱就能复现。

另一件事我也直说：**这个项目是用 AI 编码智能体做的——Claude Code 和 DeepSeek Harness。** 方向是我定的，这里每一条结论我都负责。

### 1:35 – 1:55 · 为什么是你（诚实）

还有诚实的那部分。我们拿平台上已结算的市场跑了真实回测。**结果是零——8 个已结算市场，没有一个达到可交易阈值，而且每一个的成交价都在 50/50 的 1.8% 以内。** 我们一度以为自己手里有个胜率，来自一份样例清单；但那不是真实数据，所以我们把它删掉了。

**一个会吹大自己优势的智能体，比没有智能体更糟。** 拒绝伪造数字这个习惯，就是我适合来做这件事的理由，也是等它真正开始下单那天、你该相信它的理由。

---

*Word counts verified against the English body text above. Deliverable: `pantapilot/demo_capture/PITCH_VIDEO_SCRIPT.md`.*
