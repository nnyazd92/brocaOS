"""
Tests for epistemic data models.

Tests SourceType, SourceMetadata, ConfidenceMetrics, InferenceNode,
KnowledgeEvolution, and VerificationRecord.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Dict, Any
from pydantic import ValidationError

from broca.self_model.epistemic.models import (
    SourceType,
    SourceMetadata,
    ConfidenceMetrics,
    InferenceNode,
    KnowledgeEvolution,
    VerificationRecord,
)


class TestSourceType:
    """Test SourceType enum."""
    
    def test_source_type_values(self):
        """Test that all source types are defined."""
        assert SourceType.TOOL_MEDIATED_VERIFICATION == "tool_mediated_verification"
        assert SourceType.MEMORY_RETRIEVAL == "memory_retrieval"
        assert SourceType.LOGICAL_INFERENCE == "logical_inference"
        assert SourceType.USER_PROVIDED == "user_provided"
        assert SourceType.EMERGENT_PATTERN == "emergent_pattern"


class TestSourceMetadata:
    """Test SourceMetadata data structures."""
    
    def test_tool_mediated_verification_metadata(self):
        """Test tool-mediated verification source metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="terminal",
            verification_method="direct_execution",
            timestamp=datetime.now(timezone.utc),
            success_metrics={"success": True, "exit_code": 0}
        )
        
        assert metadata.source_type == SourceType.TOOL_MEDIATED_VERIFICATION
        assert metadata.tool_type == "terminal"
        assert metadata.verification_method == "direct_execution"
        assert metadata.success_metrics["success"] is True
    
    def test_memory_retrieval_metadata(self):
        """Test memory retrieval source metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.MEMORY_RETRIEVAL,
            memory_id=123,
            retrieval_confidence=0.85,
            recency_weight=0.9,
            importance_weight=0.8,
            cross_validation_count=3
        )
        
        assert metadata.source_type == SourceType.MEMORY_RETRIEVAL
        assert metadata.memory_id == 123
        assert metadata.retrieval_confidence == 0.85
        assert metadata.cross_validation_count == 3
    
    def test_logical_inference_metadata(self):
        """Test logical inference source metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            premise_ids=["premise1", "premise2"],
            inference_type="deductive",
            logical_strength=0.9,
            assumption_flags=["assumption1"]
        )
        
        assert metadata.source_type == SourceType.LOGICAL_INFERENCE
        assert len(metadata.premise_ids) == 2
        assert metadata.inference_type == "deductive"
        assert metadata.logical_strength == 0.9
    
    def test_user_provided_metadata(self):
        """Test user-provided source metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            user_identity="developer",
            context="direct_statement",
            verification_status="unverified"
        )
        
        assert metadata.source_type == SourceType.USER_PROVIDED
        assert metadata.user_identity == "developer"
        assert metadata.verification_status == "unverified"
    
    def test_emergent_pattern_metadata(self):
        """Test emergent pattern source metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.EMERGENT_PATTERN,
            pattern_type="tool_coordination",
            observation_count=15,
            statistical_significance=0.95,
            predictive_accuracy=0.88
        )
        
        assert metadata.source_type == SourceType.EMERGENT_PATTERN
        assert metadata.pattern_type == "tool_coordination"
        assert metadata.observation_count == 15


class TestConfidenceMetrics:
    """Test ConfidenceMetrics data structure."""
    
    def test_confidence_metrics_creation(self):
        """Test creating confidence metrics with all fields."""
        metrics = ConfidenceMetrics(
            source_reliability={
                "tool_verification_score": 0.9,
                "memory_consistency_score": 0.85,
                "logical_validity_score": 0.8,
                "user_credibility_score": 0.95
            },
            temporal_stability={
                "verification_frequency": 0.1,
                "last_verification_age_hours": 24.0,
                "consistency_over_time": 0.9
            },
            cross_validation={
                "independent_verification_count": 3,
                "contradictory_evidence_count": 0,
                "consensus_strength": 0.95
            },
            contextual_factors={
                "domain_expertise_level": 0.8,
                "task_complexity_adjustment": 0.9,
                "environmental_stability": 0.85
            },
            overall_confidence=0.88,
            confidence_calibration_error=0.05
        )
        
        assert metrics.overall_confidence == 0.88
        assert metrics.source_reliability["tool_verification_score"] == 0.9
        assert metrics.cross_validation["independent_verification_count"] == 3
    
    def test_confidence_metrics_defaults(self):
        """Test confidence metrics with minimal fields."""
        metrics = ConfidenceMetrics(overall_confidence=0.5)
        
        assert metrics.overall_confidence == 0.5
        assert metrics.source_reliability is not None
        assert metrics.temporal_stability is not None
    
    def test_confidence_metrics_validation(self):
        """Test that confidence values are in valid range [0, 1]."""
        # Valid values
        metrics = ConfidenceMetrics(overall_confidence=0.5)
        assert metrics.overall_confidence == 0.5
        
        # Boundary values
        metrics_min = ConfidenceMetrics(overall_confidence=0.0)
        metrics_max = ConfidenceMetrics(overall_confidence=1.0)
        assert metrics_min.overall_confidence == 0.0
        assert metrics_max.overall_confidence == 1.0
        
        # Invalid values should raise validation error
        with pytest.raises(ValidationError):
            ConfidenceMetrics(overall_confidence=-0.1)
        
        with pytest.raises(ValidationError):
            ConfidenceMetrics(overall_confidence=1.1)


class TestVerificationRecord:
    """Test VerificationRecord data structure."""
    
    def test_verification_record_creation(self):
        """Test creating a verification record."""
        record = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="tool_test",
            result="confirmed",
            confidence_delta=0.1,
            new_evidence=[SourceMetadata(
                source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
                tool_type="terminal"
            )]
        )
        
        assert record.verification_type == "tool_test"
        assert record.result == "confirmed"
        assert record.confidence_delta == 0.1
        assert len(record.new_evidence) == 1
    
    def test_verification_record_results(self):
        """Test different verification results."""
        confirmed = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="tool_test",
            result="confirmed"
        )
        refuted = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="tool_test",
            result="refuted"
        )
        modified = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="tool_test",
            result="modified"
        )
        
        assert confirmed.result == "confirmed"
        assert refuted.result == "refuted"
        assert modified.result == "modified"


class TestInferenceNode:
    """Test InferenceNode data structure."""
    
    def test_inference_node_creation(self):
        """Test creating an inference node."""
        node = InferenceNode(
            knowledge_id="test_knowledge_1",
            node_type="inference",
            confidence=0.8,
            source=SourceMetadata(
                source_type=SourceType.LOGICAL_INFERENCE,
                inference_type="deductive"
            )
        )
        
        assert node.knowledge_id == "test_knowledge_1"
        assert node.node_type == "inference"
        assert node.confidence == 0.8
        assert node.dependencies == []
        assert node.dependents == []
    
    def test_inference_node_dependencies(self):
        """Test inference node with dependencies."""
        premise = InferenceNode(
            knowledge_id="premise_1",
            node_type="premise",
            confidence=0.9,
            source=SourceMetadata(source_type=SourceType.USER_PROVIDED)
        )
        
        inference = InferenceNode(
            knowledge_id="inference_1",
            node_type="inference",
            confidence=0.8,
            source=SourceMetadata(source_type=SourceType.LOGICAL_INFERENCE),
            dependencies=[premise]
        )
        
        assert len(inference.dependencies) == 1
        assert inference.dependencies[0].knowledge_id == "premise_1"
    
    def test_inference_node_types(self):
        """Test different node types."""
        premise = InferenceNode(
            knowledge_id="p1",
            node_type="premise",
            confidence=0.9,
            source=SourceMetadata(source_type=SourceType.USER_PROVIDED)
        )
        inference = InferenceNode(
            knowledge_id="i1",
            node_type="inference",
            confidence=0.8,
            source=SourceMetadata(source_type=SourceType.LOGICAL_INFERENCE)
        )
        conclusion = InferenceNode(
            knowledge_id="c1",
            node_type="conclusion",
            confidence=0.7,
            source=SourceMetadata(source_type=SourceType.LOGICAL_INFERENCE)
        )
        assumption = InferenceNode(
            knowledge_id="a1",
            node_type="assumption",
            confidence=0.6,
            source=SourceMetadata(source_type=SourceType.LOGICAL_INFERENCE)
        )
        
        assert premise.node_type == "premise"
        assert inference.node_type == "inference"
        assert conclusion.node_type == "conclusion"
        assert assumption.node_type == "assumption"


class TestKnowledgeEvolution:
    """Test KnowledgeEvolution data structure."""
    
    def test_knowledge_evolution_creation(self):
        """Test creating knowledge evolution tracking."""
        evolution = KnowledgeEvolution(
            creation_event={
                "timestamp": datetime.now(timezone.utc),
                "initial_confidence": 0.7,
                "initial_source": SourceMetadata(
                    source_type=SourceType.USER_PROVIDED
                )
            }
        )
        
        assert evolution.creation_event["initial_confidence"] == 0.7
        assert evolution.verification_history == []
        assert evolution.usage_patterns is not None
        assert evolution.relationship_network is not None
    
    def test_knowledge_evolution_verification_history(self):
        """Test adding verification events to history."""
        evolution = KnowledgeEvolution(
            creation_event={
                "timestamp": datetime.now(timezone.utc),
                "initial_confidence": 0.7,
                "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
            }
        )
        
        verification = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="tool_test",
            result="confirmed",
            confidence_delta=0.1
        )
        
        evolution.verification_history.append(verification)
        
        assert len(evolution.verification_history) == 1
        assert evolution.verification_history[0].result == "confirmed"
    
    def test_knowledge_evolution_usage_patterns(self):
        """Test usage pattern tracking."""
        evolution = KnowledgeEvolution(
            creation_event={
                "timestamp": datetime.now(timezone.utc),
                "initial_confidence": 0.7,
                "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
            }
        )
        
        evolution.usage_patterns["retrieval_frequency"] = 0.5
        evolution.usage_patterns["predictive_accuracy"] = 0.85
        
        assert evolution.usage_patterns["retrieval_frequency"] == 0.5
        assert evolution.usage_patterns["predictive_accuracy"] == 0.85
    
    def test_knowledge_evolution_relationships(self):
        """Test relationship network tracking."""
        evolution = KnowledgeEvolution(
            creation_event={
                "timestamp": datetime.now(timezone.utc),
                "initial_confidence": 0.7,
                "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
            }
        )
        
        evolution.relationship_network["supporting_knowledge"] = ["k1", "k2"]
        evolution.relationship_network["contradictory_knowledge"] = ["k3"]
        evolution.relationship_network["dependent_knowledge"] = ["k4"]
        
        assert len(evolution.relationship_network["supporting_knowledge"]) == 2
        assert "k3" in evolution.relationship_network["contradictory_knowledge"]

