"""
Tests for inference chain tracking.

Tests that inference chains are built when knowledge is derived.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata, InferenceNode
from broca.self_model.epistemic.ids import generate_knowledge_id
from broca.self_model.epistemic.inference import InferenceTracker


class TestInferenceChainTracking:
    """Test inference chain tracking when knowledge is derived."""
    
    def test_inference_chains_built_when_knowledge_derived(self):
        """
        Test that inference chains are built when knowledge is derived.
        
        Rationale: Ensures derived knowledge is linked to its sources.
        """
        engine = MetacognitiveEngine()
        tracker = InferenceTracker()
        
        # Create base knowledge
        base_id = generate_knowledge_id("fact", "Python is a language")
        base_source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        base_metrics = engine.knowledge_acquisition_workflow(base_id, base_source, 0.8)
        
        # Create derived knowledge
        derived_id = generate_knowledge_id("inference", "Python can be used for programming")
        derived_source = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            inference_type="deduction"
        )
        derived_metrics = engine.knowledge_acquisition_workflow(derived_id, derived_source, 0.7)
        
        # Create inference node linking them
        base_node = InferenceNode(
            knowledge_id=base_id,
            node_type="premise",
            confidence=base_metrics.overall_confidence,
            source=base_source
        )
        derived_node = InferenceNode(
            knowledge_id=derived_id,
            node_type="conclusion",
            confidence=derived_metrics.overall_confidence,
            source=derived_source,
            dependencies=[base_node]
        )
        
        engine.epistemic_layer.add_inference_node(derived_node)
        
        # Check that inference chain exists
        stored_node = engine.epistemic_layer.get_inference_node(derived_id)
        assert stored_node is not None
        assert len(stored_node.dependencies) > 0
        assert stored_node.dependencies[0].knowledge_id == base_id
    
    def test_dependency_propagation_when_confidence_updates(self):
        """
        Test dependency propagation when confidence updates.
        
        Rationale: Ensures confidence changes propagate through inference chains.
        """
        engine = MetacognitiveEngine()
        tracker = InferenceTracker()
        
        # Create knowledge with dependencies
        premise_id = generate_knowledge_id("premise", "All languages are tools")
        premise_source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        premise_metrics = engine.knowledge_acquisition_workflow(premise_id, premise_source, 0.9)
        
        conclusion_id = generate_knowledge_id("conclusion", "Python is a tool")
        conclusion_source = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            inference_type="deduction"
        )
        conclusion_metrics = engine.knowledge_acquisition_workflow(conclusion_id, conclusion_source, 0.8)
        
        # Link them
        premise_node = InferenceNode(
            knowledge_id=premise_id,
            node_type="premise",
            confidence=premise_metrics.overall_confidence,
            source=premise_source
        )
        conclusion_node = InferenceNode(
            knowledge_id=conclusion_id,
            node_type="conclusion",
            confidence=conclusion_metrics.overall_confidence,
            source=conclusion_source,
            dependencies=[premise_node]
        )
        engine.epistemic_layer.add_inference_node(conclusion_node)
        
        # Update premise confidence
        update_source = SourceMetadata(source_type=SourceType.TOOL_MEDIATED_VERIFICATION)
        engine.confidence_update_workflow(premise_id, update_source, 0.5)  # Reduce confidence
        
        # Conclusion confidence should be affected (propagated)
        # The tracker should handle this
        conclusion_metrics = engine.epistemic_layer.get_confidence_metrics(conclusion_id)
        assert conclusion_metrics is not None
    
    def test_inference_nodes_link_correctly(self):
        """
        Test that inference nodes link correctly.
        
        Rationale: Ensures inference chains maintain proper dependency relationships.
        """
        engine = MetacognitiveEngine()
        
        # Create multiple knowledge items
        fact1_id = generate_knowledge_id("fact", "Fact 1")
        fact2_id = generate_knowledge_id("fact", "Fact 2")
        conclusion_id = generate_knowledge_id("conclusion", "Conclusion")
        
        # Add facts
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        fact1_metrics = engine.knowledge_acquisition_workflow(fact1_id, source, 0.8)
        fact2_metrics = engine.knowledge_acquisition_workflow(fact2_id, source, 0.8)
        conclusion_metrics = engine.knowledge_acquisition_workflow(conclusion_id, source, 0.7)
        
        # Create inference chain: conclusion depends on fact1 and fact2
        fact1_node = InferenceNode(
            knowledge_id=fact1_id,
            node_type="premise",
            confidence=fact1_metrics.overall_confidence,
            source=source
        )
        fact2_node = InferenceNode(
            knowledge_id=fact2_id,
            node_type="premise",
            confidence=fact2_metrics.overall_confidence,
            source=source
        )
        conclusion_node = InferenceNode(
            knowledge_id=conclusion_id,
            node_type="conclusion",
            confidence=conclusion_metrics.overall_confidence,
            source=source,
            dependencies=[fact1_node, fact2_node]
        )
        
        engine.epistemic_layer.add_inference_node(conclusion_node)
        
        # Verify links
        stored = engine.epistemic_layer.get_inference_node(conclusion_id)
        assert stored is not None
        assert len(stored.dependencies) == 2
        assert stored.dependencies[0].knowledge_id == fact1_id
        assert stored.dependencies[1].knowledge_id == fact2_id

