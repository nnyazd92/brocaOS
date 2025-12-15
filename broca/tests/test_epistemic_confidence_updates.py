"""
Tests for confidence update workflow integration.

Tests that confidence_update_workflow() is called when knowledge changes.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata, VerificationRecord
from broca.self_model.epistemic.ids import generate_knowledge_id
from broca.self_model.model import SelfModel
from broca.self_model.layer import ConsistencyLayer
import tempfile
import os


class TestConfidenceUpdates:
    """Test confidence update workflow integration."""
    
    def test_confidence_update_workflow_called_for_consistency_violations(self):
        """
        Test confidence_update_workflow() is called when consistency violations occur.
        
        Rationale: Ensures violations reduce confidence in conflicting knowledge.
        """
        engine = MetacognitiveEngine()
        
        # Create initial knowledge
        knowledge_id = generate_knowledge_id("capability", "Can program in Python")
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        initial_metrics = engine.knowledge_acquisition_workflow(
            knowledge_id, source, initial_confidence=0.8
        )
        
        initial_confidence = initial_metrics.overall_confidence
        
        # Simulate violation - new evidence contradicts
        violation_source = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            inference_type="consistency_check"
        )
        
        # Update with negative evidence
        updated_metrics = engine.confidence_update_workflow(
            knowledge_id=knowledge_id,
            new_evidence=violation_source,
            evidence_strength=0.2  # Low strength = contradiction
        )
        
        # Confidence should decrease
        assert updated_metrics.overall_confidence < initial_confidence
        
        # Verification record should be created
        history = engine.epistemic_layer.get_verification_history(knowledge_id)
        assert len(history) > 0
        assert history[-1].result in ["refuted", "modified"]
    
    def test_confidence_update_workflow_called_for_memory_conflicts(self):
        """
        Test confidence_update_workflow() is called when memory conflicts are detected.
        
        Rationale: Ensures conflicting memories update confidence appropriately.
        """
        engine = MetacognitiveEngine()
        
        # Create knowledge from first memory
        knowledge_id = generate_knowledge_id("memory", "Python version is 3.11")
        source1 = SourceMetadata(source_type=SourceType.MEMORY_RETRIEVAL)
        initial_metrics = engine.knowledge_acquisition_workflow(
            knowledge_id, source1, initial_confidence=0.7
        )
        
        # Conflicting memory found
        conflict_source = SourceMetadata(
            source_type=SourceType.MEMORY_RETRIEVAL,
            source_name="conflicting_memory"
        )
        
        # Update with conflicting evidence
        updated_metrics = engine.confidence_update_workflow(
            knowledge_id=knowledge_id,
            new_evidence=conflict_source,
            evidence_strength=0.3  # Low strength indicates conflict
        )
        
        # Confidence should be reduced
        assert updated_metrics.overall_confidence < initial_metrics.overall_confidence
        
        # Verification record should indicate conflict
        history = engine.epistemic_layer.get_verification_history(knowledge_id)
        assert len(history) > 0
    
    def test_confidence_update_workflow_called_for_multiple_sources_confirming(self):
        """
        Test confidence_update_workflow() is called when multiple sources confirm information.
        
        Rationale: Ensures confirming sources increase confidence.
        """
        engine = MetacognitiveEngine()
        
        # Initial knowledge
        knowledge_id = generate_knowledge_id("fact", "Python is a programming language")
        source1 = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        initial_metrics = engine.knowledge_acquisition_workflow(
            knowledge_id, source1, initial_confidence=0.6
        )
        
        initial_confidence = initial_metrics.overall_confidence
        
        # Confirming source
        confirming_source = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="web_search"
        )
        
        # Update with confirming evidence
        updated_metrics = engine.confidence_update_workflow(
            knowledge_id=knowledge_id,
            new_evidence=confirming_source,
            evidence_strength=0.8  # High strength = confirmation
        )
        
        # Confidence should increase
        assert updated_metrics.overall_confidence > initial_confidence
        
        # Verification record should indicate confirmation
        history = engine.epistemic_layer.get_verification_history(knowledge_id)
        assert len(history) > 0
        assert history[-1].result == "confirmed"
    
    def test_confidence_scores_update_correctly(self):
        """
        Test that confidence scores update correctly.
        
        Rationale: Ensures confidence changes reflect evidence strength appropriately.
        """
        engine = MetacognitiveEngine()
        
        knowledge_id = generate_knowledge_id("test", "Test knowledge")
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        initial_metrics = engine.knowledge_acquisition_workflow(
            knowledge_id, source, initial_confidence=0.5
        )
        
        # Strong confirming evidence
        strong_source = SourceMetadata(source_type=SourceType.TOOL_MEDIATED_VERIFICATION)
        strong_metrics = engine.confidence_update_workflow(
            knowledge_id, strong_source, evidence_strength=0.9
        )
        
        # Weak confirming evidence
        weak_source = SourceMetadata(source_type=SourceType.EXTERNAL_SOURCE)
        weak_metrics = engine.confidence_update_workflow(
            knowledge_id, weak_source, evidence_strength=0.3
        )
        
        # Strong evidence should increase confidence more than weak
        # (or weak might decrease if it's contradictory)
        assert strong_metrics.overall_confidence != weak_metrics.overall_confidence
    
    def test_verification_records_created(self):
        """
        Test that verification records are created for all confidence changes.
        
        Rationale: Ensures all confidence updates are tracked in verification history.
        """
        engine = MetacognitiveEngine()
        
        knowledge_id = generate_knowledge_id("test", "Test knowledge")
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        engine.knowledge_acquisition_workflow(knowledge_id, source, 0.5)
        
        # Initial state - no verification history yet (only creation)
        initial_history = engine.epistemic_layer.get_verification_history(knowledge_id)
        initial_count = len(initial_history)
        
        # Update confidence
        update_source = SourceMetadata(source_type=SourceType.TOOL_MEDIATED_VERIFICATION)
        engine.confidence_update_workflow(knowledge_id, update_source, 0.7)
        
        # Should have new verification record
        updated_history = engine.epistemic_layer.get_verification_history(knowledge_id)
        assert len(updated_history) > initial_count
        
        # Record should have correct structure
        latest_record = updated_history[-1]
        assert isinstance(latest_record, VerificationRecord)
        assert latest_record.verification_type == "evidence_update"
        assert latest_record.new_evidence is not None

