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


def _evidence_block(rec: dict[str, Any]) -> str:
    """决策行下方的多角色证据链（无 evidence 的旧日志返回空串）。"""
    d = rec.get("decision", {}) or {}
    ev = d.get("evidence")
    if not isinstance(ev, dict):
        return ""

    parts: list[str] = []

    pipe = ev.get("pipeline")
    if pipe:
        parts.append(f'<span class="ev-pipe">{_esc(pipe)}</span>')

    est = ev.get("estimator")
    if isinstance(est, dict) and est:
        try:
            tp = float(est.get("true_prob_yes"))
            seg = f"est. YES {tp:.2f}"
            # 记录上下文里通常没有市场价；拿得到才显示 vs market
            mkt = rec.get("yesPrice", d.get("yesPrice"))
            if mkt not in (None, ""):
                try:
                    seg += f" vs market {float(mkt):.3f}"
                except (TypeError, ValueError):
                    pass
            extra = []
            if est.get("confidence") not in (None, ""):
                try:
                    extra.append(f"conf {float(est.get('confidence')):.2f}")
                except (TypeError, ValueError):
                    pass
            if est.get("uncertainty"):
                extra.append(f"unc {_esc(est.get('uncertainty'))}")
            if extra:
                seg += " · " + " · ".join(extra)
            parts.append(f'<div class="ev-line ev-est">{seg}</div>')
        except (TypeError, ValueError):
            pass
        ke = est.get("key_evidence")
        if ke:
            parts.append(f'<div class="ev-line ev-ke">key_evidence: {_esc(str(ke)[:300])}</div>')

    intel = ev.get("intel")
    if isinstance(intel, dict) and intel:
        head = intel.get("oracle_head") or intel.get("search_head") or ""
        head = str(head).strip()
        if head:
            parts.append(f'<div class="ev-line ev-intel">intel: {_esc(head[:200])}…</div>')
        queries = intel.get("queries")
        if isinstance(queries, list) and queries:
            q = " · ".join(str(q) for q in queries[:4])
            parts.append(f'<div class="ev-line ev-q">queries: {_esc(q[:200])}</div>')

    if not parts:
        return ""
    return (
        '<details class="ev"><summary class="ev-sum">Evidence chain ▾</summary>'
        f'<div class="ev-body">{"".join(parts)}</div></details>'
    )


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
    evidence = _evidence_block(rec)
    return f"""<div class="drow {cls}">
      <div class="dhead"><span class="dtag">{dec}</span>{veto}<span class="dtitle">{title}</span><span class="dtime">{ts}</span></div>
      <div class="dconf"><span style="width:{confp:.0f}%"></span></div>
      <div class="dreason">{reason} <small style="color:{conf_color}">conf {conf:.2f}</small></div>
      {evidence}
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
  /* 证据链（多角色 Agent） */
  .ev {{ margin-top: 8px; border-top: 1px dashed #242a44; padding-top: 6px; }}
  .ev-sum {{ cursor: pointer; color: #667; font-size: 11px; user-select: none; }}
  .ev-sum:hover {{ color: #7ad; }}
  .ev-body {{ margin-top: 6px; padding: 8px 10px; background: #12152440; border: 1px solid #242a44; border-radius: 6px; }}
  .ev-line {{ color: #889; font-size: 12px; line-height: 1.55; margin: 3px 0; word-break: break-word; }}
  .ev-est {{ color: #7ad; font-weight: 600; }}
  .ev-ke {{ color: #aab; }}
  .ev-intel, .ev-q {{ color: #667; }}
  .ev-pipe {{ display: inline-block; background: #1c2136; color: #889; font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 4px; margin-bottom: 4px; }}
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
    <span class="live">LIVE</span>
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