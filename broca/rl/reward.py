"""
Reward shaping utilities shared by PPO + online NN and offline dataset building.

Design:
- Base reward: extrinsic anchor (success/quality minus latency penalty) plus
  potential-based intrinsic shaping from cognitive RL signals.

Reward contract (default):
- r_ext = success/failure (+ quality bonus)
- penalty_latency = execution_time_ms * factor (clamped)
- phi(s) = bounded potential derived from rl_signals (prefer varnorm if available)
- shaping = beta * (gamma * phi(post) - phi(pre))
- total = clamp01(r_ext + shaping - penalty_latency)
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

def phi_from_rl_signals(
    rl_signals: Optional[Dict[str, Any]],
    *,
    intrinsic_keys: Iterable[str],
    use_varnorm: bool = True,
) -> float:
    """
    Extract a bounded potential Phi(s) in [0,1] from rl_signals.

    Preference order:
    - composite_reward_varnorm (if present and use_varnorm)
    - composite_reward (if present)
    - mean of intrinsic component keys (excluding exploration_balance), preferring *_varnorm if present
    """
    if not isinstance(rl_signals, dict) or not rl_signals:
        return 0.5

    if use_varnorm and "composite_reward_varnorm" in rl_signals:
        return _clamp01(_safe_float(rl_signals.get("composite_reward_varnorm"), 0.5))
    if "composite_reward" in rl_signals:
        return _clamp01(_safe_float(rl_signals.get("composite_reward"), 0.5))

    keys = [k for k in intrinsic_keys if isinstance(k, str) and k != "exploration_balance"]
    vals = []
    for k in keys:
        kk = f"{k}_varnorm" if use_varnorm else k
        v = rl_signals.get(kk, rl_signals.get(k, None))
        if v is None:
            continue
        vals.append(_clamp01(_safe_float(v, default=0.5)))
    if not vals:
        return 0.5
    return float(sum(vals) / len(vals))

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
    # Backwards-compat: callers historically passed post-action signals as rl_signals.
    rl_signals: Optional[Dict[str, Any]] = None,
    pre_rl_signals: Optional[Dict[str, Any]] = None,
    post_rl_signals: Optional[Dict[str, Any]] = None,
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
    shaping_beta: float = 0.2,
    shaping_gamma: float = 0.99,
    use_varnorm_phi: bool = True,
) -> Tuple[float, Dict[str, float]]:
    # Interpret legacy rl_signals as post-action signals if post_rl_signals not provided.
    if post_rl_signals is None and isinstance(rl_signals, dict):
        post_rl_signals = rl_signals

    # Extrinsic anchor (success/quality) and latency penalty.
    extrinsic = compute_extrinsic_reward(
        success=bool(success),
        result_quality=float(result_quality if result_quality is not None else 0.5),
        reward_success=float(reward_success),
        reward_failure=float(reward_failure),
        quality_bonus_factor=float(quality_bonus_factor),
    )
    latency_penalty = compute_latency_penalty(
        execution_time_ms=float(execution_time_ms or 0.0),
        time_penalty_factor=float(time_penalty_factor),
        max_penalty=float(max_latency_penalty),
    )

    # Potential-based shaping (credit assignment): beta*(gamma*phi(s') - phi(s)).
    phi_post = phi_from_rl_signals(
        post_rl_signals,
        intrinsic_keys=intrinsic_keys,
        use_varnorm=bool(use_varnorm_phi),
    )
    gamma = float(shaping_gamma)
    beta = float(shaping_beta)
    if isinstance(pre_rl_signals, dict):
        phi_pre = phi_from_rl_signals(
            pre_rl_signals,
            intrinsic_keys=intrinsic_keys,
            use_varnorm=bool(use_varnorm_phi),
        )
        shaping = float(beta) * (float(gamma) * float(phi_post) - float(phi_pre))
    else:
        # Backwards-compat: when we don't have pre-state signals, do NOT apply shaping.
        # (Otherwise gamma<1 would introduce a small negative bias.)
        phi_pre = float(phi_post)
        shaping = 0.0

    # NOTE: RewardWeights kept for backwards compat; not used in this contract.
    _ = weights

    total = _clamp01(float(extrinsic) + float(shaping) - float(latency_penalty))
    parts = {
        "extrinsic": float(extrinsic),
        "latency_penalty": float(latency_penalty),
        "phi_pre": float(phi_pre),
        "phi_post": float(phi_post),
        "shaping": float(shaping),
        "total": float(total),
    }
    return total, parts
