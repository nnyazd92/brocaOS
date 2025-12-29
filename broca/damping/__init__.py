"""
Damping system for BrocaOS.

Provides signal damping (EMA, rate limiting, deadband, hysteresis) and
action gating (debounce, cooldown, evidence windows) to prevent unstable
feedback loops.
"""

from .profiles import DampingProfile, PROFILE_REGISTRY, register_profile
from .pipeline import DampingPipeline
from .beta_tracker import BetaSuccessTracker
from .action_gate import ActionGate, ActionGateConfig
from .factory import (
    create_self_model_update_gate,
    create_rl_update_gate,
    create_suggestion_injection_gate,
)

__all__ = [
    "DampingProfile",
    "PROFILE_REGISTRY",
    "register_profile",
    "DampingPipeline",
    "BetaSuccessTracker",
    "ActionGate",
    "ActionGateConfig",
    "create_self_model_update_gate",
    "create_rl_update_gate",
    "create_suggestion_injection_gate",
]

