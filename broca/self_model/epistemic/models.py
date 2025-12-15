"""
Epistemic data models for second-order self-modeling.

Defines data structures for tracking knowledge sources, confidence metrics,
inference chains, and knowledge evolution.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SourceType(str, Enum):
    """Types of knowledge sources."""
    
    TOOL_MEDIATED_VERIFICATION = "tool_mediated_verification"
    MEMORY_RETRIEVAL = "memory_retrieval"
    LOGICAL_INFERENCE = "logical_inference"
    USER_PROVIDED = "user_provided"
    EMERGENT_PATTERN = "emergent_pattern"
    EXTERNAL_SOURCE = "external_source"
    SYSTEM_DEFAULT = "system_default"


class SourceMetadata(BaseModel):
    """
    Metadata about the source of knowledge.
    
    Fields vary by source type:
    - TOOL_MEDIATED_VERIFICATION: tool_type, verification_method, timestamp, success_metrics
    - MEMORY_RETRIEVAL: memory_id, retrieval_confidence, recency_weight, importance_weight, cross_validation_count
    - LOGICAL_INFERENCE: premise_ids, inference_type, logical_strength, assumption_flags
    - USER_PROVIDED: user_identity, context, verification_status
    - EMERGENT_PATTERN: pattern_type, observation_count, statistical_significance, predictive_accuracy
    """
    
    source_type: SourceType
    
    # Tool-mediated verification fields
    tool_type: Optional[str] = None
    verification_method: Optional[str] = None
    timestamp: Optional[datetime] = None
    success_metrics: Optional[Dict[str, Any]] = None
    
    # Memory retrieval fields
    memory_id: Optional[int] = None
    retrieval_confidence: Optional[float] = None
    recency_weight: Optional[float] = None
    importance_weight: Optional[float] = None
    cross_validation_count: Optional[int] = None
    
    # Logical inference fields
    premise_ids: Optional[List[str]] = None
    inference_type: Optional[str] = None  # "deductive", "inductive", "abductive"
    logical_strength: Optional[float] = None
    assumption_flags: Optional[List[str]] = None
    
    # User-provided fields
    user_identity: Optional[str] = None  # "developer", "third_party"
    context: Optional[str] = None  # "direct_statement", "correction", "clarification"
    verification_status: Optional[str] = None  # "verified", "unverified", "contradicted"
    
    # Emergent pattern fields
    pattern_type: Optional[str] = None  # "tool_coordination", "interaction_pattern"
    observation_count: Optional[int] = None
    statistical_significance: Optional[float] = None
    predictive_accuracy: Optional[float] = None
    
    model_config = ConfigDict(use_enum_values=True)


class ConfidenceMetrics(BaseModel):
    """
    Multi-dimensional confidence metrics for knowledge items.
    
    Tracks confidence from multiple dimensions:
    - Source reliability
    - Temporal stability
    - Cross-validation
    - Contextual factors
    """
    
    # Source-based confidence
    source_reliability: Dict[str, float] = Field(
        default_factory=lambda: {
            "tool_verification_score": 0.0,
            "memory_consistency_score": 0.0,
            "logical_validity_score": 0.0,
            "user_credibility_score": 0.0,
        }
    )
    
    # Temporal confidence
    temporal_stability: Dict[str, Any] = Field(
        default_factory=lambda: {
            "verification_frequency": 0.0,
            "last_verification_age_hours": float("inf"),
            "consistency_over_time": 0.0,
        }
    )
    
    # Cross-validation confidence
    cross_validation: Dict[str, Any] = Field(
        default_factory=lambda: {
            "independent_verification_count": 0,
            "contradictory_evidence_count": 0,
            "consensus_strength": 0.0,
        }
    )
    
    # Contextual confidence
    contextual_factors: Dict[str, float] = Field(
        default_factory=lambda: {
            "domain_expertise_level": 0.0,
            "task_complexity_adjustment": 0.0,
            "environmental_stability": 0.0,
        }
    )
    
    # Composite confidence score
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Calibration error (measures how well confidence predicts accuracy)
    confidence_calibration_error: float = Field(default=0.0, ge=0.0)
    
    @field_validator("overall_confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is in [0, 1] range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("overall_confidence must be between 0.0 and 1.0")
        return v


class VerificationRecord(BaseModel):
    """
    Record of a verification event for knowledge.
    
    Tracks when knowledge was verified, how, and what the result was.
    """
    
    timestamp: datetime
    verification_type: str  # "tool_test", "memory_retrieval", "logical_analysis"
    result: str  # "confirmed", "refuted", "modified"
    confidence_delta: float = 0.0  # Change in confidence from this verification
    new_evidence: List[SourceMetadata] = Field(default_factory=list)


class InferenceNode(BaseModel):
    """
    Node in an inference graph representing a piece of knowledge.
    
    Tracks dependencies (what this depends on) and dependents (what depends on this).
    """
    
    knowledge_id: str
    node_type: str  # "premise", "inference", "conclusion", "assumption"
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: SourceMetadata
    
    dependencies: List["InferenceNode"] = Field(default_factory=list)
    dependents: List["InferenceNode"] = Field(default_factory=list)
    
    logical_relationship: Dict[str, Any] = Field(
        default_factory=lambda: {
            "strength": 0.0,
            "type": "necessity",  # "necessity", "sufficiency", "correlation"
            "counterfactual_support": 0.0,
        }
    )
    
    revision_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is in [0, 1] range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class KnowledgeEvolution(BaseModel):
    """
    Tracks the evolution of knowledge over time.
    
    Records creation, verification history, usage patterns, and relationships.
    """
    
    creation_event: Dict[str, Any]  # timestamp, initial_confidence, initial_source
    verification_history: List[VerificationRecord] = Field(default_factory=list)
    usage_patterns: Dict[str, Any] = Field(
        default_factory=lambda: {
            "retrieval_frequency": 0.0,
            "context_applicability": {},
            "predictive_accuracy": 0.0,
        }
    )
    relationship_network: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "supporting_knowledge": [],
            "contradictory_knowledge": [],
            "dependent_knowledge": [],
            "similarity_clusters": [],
        }
    )

