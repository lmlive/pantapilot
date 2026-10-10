# PantaPilot 需求分析与优先级排期报告

**项目**：AI 预测市场交易智能体（Colosseum Crypto World's Fair 黑客松 · Panta API Sidetrack $5,000）
**核心循环**：扫市场 → LLM 分析 → 发现 edge 则下单 → 记录决策 → 看板展示

---

## 1. 需求清单（拆分为可交付条目）

### 功能需求（F1–F5 → 8 个交付条目）

| 条目 | 来源 | 交付内容 | 验收要点 |
|------|------|---------|---------|
| R1 市场扫描引擎 | F1 | 定时 GET /markets/ 全量拉取；过滤 status==primary && resolved==false；去重；分页 | 拉到真实 live 市场列表 |
| R2 LLM 决策引擎 | F2 | 拼装 prompt；system 约束；结构化输出；触发条件；timeout+retry | 决策字段完整、HOLD 不下单 |
| R3 交易执行（dry-run 半链路） | F3 | 走 ①② 步；DRY_RUN=true 停在此处 | 日志有 trade_dry_run |
| R4 交易执行（真机全链路） | F3 | 补 ③④⑤ 步签名广播 submit/verify | 真机下单成功/verify 通过（加分） |
| R5 决策/交易日志 | F4 | JSONL 落盘各 event | 一轮产生各 event |
| R6 看板 | F5 | 静态 HTML 60s 自刷新 + 页脚 Powered by Panta | 统计卡/决策流/价格条有数据 |
| R7 安全护栏 | §4 | DRY_RUN 默认 true；MAX_TRADE_USDC 默认 5；专用小额 keypair；try/except | 异常不崩、单市场失败不影响 |
| R8 密钥与容错 | §4 | .env+chmod600+gitignore+revoke；LLM 熔断；单市场隔离；性能底线 | 密钥不泄露、容错可测 |

### 已知坑（实现约束内嵌）
- no_proxy 含 `[::1]` → 启动清洗
- 出口授权（App 首次访问新域名）→ 一次性真机步骤
- API 返回 `items` 而非 `results`；detail 价格可能 null → 字段解析防御
- 免费 LLM 不稳定 → R2 动态降级
- market 阶段变化快，quote 失败当正常 → R8 容错
- solders 版本差异 → R4 签名广播适配

---

## 2. 优先级排序（P0 / P1 / P2）

| 需求 | Reach | Impact | Confidence | Effort(人天) | RICE | 级别 |
|------|-------|--------|-----------|------|------|------|
| R7 安全护栏 | 10 | 2 | 90% | 0.5 | 36.0 | **P0** |
| R1 市场扫描 | 10 | 3 | 100% | 2 | 15.0 | **P0** |
| R3 交易 dry-run | 8 | 3 | 100% | 2.5 | 9.6 | **P0** |
| R8 密钥与容错 | 9 | 2 | 90% | 2 | 8.1 | **P0** |
| R5 决策日志 | 10 | 1 | 100% | 1.5 | 6.7 | **P0** |
| R6 看板 | 9 | 2 | 90% | 3 | 5.4 | **P0** |
| R2 LLM 决策 | 10 | 3 | 80% | 5 | 4.8 | **P0** |
| R4 交易真机全链路 | 6 | 2 | 60% | 8 | 0.9 | **P1/P2** |

### 迭代分配

| 迭代 | 目标 | 交付条目 | 级别 |
|------|------|---------|------|
| Iteration 1 — MVP | 扫市场+LLM+日志+看板"看得见数据"+安全底线 | R1 R2 R5 R6 R7 R8 | P0 |
| Iteration 2 — 决策证据链+半链路 | 决策→动作闭环 | R3 交易 dry-run + R2 强化 + R8 压测 | P0 |
| Iteration 3 — 真机下单（加分） | 全链路真调用 | R4 真机全链路 + P2（持仓/领奖/并发） | P1 |

---

## 3. 关键风险与依赖

**必须先真机验证**：
1. Panta live API 连通性（auth→keys→markets）— Iteration 1 第一天
2. 免费 LLM 可用性（cohere/north-mini-code:free）— Iteration 1 第 1-2 天
3. 签名广播链路（③④⑤）— Iteration 3 前必测
4. 出口授权（App 首次访问新域名）

**可 mock**：LLM 决策（注入固定 JSON）、询价报价（用当前价模拟 ①②）、真机广播不可 mock。

---

## 4. 建议迭代计划

```
Iteration 1  MVP（2-3 天）
  ├─ Day 1: 探通 Panta live API + 验证免费 LLM
  ├─ Day 2: R1 市场扫描 + R2 LLM 决策 + R7/R8 安全与容错底座
  └─ Day 3: R5 日志 + R6 看板（评审已能看到完整核心循环）

Iteration 2  决策证据链闭环（1-2 天）
  ├─ R3 交易 dry-run（走 ①②，日志出 trade_dry_run）
  ├─ R2 真实 LLM 强化 + 动态降级
  └─ R8 容错压测

Iteration 3  真机下单（加分项，1-2 天，风险最高）
  ├─ 前置门禁：live key 真市场 + 免费 LLM 双探通
  ├─ R4 真机全链路（③④⑤ 签名广播）+ 小额真钱
  └─ 提交：README + SUBMISSION + demo 视频 + GitHub + 双平台
```

### 明确取舍
- **砍需求**：真机下单（R4）是唯一资金风险与时间黑洞。若免费 LLM 或 live API 未探通，果断降为 P2，专注看板与 demo——MVP 已覆盖评审 4/5 维度。
- **不画大饼**：20 市场一轮 2-5 分钟是性能底线，先单线程跑通再谈并发。
- **安全永远是 P0 顶部**：DRY_RUN 默认 true + 小额 keypair，是"做错了不扣分"的保险丝。