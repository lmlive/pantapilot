"""Scout 情报侦察模块 — 为交易员 Agent 团队搜集情报。

情报源优先级：
1. oracle 数据源：Panta 市场自带的官方结算源 URL（如 fantasy.premierleague.com 实时数据）
2. 搜索引擎：Brave Search（沙箱内实测 200 可达；DuckDuckGo 被拦截）
3. 市场自身字段兜底

所有外部抓取全程 try/except，失败返回空情报（循环不死）。
"""
from __future__ import annotations

import html
import json
import logging
import re
from typing import Any

import httpx

import config

log = logging.getLogger("pantapilot.scout")

_clean_no_proxy = config._clean_no_proxy


_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _strip_tags(raw: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_oracle_sources(market: dict[str, Any], timeout: float = 12.0, max_chars: int = 3000) -> str:
    """拉取市场 oracle 字段指向的官方数据源（最强情报）。"""
    oracle = str(market.get("oracle") or "")
    urls = [u.strip() for u in oracle.split(",") if u.strip().startswith("http")]
    _clean_no_proxy()
    chunks: list[str] = []
    for url in urls[:2]:  # 最多 2 个源，控制延迟
        try:
            with httpx.Client(timeout=timeout, headers={"User-Agent": _UA}, follow_redirects=True) as c:
                r = c.get(url)
                if r.status_code == 200:
                    body = r.text
                    # JSON 端点直接截断；HTML 也保留原文（LLM 能读）
                    chunks.append(f"[source: {url}]\n{body[:max_chars]}")
        except Exception as exc:  # noqa: BLE001
            log.info("oracle 源抓取失败 %s: %s", url, exc)
    return "\n\n".join(chunks)


def search_brave(query: str, timeout: float = 12.0, max_chars: int = 2500) -> str:
    """Brave Search 兜底情报（沙箱实测可达）。抓不到时返回空串。"""
    _clean_no_proxy()
    try:
        with httpx.Client(timeout=timeout, headers={"User-Agent": _UA}, follow_redirects=True) as c:
            r = c.get("https://search.brave.com/search", params={"q": query})
            if r.status_code != 200:
                return ""
            text = _strip_tags(r.text)
            return text[:max_chars]
    except Exception as exc:  # noqa: BLE001
        log.info("brave 搜索失败: %s", exc)
        return ""


def gather_intel(market: dict[str, Any], enable_search: bool = True) -> dict[str, Any]:
    """Scout 主入口：给定市场返回情报包。

    返回 {oracleData, searchIntel, queries, meta}
    """
    title = str(market.get("title") or "").strip()
    category = str(market.get("category") or "")
    queries = [q for q in _build_queries(title, category) if q]

    intel: dict[str, Any] = {
        "queries": queries,
        "oracleData": "",
        "searchIntel": "",
        "meta": {"oracleAttempts": 0, "searchAttempts": 0},
    }

    oracle_data = fetch_oracle_sources(market)
    if oracle_data:
        intel["oracleData"] = oracle_data
        intel["meta"]["oracleAttempts"] = 1

    # 有 oracle 官方数据时，泛搜优先级降低（节省时间/避免无关噪声）
    if enable_search and not oracle_data and queries:
        intel["meta"]["searchAttempts"] = 1
        intel["searchIntel"] = search_brave(queries[0])

    return intel


def _build_queries(title: str, category: str) -> list[str]:
    """从市场标题/分类推导搜索查询（保守，只在标题可读时构造）。"""
    if not title or len(title) < 5:
        return []
    clean = re.sub(r"[^\w\s+-]", " ", title)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return []
    queries = [clean]
    if category:
        queries.append(f"{clean} {category}")
    return queries


def summarize_for_prompt(intel: dict[str, Any]) -> str:
    """把情报包拼成给下游 Agent 读的文本。"""
    parts: list[str] = []
    if intel.get("oracleData"):
        parts.append("### OFFICIAL ORACLE DATA (live settlement source)\n" + intel["oracleData"])
    if intel.get("searchIntel"):
        parts.append("### WEB SEARCH SNIPPETS\n" + intel["searchIntel"])
    if not parts:
        parts.append("(No external intel available — judge only from market fields.)")
    return "\n\n".join(parts)