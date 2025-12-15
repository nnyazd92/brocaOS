"""
Tests for verification prioritization workflow.

Tests that verification_prioritization_workflow() identifies knowledge needing verification.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata
from broca.self_model.epistemic.ids import generate_knowledge_id


class TestVerificationPrioritization:
    """Test verification prioritization workflow."""
    
    def test_verification_prioritization_identifies_low_confidence_knowledge(self):
        """
        Test that verification_prioritization_workflow() identifies low-confidence knowledge.
        
        Rationale: Ensures knowledge with low confidence is flagged for verification.
        """
        engine = MetacognitiveEngine()
        
        # Create knowledge items with varying confidence
        high_conf_id = generate_knowledge_id("fact", "High confidence fact")
        source1 = SourceMetadata(source_type=SourceType.TOOL_MEDIATED_VERIFICATION)
        engine.knowledge_acquisition_workflow(high_conf_id, source1, 0.9)
        
        low_conf_id = generate_knowledge_id("fact", "Low confidence fact")
        source2 = SourceMetadata(source_type=SourceType.EXTERNAL_SOURCE)
        engine.knowledge_acquisition_workflow(low_conf_id, source2, 0.3)
        
        # Prepare knowledge items dict
        knowledge_items = {
            high_conf_id: {
                "confidence": 0.9,
                "type": "fact"
            },
            low_conf_id: {
                "confidence": 0.3,
                "type": "fact"
            }
        }
        
        # Get prioritized items
        prioritized = engine.verification_prioritization_workflow(knowledge_items)
        
        # Low confidence item should be prioritized
        assert len(prioritized) > 0
        assert low_conf_id in prioritized
    
    def test_verification_prioritization_can_be_triggered_periodically(self):
        """
        Test that prioritization can be triggered periodically.
        
        Rationale: Ensures the workflow can be called on a schedule to maintain knowledge quality.
        """
        engine = MetacognitiveEngine()
        
        # Create multiple knowledge items
        items = {}
        for i in range(5):
            kid = generate_knowledge_id("fact", f"Fact {i}")
            source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
            metrics = engine.knowledge_acquisition_workflow(kid, source, 0.4 + i * 0.1)
            items[kid] = {
                "confidence": metrics.overall_confidence,
                "type": "fact"
            }
        
        # Call prioritization
        prioritized = engine.verification_prioritization_workflow(items)
        
        # Should return list of IDs
        assert isinstance(prioritized, list)
        assert all(isinstance(kid, str) for kid in prioritized)
    
    def test_suggested_verifications_are_actionable(self):
        """
        Test that suggested verifications are actionable.
        
        Rationale: Ensures prioritized items can actually be verified.
        """
        engine = MetacognitiveEngine()
        
        # Create knowledge needing verification
        knowledge_id = generate_knowledge_id("fact", "Unverified fact")
        source = SourceMetadata(source_type=SourceType.EXTERNAL_SOURCE)
        metrics = engine.knowledge_acquisition_workflow(knowledge_id, source, 0.4)
        
        knowledge_items = {
            knowledge_id: {
                "confidence": metrics.overall_confidence,
                "type": "fact",
                "source": "external"
            }
        }
        
        prioritized = engine.verification_prioritization_workflow(knowledge_items)
        
        # Should include the low-confidence item
        assert knowledge_id in prioritized
        
        # The item should exist in epistemic layer for verification
        assert engine.epistemic_layer.has_knowledge(knowledge_id)

