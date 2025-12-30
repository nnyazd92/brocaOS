"""
Shared feature extraction for RL policies (Online NN + PPO) and offline datasets.

Single source of truth for the 17-dim state vector:
- 7 RL signal features (in fixed order)
- 10 lightweight context features (goals/skills/memory/rules/recent tools)
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

import numpy as np

RL_SIGNAL_KEYS: List[str] = [
    "dissonance_reward",
    "surprise_reward",
    "curiosity_reward",
    "information_gain_reward",
    "coherence_reward",
    "exploration_balance",
]


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
    except Exception:
        return default
    if v != v:  # NaN
        return default
    if v == float("inf") or v == float("-inf"):
        return default
    return v


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

def _stable_hash01(text: str) -> float:
    """
    Deterministic hashing for feature encoding.

    Python's built-in `hash()` is randomized per-process by default, which makes
    features unstable across restarts. We use sha256 and map to [0, 1).
    """
    if not text:
        return 0.0
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
    # Use 32 bits for stable bucketing while keeping collisions acceptable.
    n = int.from_bytes(h[:4], "big", signed=False)
    return n / float(2**32)


def extract_state_features(context: Optional[Dict[str, Any]], input_dim: int = 17) -> np.ndarray:
    """
    Feature extraction (parity across training + inference):
    - 7 rl_signals (clamped [0, 1], default 0.5)
    - 10 simple context features
    """
    ctx = context or {}
    features: List[float] = []

    rl_signals = ctx.get("rl_signals", {}) or {}
    if not isinstance(rl_signals, dict):
        rl_signals = {}

    for k in RL_SIGNAL_KEYS:
        features.append(_clamp01(_safe_float(rl_signals.get(k, 0.5), default=0.5)))

    active_goals = ctx.get("active_goals", []) if isinstance(ctx.get("active_goals", []), list) else []
    features.append(min(len(active_goals), 5) / 5.0)
    try:
        features.append(max((g.get("priority", 0.5) for g in active_goals if isinstance(g, dict)), default=0.5))
    except Exception:
        features.append(0.5)
    try:
        goal_types = [g.get("goal_type", "") for g in active_goals if isinstance(g, dict)]
        features.append(_stable_hash01("".join(goal_types)))
    except Exception:
        features.append(0.0)

    skills = ctx.get("applicable_skills", []) if isinstance(ctx.get("applicable_skills", []), list) else []
    features.append(min(len(skills), 5) / 5.0)
    try:
        features.append(max((s.get("proficiency_level", 0.5) for s in skills if isinstance(s, dict)), default=0.5))
    except Exception:
        features.append(0.5)
    try:
        features.append(sum(_safe_float(s.get("usage_count", 0), 0.0) for s in skills[:3] if isinstance(s, dict)) / 100.0)
    except Exception:
        features.append(0.0)

    wm_items = ctx.get("working_memory_items", []) if isinstance(ctx.get("working_memory_items", []), list) else []
    features.append(min(len(wm_items), 10) / 10.0)
    recent_tools = ctx.get("recent_tools", []) if isinstance(ctx.get("recent_tools", []), list) else []
    features.append(min(len(recent_tools), 5) / 5.0)

    rules = ctx.get("production_rules", []) if isinstance(ctx.get("production_rules", []), list) else []
    features.append(min(len(rules), 10) / 10.0)
    try:
        active_rules = sum(1 for r in rules if isinstance(r, dict) and r.get("active", False))
        features.append(min(active_rules, 5) / 5.0)
    except Exception:
        features.append(0.0)

    while len(features) < input_dim:
        features.append(0.0)

    return np.array(features[:input_dim], dtype=np.float32)
