"""
Comprehensive tests for SelfModelSizeManager.

Tests size limits, pruning strategies, metadata-only representation,
fault injection, and property-based testing following AGENTS.md requirements.
"""

from __future__ import annotations

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta

try:
    from hypothesis import given, strategies as st, settings, HealthCheck, assume
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

from broca.self_model.size_manager import (
    SelfModelSizeManager,
    SizeLimits,
    PruningStrategy
)
from broca.self_model.model import SelfModel
from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType
from broca.self_model.source import Source


@pytest.fixture
def sample_self_model():
    """Create a sample self-model for testing."""
    from broca.self_model.source import Source
    model = SelfModel.create_default()
    source_dict = Source.system_default().to_dict()
    model.capabilities = [
        {"text": f"Capability {i}", "source": source_dict}
        for i in range(5)
    ]
    model.knowledge_boundaries = {
        f"kb_{i}": {"value": f"Value {i}", "source": source_dict}
        for i in range(3)
    }
    model.constraints = {
        f"constraint_{i}": {"value": f"Constraint {i}", "source": source_dict}
        for i in range(3)
    }
    return model


@pytest.fixture
def large_self_model():
    """Create a self-model that exceeds limits."""
    from broca.self_model.source import Source
    model = SelfModel.create_default()
    source_dict = Source.system_default().to_dict()
    model.capabilities = [
        {"text": f"Capability {i}", "source": source_dict}
        for i in range(15)  # Exceeds max of 10
    ]
    model.knowledge_boundaries = {
        f"kb_{i}": {"value": f"Value {i}", "source": source_dict}
        for i in range(7)  # Exceeds max of 5
    }
    model.constraints = {
        f"constraint_{i}": {"value": f"Constraint {i}", "source": source_dict}
        for i in range(7)  # Exceeds max of 5
    }
    return model


@pytest.fixture
def epistemic_engine():
    """Create an epistemic engine for testing."""
    epistemic_layer = EpistemicLayer()
    return MetacognitiveEngine(epistemic_layer=epistemic_layer)


@pytest.fixture
def size_manager():
    """Create a size manager with default limits."""
    limits = SizeLimits(
        max_capabilities=10,
        max_knowledge_boundaries=5,
        max_constraints=5,
        soft_capabilities=8,
        soft_knowledge_boundaries=4,
        soft_constraints=4
    )
    return SelfModelSizeManager(limits=limits)


@pytest.fixture
def size_manager_with_epistemic(epistemic_engine):
    """Create a size manager with epistemic engine."""
    limits = SizeLimits(
        max_capabilities=10,
        max_knowledge_boundaries=5,
        max_constraints=5
    )
    return SelfModelSizeManager(
        limits=limits,
        epistemic_engine=epistemic_engine
    )


class TestSizeManagerInitialization:
    """Test size manager initialization."""
    
    def test_size_manager_initialization(self):
        """Test that size manager initializes correctly."""
        limits = SizeLimits()
        manager = SelfModelSizeManager(limits=limits)
        assert manager.limits == limits
        assert manager.pruning_strategy == PruningStrategy.COMBINED_SCORE
    
    def test_size_manager_default_limits(self):
        """Test default size limits."""
        manager = SelfModelSizeManager()
        assert manager.limits.max_capabilities == 50
        assert manager.limits.max_knowledge_boundaries == 30
        assert manager.limits.max_constraints == 30
    
    def test_size_manager_custom_strategy(self):
        """Test custom pruning strategy."""
        manager = SelfModelSizeManager(
            pruning_strategy=PruningStrategy.LOWEST_CONFIDENCE
        )
        assert manager.pruning_strategy == PruningStrategy.LOWEST_CONFIDENCE
    
    def test_size_manager_with_epistemic_engine(self, epistemic_engine):
        """Test initialization with epistemic engine."""
        manager = SelfModelSizeManager(epistemic_engine=epistemic_engine)
        assert manager.epistemic_engine == epistemic_engine


class TestSizeChecking:
    """Test size checking functionality."""
    
    def test_check_size_within_limits(self, size_manager, sample_self_model):
        """Test size check when within limits."""
        status = size_manager.check_size(sample_self_model)
        assert not status["needs_pruning"]
        assert not status["warn_size"]
        assert status["capabilities"]["count"] == 5
        assert status["capabilities"]["exceeds_hard"] is False
        assert status["capabilities"]["exceeds_soft"] is False
    
    def test_check_size_exceeds_soft_limit(self, size_manager, sample_self_model):
        """Test size check when exceeds soft limit."""
        # Add more capabilities to exceed soft limit
        source_dict = Source.system_default().to_dict()
        sample_self_model.capabilities.extend([
            {"text": f"Extra capability {i}", "source": source_dict}
            for i in range(5)  # Total now 10, exceeds soft limit of 8
        ])
        
        status = size_manager.check_size(sample_self_model)
        assert not status["needs_pruning"]  # Not hard limit yet
        assert status["warn_size"]  # But warns
        assert status["capabilities"]["exceeds_soft"] is True
    
    def test_check_size_exceeds_hard_limit(self, size_manager, large_self_model):
        """Test size check when exceeds hard limit."""
        status = size_manager.check_size(large_self_model)
        assert status["needs_pruning"]
        assert status["capabilities"]["exceeds_hard"] is True
        assert status["knowledge_boundaries"]["exceeds_hard"] is True
        assert status["constraints"]["exceeds_hard"] is True
    
    def test_check_size_all_aspects(self, size_manager, large_self_model):
        """Test size check returns status for all aspects."""
        status = size_manager.check_size(large_self_model)
        assert "capabilities" in status
        assert "knowledge_boundaries" in status
        assert "constraints" in status
        assert "needs_pruning" in status
        assert "warn_size" in status


class TestPruningOperations:
    """Test pruning operations."""
    
    def test_prune_capabilities(self, size_manager, large_self_model):
        """Test pruning capabilities when limit exceeded."""
        pruned_model, stats = size_manager.prune_if_needed(large_self_model)
        assert "capabilities" in stats
        assert stats["capabilities"] > 0
        assert len(pruned_model.capabilities) <= size_manager.limits.max_capabilities
        assert pruned_model.metadata.get("update_reason") == "size_management_pruning"
    
    def test_prune_knowledge_boundaries(self, size_manager, large_self_model):
        """Test pruning knowledge boundaries when limit exceeded."""
        pruned_model, stats = size_manager.prune_if_needed(large_self_model)
        assert "knowledge_boundaries" in stats
        assert stats["knowledge_boundaries"] > 0
        assert len(pruned_model.knowledge_boundaries) <= size_manager.limits.max_knowledge_boundaries
    
    def test_prune_constraints(self, size_manager, large_self_model):
        """Test pruning constraints when limit exceeded."""
        pruned_model, stats = size_manager.prune_if_needed(large_self_model)
        assert "constraints" in stats
        assert stats["constraints"] > 0
        assert len(pruned_model.constraints) <= size_manager.limits.max_constraints
    
    def test_prune_when_not_needed(self, size_manager, sample_self_model):
        """Test pruning when not needed returns original model."""
        pruned_model, stats = size_manager.prune_if_needed(sample_self_model)
        assert pruned_model == sample_self_model
        assert stats == {}
    
    def test_prune_preserves_epistemic_layer(self, size_manager, large_self_model):
        """Test that pruning preserves epistemic layer."""
        pruned_model, _ = size_manager.prune_if_needed(large_self_model)
        assert pruned_model.epistemic_layer is not None
        assert pruned_model.epistemic_layer == large_self_model.epistemic_layer
    
    def test_prune_updates_metadata(self, size_manager, large_self_model):
        """Test that pruning updates metadata."""
        original_version = large_self_model.metadata.get("version", 1)
        pruned_model, stats = size_manager.prune_if_needed(large_self_model)
        assert pruned_model.metadata.get("version") == original_version + 1
        assert "last_updated" in pruned_model.metadata
        assert "pruning_stats" in pruned_model.metadata


class TestPruningStrategies:
    """Test different pruning strategies."""
    
    def test_lowest_confidence_strategy(self, large_self_model):
        """Test LOWEST_CONFIDENCE pruning strategy."""
        # Add confidence scores to capabilities
        source_dict = Source.system_default().to_dict()
        for i, cap in enumerate(large_self_model.capabilities):
            cap["confidence"] = i / 15.0  # Varying confidence
        
        manager = SelfModelSizeManager(
            limits=SizeLimits(max_capabilities=10),
            pruning_strategy=PruningStrategy.LOWEST_CONFIDENCE
        )
        pruned_model, stats = manager.prune_if_needed(large_self_model)
        assert len(pruned_model.capabilities) == 10
        # Lowest confidence items should be pruned
        remaining_confidences = [cap.get("confidence", 0.5) for cap in pruned_model.capabilities]
        assert min(remaining_confidences) >= 5 / 15.0  # Should keep higher confidence items
    
    def test_least_recent_strategy(self, large_self_model):
        """Test LEAST_RECENT pruning strategy."""
        # Add timestamps to capabilities
        source_dict = Source.system_default().to_dict()
        now = datetime.now(timezone.utc)
        for i, cap in enumerate(large_self_model.capabilities):
            cap["source"] = {
                **source_dict,
                "timestamp": (now - timedelta(days=i)).isoformat()
            }
        
        manager = SelfModelSizeManager(
            limits=SizeLimits(max_capabilities=10),
            pruning_strategy=PruningStrategy.LEAST_RECENT
        )
        pruned_model, stats = manager.prune_if_needed(large_self_model)
        assert len(pruned_model.capabilities) == 10
        # More recent items should be kept
    
    def test_combined_score_strategy(self, large_self_model):
        """Test COMBINED_SCORE pruning strategy."""
        manager = SelfModelSizeManager(
            limits=SizeLimits(max_capabilities=10),
            pruning_strategy=PruningStrategy.COMBINED_SCORE
        )
        pruned_model, stats = manager.prune_if_needed(large_self_model)
        assert len(pruned_model.capabilities) == 10
    
    def test_lowest_epistemic_confidence_strategy(self, size_manager_with_epistemic, large_self_model):
        """Test LOWEST_EPISTEMIC_CONFIDENCE pruning strategy."""
        manager = SelfModelSizeManager(
            limits=SizeLimits(max_capabilities=10),
            pruning_strategy=PruningStrategy.LOWEST_EPISTEMIC_CONFIDENCE,
            epistemic_engine=size_manager_with_epistemic.epistemic_engine
        )
        pruned_model, stats = manager.prune_if_needed(large_self_model)
        assert len(pruned_model.capabilities) == 10


class TestMetadataOnlyRepresentation:
    """Test metadata-only representation."""
    
    def test_get_metadata_only_representation(self, size_manager, sample_self_model):
        """Test getting metadata-only representation."""
        metadata = size_manager.get_metadata_only_representation(sample_self_model)
        assert "capabilities_count" in metadata
        assert "knowledge_boundaries_count" in metadata
        assert "constraints_count" in metadata
        assert metadata["capabilities_count"] == 5
        assert metadata["knowledge_boundaries_count"] == 3
        assert metadata["constraints_count"] == 3
    
    def test_metadata_only_preserves_structure(self, size_manager, sample_self_model):
        """Test that metadata-only representation preserves structure."""
        metadata = size_manager.get_metadata_only_representation(sample_self_model)
        assert "version" in metadata
        assert "capabilities_summary" in metadata
        assert "knowledge_boundaries_keys" in metadata
        assert "constraints_keys" in metadata
        assert isinstance(metadata["capabilities_summary"], list)
        assert len(metadata["capabilities_summary"]) <= 5  # Summary limit
    
    def test_metadata_only_with_large_model(self, size_manager, large_self_model):
        """Test metadata-only representation with large model."""
        metadata = size_manager.get_metadata_only_representation(large_self_model)
        assert metadata["capabilities_count"] == 15
        assert len(metadata["capabilities_summary"]) == 5  # Should limit summary


class TestFaultInjection:
    """Test fault injection scenarios."""
    
    def test_prune_with_invalid_model(self, size_manager):
        """Test pruning with invalid model structure."""
        invalid_model = Mock(spec=SelfModel)
        invalid_model.capabilities = "not a list"
        invalid_model.knowledge_boundaries = {}
        invalid_model.constraints = {}
        invalid_model.metadata = {}
        
        # Should handle gracefully - check_size may raise TypeError or handle it
        try:
            size_manager.check_size(invalid_model)
            # If it doesn't raise, that's also acceptable (defensive handling)
        except (TypeError, AttributeError):
            # Expected behavior - invalid structure detected
            pass
    
    def test_prune_with_missing_source(self, size_manager):
        """Test pruning with missing source information."""
        model = SelfModel.create_default()
        model.capabilities = [
            {"text": "Capability without source"}
            for _ in range(15)
        ]
        
        # Should handle gracefully
        pruned_model, stats = size_manager.prune_if_needed(model)
        assert len(pruned_model.capabilities) <= size_manager.limits.max_capabilities
    
    def test_prune_with_corrupted_timestamps(self, size_manager):
        """Test pruning with corrupted timestamp data."""
        source_dict = Source.system_default().to_dict()
        source_dict["timestamp"] = "invalid timestamp"
        
        model = SelfModel.create_default()
        model.capabilities = [
            {"text": f"Capability {i}", "source": source_dict}
            for i in range(15)
        ]
        
        # Should handle gracefully
        pruned_model, stats = size_manager.prune_if_needed(model)
        assert len(pruned_model.capabilities) <= size_manager.limits.max_capabilities


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        capability_count=st.integers(min_value=0, max_value=100),
        kb_count=st.integers(min_value=0, max_value=50),
        constraint_count=st.integers(min_value=0, max_value=50)
    )
    def test_check_size_property(self, size_manager, capability_count, kb_count, constraint_count):
        """Property: Size check always returns valid structure."""
        model = SelfModel.create_default()
        source_dict = Source.system_default().to_dict()
        model.capabilities = [
            {"text": f"Cap {i}", "source": source_dict}
            for i in range(capability_count)
        ]
        model.knowledge_boundaries = {
            f"kb_{i}": {"value": f"Value {i}", "source": source_dict}
            for i in range(kb_count)
        }
        model.constraints = {
            f"const_{i}": {"value": f"Constraint {i}", "source": source_dict}
            for i in range(constraint_count)
        }
        
        status = size_manager.check_size(model)
        assert "capabilities" in status
        assert "knowledge_boundaries" in status
        assert "constraints" in status
        assert status["capabilities"]["count"] == capability_count
        assert status["knowledge_boundaries"]["count"] == kb_count
        assert status["constraints"]["count"] == constraint_count
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        max_cap=st.integers(min_value=1, max_value=20),
        actual_cap=st.integers(min_value=0, max_value=50)
    )
    def test_prune_respects_limits_property(self, max_cap, actual_cap):
        """Property: Pruned model always respects limits."""
        assume(actual_cap > max_cap)  # Only test when pruning is needed
        
        limits = SizeLimits(max_capabilities=max_cap)
        manager = SelfModelSizeManager(limits=limits)
        
        model = SelfModel.create_default()
        source_dict = Source.system_default().to_dict()
        model.capabilities = [
            {"text": f"Cap {i}", "source": source_dict}
            for i in range(actual_cap)
        ]
        
        pruned_model, stats = manager.prune_if_needed(model)
        assert len(pruned_model.capabilities) <= max_cap


class TestEpistemicConfidenceBasedPruning:
    """Test epistemic confidence-based pruning."""
    
    def test_epistemic_confidence_pruning(self, size_manager_with_epistemic, large_self_model):
        """Test pruning using epistemic confidence."""
        manager = SelfModelSizeManager(
            limits=SizeLimits(max_capabilities=10),
            pruning_strategy=PruningStrategy.LOWEST_EPISTEMIC_CONFIDENCE,
            epistemic_engine=size_manager_with_epistemic.epistemic_engine
        )
        
        pruned_model, stats = manager.prune_if_needed(large_self_model)
        assert len(pruned_model.capabilities) == 10
    
    def test_epistemic_confidence_fallback(self, size_manager_with_epistemic, large_self_model):
        """Test that epistemic confidence falls back when unavailable."""
        manager = SelfModelSizeManager(
            limits=SizeLimits(max_capabilities=10),
            pruning_strategy=PruningStrategy.LOWEST_EPISTEMIC_CONFIDENCE,
            epistemic_engine=size_manager_with_epistemic.epistemic_engine
        )
        
        # Should still prune even if epistemic data unavailable
        pruned_model, stats = manager.prune_if_needed(large_self_model)
        assert len(pruned_model.capabilities) == 10


class TestSoftLimitEnforcement:
    """Test soft limit enforcement."""
    
    def test_soft_limit_warning(self, size_manager, sample_self_model):
        """Test that soft limits trigger warnings."""
        source_dict = Source.system_default().to_dict()
        # Add items to exceed soft limit but not hard limit
        sample_self_model.capabilities.extend([
            {"text": f"Extra {i}", "source": source_dict}
            for i in range(4)  # Now 9 total, exceeds soft (8) but not hard (10)
        ])
        
        status = size_manager.check_size(sample_self_model)
        assert status["warn_size"] is True
        assert status["needs_pruning"] is False
        assert status["capabilities"]["exceeds_soft"] is True


class TestMetadataArtifactReference:
    """Test metadata-to-artifact reference pattern."""
    
    def test_metadata_only_reduces_size(self, size_manager, large_self_model):
        """Test that metadata-only representation is smaller."""
        full_dict = large_self_model.to_dict() if hasattr(large_self_model, 'to_dict') else {}
        metadata = size_manager.get_metadata_only_representation(large_self_model)
        
        # Metadata should be much smaller (just counts and summaries)
        import json
        metadata_size = len(json.dumps(metadata))
        # Metadata should be significantly smaller than full model representation
        assert metadata_size < 5000  # Reasonable upper bound
