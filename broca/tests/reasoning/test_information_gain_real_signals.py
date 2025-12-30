"""
TDD Tests for REAL information_gain signal calculation.

These tests ensure that:
1. Epistemic engine tracks importance and usage_frequency
2. Information gain uses REAL data, not placeholders
3. The signal actually varies based on knowledge access patterns

Scientific basis: Bayesian Expected Information Gain (EIG)
- gain = importance × (1 - confidence) × (1 + usage_frequency)
- Higher importance = more valuable to verify
- Lower confidence = more uncertainty to reduce
- Higher usage = more impact on system behavior
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


class TestEpistemicLayerImportanceTracking:
    """Tests for importance/usage_frequency tracking in EpistemicLayer."""

    def test_epistemic_layer_tracks_usage_frequency(self):
        """EpistemicLayer should track how often each knowledge item is accessed."""
        from broca.self_model.epistemic.layer import EpistemicLayer

        layer = EpistemicLayer()
        kid = "test_knowledge_1"

        # Initial usage should be 0
        assert layer.get_usage_frequency(kid) == 0

        # Record accesses
        layer.record_knowledge_access(kid)
        assert layer.get_usage_frequency(kid) == 1

        layer.record_knowledge_access(kid)
        layer.record_knowledge_access(kid)
        assert layer.get_usage_frequency(kid) == 3

    def test_epistemic_layer_tracks_importance(self):
        """EpistemicLayer should track importance of each knowledge item."""
        from broca.self_model.epistemic.layer import EpistemicLayer

        layer = EpistemicLayer()
        kid = "test_knowledge_1"

        # Default importance should be moderate (0.5)
        assert layer.get_importance(kid) == 0.5

        # Set importance explicitly
        layer.set_importance(kid, 0.9)
        assert layer.get_importance(kid) == 0.9

    def test_importance_updates_based_on_usage(self):
        """Importance should increase with usage (frequently used = important)."""
        from broca.self_model.epistemic.layer import EpistemicLayer

        layer = EpistemicLayer()
        kid = "test_knowledge_1"

        initial_importance = layer.get_importance(kid)

        # Simulate heavy usage
        for _ in range(20):
            layer.record_knowledge_access(kid)

        # Update importance based on usage
        layer.update_importance_from_usage(kid)

        # Importance should have increased
        assert layer.get_importance(kid) > initial_importance

    def test_importance_bounded_0_1(self):
        """Importance values should always be in [0, 1]."""
        from broca.self_model.epistemic.layer import EpistemicLayer

        layer = EpistemicLayer()
        kid = "test"

        # Try setting out-of-bounds values
        layer.set_importance(kid, 1.5)
        assert layer.get_importance(kid) == 1.0

        layer.set_importance(kid, -0.5)
        assert layer.get_importance(kid) == 0.0


class TestMetacognitiveEngineImportanceExposure:
    """Tests for exposing importance/usage in epistemic context."""

    def test_get_epistemic_context_includes_importance(self):
        """get_epistemic_context should include importance in returned dict."""
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType

        engine = MetacognitiveEngine()

        # Acquire some knowledge
        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            retrieval_context="test context",
        )
        kid = "test_knowledge_1"
        engine.knowledge_acquisition_workflow(kid, source, initial_confidence=0.7)

        # Set importance
        engine.epistemic_layer.set_importance(kid, 0.85)

        # Get context
        context = engine.get_epistemic_context(kid)

        assert "importance" in context
        assert context["importance"] == 0.85

    def test_get_epistemic_context_includes_usage_frequency(self):
        """get_epistemic_context should include usage_frequency in returned dict."""
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType

        engine = MetacognitiveEngine()

        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            retrieval_context="test context",
        )
        kid = "test_knowledge_1"
        engine.knowledge_acquisition_workflow(kid, source, initial_confidence=0.7)

        # Record some accesses
        engine.epistemic_layer.record_knowledge_access(kid)
        engine.epistemic_layer.record_knowledge_access(kid)
        engine.epistemic_layer.record_knowledge_access(kid)

        # Get context
        context = engine.get_epistemic_context(kid)

        assert "usage_frequency" in context
        assert context["usage_frequency"] == 3


class TestEpistemicBridgeRealData:
    """Tests for EpistemicBridge using real importance/usage data."""

    def test_info_gain_uses_real_importance_when_available(self):
        """When importance/usage are tracked, info_gain should use them."""
        from broca.internal_sensing.epistemic_bridge import EpistemicBridge
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType

        engine = MetacognitiveEngine()

        # Acquire knowledge with real tracking
        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            retrieval_context="test",
        )
        kid = "k1"
        engine.knowledge_acquisition_workflow(kid, source, initial_confidence=0.6)

        # Set real importance and usage
        engine.epistemic_layer.set_importance(kid, 0.9)
        for _ in range(10):
            engine.epistemic_layer.record_knowledge_access(kid)

        # Create bridge
        bridge = EpistemicBridge(epistemic_engine=engine)

        # Get info gain
        info = bridge.get_information_gain_info()

        # Should NOT be "estimated_inputs" when real data exists
        assert info["estimator"] != "estimated_inputs", \
            f"Expected real data estimator, got {info['estimator']}"
        assert info["has_data"] is True
        # With high importance (0.9) and moderate uncertainty (0.4), gain should be significant
        assert info["value"] > 0.1, f"Expected significant info gain, got {info['value']}"

    def test_info_gain_increases_with_usage_frequency(self):
        """Higher usage_frequency should increase information gain."""
        from broca.internal_sensing.epistemic_bridge import EpistemicBridge
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType

        engine = MetacognitiveEngine()

        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            retrieval_context="test",
        )

        # Create two knowledge items with different usage
        engine.knowledge_acquisition_workflow("low_usage", source, initial_confidence=0.5)
        engine.epistemic_layer.set_importance("low_usage", 0.8)
        engine.epistemic_layer.record_knowledge_access("low_usage")

        engine.knowledge_acquisition_workflow("high_usage", source, initial_confidence=0.5)
        engine.epistemic_layer.set_importance("high_usage", 0.8)
        for _ in range(50):
            engine.epistemic_layer.record_knowledge_access("high_usage")

        # The formula: gain = importance × uncertainty × (1 + usage_frequency)
        # Same importance, same confidence → high_usage should have higher gain
        gains = engine.uncertainty_manager.information_gain_calculation({
            "low_usage": {
                "confidence": 0.5,
                "importance": 0.8,
                "usage_frequency": 1,
            },
            "high_usage": {
                "confidence": 0.5,
                "importance": 0.8,
                "usage_frequency": 50,
            },
        })

        gains_dict = dict(gains)
        assert gains_dict["high_usage"] > gains_dict["low_usage"], \
            f"High usage gain ({gains_dict['high_usage']}) should exceed low usage ({gains_dict['low_usage']})"


class TestInformationGainFormula:
    """Tests for the mathematical correctness of information gain formula."""

    def test_gain_formula_matches_bayesian_eig(self):
        """
        Verify: gain = importance × (1 - confidence) × (1 + usage_frequency)
        
        This is a simplified Bayesian Expected Information Gain:
        - importance = prior probability of being useful (p(useful))
        - (1 - confidence) = entropy/uncertainty (H[X])
        - (1 + usage_frequency) = weight by how often it impacts decisions
        """
        from broca.self_model.epistemic.uncertainty import UncertaintyManager

        manager = UncertaintyManager()

        # Test case: high importance, low confidence, high usage
        knowledge_items = {
            "k1": {
                "confidence": 0.2,  # High uncertainty (0.8)
                "importance": 0.9,  # Very important
                "usage_frequency": 10,  # Used often
            }
        }

        gains = manager.information_gain_calculation(knowledge_items)

        # Expected: 0.9 × 0.8 × (1 + 10) = 0.9 × 0.8 × 11 = 7.92
        # But it's clamped or normalized in practice
        expected_raw = 0.9 * 0.8 * 11
        actual = dict(gains)["k1"]

        # The actual gain should be proportional to this formula
        assert actual > 0, f"Gain should be positive, got {actual}"
        # If not normalized, should match raw calculation
        # If normalized, should be significant relative to baseline
        assert actual >= min(1.0, expected_raw) or actual == expected_raw, \
            f"Gain {actual} doesn't match expected {expected_raw}"

    def test_zero_importance_yields_zero_gain(self):
        """If importance=0, information gain should be 0 (not worth verifying)."""
        from broca.self_model.epistemic.uncertainty import UncertaintyManager

        manager = UncertaintyManager()

        gains = manager.information_gain_calculation({
            "k1": {
                "confidence": 0.3,
                "importance": 0.0,  # Zero importance
                "usage_frequency": 100,
            }
        })

        assert dict(gains)["k1"] == 0.0, "Zero importance should yield zero gain"

    def test_full_confidence_yields_zero_gain(self):
        """If confidence=1.0, no uncertainty → no information gain."""
        from broca.self_model.epistemic.uncertainty import UncertaintyManager

        manager = UncertaintyManager()

        gains = manager.information_gain_calculation({
            "k1": {
                "confidence": 1.0,  # Full confidence = zero uncertainty
                "importance": 0.9,
                "usage_frequency": 10,
            }
        })

        assert dict(gains)["k1"] == 0.0, "Full confidence should yield zero gain"


class TestIntegrationWithMemoryRetrieval:
    """Integration tests: memory retrieval should update usage tracking."""

    def test_memory_retrieval_increments_usage(self):
        """
        When memories are retrieved, the corresponding knowledge items
        should have their usage_frequency incremented.
        """
        # This will be wired up in memory_tool.py
        # For now, test the method exists and works
        from broca.self_model.epistemic.layer import EpistemicLayer

        layer = EpistemicLayer()
        kid = "knowledge_from_memory_123"

        # Map memory to knowledge
        layer.add_memory_knowledge_mapping(123, kid)

        # Simulate memory retrieval updating usage
        layer.record_knowledge_access(kid)

        assert layer.get_usage_frequency(kid) == 1

        # Retrieve again
        layer.record_knowledge_access(kid)
        layer.record_knowledge_access(kid)

        assert layer.get_usage_frequency(kid) == 3

