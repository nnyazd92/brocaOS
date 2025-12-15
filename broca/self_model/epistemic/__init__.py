"""
Epistemic layer for second-order self-modeling.

Provides tracking of knowledge sources, confidence calibration, inference chains,
and temporal dynamics of knowledge evolution.
"""

from .models import (
    SourceType,
    SourceMetadata,
    ConfidenceMetrics,
    InferenceNode,
    KnowledgeEvolution,
    VerificationRecord,
)
from .layer import EpistemicLayer
from .ids import generate_knowledge_id, KnowledgeID
from .calibration import ConfidenceCalibrator
from .validation import SourceValidator
from .inference import InferenceTracker
from .integration import KnowledgeIntegrator
from .uncertainty import UncertaintyManager
from .engine import MetacognitiveEngine

__all__ = [
    "SourceType",
    "SourceMetadata",
    "ConfidenceMetrics",
    "InferenceNode",
    "KnowledgeEvolution",
    "VerificationRecord",
    "EpistemicLayer",
    "generate_knowledge_id",
    "KnowledgeID",
    "ConfidenceCalibrator",
    "SourceValidator",
    "InferenceTracker",
    "KnowledgeIntegrator",
    "UncertaintyManager",
    "MetacognitiveEngine",
]

