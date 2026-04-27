from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
AUDIT_LOG_FILE = LOG_DIR / "audit_log.jsonl"
PIPELINE_LOG_FILE = LOG_DIR / "logs.jsonl"


def log_audit(event: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with AUDIT_LOG_FILE.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def log_pipeline(event: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with PIPELINE_LOG_FILE.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
