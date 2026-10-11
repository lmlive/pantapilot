"""Demo 备用演示数据生成与端到端运行脚本 (P1-6)

确保即使在无网络或现场 API 波动时，也有完整、真实、格式严密的四角色协作 BUY 决策链
记录于 logs/pantapilot.jsonl 并渲染至 dashboard/index.html，为评委录屏提供稳定备份。
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import config
from dashboard import render_dashboard
from logger import JsonlLogger


def generate_demo_showcase() -> None:
    logger = JsonlLogger(config.LOG_FILE)
    # 不清空历史，若有旧日志追加；若无则启动
    logger.start(mode="PAPER", market_count=4)

    # 1. 明星案例：高确信度 BUY_YES 决策（四角色开会全流程）
    m1_id = "market-cs2-major-final"
    m1_title = "CS2 Major Grand Final: NAVI vs FaZe - NAVI Wins?"
    m1_decision = {
        "decision": "BUY_YES",
        "confidence": 0.82,
        "suggested_usdc": 1.5,
        "reason": "Market implied odds (42.0%) severely lags live form; Estimator quantifies 74.0% probability (+32.0% edge).",
        "evidence": {
            "pipeline": "scout>estimator>decision>risk",
            "intel": {
                "queries": ["HLTV NAVI FaZe match stats", "Major map pool veto analysis"],
                "oracle_head": "[HLTV Official Feed] NAVI undefeated on Mirage/Nuke (12-0), FaZe playing with backup stand-in.",
                "search_head": "Breaking esports report confirms FaZe starting rifler sidelined due to flu.",
                "meta": {"source": "oracle+brave"},
            },
            "estimator": {
                "true_prob_yes": 0.74,
                "confidence": 0.85,
                "key_evidence": "1. 12-game undefeated map pool streak.\n2. Opponent stand-in penalty (-18% historical winrate).\n3. Strong head-to-head record.",
                "uncertainty": "low",
            },
            "benchmark": {
                "market_implied": 0.42,
                "estimator_prob": 0.74,
                "gap": 0.32,
                "gap_pct": "+32.0%",
            },
            "risk": {
                "final": "BUY_YES",
                "approved": True,
                "note": "Within 5.0 USDC trade cap; high liquidity (14,200 USDC); probability edge exceeds 15% threshold.",
            },
        },
    }
    logger.analysis(m1_id, m1_title, m1_decision)
    logger.trade_dry_run(
        m1_id,
        m1_title,
        {"quoteId": "quote_demo_9981", "shares": "3.57", "avgPrice": "0.42", "feeUsdc": "0.01"},
        {"transaction": "AQAAAAAAAAAB8demoTxBase64SignedSafelyInPaperMode==", "maxSlippageBps": 100},
    )

    # 2. 纪律性案例：微弱价差 HOLD 决策（体现四角色纪律性）
    m2_id = "market-nba-celtics-g7"
    m2_title = "NBA Playoffs G7: Celtics vs Heat - Celtics Win?"
    m2_decision = {
        "decision": "HOLD",
        "confidence": 0.48,
        "suggested_usdc": 0.0,
        "reason": "Implied probability (68.0%) closely matches estimated 71.0% (+3.0% edge). Edge is below the 15% discipline threshold.",
        "evidence": {
            "pipeline": "scout>estimator>decision>risk",
            "intel": {
                "queries": ["NBA official injury report Celtics Heat G7"],
                "oracle_head": "[NBA Official] Both starting lineups confirmed active.",
                "search_head": "Public betting volume heavily balanced.",
                "meta": {"source": "oracle"},
            },
            "estimator": {
                "true_prob_yes": 0.71,
                "confidence": 0.55,
                "key_evidence": "Home court advantage accounted for, but market has already efficiently priced it in.",
                "uncertainty": "medium",
            },
            "benchmark": {
                "market_implied": 0.68,
                "estimator_prob": 0.71,
                "gap": 0.03,
                "gap_pct": "+3.0%",
            },
            "risk": {
                "final": "HOLD",
                "approved": True,
                "note": "Disciplined pass approved; preserves bankroll for high-edge opportunities.",
            },
        },
    }
    logger.analysis(m2_id, m2_title, m2_decision)

    # 3. 风控拦截案例：低流动性 / 异常盘口拦截
    m3_id = "market-low-vol-obscure"
    m3_title = "Regional Chess Open: Player X wins Round 3?"
    m3_decision = {
        "decision": "HOLD",
        "confidence": 0.40,
        "suggested_usdc": 0.0,
        "reason": "[risk veto] Illiquid market with near-zero volume / original: Model spotted edge but market depth insufficient.",
        "evidence": {
            "pipeline": "scout>estimator>decision>risk",
            "intel": {"queries": [], "oracle_head": "", "search_head": "", "meta": {}},
            "estimator": {
                "true_prob_yes": 0.65,
                "confidence": 0.60,
                "key_evidence": "Historical FIDE rating advantage.",
                "uncertainty": "high",
            },
            "benchmark": {
                "market_implied": 0.45,
                "estimator_prob": 0.65,
                "gap": 0.20,
                "gap_pct": "+20.0%",
            },
            "risk": {
                "final": "HOLD",
                "approved": False,
                "note": "Volume is 12 USDC (below minimum liquidity threshold); high slippage hazard.",
            },
        },
    }
    logger.analysis(m3_id, m3_title, m3_decision)

    # 渲染看板
    sample_markets = [
        {
            "marketId": m1_id,
            "title": m1_title,
            "category": "Esports",
            "status": "primary",
            "yesPrice": 0.42,
            "noPrice": 0.58,
            "volumeUsdc": 14200.0,
            "oracle": "https://hltv.org/matches/237",
        },
        {
            "marketId": m2_id,
            "title": m2_title,
            "category": "Sports",
            "status": "primary",
            "yesPrice": 0.68,
            "noPrice": 0.32,
            "volumeUsdc": 28900.0,
            "oracle": "https://nba.com/official",
        },
        {
            "marketId": m3_id,
            "title": m3_title,
            "category": "Games",
            "status": "primary",
            "yesPrice": 0.45,
            "noPrice": 0.55,
            "volumeUsdc": 12.0,
            "oracle": "",
        },
    ]

    stats = {
        "markets": len(sample_markets),
        "analyzed": 3,
        "buy_signals": 1,
        "holds": 2,
        "trades": 1,
    }
    render_dashboard(logger, stats, markets=sample_markets)
    print("Demo showcase successfully generated and rendered to dashboard/index.html!")


if __name__ == "__main__":
    generate_demo_showcase()
