"""
Type definitions for environment access system.
"""

from enum import Enum


class AccessLevel(Enum):
    """Access levels for environment access."""
    
    SANDBOXED = 0      # Read-only, simulated environment
    SUPERVISED = 1     # Read-only real sensors, approval for writes
    AUTONOMOUS = 2     # Full access with safety constraints
    EMERGENCY = 3      # Override mode for critical situations

