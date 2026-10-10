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

    markets = client.primary_markets()
    stats["markets"] = len(markets)
    logger.start(mode="LIVE" if not config.DRY_RUN else "PAPER", market_count=len(markets))
    log.info("本轮扫描到 %d 个 primary 市场", len(markets))

    for m in markets:
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

    # 刷新看板
    try:
        render_dashboard(logger, stats)
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