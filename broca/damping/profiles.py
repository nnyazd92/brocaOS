"""
Damping profile definitions.

Profiles define how signals are damped (EMA, rate limiting, deadband, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Callable


@dataclass
class DampingProfile:
    """Damping profile configuration."""
    name: str
    smoothing_tau: Optional[float] = None  # Time constant for EMA (seconds), None to disable
    smoothing_alpha: Optional[float] = None  # Direct EMA alpha (0-1), None to disable
    deadband: float = 0.0  # Ignore changes smaller than this (epsilon)
    hysteresis_on: Optional[float] = None  # Threshold for ON state (for boolean triggers)
    hysteresis_off: Optional[float] = None  # Threshold for OFF state (for boolean triggers)
    rate_limit: Optional[float] = None  # Max delta per second, None to disable
    cooldown: Optional[float] = None  # Min time between actions (seconds), None to disable
    clamp_min: Optional[float] = None  # Hard minimum, None to disable
    clamp_max: Optional[float] = None  # Hard maximum, None to disable
    outlier_reject_zscore: Optional[float] = None  # Z-score threshold for outlier rejection, None to disable
    outlier_reject_percentile: Optional[tuple[float, float]] = None  # (low, high) percentile clip, None to disable
    trust_gate: Optional[Callable[[float], bool]] = None  # Optional condition predicate
    
    def __post_init__(self):
        """Validate profile configuration."""
        if self.smoothing_tau is not None and self.smoothing_alpha is not None:
            raise ValueError("Cannot specify both smoothing_tau and smoothing_alpha")
        if self.smoothing_tau is None and self.smoothing_alpha is None:
            # Default to no smoothing
            self.smoothing_tau = None
            self.smoothing_alpha = None


# Global profile registry
PROFILE_REGISTRY: Dict[str, DampingProfile] = {}


def register_profile(profile: DampingProfile) -> None:
    """Register a damping profile."""
    PROFILE_REGISTRY[profile.name] = profile


# Pre-register default profiles (as per spec section 11)
# FAST: alpha=0.35, rate_limit=2.0/sec, deadband=0.01
register_profile(DampingProfile(
    name="FAST",
    smoothing_alpha=0.35,
    rate_limit=2.0,
    deadband=0.01
))

# MED: alpha=0.15, rate_limit=0.8/sec, deadband=0.02
register_profile(DampingProfile(
    name="MED",
    smoothing_alpha=0.15,
    rate_limit=0.8,
    deadband=0.02
))

# SLOW: alpha=0.05, rate_limit=0.25/sec, deadband=0.03
register_profile(DampingProfile(
    name="SLOW",
    smoothing_alpha=0.05,
    rate_limit=0.25,
    deadband=0.03
))

# EVENT: debounce_ms=250, cooldown_ms=1000, hysteresis_on=0.65, hysteresis_off=0.45
register_profile(DampingProfile(
    name="EVENT",
    smoothing_alpha=0.1,  # Light smoothing
    deadband=0.05,
    hysteresis_on=0.65,
    hysteresis_off=0.45,
    cooldown=1.0  # 1 second cooldown
))

