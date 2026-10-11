"""PantaPilot 主循环

核心循环：扫市场 → LLM 分析 → 发现 edge 则下单 → 记录决策 → 刷新看板
每 SCAN_INTERVAL_MINUTES 一轮。单市场失败不影响其他；LLM 超时熔断；主循环 try/except 包住。
"""
from __future__ import annotations

import logging
import sys
import time

import config
from agents import AgentTeam
from dashboard import render_dashboard
from llm import LLMDecisionEngine
from logger import JsonlLogger
from panta import PantaClient, market_to_prompt_block, normalize_status
from trader import Trader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("pantapilot.main")


def select_demo_markets(markets: list[dict], limit: int = 5) -> list[dict]:
    """挑出最有演示看点的市场（有交易量、有情报源）。控制在 3-5 个以内，适合 90 秒视频演示。"""
    if limit <= 0 or len(markets) <= limit:
        return markets

    def score(m: dict) -> tuple[int, float]:
        vol = 0.0
        try:
            vol = float(m.get("volumeUsdc") or 0.0)
        except (ValueError, TypeError):
            vol = 0.0
        has_oracle = 1 if bool(m.get("oracle")) else 0
        has_desc = 1 if len(str(m.get("description") or "")) > 30 else 0
        has_vol = 1 if vol > 0 else 0
        # 优先级：(有交易量且有情报) > (有交易量) > (有情报) > (其它)
        priority = (has_vol * 2) + has_oracle + has_desc
        return (priority, vol)

    sorted_markets = sorted(markets, key=score, reverse=True)
    return sorted_markets[:limit]


def run_once(
    client: PantaClient,
    llm: LLMDecisionEngine,
    trader: Trader,
    logger: JsonlLogger,
    seen: set[str],
    team: AgentTeam | None = None,
) -> dict:
    """执行一轮扫描。返回统计。"""
    stats = {"markets": 0, "analyzed": 0, "buy_signals": 0, "holds": 0, "trades": 0}

    all_markets = client.primary_markets()
    stats["markets"] = len(all_markets)
    logger.start(mode="LIVE" if not config.DRY_RUN else "PAPER", market_count=len(all_markets))
    log.info("本轮扫描到 %d 个 primary 市场", len(all_markets))

    # Demo 模式挑选 3-5 个高质量市场进行深入决策，避免过多市场拖慢 90 秒视频节奏
    target_markets = select_demo_markets(all_markets, limit=config.DEMO_MARKET_LIMIT)
    log.info("精选 %d 个市场进行 AI 团队决策流 (DEMO_MARKET_LIMIT=%d)", len(target_markets), config.DEMO_MARKET_LIMIT)

    for m in target_markets:
        market_id = str(m.get("marketId") or m.get("id") or "")
        if not market_id or market_id in seen:
            continue
        seen.add(market_id)
        title = m.get("title", "")
        try:
            stats["analyzed"] += 1
            text = market_to_prompt_block(m)
            if team is not None:
                decision = team.analyze(m, text, enable_search=config.SCOUT_SEARCH_ENABLED)
            else:
                decision = llm.analyze(text)
            logger.analysis(market_id, title, decision)
            log.info("[%s] %s => %s (%.2f)", market_id, title, decision["decision"], decision["confidence"])

            if decision["decision"] in ("BUY_YES", "BUY_NO") and decision["confidence"] >= config.MIN_CONFIDENCE:
                stats["buy_signals"] += 1
                res = trader.execute(m, decision)
                if res.get("ok"):
                    stats["trades"] += 1
            else:
                stats["holds"] += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("处理市场 %s 失败: %s", market_id, exc)
            logger.error(market_id, f"analysis error: {exc}")

    # 刷新看板（传入所有市场以展示市场网格）
    try:
        render_dashboard(logger, stats, markets=all_markets)
    except Exception as exc:  # noqa: BLE001
        log.warning("看板渲染失败: %s", exc)

    return stats


def main() -> None:
    missing = config.require_live_config()
    if missing and not config.DRY_RUN:
        log.error("DRY_RUN=false 需要配置: %s", ", ".join(missing))
        sys.exit(1)

    log.info(
        "PantaPilot 启动 mode=%s interval=%.0fmin max_trade=%.1fUSDC model=%s",
        "LIVE" if not config.DRY_RUN else "PAPER",
        config.SCAN_INTERVAL_MINUTES,
        config.MAX_TRADE_USDC,
        config.LLM_MODEL,
    )

    client = PantaClient()
    llm = LLMDecisionEngine()
    logger = JsonlLogger()
    trader = Trader(client, logger)
    team = AgentTeam() if config.AGENTS_ENABLED else None
    log.info(
        "决策引擎: %s",
        "多角色 Agent 团队 (Scout>Estimator>Decision>Risk)" if team else "单 agent 静态",
    )
    seen: set[str] = set()

    try:
        while True:
            try:
                run_once(client, llm, trader, logger, seen, team)
            except Exception as exc:  # noqa: BLE001
                log.error("本轮执行异常（主循环继续）: %s", exc)
            time.sleep(config.SCAN_INTERVAL_MINUTES * 60)
    except KeyboardInterrupt:
        log.info("收到中断，退出")
    finally:
        client.close()


if __name__ == "__main__":
    main()