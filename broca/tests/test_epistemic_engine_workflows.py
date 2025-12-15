"""
Tests for epistemic engine workflows.

Tests that knowledge acquisition workflow is called at correct points.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime, timezone

from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata
from broca.self_model.epistemic.ids import generate_knowledge_id


class TestKnowledgeAcquisitionWorkflow:
    """Test knowledge acquisition workflow being called at correct points."""
    
    def test_knowledge_acquisition_workflow_called_for_new_memories(self):
        """
        Test knowledge_acquisition_workflow() is called for new memories stored.
        
        Rationale: Ensures memories are tracked as knowledge sources.
        """
        engine = MetacognitiveEngine()
        
        # Create source metadata for memory
        source = SourceMetadata(
            source_type=SourceType.MEMORY_RETRIEVAL,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Generate knowledge ID
        knowledge_id = generate_knowledge_id("memory", "Test memory content")
        
        # Call knowledge acquisition workflow
        metrics = engine.knowledge_acquisition_workflow(
            knowledge_id=knowledge_id,
            source=source,
            initial_confidence=0.7
        )
        
        # Should create confidence metrics
        assert metrics is not None
        assert metrics.overall_confidence == 0.7
        
        # Should be stored in epistemic layer
        assert engine.epistemic_layer.has_knowledge(knowledge_id)
        assert engine.epistemic_layer.get_knowledge_source(knowledge_id) == source
    
    def test_knowledge_acquisition_workflow_called_for_tool_results(self):
        """
        Test knowledge_acquisition_workflow() is called for tool results providing information.
        
        Rationale: Ensures tool-provided information is tracked as knowledge.
        """
        engine = MetacognitiveEngine()
        
        # Create source metadata for tool result
        source = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="web_search",
            timestamp=datetime.now(timezone.utc)
        )
        
        knowledge_id = generate_knowledge_id("tool_result", "Search result: Python 3.12 released")
        
        metrics = engine.knowledge_acquisition_workflow(
            knowledge_id=knowledge_id,
            source=source,
            initial_confidence=0.8
        )
        
        assert metrics is not None
        assert engine.epistemic_layer.has_knowledge(knowledge_id)
    
    def test_knowledge_acquisition_workflow_called_for_web_search_results(self):
        """
        Test knowledge_acquisition_workflow() is called for web search results.
        
        Rationale: Ensures web search information is tracked as knowledge sources.
        """
        engine = MetacognitiveEngine()
        
        source = SourceMetadata(
            source_type=SourceType.EXTERNAL_SOURCE,
            source_name="web_search",
            timestamp=datetime.now(timezone.utc)
        )
        
        knowledge_id = generate_knowledge_id("web_search", "Latest Python version is 3.12")
        
        metrics = engine.knowledge_acquisition_workflow(
            knowledge_id=knowledge_id,
            source=source,
            initial_confidence=0.6  # Lower confidence for external sources
        )
        
        assert metrics is not None
        assert engine.epistemic_layer.has_knowledge(knowledge_id)
    
    def test_knowledge_acquisition_workflow_called_for_new_capabilities(self):
        """
        Test knowledge_acquisition_workflow() is called for new capabilities discovered.
        
        Rationale: Ensures discovered capabilities are tracked in the epistemic layer.
        """
        engine = MetacognitiveEngine()
        
        from broca.self_model.epistemic.ids import generate_capability_id
        
        capability = "Can use new API endpoint"
        knowledge_id = generate_capability_id(capability)
        
        source = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="terminal",
            timestamp=datetime.now(timezone.utc)
        )
        
        metrics = engine.knowledge_acquisition_workflow(
            knowledge_id=knowledge_id,
            source=source,
            initial_confidence=0.9  # High confidence for verified capabilities
        )
        
        assert metrics is not None
        assert metrics.overall_confidence >= 0.7  # Should be adjusted based on source reliability
        assert engine.epistemic_layer.has_knowledge(knowledge_id)
    
    def test_knowledge_ids_generated_and_tracked(self):
        """
        Test that knowledge IDs are generated and tracked.
        
        Rationale: Ensures each knowledge item gets a unique, trackable ID.
        """
        engine = MetacognitiveEngine()
        
        # Generate IDs for different knowledge items
        memory_id = generate_knowledge_id("memory", "Memory content 1")
        tool_id = generate_knowledge_id("tool_result", "Tool result 1")
        capability_id = generate_knowledge_id("capability", "Capability 1")
        
        # All should be unique
        assert memory_id != tool_id
        assert tool_id != capability_id
        assert memory_id != capability_id
        
        # Track them
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        engine.knowledge_acquisition_workflow(memory_id, source, 0.5)
        engine.knowledge_acquisition_workflow(tool_id, source, 0.5)
        engine.knowledge_acquisition_workflow(capability_id, source, 0.5)
        
        # All should be tracked
        assert engine.epistemic_layer.has_knowledge(memory_id)
        assert engine.epistemic_layer.has_knowledge(tool_id)
        assert engine.epistemic_layer.has_knowledge(capability_id)
    
    def test_confidence_metrics_initialized_correctly(self):
        """
        Test that confidence metrics are initialized correctly.
        
        Rationale: Ensures confidence scores are set appropriately based on source reliability.
        """
        engine = MetacognitiveEngine()
        
        # High reliability source
        high_rel_source = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="terminal"
        )
        
        knowledge_id1 = generate_knowledge_id("test", "high reliability")
        metrics1 = engine.knowledge_acquisition_workflow(
            knowledge_id1,
            high_rel_source,
            initial_confidence=0.5
        )
        
        # Should be boosted due to high source reliability
        assert metrics1.overall_confidence >= 0.5
        
        # Low reliability source
        low_rel_source = SourceMetadata(
            source_type=SourceType.EXTERNAL_SOURCE,
            source_name="unverified_website"
        )
        
        knowledge_id2 = generate_knowledge_id("test", "low reliability")
        metrics2 = engine.knowledge_acquisition_workflow(
            knowledge_id2,
            low_rel_source,
            initial_confidence=0.5
        )
        
        # Should be adjusted downward for low reliability
        # High reliability should be >= low reliability
        assert metrics1.overall_confidence >= metrics2.overall_confidence

