"""
World state aggregation and formatting for dynamic system prompts.

Provides unified access to internal sensing, self-model, project state,
and system information for inclusion in LLM system prompts.
"""

from __future__ import annotations

from .aggregator import WorldStateAggregator
from .formatter import WorldStateFormatter

__all__ = ["WorldStateAggregator", "WorldStateFormatter"]

