"""
Utilities for appending RL experience records and streaming events.

Provides thread-safe JSONL append helpers used by instrumentation.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, Any

_LOCK = threading.Lock()
_BASE = Path("data/rl")
_BASE.mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    with _LOCK:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False))
            f.write("
")


def append_experience(record: Dict[str, Any]) -> None:
    """Append a structured experience to data/rl/experiences.jsonl"""
    path = _BASE / "experiences.jsonl"
    _append_jsonl(path, record)


def append_stream_event(event: Dict[str, Any]) -> None:
    """Append a lightweight stream event for near-real-time ingestion."""
    path = _BASE / "stream.jsonl"
    _append_jsonl(path, event)


def append_reward(record: Dict[str, Any]) -> None:
    """Append reward record to data/rl/rewards.jsonl"""
    path = _BASE / "rewards.jsonl"
    _append_jsonl(path, record)
