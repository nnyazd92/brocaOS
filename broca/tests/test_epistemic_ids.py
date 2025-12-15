"""
Tests for knowledge ID generation.
"""

from __future__ import annotations

import pytest

from broca.self_model.epistemic.ids import (
    generate_knowledge_id,
    generate_capability_id,
    generate_constraint_id,
    generate_knowledge_boundary_id,
    generate_preference_id,
    generate_behavioral_pattern_id,
    KnowledgeID,
)


class TestKnowledgeIDGeneration:
    """Test knowledge ID generation."""
    
    def test_generate_knowledge_id_basic(self):
        """Test basic knowledge ID generation."""
        kid = generate_knowledge_id("capability", "Python programming")
        
        assert isinstance(kid, str)
        assert kid.startswith("capability_")
        assert len(kid) > len("capability_")
    
    def test_generate_knowledge_id_deterministic(self):
        """Test that same inputs produce same ID."""
        kid1 = generate_knowledge_id("capability", "Python programming")
        kid2 = generate_knowledge_id("capability", "Python programming")
        
        assert kid1 == kid2
    
    def test_generate_knowledge_id_different_content(self):
        """Test that different content produces different IDs."""
        kid1 = generate_knowledge_id("capability", "Python programming")
        kid2 = generate_knowledge_id("capability", "JavaScript programming")
        
        assert kid1 != kid2
    
    def test_generate_knowledge_id_different_category(self):
        """Test that different categories produce different IDs."""
        kid1 = generate_knowledge_id("capability", "Python programming")
        kid2 = generate_knowledge_id("constraint", "Python programming")
        
        assert kid1 != kid2
    
    def test_generate_knowledge_id_with_context(self):
        """Test knowledge ID generation with context."""
        kid1 = generate_knowledge_id("capability", "Python programming", {"version": "3.9"})
        kid2 = generate_knowledge_id("capability", "Python programming", {"version": "3.10"})
        
        assert kid1 != kid2
    
    def test_generate_capability_id(self):
        """Test capability ID generation."""
        kid = generate_capability_id("Python programming")
        
        assert kid.startswith("capability_")
    
    def test_generate_constraint_id(self):
        """Test constraint ID generation."""
        kid = generate_constraint_id("cannot_execute_arbitrary_code", "limited to whitelisted commands")
        
        assert kid.startswith("constraint_")
    
    def test_generate_knowledge_boundary_id(self):
        """Test knowledge boundary ID generation."""
        kid = generate_knowledge_boundary_id("training_cutoff", "unknown")
        
        assert kid.startswith("knowledge_boundary_")
    
    def test_generate_preference_id(self):
        """Test preference ID generation."""
        kid = generate_preference_id("response_style", "helpful and informative")
        
        assert kid.startswith("preference_")
    
    def test_generate_behavioral_pattern_id(self):
        """Test behavioral pattern ID generation."""
        pattern = {"pattern": "Frequently uses terminal tool", "evidence": "Used 15 times"}
        kid = generate_behavioral_pattern_id(pattern)
        
        assert kid.startswith("behavioral_pattern_")
    
    def test_generate_behavioral_pattern_id_deterministic(self):
        """Test that same pattern produces same ID."""
        pattern = {"pattern": "Frequently uses terminal tool", "evidence": "Used 15 times"}
        kid1 = generate_behavioral_pattern_id(pattern)
        kid2 = generate_behavioral_pattern_id(pattern)
        
        assert kid1 == kid2


class TestSystematicKnowledgeIDGeneration:
    """Test systematic knowledge ID generation for all self-model components."""
    
    def test_generate_ids_for_all_capabilities(self):
        """
        Test that IDs can be generated for all capabilities in a self-model.
        
        Rationale: Ensures all capabilities can be tracked with unique IDs.
        """
        capabilities = [
            "General conversation and assistance",
            "Tool usage (memory, web search, terminal, critic)",
            "Code execution and analysis"
        ]
        
        ids = [generate_capability_id(cap) for cap in capabilities]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
        # All should start with "capability_"
        assert all(kid.startswith("capability_") for kid in ids)
    
    def test_generate_ids_for_all_preferences(self):
        """
        Test that IDs can be generated for all preferences in a self-model.
        
        Rationale: Ensures all preferences can be tracked with unique IDs.
        """
        preferences = {
            "response_style": "helpful and informative",
            "uncertainty_handling": "acknowledge when uncertain"
        }
        
        ids = [generate_preference_id(key, value) for key, value in preferences.items()]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
        # All should start with "preference_"
        assert all(kid.startswith("preference_") for kid in ids)
    
    def test_generate_ids_for_all_constraints(self):
        """
        Test that IDs can be generated for all constraints in a self-model.
        
        Rationale: Ensures all constraints can be tracked with unique IDs.
        """
        constraints = {
            "cannot_execute_arbitrary_code": "limited to whitelisted terminal commands",
            "cannot_access_internet_directly": "requires web search tool"
        }
        
        ids = [generate_constraint_id(key, value) for key, value in constraints.items()]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
        # All should start with "constraint_"
        assert all(kid.startswith("constraint_") for kid in ids)
    
    def test_generate_ids_for_all_knowledge_boundaries(self):
        """
        Test that IDs can be generated for all knowledge boundaries in a self-model.
        
        Rationale: Ensures all knowledge boundaries can be tracked with unique IDs.
        """
        boundaries = {
            "training_cutoff": "unknown",
            "real_time_info": "requires web search or tools"
        }
        
        ids = [generate_knowledge_boundary_id(key, value) for key, value in boundaries.items()]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
        # All should start with "knowledge_boundary_"
        assert all(kid.startswith("knowledge_boundary_") for kid in ids)
    
    def test_generate_ids_for_behavioral_patterns(self):
        """
        Test that IDs can be generated for behavioral patterns in a self-model.
        
        Rationale: Ensures all behavioral patterns can be tracked with unique IDs.
        """
        patterns = [
            {"pattern": "Frequently uses terminal tool", "evidence": "Used 15 times"},
            {"pattern": "Prefers detailed explanations", "evidence": "Observed in responses"}
        ]
        
        ids = [generate_behavioral_pattern_id(pattern) for pattern in patterns]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
        # All should start with "behavioral_pattern_"
        assert all(kid.startswith("behavioral_pattern_") for kid in ids)
    
    def test_ids_are_deterministic_and_consistent(self):
        """
        Test that IDs are deterministic and consistent across calls.
        
        Rationale: Ensures the same knowledge item always gets the same ID.
        """
        capability = "Python programming"
        preference_key = "response_style"
        preference_value = "helpful"
        constraint_key = "cannot_execute_arbitrary_code"
        constraint_value = "limited to whitelisted commands"
        
        # Generate IDs multiple times
        cap_id1 = generate_capability_id(capability)
        cap_id2 = generate_capability_id(capability)
        
        pref_id1 = generate_preference_id(preference_key, preference_value)
        pref_id2 = generate_preference_id(preference_key, preference_value)
        
        constraint_id1 = generate_constraint_id(constraint_key, constraint_value)
        constraint_id2 = generate_constraint_id(constraint_key, constraint_value)
        
        # All should be consistent
        assert cap_id1 == cap_id2
        assert pref_id1 == pref_id2
        assert constraint_id1 == constraint_id2

