"""
Persisted reward design loader.

DESIGN_REWARD writes an audit-friendly JSON file containing the chosen reward shaping
parameters. This module loads that file and applies it to runtime config on startup.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..config import config


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def load_reward_design(path: str) -> Optional[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    current = data.get("current")
    if not isinstance(current, dict):
        return None
    return current


def apply_reward_design(current: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply persisted reward design values to runtime config.

    Returns a dict of changes applied.
    """
    before = {
        "reward_success": float(config.rl.reward_success),
        "reward_failure": float(config.rl.reward_failure),
        "time_penalty_factor": float(config.rl.time_penalty_factor),
        "max_latency_penalty": float(config.rl.max_latency_penalty),
        "quality_bonus_factor": float(config.rl.quality_bonus_factor),
    }

    if "reward_success" in current:
        config.rl.reward_success = _clamp01(float(current["reward_success"]))
    if "reward_failure" in current:
        config.rl.reward_failure = _clamp01(float(current["reward_failure"]))
    if "time_penalty_factor" in current:
        config.rl.time_penalty_factor = max(0.0, float(current["time_penalty_factor"]))
    if "max_latency_penalty" in current:
        config.rl.max_latency_penalty = _clamp01(float(current["max_latency_penalty"]))
    if "quality_bonus_factor" in current:
        config.rl.quality_bonus_factor = _clamp01(float(current["quality_bonus_factor"]))

    after = {
        "reward_success": float(config.rl.reward_success),
        "reward_failure": float(config.rl.reward_failure),
        "time_penalty_factor": float(config.rl.time_penalty_factor),
        "max_latency_penalty": float(config.rl.max_latency_penalty),
        "quality_bonus_factor": float(config.rl.quality_bonus_factor),
    }
    return {k: {"before": before[k], "after": after[k]} for k in before.keys() if before[k] != after[k]}


def apply_persisted_reward_design(path: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Load and apply persisted reward design. Returns (applied, changes).
    """
    design_path = path or getattr(config.rl, "reward_design_path", "data/rl/reward_design.json")
    current = load_reward_design(design_path)
    if current is None:
        return False, {}
    changes = apply_reward_design(current)
    return True, changes

