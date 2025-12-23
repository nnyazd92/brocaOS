from __future__ import annotations

"""Helpers for world-state-aware LLM caching.

This module provides utilities to reduce the full world state into a
stable, cache-relevant subset and compute a deterministic fingerprint
for use in LLM cache keys.

Design goals:
- Respect that system prompts are world-state-driven and mutable.
- Avoid over-fragmenting the cache on high-churn details (exact timestamps).
- Capture meaningful changes in self-model, tools, memory index, repo tree, and
  coarse time buckets.
"""

from typing import Any, Dict
import hashlib
import json


def _extract_time_bucket(system_info: Dict[str, Any]) -> str | None:
    """Extract a coarse time bucket from system datetime.

    Currently buckets by hour (e.g. "2025-12-23T22"). This keeps the model
    time-aware while allowing cache reuse within a short window.
    """
    dt = system_info.get("datetime")
    if not isinstance(dt, str):
        return None
    # Expecting ISO format like "2025-12-23T22:11:05.506613+00:00" or similar
    # We take the first 13 chars: "YYYY-MM-DDTHH"
    if len(dt) >= 13:
        return dt[:13]
    return dt


def world_state_for_cache(world_state: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce full world_state into a stable, cache-relevant subset.

    Drops high-churn, low-semantic details while preserving:
    - Coarse time bucket (hourly) from system datetime
    - Self-model summary + version metadata
    - Tools registry version/hash
    - Memory index metadata
    - Repo root + tree hash
    - Coarse internal health metrics (if present)
    """
    reduced: Dict[str, Any] = {}

    system = world_state.get("system") or {}
    reduced["time_bucket"] = _extract_time_bucket(system)

    # Self-model: summary + version info
    sm = world_state.get("self_model") or {}
    reduced["self_model"] = {
        "summary": sm.get("summary"),
        "metadata": {
            "version": (sm.get("metadata") or {}).get("version"),
            "last_updated": (sm.get("metadata") or {}).get("last_updated"),
        },
    }

    # Tools: registry version + hash only
    tr = world_state.get("tools_registry") or {}
    reduced["tools_registry"] = {
        "version": tr.get("version"),
        "hash": tr.get("hash"),
    }

    # Memory: index metadata
    mem = (world_state.get("memory") or {}).get("memory_index") or {}
    reduced["memory_index"] = {
        "schema_version": mem.get("schema_version"),
        "last_indexed": mem.get("last_indexed"),
    }

    # Repo: directory structure hash and root
    repo = world_state.get("repo") or {}
    reduced["repo"] = {
        "root": repo.get("root"),
        "tree_hash": repo.get("tree_hash"),
    }

    # Internal state: coarse health only (if present)
    internal = world_state.get("internal_state") or {}
    physiology = internal.get("physiology") or {}
    reduced["internal_state"] = {
        "health": physiology.get("health"),
    }

    return reduced


def world_state_fingerprint(world_state: Dict[str, Any]) -> str:
    """Produce a stable SHA-256 fingerprint for the reduced world state."""
    reduced = world_state_for_cache(world_state)
    payload = json.dumps(reduced, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
