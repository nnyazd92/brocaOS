"""
Actuator control system for environment access.

Provides actuator abstraction, approval system, and safety interlocks.
"""

from .base import Actuator, ActivationResult, DeactivationResult
from .approval import ApprovalSystem
from .safety import SafetyInterlock

__all__ = ["Actuator", "ActivationResult", "DeactivationResult", "ApprovalSystem", "SafetyInterlock"]

