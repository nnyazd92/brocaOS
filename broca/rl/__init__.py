"""
Reinforcement Learning module for BrocaOS.

This module provides RL-primary tool selection with confidence-gated modes:
- ≥85% confidence: RL forces tool selection (LLM bypassed)
- 30-85% confidence: RL suggests top-K tools (LLM picks from subset)
- <30% confidence: LLM has full choice (failsafe mode)
"""

from .online_policy import OnlinePolicyRanker, ToolSelection, PrioritizedReplayBuffer, Experience
from .policy import PolicyRanker

__all__ = [
    "OnlinePolicyRanker",
    "ToolSelection",
    "PrioritizedReplayBuffer",
    "Experience",
    "PolicyRanker",
]

