"""
Signal schema definitions and registry.

Defines all runtime signals with their types, ranges, units, and damping profiles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Union, Any
from enum import Enum


class SignalType(Enum):
    """Signal value type."""
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    CATEGORICAL = "categorical"


@dataclass
class SignalSpec:
    """Specification for a signal."""
    name: str
    type: SignalType
    range: tuple[float, float] | tuple[int, int] | list[str]  # [min, max] for numeric, enum list for categorical
    units: str  # "prob", "zscore", "score", "rate", etc.
    default: float | int | bool | str
    update_frequency_hz: float  # Expected update frequency
    damping_profile_id: str  # Profile ID from damping profiles
    
    def validate_value(self, value: Any) -> bool:
        """Validate that a value matches the signal spec."""
        if self.type == SignalType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
            min_val, max_val = self.range
            return min_val <= float(value) <= max_val
        elif self.type == SignalType.INT:
            if not isinstance(value, int):
                return False
            min_val, max_val = self.range
            return min_val <= value <= max_val
        elif self.type == SignalType.BOOL:
            return isinstance(value, bool)
        elif self.type == SignalType.CATEGORICAL:
            return value in self.range
        return False
    
    def clamp_value(self, value: Any) -> float | int | bool | str:
        """Clamp a value to the signal's range."""
        if self.type == SignalType.FLOAT:
            val = float(value)
            min_val, max_val = self.range
            return max(min_val, min(val, max_val))
        elif self.type == SignalType.INT:
            val = int(value)
            min_val, max_val = self.range
            return max(min_val, min(val, max_val))
        elif self.type == SignalType.BOOL:
            return bool(value)
        elif self.type == SignalType.CATEGORICAL:
            if value in self.range:
                return value
            return self.default
        return value


# Global signal registry
SIGNAL_REGISTRY: Dict[str, SignalSpec] = {}


def register_signal(spec: SignalSpec) -> None:
    """Register a signal specification."""
    SIGNAL_REGISTRY[spec.name] = spec


# Pre-register all signals from spec
# Affect signals
register_signal(SignalSpec(
    name="affect.valence",
    type=SignalType.FLOAT,
    range=(-1.0, 1.0),
    units="prob",
    default=0.0,
    update_frequency_hz=1.0,
    damping_profile_id="MED"
))

register_signal(SignalSpec(
    name="affect.arousal",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.5,
    update_frequency_hz=1.0,
    damping_profile_id="MED"
))

# Self-model uncertainty
register_signal(SignalSpec(
    name="self_model.uncertainty",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.5,
    update_frequency_hz=0.5,
    damping_profile_id="SLOW"
))

# Dissonance signals
register_signal(SignalSpec(
    name="dissonance.level",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.0,
    update_frequency_hz=0.5,
    damping_profile_id="SLOW"
))

register_signal(SignalSpec(
    name="dissonance.logical",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.0,
    update_frequency_hz=0.5,
    damping_profile_id="SLOW"
))

register_signal(SignalSpec(
    name="dissonance.factual",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.0,
    update_frequency_hz=0.5,
    damping_profile_id="SLOW"
))

register_signal(SignalSpec(
    name="dissonance.behavioral",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.0,
    update_frequency_hz=0.5,
    damping_profile_id="SLOW"
))

register_signal(SignalSpec(
    name="dissonance.goal",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.0,
    update_frequency_hz=0.5,
    damping_profile_id="SLOW"
))

# LLM suggestion confidence
register_signal(SignalSpec(
    name="llm.suggestion_confidence",
    type=SignalType.FLOAT,
    range=(0.0, 1.0),
    units="prob",
    default=0.5,
    update_frequency_hz=2.0,
    damping_profile_id="FAST"
))

# Toolchain signals are registered dynamically per tool
# Pattern: toolchain.{tool_name}.success_rate, toolchain.{tool_name}.latency_ms

