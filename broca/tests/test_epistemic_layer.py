"""
Tests for EpistemicLayer class.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.epistemic.models import (
    SourceType,
    SourceMetadata,
    ConfidenceMetrics,
    InferenceNode,
    KnowledgeEvolution,
    VerificationRecord,
)
from broca.self_model.epistemic.ids import generate_knowledge_id


class TestEpistemicLayer:
    """Test EpistemicLayer class."""
    
    def test_epistemic_layer_creation(self):
        """Test creating an empty epistemic layer."""
        layer = EpistemicLayer()
        
        assert layer.knowledge_sources == {}
        assert layer.confidence_calibration == {}
        assert layer.verification_history == {}
        assert layer.inference_chains == {}
        assert layer.temporal_dynamics == {}
    
    def test_add_knowledge_source(self):
        """Test adding a knowledge source."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            user_identity="developer"
        )
        
        layer.add_knowledge_source(knowledge_id, source)
        
        assert knowledge_id in layer.knowledge_sources
        assert layer.knowledge_sources[knowledge_id] == source
    
    def test_add_confidence_metrics(self):
        """Test adding confidence metrics."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        metrics = ConfidenceMetrics(overall_confidence=0.8)
        
        layer.add_confidence_metrics(knowledge_id, metrics)
        
        assert knowledge_id in layer.confidence_calibration
        assert layer.confidence_calibration[knowledge_id].overall_confidence == 0.8
    
    def test_add_verification_record(self):
        """Test adding a verification record."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        record = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="tool_test",
            result="confirmed"
        )
        
        layer.add_verification_record(knowledge_id, record)
        
        assert knowledge_id in layer.verification_history
        assert len(layer.verification_history[knowledge_id]) == 1
        assert layer.verification_history[knowledge_id][0] == record
    
    def test_add_inference_node(self):
        """Test adding an inference node."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        node = InferenceNode(
            knowledge_id=knowledge_id,
            node_type="inference",
            confidence=0.8,
            source=SourceMetadata(source_type=SourceType.LOGICAL_INFERENCE)
        )
        
        layer.add_inference_node(node)
        
        assert knowledge_id in layer.inference_chains
        assert layer.inference_chains[knowledge_id] == node
    
    def test_add_knowledge_evolution(self):
        """Test adding knowledge evolution tracking."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        evolution = KnowledgeEvolution(
            creation_event={
                "timestamp": datetime.now(timezone.utc),
                "initial_confidence": 0.7,
                "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
            }
        )
        
        layer.add_knowledge_evolution(knowledge_id, evolution)
        
        assert knowledge_id in layer.temporal_dynamics
        assert layer.temporal_dynamics[knowledge_id] == evolution
    
    def test_get_knowledge_source(self):
        """Test retrieving a knowledge source."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            user_identity="developer"
        )
        
        layer.add_knowledge_source(knowledge_id, source)
        
        retrieved = layer.get_knowledge_source(knowledge_id)
        assert retrieved == source
        
        # Test non-existent
        assert layer.get_knowledge_source("nonexistent") is None
    
    def test_get_confidence_metrics(self):
        """Test retrieving confidence metrics."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        metrics = ConfidenceMetrics(overall_confidence=0.8)
        layer.add_confidence_metrics(knowledge_id, metrics)
        
        retrieved = layer.get_confidence_metrics(knowledge_id)
        assert retrieved == metrics
        
        # Test non-existent
        assert layer.get_confidence_metrics("nonexistent") is None
    
    def test_get_verification_history(self):
        """Test retrieving verification history."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        record1 = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="tool_test",
            result="confirmed"
        )
        record2 = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="memory_retrieval",
            result="confirmed"
        )
        
        layer.add_verification_record(knowledge_id, record1)
        layer.add_verification_record(knowledge_id, record2)
        
        history = layer.get_verification_history(knowledge_id)
        assert len(history) == 2
        assert record1 in history
        assert record2 in history
        
        # Test non-existent
        assert layer.get_verification_history("nonexistent") == []
    
    def test_get_inference_node(self):
        """Test retrieving an inference node."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        node = InferenceNode(
            knowledge_id=knowledge_id,
            node_type="inference",
            confidence=0.8,
            source=SourceMetadata(source_type=SourceType.LOGICAL_INFERENCE)
        )
        
        layer.add_inference_node(node)
        
        retrieved = layer.get_inference_node(knowledge_id)
        assert retrieved == node
        
        # Test non-existent
        assert layer.get_inference_node("nonexistent") is None
    
    def test_get_knowledge_evolution(self):
        """Test retrieving knowledge evolution."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        evolution = KnowledgeEvolution(
            creation_event={
                "timestamp": datetime.now(timezone.utc),
                "initial_confidence": 0.7,
                "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
            }
        )
        
        layer.add_knowledge_evolution(knowledge_id, evolution)
        
        retrieved = layer.get_knowledge_evolution(knowledge_id)
        assert retrieved == evolution
        
        # Test non-existent
        assert layer.get_knowledge_evolution("nonexistent") is None
    
    def test_has_knowledge(self):
        """Test checking if knowledge exists."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        assert not layer.has_knowledge(knowledge_id)
        
        layer.add_knowledge_source(knowledge_id, SourceMetadata(source_type=SourceType.USER_PROVIDED))
        
        assert layer.has_knowledge(knowledge_id)
    
    def test_to_dict(self):
        """Test converting epistemic layer to dictionary."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        layer.add_knowledge_source(knowledge_id, source)
        
        metrics = ConfidenceMetrics(overall_confidence=0.8)
        layer.add_confidence_metrics(knowledge_id, metrics)
        
        data = layer.to_dict()
        
        assert isinstance(data, dict)
        assert "knowledge_sources" in data
        assert "confidence_calibration" in data
    
    def test_from_dict(self):
        """Test creating epistemic layer from dictionary."""
        layer = EpistemicLayer()
        knowledge_id = "test_knowledge_1"
        
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        layer.add_knowledge_source(knowledge_id, source)
        
        metrics = ConfidenceMetrics(overall_confidence=0.8)
        layer.add_confidence_metrics(knowledge_id, metrics)
        
        data = layer.to_dict()
        new_layer = EpistemicLayer.from_dict(data)
        
        assert new_layer.has_knowledge(knowledge_id)
        assert new_layer.get_confidence_metrics(knowledge_id).overall_confidence == 0.8

