"""
Relevance scoring algorithms for context graph nodes.

Computes relevance scores based on thread membership, recency, depth,
and other factors to prioritize which messages to retain.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .context_graph import MessageNode


def compute_relevance_score(
    node: "MessageNode",
    is_main_thread: bool,
    is_recent: bool,
    main_thread_boost: float = 2.0,
    recency_decay_factor: float = 0.9,
) -> float:
    """
    Compute relevance score for a message node.
    
    Args:
        node: Message node to score
        is_main_thread: Whether node is in main conversation thread
        is_recent: Whether node is in recent messages
        main_thread_boost: Multiplier for main thread messages
        recency_decay_factor: How quickly relevance decays with age
        
    Returns:
        Relevance score (higher = more relevant)
    """
    score = 1.0
    
    # Main thread boost
    if is_main_thread:
        score *= main_thread_boost
    
    # Recency boost
    if is_recent:
        score *= 1.5
    
    # Recency decay based on last_accessed
    now = datetime.now(timezone.utc)
    age_seconds = (now - node.last_accessed).total_seconds()
    age_hours = age_seconds / 3600.0
    
    # Decay factor: older messages get lower scores
    if age_hours > 0:
        decay = recency_decay_factor ** (age_hours / 24.0)  # Decay per day
        score *= decay
    
    # Role-based adjustments
    if node.role == "user":
        score *= 1.2  # User messages are important
    elif node.role == "system":
        score *= 1.1  # System messages are important
    elif node.role == "tool":
        score *= 0.8  # Tool messages less critical (can be truncated)
    
    # Depth bonus: deeper in active threads = more relevant
    # (This is handled implicitly by main thread membership)
    
    # Orphan penalty
    if node.is_orphan:
        score *= 0.1  # Heavy penalty for orphans
    
    return max(0.0, score)  # Ensure non-negative

