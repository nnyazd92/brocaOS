"""
Self-model system for maintaining LLM's model of itself.

Provides recursive self-modeling capabilities where the LLM builds and maintains
a model of its capabilities, preferences, knowledge boundaries, constraints,
and behavioral patterns. All responses are validated against this self-model
for consistency.
"""

from .model import SelfModel
from .storage import SelfModelSQLiteStorage, SelfModelStorage  # SelfModelStorage deprecated, use SelfModelSQLiteStorage
from .consistency import ConsistencyChecker, ConsistencyResult
from .updater import SelfModelUpdater
from .layer import ConsistencyLayer

__all__ = [
    "SelfModel",
    "SelfModelSQLiteStorage",  # Preferred storage backend
    "SelfModelStorage",  # Deprecated: use SelfModelSQLiteStorage
    "ConsistencyChecker",
    "ConsistencyResult",
    "SelfModelUpdater",
    "ConsistencyLayer",
]

