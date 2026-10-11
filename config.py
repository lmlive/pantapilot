"""PantaPilot 配置与安全护栏 (R7/R8)

所有环境变量集中在此读取，带默认值。安全相关参数默认取最保守值。
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 清洗环境变量中会导致 httpx 解析失败的 no_proxy 条目（见需求文档 §5.1）
def clean_no_proxy() -> None:
    """清洗环境变量中会导致 httpx 解析失败的 no_proxy 条目。"""
    for key in ("no_proxy", "NO_PROXY"):
        val = os.environ.get(key, "")
        if not val:
            continue
        cleaned = ",".join(
            item for item in val.split(",") if item.strip() and "[" not in item and "]" not in item
        )
        if cleaned != val:
            os.environ[key] = cleaned

_clean_no_proxy = clean_no_proxy  # 兼容别名
_clean_no_proxy()

# 加载 .env（密钥）
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# 安全护栏（默认最保守）
# ---------------------------------------------------------------------------
# 是否 DRY_RUN：默认 True。True 时交易只走到询价+构建未签名交易即停，绝不签名广播。
DRY_RUN: bool = _env_bool("DRY_RUN", True)

# 单笔交易 USDC 上限（默认 5，评审要求"单笔不超几 USDC"）
MAX_TRADE_USDC: float = _env_float("MAX_TRADE_USDC", 5.0)

# 扫描间隔（分钟）
SCAN_INTERVAL_MINUTES: float = _env_float("SCAN_INTERVAL_MINUTES", 3.0)

# ---------------------------------------------------------------------------
# Panta API
# ---------------------------------------------------------------------------
PANTA_BASE_URL: str = os.getenv("PANTA_BASE_URL", "https://live-api.panta.market/api/v1")
PANTA_API_KEY: str = os.getenv("PANTA_API_KEY", "")

# 钱包私钥（专用小额 keypair，base58 编码）
WALLET_PRIVATE_KEY: str = os.getenv("WALLET_PRIVATE_KEY", "")
WALLET_ADDRESS: str = os.getenv("WALLET_ADDRESS", "")

# Solana RPC（仅真机广播需要）
SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "cohere/north-mini-code:free")
# 免费模型可能抽风，超时 60s + 重试 1 次（需求明确）
LLM_TIMEOUT_SECONDS: float = _env_float("LLM_TIMEOUT_SECONDS", 60.0)
LLM_MAX_RETRIES: int = _env_int("LLM_MAX_RETRIES", 1)

# 触发下单的最小置信度（降到 0.5 促成高质量 BUY 决策，避免全 HOLD）
MIN_CONFIDENCE: float = _env_float("MIN_CONFIDENCE", 0.5)

# Demo 演示限制：只跑 3-5 个精选市场（默认最多 5 个，0 表示不限制）
DEMO_MARKET_LIMIT: int = _env_int("DEMO_MARKET_LIMIT", 5)

# 多角色 Agent 团队（Scout→Estimator→Decision→Risk）开关；false 时退回单 agent 静态分析
AGENTS_ENABLED: bool = _env_bool("AGENTS_ENABLED", True)
# Scout 是否开启外部 web 搜索兜底（oracle 官方源始终尝试）
SCOUT_SEARCH_ENABLED: bool = _env_bool("SCOUT_SEARCH_ENABLED", True)

# ---------------------------------------------------------------------------
# 运行参数
# ---------------------------------------------------------------------------
LOG_FILE: Path = Path(os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "pantapilot.jsonl")))
DASHBOARD_FILE: Path = Path(os.getenv("DASHBOARD_FILE", str(BASE_DIR / "dashboard" / "index.html")))
MAX_DESC_CHARS: int = _env_int("MAX_DESC_CHARS", 1200)


def require_live_config() -> list[str]:
    """校验非 DRY_RUN 时必须具备的配置，返回缺失项列表。"""
    missing: list[str] = []
    if not PANTA_API_KEY:
        missing.append("PANTA_API_KEY")
    if not WALLET_PRIVATE_KEY or not WALLET_ADDRESS:
        missing.append("WALLET_PRIVATE_KEY / WALLET_ADDRESS")
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    return missing