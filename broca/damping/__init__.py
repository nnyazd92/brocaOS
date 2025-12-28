"""
Damping system for BrocaOS.

Provides signal damping (EMA, rate limiting, deadband, hysteresis) and
action gating (debounce, cooldown, evidence windows) to prevent unstable
feedback loops.
"""

from .profiles import DampingProfile, PROFILE_REGISTRY, register_profile
from .pipeline import DampingPipeline

__all__ = [
    "DampingProfile",
    "PROFILE_REGISTRY",
    "register_profile",
    "DampingPipeline",
]

