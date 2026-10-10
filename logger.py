"""JSONL 日志模块（R5/F4）

每行 JSON，含 ts(UTC ISO)、event、以及决策全文。看板和复盘都读此文件。
event: start / analysis / trade_start / trade_done / error / trade_dry_run
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config


class JsonlLogger:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config.LOG_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, event: str, **extra: Any) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **extra,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def start(self, mode: str, market_count: int) -> None:
        self._write("start", mode=mode, marketCount=market_count)

    def analysis(self, market_id: str, title: str, decision: dict) -> None:
        self._write("analysis", marketId=market_id, title=title, decision=decision)

    def trade_start(self, market_id: str, title: str, decision: dict, amount: float, side: str) -> None:
        self._write("trade_start", marketId=market_id, title=title, decision=decision, amountUsdc=amount, side=side)

    def trade_dry_run(self, market_id: str, title: str, quote: dict, build: dict) -> None:
        self._write("trade_dry_run", marketId=market_id, title=title, quote=quote, build=build)

    def trade_done(self, market_id: str, title: str, signature: str, result: dict) -> None:
        self._write("trade_done", marketId=market_id, title=title, signature=signature, result=result)

    def error(self, market_id: str | None, message: str, **extra: Any) -> None:
        self._write("error", marketId=market_id, message=message, **extra)

    def read_all(self) -> list[dict[str, Any]]:
        """读取全部日志行（供看板与复盘）。"""
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records