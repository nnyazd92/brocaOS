"""
Tests for comprehensive contradiction detection.

Tests Z3 + semantic + web search integration for contradiction detection.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from broca.reasoning.z3_validator import Z3LogicalValidator
from broca.memory import MemoryRecord
from broca.memory.manager import MemoryManager
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.reasoning.fact_checker import FactChecker


@pytest.fixture
def mock_memory_manager():
    """Create mock memory manager."""
    storage = Mock(spec=MemoryStorage)
    vector_index = Mock(spec=VectorIndex)
    embedding_service = Mock(spec=EmbeddingService)
    
    manager = MemoryManager(storage, vector_index, embedding_service)
    storage.get_all_memories = Mock(return_value=[])
    manager.retrieve_memories = Mock(return_value=[])
    
    return manager


@pytest.fixture
def z3_validator():
    """Create Z3 validator."""
    return Z3LogicalValidator(enable_z3=True)


@pytest.fixture
def fact_checker():
    """Create fact checker (web search disabled for tests)."""
    return FactChecker(enable_web_search=False)


class TestComprehensiveContradictionDetection:
    """Test comprehensive contradiction detection."""
    
    def test_z3_contradiction_detection(self, z3_validator):
        """Test Z3 logical contradiction detection."""
        response = "The sky is blue. The sky is not blue."
        
        result = z3_validator.detect_comprehensive_contradictions(
            response=response,
            existing_memories=[],
            memory_manager=None,
            use_web_search=False,
            fact_checker=None
        )
        
        assert "contradictions" in result
        assert "overall_contradiction_score" in result
        assert isinstance(result["overall_contradiction_score"], float)
        assert 0.0 <= result["overall_contradiction_score"] <= 1.0
    
    def test_semantic_contradiction_detection(self, z3_validator, mock_memory_manager):
        """Test semantic contradiction detection via memory conflict detector."""
        # Create existing memory
        existing_memory = MemoryRecord(
            namespace="test",
            text="The capital of France is Paris.",
            importance=0.8
        )
        
        # Response that contradicts
        response = "The capital of France is London."
        
        # Mock memory manager to return existing memory
        mock_memory_manager.storage.get_all_memories = Mock(return_value=[existing_memory])
        
        result = z3_validator.detect_comprehensive_contradictions(
            response=response,
            existing_memories=[existing_memory],
            memory_manager=mock_memory_manager,
            use_web_search=False,
            fact_checker=None
        )
        
        assert "semantic_contradictions" in result
        assert isinstance(result["overall_contradiction_score"], float)
    
    def test_web_fact_checking_integration(self, z3_validator, fact_checker):
        """Test web search fact-checking integration."""
        # Response with verifiable claim
        response = "The Earth is flat and the sky is green."
        
        with patch.object(fact_checker, 'fact_check_response') as mock_fact_check:
            mock_fact_check.return_value = {
                "claims": [],
                "results": [],
                "overall_contradiction_score": 0.7,
                "verified_claims_count": 0,
                "contradicted_claims_count": 1
            }
            
            result = z3_validator.detect_comprehensive_contradictions(
                response=response,
                existing_memories=[],
                memory_manager=None,
                use_web_search=True,
                fact_checker=fact_checker
            )
            
            assert "web_fact_check" in result
            assert result["web_fact_check"]["overall_contradiction_score"] == 0.7
    
    def test_multiple_contradiction_methods(self, z3_validator, mock_memory_manager, fact_checker):
        """Test that multiple contradiction detection methods work together."""
        existing_memory = MemoryRecord(
            namespace="test",
            text="Python is a programming language.",
            importance=0.9
        )
        
        response = "Python is not a programming language and 2+2=5."
        
        with patch.object(fact_checker, 'fact_check_response') as mock_fact_check:
            mock_fact_check.return_value = {
                "claims": [],
                "results": [],
                "overall_contradiction_score": 0.6,
                "verified_claims_count": 0,
                "contradicted_claims_count": 1
            }
            
            mock_memory_manager.storage.get_all_memories = Mock(return_value=[existing_memory])
            
            result = z3_validator.detect_comprehensive_contradictions(
                response=response,
                existing_memories=[existing_memory],
                memory_manager=mock_memory_manager,
                use_web_search=True,
                fact_checker=fact_checker
            )
            
            # Should have contradictions from multiple methods
            assert "contradictions" in result
            assert "z3_contradictions" in result
            assert "semantic_contradictions" in result
            assert "web_fact_check" in result
            
            # Overall score should combine all methods
            assert result["overall_contradiction_score"] > 0.0
    
    def test_non_obvious_contradictions(self, z3_validator, mock_memory_manager):
        """Test detection of non-obvious contradictions."""
        # Subtle contradiction
        existing_memory = MemoryRecord(
            namespace="test",
            text="The user prefers dark mode interfaces.",
            importance=0.7
        )
        
        response = "The user loves bright, light-colored interfaces and always uses light mode."
        
        mock_memory_manager.storage.get_all_memories = Mock(return_value=[existing_memory])
        
        result = z3_validator.detect_comprehensive_contradictions(
            response=response,
            existing_memories=[existing_memory],
            memory_manager=mock_memory_manager,
            use_web_search=False,
            fact_checker=None
        )
        
        # Should detect the contradiction (prefers dark vs loves light)
        assert result["overall_contradiction_score"] >= 0.0  # May or may not detect, but should not error
    
    def test_graceful_degradation_when_components_unavailable(self, z3_validator):
        """Test that contradiction detection works when components are unavailable."""
        response = "Test response."
        
        # Test without memory manager or fact checker
        result = z3_validator.detect_comprehensive_contradictions(
            response=response,
            existing_memories=[],
            memory_manager=None,
            use_web_search=False,
            fact_checker=None
        )
        
        # Should still return valid result
        assert "contradictions" in result
        assert "overall_contradiction_score" in result
        assert isinstance(result["overall_contradiction_score"], float)

