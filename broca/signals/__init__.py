"""
Signal management system for BrocaOS.

Provides centralized signal management with damping to prevent
unstable feedback loops across sensing → affect → self-model → dissonance → RL.
"""

from .schema import SignalSpec, SIGNAL_REGISTRY, register_signal
from .manager import SignalManager
from .models import SignalState

__all__ = [
    "SignalSpec",
    "SIGNAL_REGISTRY",
    "register_signal",
    "SignalManager",
    "SignalState",
]

