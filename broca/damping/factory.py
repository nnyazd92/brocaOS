"""
Factory functions for creating ActionGates from configuration.

Provides helpers to create ActionGates with appropriate configurations
for different action types (self-model updates, RL updates, suggestions).
"""

from __future__ import annotations

import logging
from typing import Optional

from .action_gate import ActionGate, ActionGateConfig
from ..config import config

logger = logging.getLogger(__name__)


def create_self_model_update_gate() -> Optional[ActionGate]:
    """
    Create ActionGate for self-model updates using config.
    
    Returns:
        ActionGate instance or None if damping is disabled
    """
    if not config.damping.enabled:
        return None
    
    gate_config = ActionGateConfig(
        cooldown_seconds=config.damping.self_model_update_cooldown,
        min_evidence_window_seconds=config.damping.self_model_update_min_evidence_window,
        min_evidence_count=config.damping.self_model_update_min_evidence_count,
        sustained_trigger_threshold=0.5,  # Trigger if dissonance > 0.5
        sustained_trigger_window_seconds=30.0,  # Require sustained for 30s
    )
    
    return ActionGate(gate_config, action_name="self_model_update")


def create_rl_update_gate() -> Optional[ActionGate]:
    """
    Create ActionGate for RL policy updates using config.
    
    Returns:
        ActionGate instance or None if damping is disabled
    """
    if not config.damping.enabled:
        return None
    
    gate_config = ActionGateConfig(
        cooldown_seconds=config.damping.rl_update_cooldown,
        min_evidence_window_seconds=config.damping.rl_update_min_evidence_window,
        min_evidence_count=config.damping.rl_update_min_evidence_count,
        sustained_trigger_threshold=0.3,  # Lower threshold for RL (learn from small rewards)
        sustained_trigger_window_seconds=10.0,  # Shorter window for RL
    )
    
    return ActionGate(gate_config, action_name="rl_update")


def create_suggestion_injection_gate() -> Optional[ActionGate]:
    """
    Create ActionGate for LLM suggestion injection using config.
    
    Returns:
        ActionGate instance or None if damping is disabled
    """
    if not config.damping.enabled:
        return None
    
    gate_config = ActionGateConfig(
        debounce_seconds=config.damping.suggestion_injection_debounce,
        cooldown_seconds=config.damping.suggestion_injection_cooldown,
        min_evidence_count=config.damping.suggestion_injection_min_evidence_count,
        sustained_trigger_threshold=0.5,  # Trigger if suggestion confidence > 0.5
        sustained_trigger_window_seconds=5.0,  # Require sustained for 5s
    )
    
    return ActionGate(gate_config, action_name="suggestion_injection")

