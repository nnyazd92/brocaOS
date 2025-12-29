"""
Context management system using tree/graph structure.

Provides intelligent context pruning that preserves main conversation thread
while automatically removing orphaned branches.
"""

from .context_graph import ContextGraph, MessageNode
from .relevance import compute_relevance_score

__all__ = ["ContextGraph", "MessageNode", "compute_relevance_score"]

