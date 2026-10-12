# Colosseum 提交 · 人工操作清单

> 自动流程卡在「Languages spoken」下拉框（会锁死浏览器调试会话），
> 且表单不保存草稿、刷新即清空。以下内容可直接复制粘贴，人工操作约 5 分钟。

**截止：2026-10-12 23:59 PDT = 2026-10-13 14:59 北京时间（约剩 23 小时）**

---

## 0. 账号现状（已完成，无需重做）

- 账号已建好：**Liming** / `@lmlive`，通过 GitHub OAuth 登录
- 绑定邮箱是 `live_lm@live.cn`（GitHub 上的邮箱），不是你给我的 Gmail
- 登录方式：**Continue with GitHub**（没有设密码）

浏览器已登录，直接访问 https://colosseum.com/arena/hackathon 即可。

---

## 1. 注册 hackathon（表单字段）

页面：Hackathon dashboard → **Register**

| 字段 | 填入 |
|---|---|
| Country * | `China` |
| City * | `Changsha` |
| Which chains * | 勾选 **Solana**（只勾这一个） |
| 协议 | 勾选 "I have read and agree to the Official Rules." |

然后点 **Register for hackathon**。

⚠️ **点击后请回到 dashboard 确认**——按钮变灰不代表成功。如果 dashboard 仍显示
"Register"，说明没存上，需重试。我上次就是在这里误判了。

---

## 2. 补全 Profile

页面：dashboard 上方的 **Complete profile** → Step 1「About you」

| 字段 | 填入 |
|---|---|
| Display name * | `Liming` |
| Username * | `lmlive` |
| Headline * | `Full-stack Engineer building autonomous trading agents` |
| Country * | `China` |
| City * | `Changsha` |
| Languages spoken * | `English` + `Chinese`（可搜索，输入 English 回车） |
| About you * | 见下方长文本 |

**About you 全文（直接复制）：**

```
10-year full-stack engineer (Python/Java/Vue). I build production systems for pharma ERP, retail POS and CRM, with deep experience in regulated third-party integrations. Currently building PantaPilot, an autonomous multi-agent trading desk for Solana prediction markets.
```

填完点 **Continue** → 进入 Step 2「What you want to build」，按实际情况填即可。

---

## 3. 创建并提交项目

Profile 完成后，在 dashboard 找到创建项目的入口（Hackathon → 你的项目 / Create project）。

### 项目名
```
PantaPilot
```

### 一句话简介（Tagline）
```
An autonomous four-agent trading desk that finds and acts on mispriced Panta prediction markets.
```

### 仓库链接
```
https://github.com/lmlive/pantapilot
```

### 视频链接
```
https://github.com/lmlive/pantapilot/blob/master/docs/demo.mp4
```

### 详细描述（直接复制，长版）

```
PantaPilot is an autonomous trading desk for Panta prediction markets. Instead of one
prompt and one guess, it runs four specialised roles that deliberate before any order:

1. Scout - gathers grounded intel from the market's own oracle sources first, then falls
   back to live web search. An empty intel set never crashes the loop.
2. Estimator - independently assesses the true probability of the outcome, with an
   explicit uncertainty label, deliberately before seeing any trade decision.
3. Decision - compares the market-implied probability against the model's estimate and
   only proposes a trade when the gap is material and articulable.
4. Risk - holds absolute veto over per-trade caps, liquidity and rationale quality.

Consensus then flows through Panta's real 5-step non-custodial order chain against the
production API (quote -> build -> sign -> submit -> verify). DRY_RUN=true is the default,
so anyone can reproduce the entire pipeline with no wallet and no capital at risk.

Every agent step is persisted to JSONL and rendered as an expandable evidence chain on a
live dashboard, so a human can audit exactly why any order happened.

We report measurements, not a flattering graph. Run `python backtest_real.py` and you
will see our honest null result: Panta's venue currently has 1 tradeable market and its
settled markets resolved within 1.8% of 50/50, so there is no mispricing history to claim
profit from. The integration is real; the edge is not there yet - and we would rather tell
you that than fake a 100% win rate.
```

### 赛道 / Track
选 **Panta API Sidetrack**（如有该选项）

---

## 4. 提交后必做

- [ ] 确认状态是 **submitted**，不是 draft
- [ ] 截图保存确认页
- [ ] 去 **Superteam Earn** 用同样内容再交一次（双平台都要交，只交 Earn 不算数）

---

## 5. 遗留事项

- **改密码**：首轮对话里密码以明文发过，若该密码用于其他地方请一并更换
- **邮箱**：账号绑的是 `live_lm@live.cn`。改成 Gmail 会把登录方式从 GitHub 切换成
  邮箱+密码（依赖密码），当前建议不动；如需提醒可用邮件转发规则
- **真录屏版视频**（可选）：本地跑 `python main.py`（约 11 分钟）用 OBS 或
  `asciinema` 录制，可替换掉现在这版「重绘式」终端演示
