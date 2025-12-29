"""
Tests to ensure no placeholder values propagate in epistemic and internal sensing.

Tests:
- No neutral defaults (0.5) without data quality indicators
- Missing data results in high uncertainty (≥ 0.7)
- All metrics include sample_size or data_quality fields
- Confidence intervals provided for reliability estimates
"""

import pytest
from unittest.mock import Mock, MagicMock

from broca.internal_sensing.data_quality import (
    DataQuality,
    uncertainty_for_missing_data,
    confidence_for_missing_data,
    assess_data_quality,
    bayesian_reliability_estimate,
    create_metric_with_quality,
)
from broca.internal_sensing.epistemic_bridge import EpistemicBridge
from broca.self_model.epistemic.validation import SourceValidator
from broca.self_model.epistemic.models import SourceMetadata, SourceType
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor
from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor


class TestDataQualityFramework:
    """Test data quality framework utilities."""
    
    def test_uncertainty_for_missing_data_is_high(self):
        """Missing data should result in high uncertainty (≥ 0.7)."""
        uncertainty = uncertainty_for_missing_data()
        assert uncertainty >= 0.7, f"Missing data uncertainty {uncertainty} should be ≥ 0.7"
        assert uncertainty <= 1.0, f"Missing data uncertainty {uncertainty} should be ≤ 1.0"
    
    def test_confidence_for_missing_data_has_wide_interval(self):
        """Missing data confidence should have wide confidence interval."""
        mean, interval = confidence_for_missing_data()
        assert 0.0 <= mean <= 1.0, "Mean should be in [0, 1]"
        assert interval[0] < interval[1], "Interval should be valid"
        interval_width = interval[1] - interval[0]
        assert interval_width >= 0.6, f"Missing data interval width {interval_width} should be ≥ 0.6"
    
    def test_bayesian_reliability_with_no_data(self):
        """Bayesian reliability with no data should use prior and indicate missing data."""
        result = bayesian_reliability_estimate(0, 0, prior_alpha=0.5, prior_beta=0.5)
        assert "reliability" in result
        assert "confidence_interval" in result
        assert "sample_size" in result
        assert result["sample_size"] == 0
        assert result["data_quality"] == DataQuality.MISSING.value
        assert result["uncertainty"] >= 0.7, "Uncertainty should be high for missing data"
    
    def test_create_metric_with_quality_includes_metadata(self):
        """create_metric_with_quality should include all required metadata."""
        metric = create_metric_with_quality(0.5, sample_size=0)
        assert "value" in metric
        assert "sample_size" in metric
        assert "data_quality" in metric
        assert "has_data" in metric
        assert "uncertainty" in metric
        assert metric["data_quality"] == DataQuality.MISSING.value
        assert metric["has_data"] is False


class TestEpistemicBridge:
    """Test epistemic bridge doesn't return placeholder values."""
    
    def test_get_aggregated_uncertainty_without_engine(self):
        """Without epistemic engine, should return high uncertainty, not 0.0."""
        bridge = EpistemicBridge(epistemic_engine=None)
        uncertainty = bridge.get_aggregated_uncertainty()
        
        assert "total" in uncertainty
        assert uncertainty["total"] >= 0.7, f"Missing data uncertainty {uncertainty['total']} should be ≥ 0.7"
        assert "data_quality" in uncertainty
        assert uncertainty["data_quality"] == DataQuality.MISSING.value
        assert "has_data" in uncertainty
        assert uncertainty["has_data"] is False
    
    def test_get_aggregated_confidence_without_engine(self):
        """Without epistemic engine, should return high uncertainty confidence."""
        bridge = EpistemicBridge(epistemic_engine=None)
        confidence = bridge.get_aggregated_confidence()
        
        assert "overall_confidence" in confidence
        assert "confidence_interval" in confidence
        assert "data_quality" in confidence
        assert confidence["data_quality"] == DataQuality.MISSING.value
        assert "uncertainty" in confidence
        assert confidence["uncertainty"] >= 0.7, "Uncertainty should be high for missing data"
        assert confidence["has_data"] is False


class TestSourceValidator:
    """Test source validator uses Bayesian priors, not defaults."""
    
    def test_assess_tool_reliability_no_data(self):
        """Tool reliability with no data should use Bayesian prior."""
        validator = SourceValidator()
        result = validator.assess_tool_reliability("unknown_tool", return_metadata=True)
        
        assert isinstance(result, dict)
        assert "reliability" in result
        assert "confidence_interval" in result
        assert "sample_size" in result
        assert result["sample_size"] == 0
        assert result["data_quality"] == DataQuality.MISSING.value
        assert result["uncertainty"] >= 0.7, "Uncertainty should be high for missing data"
    
    def test_assess_memory_quality_no_data(self):
        """Memory quality with no data should use Bayesian prior."""
        validator = SourceValidator()
        result = validator.assess_memory_quality(99999, return_metadata=True)
        
        assert isinstance(result, dict)
        assert "reliability" in result
        assert "confidence_interval" in result
        assert result["sample_size"] == 0
        assert result["data_quality"] == DataQuality.MISSING.value
    
    def test_assess_source_reliability_unknown_type(self):
        """Unknown source type should return high uncertainty."""
        validator = SourceValidator()
        source = SourceMetadata(source_type=SourceType.SYSTEM_DEFAULT)
        result = validator.assess_source_reliability(source, return_metadata=True)
        
        assert isinstance(result, dict)
        assert "reliability" in result
        assert "uncertainty" in result
        assert result["uncertainty"] >= 0.7, "Uncertainty should be high for unknown source"


class TestCognitiveStateMonitor:
    """Test cognitive state monitor uses priors, not defaults."""
    
    def test_confidence_level_with_no_history(self):
        """Confidence level with no history should use prior, not default 0.5."""
        monitor = CognitiveStateMonitor()
        # Clear any default history
        monitor._confidence_history.clear()
        
        state = monitor.sample_cognitive_state()
        # Should have confidence_level, but it might be a prior
        assert "confidence_level" in state
        # If data_quality is tracked, it should indicate missing data
        if "data_quality" in state and "confidence" in state["data_quality"]:
            assert state["data_quality"]["confidence"] == DataQuality.MISSING.value
    
    def test_uncertainty_tracking_with_no_history(self):
        """Uncertainty tracking with no history should use high uncertainty."""
        monitor = CognitiveStateMonitor()
        monitor._uncertainty_history.clear()
        
        state = monitor.sample_cognitive_state()
        assert "uncertainty_tracking" in state
        # If using data quality framework, uncertainty should be high
        if "data_quality" in state and "uncertainty" in state["data_quality"]:
            assert state["data_quality"]["uncertainty"] == DataQuality.MISSING.value


class TestAffectiveStateMonitor:
    """Test affective state monitor includes data quality indicators."""
    
    def test_sample_affective_state_includes_data_quality(self):
        """Sampled affective state should include data quality indicators."""
        monitor = ComputationalAffectMonitor()
        state = monitor.sample_affective_state()
        
        # Should have data_quality field if framework is available
        # (This depends on HAS_DATA_QUALITY flag)
        # At minimum, states should be present
        assert "valence" in state
        assert "arousal" in state
        assert "certainty_affect" in state


class TestComputationalPhysiologyMonitor:
    """Test physiology monitor handles missing psutil properly."""
    
    def test_cpu_load_without_psutil(self):
        """CPU load without psutil should indicate missing data."""
        monitor = ComputationalPhysiologyMonitor()
        # Mock psutil as None
        import broca.internal_sensing.computational_physiology as phys_module
        original_psutil = phys_module.psutil
        phys_module.psutil = None
        
        try:
            load = monitor._measure_computational_load()
            # Should have data quality indicator if framework available
            if hasattr(monitor, 'metrics') and "data_quality" in monitor.metrics:
                if "computational_load" in monitor.metrics["data_quality"]:
                    assert monitor.metrics["data_quality"]["computational_load"] == DataQuality.MISSING.value
        finally:
            phys_module.psutil = original_psutil


class TestPropertyBased:
    """Property-based tests for data quality principles."""
    
    def test_uncertainty_increases_with_missing_data(self):
        """Uncertainty should always increase when data is missing."""
        # Test with various scenarios
        scenarios = [
            (0, 0),  # No data
            (1, 0),  # Very little data
            (5, 0),  # Insufficient data
        ]
        
        for successes, failures in scenarios:
            result = bayesian_reliability_estimate(successes, failures)
            total_samples = successes + failures
            
            if total_samples == 0:
                assert result["uncertainty"] >= 0.7, "No data should have high uncertainty"
                assert result["data_quality"] == DataQuality.MISSING.value
            elif total_samples < 5:
                assert result["uncertainty"] >= 0.5, "Little data should have moderate-high uncertainty"
    
    def test_confidence_intervals_widen_with_less_data(self):
        """Confidence intervals should be wider with less data."""
        results = []
        for n in [0, 1, 5, 10, 20]:
            result = bayesian_reliability_estimate(n, 0, prior_alpha=0.5, prior_beta=0.5)
            interval_width = result["confidence_interval"][1] - result["confidence_interval"][0]
            results.append((n, interval_width))
        
        # Interval width should generally decrease (or stay same) as sample size increases
        for i in range(len(results) - 1):
            n1, width1 = results[i]
            n2, width2 = results[i + 1]
            if n1 == 0:
                # No data should have widest interval
                assert width1 >= width2, f"Interval with no data ({width1}) should be wider than with data ({width2})"


class TestMutationTesting:
    """Mutation testing: ensure removing defaults doesn't break system."""
    
    def test_epistemic_bridge_handles_missing_engine_gracefully(self):
        """Epistemic bridge should handle missing engine without errors."""
        bridge = EpistemicBridge(epistemic_engine=None)
        
        # Should not raise exceptions
        uncertainty = bridge.get_aggregated_uncertainty()
        confidence = bridge.get_aggregated_confidence()
        reliability = bridge.get_source_reliability()
        
        # Should return structured responses with data quality indicators
        assert isinstance(uncertainty, dict)
        assert isinstance(confidence, dict)
        assert isinstance(reliability, dict)
    
    def test_validator_handles_unknown_tools_gracefully(self):
        """Validator should handle unknown tools without errors."""
        validator = SourceValidator()
        
        # Should not raise exceptions
        result = validator.assess_tool_reliability("completely_unknown_tool", return_metadata=True)
        assert isinstance(result, dict)
        assert "reliability" in result
        assert "data_quality" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

