"""Panta API 客户端（R1 市场扫描 + 交易链路）

封装 Panta 预测市场 HTTP 接口。所有调用走 httpx，容错处理包含：
- 清洗 no_proxy 中含 '[' 的条目（避免 httpx 解析 Invalid port: ':1]'）
- 状态值宽容匹配（大小写不敏感 + 多别名）
- 列表字段为 items 而非 results；detail 价格可能为 null，以列表为准
"""
from __future__ import annotations

import os
import time
import logging
from typing import Any

import httpx

import config

log = logging.getLogger("pantapilot.panta")

# 状态别名 → 归一化状态
# 注意：secondary_active 属于 secondary（只能二级交易），不能当作 primary
_PRIMARY_ALIASES = {"primary", "Primary", "PRIMARY", "open", "Open", "trading"}
_SECONDARY_ALIASES = {"secondary", "Secondary", "SECONDARY", "secondary_active", "SecondaryActive"}
_RESOLVED_ALIASES = {"resolved", "Resolved", "RESOLVED", "closed", "Closed", "settled", "Settled"}


def _clean_no_proxy() -> None:
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


def normalize_status(raw: Any) -> str:
    """把不稳定的 status 值归一化为 primary / secondary / resolved / unknown。"""
    s = str(raw or "").strip()
    if not s:
        return "unknown"
    if s in _SECONDARY_ALIASES:
        return "secondary"
    if s in _RESOLVED_ALIASES:
        return "resolved"
    if s in _PRIMARY_ALIASES:
        return "primary"
    if "resolved" in s.lower() or "settled" in s.lower() or "closed" in s.lower():
        return "resolved"
    if "secondary" in s.lower() or "market_not_in_primary" in s.lower():
        return "secondary"
    if "primary" in s.lower() or "open" in s.lower() or "trading" in s.lower():
        return "primary"
    return "secondary"


class PantaClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        _clean_no_proxy()
        self.base_url = (base_url or config.PANTA_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else config.PANTA_API_KEY
        self.timeout = timeout
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        self._client = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # 市场扫描
    # ------------------------------------------------------------------
    def list_markets(self) -> list[dict[str, Any]]:
        """GET /markets/ 拉取全量市场（处理 items/nextCursor 分页）。"""
        markets: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params = {} if cursor is None else {"cursor": cursor}
            resp = self._client.get("/markets/", params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items") or data.get("results") or []
            markets.extend(items)
            cursor = data.get("nextCursor")
            if not cursor:
                break
        return markets

    def market_detail(self, market_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/markets/{market_id}/")
        resp.raise_for_status()
        return resp.json()

    def list_categories(self) -> list[dict[str, Any]]:
        resp = self._client.get("/categories/")
        resp.raise_for_status()
        data = resp.json()
        return data.get("items") or data.get("results") or []

    # ------------------------------------------------------------------
    # 交易链路（primary 阶段）
    # ------------------------------------------------------------------
    def primary_order_quote(self, wallet: str, market_id: str, side: str, amount_usdc: float) -> dict[str, Any]:
        """① 询价。amount 用人类可读小数。"""
        body = {
            "wallet": wallet,
            "marketId": market_id,
            "side": side,
            "amountUsdc": f"{amount_usdc:.2f}",
        }
        resp = self._client.post("/primaryorderquote/", json=body)
        resp.raise_for_status()
        return resp.json()

    def primary_order_build(self, quote_id: str, wallet: str, max_slippage_bps: int = 100) -> dict[str, Any]:
        """② 构建未签名交易。返回 base64 transaction。"""
        body = {"quoteId": quote_id, "wallet": wallet, "maxSlippageBps": max_slippage_bps}
        resp = self._client.post("/primaryorderbuild/", json=body)
        resp.raise_for_status()
        return resp.json()

    def primary_order_submit(self, signature: str, quote_id: str, wallet: str) -> dict[str, Any]:
        """④ 提交签名后的交易。"""
        body = {"signature": signature, "quoteId": quote_id, "wallet": wallet}
        resp = self._client.post("/primaryordersubmit/", json=body)
        resp.raise_for_status()
        return resp.json()

    def primary_order_verify(self, signature: str) -> dict[str, Any]:
        """⑤ 校验。"""
        resp = self._client.post("/primaryorderverify/", json={"signature": signature})
        resp.raise_for_status()
        return resp.json()

    def claim_build(self, wallet: str) -> dict[str, Any]:
        resp = self._client.post("/claim/build/", json={"wallet": wallet})
        resp.raise_for_status()
        return resp.json()

    def positions(self, wallet: str) -> list[dict[str, Any]]:
        resp = self._client.get("/positions/", params={"wallet": wallet})
        resp.raise_for_status()
        data = resp.json()
        return data.get("items") or data.get("results") or []

    # ------------------------------------------------------------------
    # 便捷方法
    # ------------------------------------------------------------------
    def primary_markets(self) -> list[dict[str, Any]]:
        """返回可下单的 primary 且未结算的市场，并用 detail 补充价格字段。

        list 端点价格字段不稳定（可能为 None）；detail 端点通常有完整价格。
        列表缺价格时用 detail 兜底，保证 LLM/看板拿到真实价格。
        """
        candidates = []
        for m in self.list_markets():
            status = normalize_status(m.get("status") or m.get("phase"))
            resolved = bool(m.get("resolved", False))
            if status == "primary" and not resolved:
                candidates.append(m)

        enriched = []
        for m in candidates:
            mid = str(m.get("marketId") or m.get("id") or "")
            if mid and (m.get("yesPrice") in (None, "") or m.get("noPrice") in (None, "")):
                try:
                    detail = self.market_detail(mid)
                    merged = dict(m)
                    merged.update({k: v for k, v in detail.items() if v is not None})
                    m = merged
                except Exception as exc:  # noqa: BLE001
                    log.warning("市场详情拉取失败 %s: %s", mid, exc)
            enriched.append(m)
        return enriched


def market_to_prompt_block(m: dict[str, Any], max_desc: int | None = None) -> str:
    """把市场对象拼成喂给 LLM 的文本（F2 输入格式）。"""
    max_desc = max_desc or config.MAX_DESC_CHARS
    desc = (m.get("description") or "")[:max_desc]
    end_time = m.get("endTime")
    end_str = _format_end_time(end_time)
    yes_price = _get_price(m, "yes")
    no_price = _get_price(m, "no")
    return (
        f"Market: {m.get('title', '')}\n"
        f"Description: {desc}\n"
        f"Category: {m.get('category', '')}\n"
        f"CURRENT YES PRICE: {yes_price} (probability the event happens)\n"
        f"CURRENT NO PRICE: {no_price}\n"
        f"Volume: {m.get('volumeUsdc', '')} USDC\n"
        f"Resolves: {end_str}\n"
        f"Oracle: {m.get('oracle', '')}\n"
    )


def _get_price(m: dict[str, Any], side: str) -> Any:
    """获取 YES/NO 价格，带主价/次价兜底。返回可显示的值或 ''。"""
    if side == "yes":
        keys = ("yesPrice", "primaryYesPrice")
    else:
        keys = ("noPrice", "primaryNoPrice")
    for k in keys:
        v = m.get(k)
        if v is not None and v != "":
            return v
    return ""


def _format_end_time(end_time: Any) -> str:
    if end_time is None:
        return "unknown"
    try:
        ts = float(end_time)
    except (TypeError, ValueError):
        return str(end_time)
    if ts > 1e12:
        ts /= 1000.0  # 毫秒转秒
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(ts))