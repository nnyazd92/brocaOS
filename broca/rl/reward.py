"""
Reward shaping utilities shared by PPO + online NN and offline dataset building.

Design:
- Base reward: composite_reward (0..1) from cognitive RL signals.
- Tool-related adjustment: +/- success/failure + optional quality + latency penalty.
- Latency is a reward-only penalty (NOT included as a feature).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


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


@dataclass(frozen=True)
class RewardWeights:
    extrinsic_weight: float = 0.5
    intrinsic_weight: float = 0.5


def compute_intrinsic_reward(
    rl_signals: Optional[Dict[str, Any]],
    *,
    keys: Iterable[str],
) -> Optional[float]:
    if not rl_signals or not isinstance(rl_signals, dict):
        return None

    vals = []
    for k in keys:
        if k not in rl_signals:
            continue
        vals.append(_clamp01(_safe_float(rl_signals.get(k), default=0.0)))

    if not vals:
        return None
    return float(sum(vals) / len(vals))

def compute_base_composite_reward(rl_signals: Optional[Dict[str, Any]], *, intrinsic_keys: Iterable[str]) -> float:
    """
    Prefer composite_reward if present. If missing, fall back to the mean of the
    intrinsic components (excluding exploration_balance if included in intrinsic_keys).
    """
    if isinstance(rl_signals, dict):
        if "composite_reward" in rl_signals:
            return _clamp01(_safe_float(rl_signals.get("composite_reward"), 0.0))

    # Fallback: recompute from components (best-effort). This is only used when
    # callers didn't supply composite_reward in post_context/CSV.
    keys = [k for k in intrinsic_keys if k != "exploration_balance"]
    intrinsic = compute_intrinsic_reward(rl_signals, keys=keys)
    return _clamp01(intrinsic) if intrinsic is not None else 0.0


def compute_extrinsic_reward(
    *,
    success: bool,
    result_quality: float = 0.5,
    reward_success: float = 0.8,
    reward_failure: float = 0.2,
    quality_bonus_factor: float = 0.2,
) -> float:
    base = float(reward_success if success else reward_failure)
    base = _clamp01(base)
    bonus = _clamp01(_safe_float(result_quality, 0.5)) * float(quality_bonus_factor)
    return _clamp01(base + bonus)

def compute_tool_adjustment(
    *,
    success: bool,
    reward_success: float,
    reward_failure: float,
    result_quality: float,
    quality_bonus_factor: float,
) -> float:
    """
    Tool-related +/- adjustment centered around 0:
    - success contributes (reward_success - 0.5)
    - failure contributes (reward_failure - 0.5)
    - quality contributes (result_quality - 0.5) * quality_bonus_factor
    """
    base = float(reward_success if success else reward_failure) - 0.5
    q = (_clamp01(_safe_float(result_quality, 0.5)) - 0.5) * float(quality_bonus_factor)
    return float(base + q)


def compute_latency_penalty(
    *,
    execution_time_ms: float,
    time_penalty_factor: float = 0.00002,
    max_penalty: float = 0.2,
) -> float:
    ms = max(0.0, _safe_float(execution_time_ms, 0.0))
    penalty = ms * float(time_penalty_factor)
    return max(0.0, min(float(max_penalty), float(penalty)))


def compute_total_reward(
    *,
    base_composite_reward: float,
    tool_adjustment: float,
    latency_penalty: float,
    weights: RewardWeights = RewardWeights(),
) -> float:
    # NOTE: weights kept for backwards compat; formula is now:
    # composite_reward +/- (tool adjustment) - latency_penalty
    return _clamp01(_clamp01(base_composite_reward) + float(tool_adjustment) - _clamp01(latency_penalty))


def compute_reward_from_outcome(
    *,
    rl_signals: Optional[Dict[str, Any]],
    intrinsic_keys: Iterable[str],
    success: bool,
    execution_time_ms: float,
    result_quality: float = 0.5,
    reward_success: float = 0.8,
    reward_failure: float = 0.2,
    time_penalty_factor: float = 0.00002,
    max_latency_penalty: float = 0.2,
    quality_bonus_factor: float = 0.2,
    weights: RewardWeights = RewardWeights(),
) -> Tuple[float, Dict[str, float]]:
    base = compute_base_composite_reward(rl_signals, intrinsic_keys=intrinsic_keys)
    tool_adj = compute_tool_adjustment(
        success=success,
        reward_success=reward_success,
        reward_failure=reward_failure,
        result_quality=result_quality,
        quality_bonus_factor=quality_bonus_factor,
    )
    penalty = compute_latency_penalty(
        execution_time_ms=execution_time_ms,
        time_penalty_factor=time_penalty_factor,
        max_penalty=max_latency_penalty,
    )
    total = compute_total_reward(
        base_composite_reward=base,
        tool_adjustment=tool_adj,
        latency_penalty=penalty,
        weights=weights,
    )
    parts = {
        "composite_reward": float(base),
        "tool_adjustment": float(tool_adj),
        "latency_penalty": float(penalty),
        "total": float(total),
    }
    return total, parts
