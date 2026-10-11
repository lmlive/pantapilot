"""交易执行（R3 半链路 / R4 全链路）

按需求五步走：
① quote → ② build(未签名交易) → ③ 本地签名+广播 → ④ submit → ⑤ verify

- DRY_RUN=true（默认）：只走到 ② 即停，记 trade_dry_run，绝不签名广播。
- DRY_RUN=false：完整 ③④⑤。
- 任一异常记日志，循环不死。
"""
from __future__ import annotations

import base64
import logging
from typing import Any

import config
from logger import JsonlLogger
from panta import PantaClient

log = logging.getLogger("pantapilot.trader")


class Trader:
    def __init__(
        self,
        client: PantaClient,
        logger: JsonlLogger,
        wallet: str | None = None,
        dry_run: bool | None = None,
        max_trade_usdc: float | None = None,
    ) -> None:
        self.client = client
        self.logger = logger
        self.wallet = wallet or config.WALLET_ADDRESS
        self.dry_run = config.DRY_RUN if dry_run is None else dry_run
        self.max_trade_usdc = config.MAX_TRADE_USDC if max_trade_usdc is None else max_trade_usdc

    # ------------------------------------------------------------------
    def execute(self, market: dict[str, Any], decision: dict) -> dict[str, Any]:
        """根据 LLM 决策尝试下单。返回执行结果字典。"""
        result: dict[str, Any] = {"ok": False, "stage": "init"}
        market_id = str(market.get("marketId") or market.get("id") or "")
        title = market.get("title", "")
        side = "YES" if decision.get("decision") == "BUY_YES" else "NO"

        # amount = min(suggested, MAX_TRADE_USDC)
        suggested = float(decision.get("suggested_usdc", 0.0) or 0.0)
        amount = min(suggested, self.max_trade_usdc)
        if amount <= 0:
            amount = self.max_trade_usdc  # 有信号但没给额度时用上限内的保守值

        if not self.wallet:
            self.logger.error(market_id, "wallet 未配置，无法交易")
            result["stage"] = "no_wallet"
            return result

        try:
            # ① 询价
            quote = self.client.primary_order_quote(self.wallet, market_id, side, amount)
            result["stage"] = "quote"
            result["quote"] = quote
            quote_id = quote.get("quoteId")
            if not quote_id:
                raise RuntimeError(f"quote 无 quoteId: {quote}")

            # ② 构建未签名交易
            build = self.client.primary_order_build(quote_id, self.wallet)
            result["stage"] = "build"
            result["build"] = build

            self.logger.trade_start(market_id, title, decision, amount, side)

            # DRY_RUN：到此为止
            if self.dry_run:
                self.logger.trade_dry_run(market_id, title, quote, build)
                result["ok"] = True
                result["stage"] = "dry_run"
                return result

            # ③ 本地签名 + 广播
            signature = self._sign_and_send(build)
            result["signature"] = signature
            result["stage"] = "submitted"

            # ④ submit
            submit_resp = self.client.primary_order_submit(signature, quote_id, self.wallet)
            result["submit"] = submit_resp

            # ⑤ verify
            verify_resp = self.client.primary_order_verify(signature)
            result["verify"] = verify_resp

            self.logger.trade_done(market_id, title, signature, verify_resp)
            result["ok"] = True
            result["stage"] = "done"
            return result

        except Exception as exc:  # noqa: BLE001
            log.warning("交易失败 market=%s stage=%s: %s", market_id, result.get("stage"), exc)
            self.logger.error(market_id, f"trade failed at {result.get('stage')}: {exc}")
            result["error"] = str(exc)
            return result

    # ------------------------------------------------------------------
    def _sign_and_send(self, build: dict[str, Any]) -> str:
        """③ 本地签名（solders）+ RPC 广播，返回 signature。"""
        raw = build.get("transaction")
        if not raw:
            raise RuntimeError("build 无 transaction 字段")
        msg_bytes = base64.b64decode(raw)
        return _sign_and_send_bytes(msg_bytes, config.WALLET_PRIVATE_KEY, config.SOLANA_RPC_URL)


def _sign_and_send_bytes(msg_bytes: bytes, private_key_b58: str, rpc_url: str) -> str:
    """独立函数便于版本适配与测试。使用 solders 签名并广播。"""
    from base58 import b58decode

    from solders.keypair import Keypair
    from solders.transaction import VersionedTransaction

    keypair = Keypair.from_base58_string(private_key_b58)
    tx = VersionedTransaction.deserialize(msg_bytes)
    sig = keypair.sign_message(bytes(tx.message.serialize())) if hasattr(keypair, "sign_message") else None
    # solders 0.29 签名方式
    if sig is None:
        from solders.signature import Signature

        signed = tx.sign([keypair])
        sig = Signature.from_bytes(bytes(signed.signatures[0])) if signed.signatures else None
    if sig is None:
        raise RuntimeError("签名失败")

    populated = VersionedTransaction.populate(tx.message, [sig])
    # 广播
    _broadcast(populated, rpc_url)
    return str(sig)


def _broadcast(tx: Any, rpc_url: str) -> Any:
    import httpx

    from solders.signature import Signature

    from config import _clean_no_proxy

    _clean_no_proxy()
    raw = base64.b64encode(bytes(tx)).decode()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendTransaction",
        "params": [raw, {"encoding": "base64", "preflightCommitment": "confirmed"}],
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(rpc_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise RuntimeError(f"RPC 广播失败: {data['error']}")
        return Signature.from_string(data.get("result", ""))