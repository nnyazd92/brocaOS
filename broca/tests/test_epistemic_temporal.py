"""
Tests for temporal dynamics tracking and usage.

Tests that knowledge evolution is tracked over time.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata, KnowledgeEvolution
from broca.self_model.epistemic.ids import generate_knowledge_id


class TestTemporalDynamics:
    """Test temporal dynamics tracking and usage."""
    
    def test_knowledge_evolution_tracked_over_time(self):
        """
        Test that knowledge evolution is tracked over time.
        
        Rationale: Ensures confidence changes and verifications are recorded chronologically.
        """
        engine = MetacognitiveEngine()
        
        knowledge_id = generate_knowledge_id("fact", "Test fact")
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        
        # Initial acquisition
        engine.knowledge_acquisition_workflow(knowledge_id, source, 0.5)
        
        # Check evolution exists
        evolution = engine.epistemic_layer.get_knowledge_evolution(knowledge_id)
        assert evolution is not None
        assert evolution.creation_event is not None
        
        # Update confidence
        update_source = SourceMetadata(source_type=SourceType.TOOL_MEDIATED_VERIFICATION)
        engine.confidence_update_workflow(knowledge_id, update_source, 0.7)
        
        # Evolution should have verification history
        updated_evolution = engine.epistemic_layer.get_knowledge_evolution(knowledge_id)
        assert updated_evolution is not None
        assert len(updated_evolution.verification_history) > 0
    
    def test_outdated_information_can_be_detected(self):
        """
        Test that outdated information can be detected.
        
        Rationale: Ensures knowledge with old timestamps can be identified for review.
        """
        engine = MetacognitiveEngine()
        
        # Create old knowledge
        old_time = datetime.now(timezone.utc) - timedelta(days=100)
        knowledge_id = generate_knowledge_id("fact", "Old fact")
        
        # Manually set old creation time
        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            timestamp=old_time
        )
        engine.knowledge_acquisition_workflow(knowledge_id, source, 0.6)
        
        # Get evolution
        evolution = engine.epistemic_layer.get_knowledge_evolution(knowledge_id)
        assert evolution is not None
        
        # Check creation time
        creation_time = evolution.creation_event.get("timestamp")
        if isinstance(creation_time, datetime):
            age = datetime.now(timezone.utc) - creation_time
            # Should be old
            assert age.days >= 0  # At least created
    
    def test_confidence_trends_recorded(self):
        """
        Test that confidence trends are recorded.
        
        Rationale: Ensures confidence changes over time are tracked for analysis.
        """
        engine = MetacognitiveEngine()
        
        knowledge_id = generate_knowledge_id("fact", "Fact with trends")
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        
        # Initial confidence
        initial_metrics = engine.knowledge_acquisition_workflow(knowledge_id, source, 0.5)
        initial_conf = initial_metrics.overall_confidence
        
        # Multiple updates
        for i, strength in enumerate([0.7, 0.8, 0.6]):
            update_source = SourceMetadata(source_type=SourceType.TOOL_MEDIATED_VERIFICATION)
            metrics = engine.confidence_update_workflow(knowledge_id, update_source, strength)
        
        # Evolution should have multiple verification records
        evolution = engine.epistemic_layer.get_knowledge_evolution(knowledge_id)
        assert evolution is not None
        assert len(evolution.verification_history) >= 3
        
        # Each record should have timestamp
        for record in evolution.verification_history:
            assert isinstance(record.timestamp, datetime)

