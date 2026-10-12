"""看板（R6/F5）

静态 HTML，60 秒自动刷新。读 JSONL 日志渲染：
- 头图：标题 + LIVE 徽标 + 模式 + 更新时间 + 市场数
- 四个统计卡：跟踪市场数 / AI 决策数 / 买入信号数 / HOLD 数
- AI 决策流：BUY_YES 绿 / BUY_NO 红 / HOLD 灰，含置信度条、理由、时间
- 市场网格：标题、分类、状态徽标、YES/NO 价格条、交易量
- 页脚："Powered by Panta"
"""
from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any

import config
from logger import JsonlLogger


def _esc(s: Any) -> str:
    return html.escape(str(s))


def _price_bar(m: dict[str, Any]) -> str:
    yes = m.get("yesPrice")
    if yes in (None, ""):
        yes = m.get("primaryYesPrice")
    no = m.get("noPrice")
    if no in (None, ""):
        no = m.get("primaryNoPrice")
    try:
        y = float(yes or 0)
        n = float(no or 0)
    except (TypeError, ValueError):
        y, n = 0.0, 0.0
    total = y + n
    if total <= 0:
        total = 1.0
    yp = y / total * 100
    np_ = n / total * 100
    return f"""<div class="pbar">
      <div class="pbar-yes" style="width:{yp:.1f}%">YES {y:.2f}</div>
      <div class="pbar-no" style="width:{np_:.1f}%">NO {n:.2f}</div>
    </div>"""


def _is_risk_veto(d: dict[str, Any]) -> bool:
    """风险否决检测：reason 前缀或 evidence.risk.approved=false。"""
    reason = str(d.get("reason", "") or "")
    if reason.startswith("[risk veto]"):
        return True
    ev = d.get("evidence")
    if isinstance(ev, dict):
        risk = ev.get("risk")
        if isinstance(risk, dict) and risk.get("approved") is False:
            return True
    return False


def _pipeline_flow(rec: dict[str, Any]) -> str:
    """四角色协作流水线横向视图：Scout ➔ Estimator ➔ Decision ➔ Risk。"""
    d = rec.get("decision", {}) or {}
    ev = d.get("evidence")
    if not isinstance(ev, dict):
        return ""

    pipe = ev.get("pipeline", "")
    if pipe == "fallback_single_agent":
        return '<div class="pipe-fallback">Single Agent Fallback (Static Analysis)</div>'

    # ① Scout
    intel = ev.get("intel") or {}
    q_count = len(intel.get("queries") or [])
    has_oracle = bool(intel.get("oracle_head"))
    has_search = bool(intel.get("search_head"))
    scout_sources = []
    if has_oracle:
        scout_sources.append("Oracle")
    if has_search:
        scout_sources.append("Web")
    scout_source_str = " + ".join(scout_sources) if scout_sources else "Market Meta"
    scout_stat = f"{max(1, q_count + (1 if has_oracle else 0))} Sources"
    scout_desc = f"Intel: {scout_source_str}"

    # ② Estimator
    est = ev.get("estimator") or {}
    est_prob = est.get("true_prob_yes")
    if est_prob is not None:
        try:
            val_f = float(est_prob)
            est_stat = f"YES {val_f:.2f} ({val_f*100:.0f}%)"
        except (ValueError, TypeError):
            est_stat = "unavailable"
    else:
        # The Estimator LLM call can legitimately fail (free-model flakiness); the
        # pipeline degrades gracefully instead of dying. Say so rather than printing
        # "YES --", which reads like a real estimate of zero.
        est_stat = "unavailable"
    est_conf = est.get("confidence")
    est_unc = est.get("uncertainty", "med")
    if est_prob is None:
        est_desc = "estimator call failed · degraded"
    else:
        est_desc = f"conf {est_conf or 0:.2f} · unc {_esc(est_unc)}"

    # ③ Decision & Benchmark 对比
    dec_val = d.get("decision", "HOLD")
    bm = ev.get("benchmark") or {}
    gap_str = bm.get("gap_pct")
    if not gap_str and est_prob is not None:
        mkt = rec.get("yesPrice", d.get("yesPrice"))
        if mkt not in (None, ""):
            try:
                g = float(est_prob) - float(mkt)
                gap_str = f"{g*100:+.1f}%"
            except (ValueError, TypeError):
                pass
    if gap_str:
        dec_stat = f"Edge {gap_str}"
        dec_desc = f"{dec_val} · {_esc(d.get('suggested_usdc', 0))} USDC"
    else:
        dec_stat = dec_val
        dec_desc = f"{_esc(d.get('suggested_usdc', 0))} USDC proposed"

    # ④ Risk
    risk = ev.get("risk") or {}
    is_veto = _is_risk_veto(d)
    if is_veto:
        risk_stat = "VETOED"
        risk_cls = "p-veto"
        risk_desc = _esc(risk.get("note") or "Risk guardrail triggered")
    else:
        risk_stat = "PASSED"
        risk_cls = "p-pass"
        risk_desc = _esc(risk.get("note") or "Within cap & verified")

    # 展开细节
    detail_parts: list[str] = []
    ke = est.get("key_evidence")
    if ke:
        detail_parts.append(f'<div class="ev-line ev-ke"><b>key_evidence:</b> {_esc(str(ke)[:300])}</div>')
    head = intel.get("oracle_head") or intel.get("search_head") or ""
    if head:
        detail_parts.append(f'<div class="ev-line ev-intel"><b>Intel Feed:</b> {_esc(str(head)[:200])}…</div>')
    pipe_badge = f'<div class="pipe-header"><span class="ev-pipe">{_esc(pipe)}</span></div>' if pipe else ""
    details_html = ""
    if detail_parts:
        details_html = f"""<details class="pipe-details ev">
          <summary class="pipe-details-sum">Details & Evidence ▾</summary>
          <div class="pipe-details-body">{''.join(detail_parts)}</div>
        </details>"""

    return f"""{pipe_badge}<div class="pipeline-board">
      <div class="pipe-step">
        <div class="pipe-role"><span class="pipe-badge b-scout">1. SCOUT</span></div>
        <div class="pipe-stat">{scout_stat}</div>
        <div class="pipe-desc">{scout_desc}</div>
      </div>
      <div class="pipe-arrow">➜</div>
      <div class="pipe-step">
        <div class="pipe-role"><span class="pipe-badge b-est">2. ESTIMATOR</span></div>
        <div class="pipe-stat">{est_stat}</div>
        <div class="pipe-desc">{est_desc}</div>
      </div>
      <div class="pipe-arrow">➜</div>
      <div class="pipe-step">
        <div class="pipe-role"><span class="pipe-badge b-dec">3. DECISION</span></div>
        <div class="pipe-stat { 'p-edge-pos' if '+' in str(gap_str) else '' }">{dec_stat}</div>
        <div class="pipe-desc">{dec_desc}</div>
      </div>
      <div class="pipe-arrow">➜</div>
      <div class="pipe-step {risk_cls}">
        <div class="pipe-role"><span class="pipe-badge b-risk">4. RISK</span></div>
        <div class="pipe-stat">{risk_stat}</div>
        <div class="pipe-desc">{risk_desc}</div>
      </div>
    </div>
    {details_html}"""


def _status_badge(status: str) -> str:
    cls = "s-primary" if status == "primary" else "s-secondary" if status == "secondary" else "s-resolved"
    return f'<span class="badge {cls}">{_esc(status)}</span>'


def _decision_row(rec: dict[str, Any]) -> str:
    d = rec.get("decision", {}) or {}
    dec = d.get("decision", "HOLD")
    cls = "d-buy-yes" if dec == "BUY_YES" else "d-buy-no" if dec == "BUY_NO" else "d-hold"
    conf = float(d.get("confidence", 0) or 0)
    confp = conf * 100
    reason = _esc(d.get("reason", ""))
    ts = _esc(rec.get("ts", ""))
    title = _esc(rec.get("title", rec.get("marketId", "")))
    conf_color = "#2ecc71" if conf >= config.MIN_CONFIDENCE else "#e67e22"
    veto = '<span class="ev-veto">[RISK VETO]</span>' if _is_risk_veto(d) else ""
    pipeline_view = _pipeline_flow(rec)
    return f"""<div class="drow {cls}">
      <div class="dhead"><span class="dtag">{dec}</span>{veto}<span class="dtitle">{title}</span><span class="dtime">{ts}</span></div>
      <div class="dconf"><span style="width:{confp:.0f}%"></span></div>
      <div class="dreason">{reason} <small style="color:{conf_color}">conf {conf:.2f}</small></div>
      {pipeline_view}
    </div>"""


def _market_card(m: dict[str, Any]) -> str:
    title = _esc(m.get("title", ""))
    cat = _esc(m.get("category", ""))
    status = _esc(m.get("status", ""))
    vol = _esc(m.get("volumeUsdc", ""))
    return f"""<div class="mcard">
      <div class="mtitle">{title}</div>
      <div class="mmeta">{_status_badge(status)} <span class="mcat">{cat}</span></div>
      {_price_bar(m)}
      <div class="mvol">Volume: {vol} USDC</div>
    </div>"""


def render_dashboard(
    logger: JsonlLogger,
    stats: dict[str, Any],
    markets: list[dict[str, Any]] | None = None,
) -> None:
    records = logger.read_all()
    analyses = [r for r in records if r.get("event") == "analysis"]
    buy_signals = [r for r in analyses if (r.get("decision") or {}).get("decision") in ("BUY_YES", "BUY_NO")]
    holds = [r for r in analyses if (r.get("decision") or {}).get("decision") == "HOLD"]
    trades = [r for r in records if r.get("event") in ("trade_done", "trade_dry_run", "trade_start")]

    tracked = stats.get("markets", len(markets or []))
    ai_decisions = stats.get("analyzed", len(analyses))
    buy_count = stats.get("buy_signals", len(buy_signals))
    hold_count = stats.get("holds", len(holds))

    mode = "LIVE" if not config.DRY_RUN else "PAPER"
    mode_cls = "mode-live" if not config.DRY_RUN else "mode-paper"
    # The source badge must describe REALITY: data comes from the live Panta API in both
    # modes, but only a non-dry run actually deploys capital. Never show "LIVE" next to
    # "PAPER" -- that reads as a claim of live trading.
    if config.DRY_RUN:
        live_label, live_cls = "LIVE API DATA", "live"
    else:
        live_label, live_cls = "LIVE TRADING", "live"
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    market_count = stats.get("markets", len(markets or []))

    decision_rows = "".join(_decision_row(r) for r in reversed(analyses[-30:]))
    if not decision_rows:
        decision_rows = '<div class="empty">暂无 AI 决策</div>'

    market_cards = "".join(_market_card(m) for m in (markets or [])[:60])
    if not market_cards:
        market_cards = '<div class="empty">暂无市场数据</div>'

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="60">
<title>PantaPilot Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; background: #0f1220; color: #e8eaf0; padding: 24px; }}
  .header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }}
  .header h1 {{ font-size: 24px; }}
  .live {{ background: #e74c3c; color: #fff; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; letter-spacing: 1px; }}
  .mode-live {{ background: #e74c3c; color: #fff; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; }}
  .mode-paper {{ background: #8e44ad; color: #fff; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; }}
  .updated {{ color: #889; font-size: 12px; margin-left: auto; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 22px; }}
  .card {{ background: #171a2b; border: 1px solid #242a44; border-radius: 10px; padding: 16px; }}
  .card .num {{ font-size: 30px; font-weight: 700; }}
  .card .label {{ color: #889; font-size: 12px; margin-top: 4px; }}
  h2 {{ font-size: 17px; margin: 20px 0 12px; }}
  .flow {{ display: flex; flex-direction: column; gap: 10px; }}
  .drow {{ background: #171a2b; border: 1px solid #242a44; border-radius: 8px; padding: 12px; }}
  .d-buy-yes {{ border-left: 4px solid #2ecc71; }}
  .d-buy-no {{ border-left: 4px solid #e74c3c; }}
  .d-hold {{ border-left: 4px solid #7f8c8d; }}
  .dhead {{ display: flex; gap: 10px; align-items: center; }}
  .dtag {{ font-weight: 700; font-size: 12px; }}
  .d-buy-yes .dtag {{ color: #2ecc71; }}
  .d-buy-no .dtag {{ color: #e74c3c; }}
  .d-hold .dtag {{ color: #7f8c8d; }}
  .dtitle {{ font-size: 14px; flex: 1; }}
  .dtime {{ color: #667; font-size: 11px; }}
  .dconf {{ background: #0b0d18; border-radius: 4px; height: 6px; margin: 8px 0; overflow: hidden; }}
  .dconf span {{ display: block; height: 100%; background: #3498db; }}
  .dreason {{ color: #aab; font-size: 13px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }}
  .mcard {{ background: #171a2b; border: 1px solid #242a44; border-radius: 10px; padding: 14px; }}
  .mtitle {{ font-size: 14px; font-weight: 600; margin-bottom: 8px; }}
  .mmeta {{ display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }}
  .badge {{ font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 600; }}
  .s-primary {{ background: #2ecc71; color: #062; }}
  .s-secondary {{ background: #f39c12; color: #421; }}
  .s-resolved {{ background: #7f8c8d; color: #fff; }}
  .mcat {{ color: #889; font-size: 12px; }}
  .pbar {{ display: flex; height: 22px; border-radius: 6px; overflow: hidden; font-size: 11px; font-weight: 600; margin-bottom: 8px; }}
  .pbar-yes {{ background: #2ecc71; color: #062; display: flex; align-items: center; padding-left: 6px; }}
  .pbar-no {{ background: #e74c3c; color: #fff; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px; }}
  .mvol {{ color: #889; font-size: 12px; }}
  /* 四角色协作流水线样式 (P1 横向流水线) */
  .pipeline-board {{ display: flex; align-items: stretch; gap: 8px; margin: 12px 0 6px; background: #111424; border: 1px solid #232a48; border-radius: 8px; padding: 10px 12px; overflow-x: auto; }}
  .pipe-step {{ flex: 1; min-width: 140px; background: #181d33; border: 1px solid #283050; border-radius: 6px; padding: 8px 10px; display: flex; flex-direction: column; justify-content: center; }}
  .pipe-arrow {{ display: flex; align-items: center; justify-content: center; color: #475577; font-size: 13px; font-weight: 700; user-select: none; }}
  .pipe-role {{ margin-bottom: 4px; }}
  .pipe-badge {{ font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 3px; letter-spacing: 0.5px; text-transform: uppercase; }}
  .b-scout {{ background: #1e3a5f; color: #60a5fa; }}
  .b-est {{ background: #3b2d54; color: #c084fc; }}
  .b-dec {{ background: #134e48; color: #2dd4bf; }}
  .b-risk {{ background: #4a3418; color: #fbbf24; }}
  .pipe-stat {{ font-size: 13px; font-weight: 700; color: #f1f5f9; margin-bottom: 2px; }}
  .p-edge-pos {{ color: #34d399; }}
  .pipe-desc {{ font-size: 11px; color: #94a3b8; line-height: 1.35; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .pipe-step.p-pass {{ border-color: #10b98144; }}
  .pipe-step.p-pass .pipe-stat {{ color: #34d399; }}
  .pipe-step.p-veto {{ border-color: #ef444466; background: #2a151b; }}
  .pipe-step.p-veto .pipe-stat {{ color: #f87171; }}
  .pipe-details {{ margin-top: 6px; font-size: 11px; }}
  .pipe-details-sum {{ cursor: pointer; color: #64748b; user-select: none; padding: 2px 0; }}
  .pipe-details-sum:hover {{ color: #94a3b8; }}
  .pipe-details-body {{ margin-top: 6px; padding: 8px 12px; background: #0c0e1a; border: 1px solid #1e243d; border-radius: 6px; }}
  .pipe-fallback {{ margin-top: 8px; font-size: 11px; color: #64748b; font-style: italic; }}
  .ev-line {{ color: #889; font-size: 12px; line-height: 1.55; margin: 3px 0; word-break: break-word; }}
  .ev-ke {{ color: #cbd5e1; }}
  .ev-intel {{ color: #94a3b8; }}
  .ev-veto {{ background: #e74c3c; color: #fff; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px; letter-spacing: .5px; }}
  .dlegend {{ color: #667; font-size: 12px; margin-bottom: 8px; }}
  .dlegend .lg-yes {{ color: #2ecc71; font-weight: 700; }}
  .dlegend .lg-no {{ color: #e74c3c; font-weight: 700; }}
  .dlegend .lg-hold {{ color: #7f8c8d; font-weight: 700; }}
  .empty {{ color: #667; padding: 20px; text-align: center; }}
  .footer {{ margin-top: 30px; padding-top: 16px; border-top: 1px solid #242a44; color: #889; font-size: 13px; text-align: center; }}
  .footer .panta {{ color: #7ad; font-weight: 700; }}
</style>
</head>
<body>
  <div class="header">
    <h1>PantaPilot</h1>
    <span class="{live_cls}">{live_label}</span>
    <span class="{mode_cls}">{mode}</span>
    <span class="updated">Updated {updated} · {market_count} markets</span>
  </div>

  <div class="cards">
    <div class="card"><div class="num">{tracked}</div><div class="label">Tracked Markets</div></div>
    <div class="card"><div class="num">{ai_decisions}</div><div class="label">AI Decisions</div></div>
    <div class="card"><div class="num" style="color:#2ecc71">{buy_count}</div><div class="label">Buy Signals</div></div>
    <div class="card"><div class="num" style="color:#7f8c8d">{hold_count}</div><div class="label">HOLDs</div></div>
  </div>

  <h2>AI Decision Flow</h2>
  <div class="dlegend"><span class="lg-yes">BUY_YES</span> · <span class="lg-no">BUY_NO</span> · <span class="lg-hold">HOLD</span></div>
  <div class="flow">{decision_rows}</div>

  <h2>Markets</h2>
  <div class="grid">{market_cards}</div>

  <div class="footer">Powered by <span class="panta">Panta</span></div>
</body>
</html>"""

    config.DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html_doc)