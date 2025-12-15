"""
Tests for ConfidenceCalibrator.

Tests Bayesian updating, frequentist calibration, ensemble weighting,
and temporal discounting methods.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from broca.self_model.epistemic.calibration import ConfidenceCalibrator
from broca.self_model.epistemic.models import ConfidenceMetrics, SourceMetadata, SourceType


class TestConfidenceCalibratorBayesian:
    """Test Bayesian updating methods."""
    
    def test_bayesian_updating_confirming_evidence(self):
        """Test Bayesian updating with confirming evidence."""
        calibrator = ConfidenceCalibrator()
        
        prior = 0.7
        evidence_strength = 0.8  # Strong confirming evidence
        
        posterior = calibrator.bayesian_updating(prior, evidence_strength)
        
        assert posterior > prior
        assert 0.0 <= posterior <= 1.0
    
    def test_bayesian_updating_contradicting_evidence(self):
        """Test Bayesian updating with contradicting evidence."""
        calibrator = ConfidenceCalibrator()
        
        prior = 0.7
        evidence_strength = 0.2  # Weak evidence (contradicting)
        
        posterior = calibrator.bayesian_updating(prior, evidence_strength)
        
        assert posterior < prior
        assert 0.0 <= posterior <= 1.0
    
    def test_bayesian_updating_boundary_cases(self):
        """Test Bayesian updating with boundary values."""
        calibrator = ConfidenceCalibrator()
        
        # Prior at 0.0
        posterior1 = calibrator.bayesian_updating(0.0, 0.8)
        assert 0.0 <= posterior1 <= 1.0
        
        # Prior at 1.0
        posterior2 = calibrator.bayesian_updating(1.0, 0.2)
        assert 0.0 <= posterior2 <= 1.0
        assert posterior2 < 1.0  # Should decrease from 1.0


class TestConfidenceCalibratorFrequentist:
    """Test frequentist calibration methods."""
    
    def test_frequentist_calibration_high_success(self):
        """Test frequentist calibration with high success rate."""
        calibrator = ConfidenceCalibrator()
        
        success_rate = 0.9
        sample_size = 100
        
        confidence = calibrator.frequentist_calibration(success_rate, sample_size)
        
        assert confidence > 0.8  # Should be high
        assert 0.0 <= confidence <= 1.0
    
    def test_frequentist_calibration_low_success(self):
        """Test frequentist calibration with low success rate."""
        calibrator = ConfidenceCalibrator()
        
        success_rate = 0.3
        sample_size = 100
        
        confidence = calibrator.frequentist_calibration(success_rate, sample_size)
        
        assert confidence < 0.5  # Should be low
        assert 0.0 <= confidence <= 1.0
    
    def test_frequentist_calibration_small_sample(self):
        """Test frequentist calibration with small sample size."""
        calibrator = ConfidenceCalibrator()
        
        success_rate = 0.9
        sample_size = 5  # Small sample
        
        confidence = calibrator.frequentist_calibration(success_rate, sample_size)
        
        # Should be lower than with large sample due to uncertainty
        assert 0.0 <= confidence <= 1.0


class TestConfidenceCalibratorEnsemble:
    """Test ensemble weighting methods."""
    
    def test_ensemble_weighting_multiple_sources(self):
        """Test ensemble weighting with multiple sources."""
        calibrator = ConfidenceCalibrator()
        
        sources = [
            {"confidence": 0.8, "weight": 0.5},
            {"confidence": 0.9, "weight": 0.3},
            {"confidence": 0.7, "weight": 0.2},
        ]
        
        weighted = calibrator.ensemble_weighting(sources)
        
        assert 0.0 <= weighted <= 1.0
        # Should be between min and max
        assert 0.7 <= weighted <= 0.9
    
    def test_ensemble_weighting_single_source(self):
        """Test ensemble weighting with single source."""
        calibrator = ConfidenceCalibrator()
        
        sources = [{"confidence": 0.8, "weight": 1.0}]
        
        weighted = calibrator.ensemble_weighting(sources)
        
        assert weighted == 0.8
    
    def test_ensemble_weighting_equal_weights(self):
        """Test ensemble weighting with equal weights."""
        calibrator = ConfidenceCalibrator()
        
        sources = [
            {"confidence": 0.6, "weight": 0.33},
            {"confidence": 0.8, "weight": 0.33},
            {"confidence": 0.7, "weight": 0.34},
        ]
        
        weighted = calibrator.ensemble_weighting(sources)
        
        # Should be approximately average
        assert 0.6 <= weighted <= 0.8


class TestConfidenceCalibratorTemporal:
    """Test temporal discounting methods."""
    
    def test_temporal_discounting_recent(self):
        """Test temporal discounting with recent evidence."""
        calibrator = ConfidenceCalibrator()
        
        confidence = 0.8
        age_hours = 1.0  # Very recent
        
        discounted = calibrator.temporal_discounting(confidence, age_hours)
        
        assert discounted <= confidence  # Should be same or slightly lower
        assert discounted > confidence * 0.9  # Should not discount much
    
    def test_temporal_discounting_old(self):
        """Test temporal discounting with old evidence."""
        calibrator = ConfidenceCalibrator()
        
        confidence = 0.8
        age_hours = 720.0  # 30 days old
        
        discounted = calibrator.temporal_discounting(confidence, age_hours)
        
        assert discounted < confidence  # Should be discounted
        assert discounted > 0.0  # Should still be positive
    
    def test_temporal_discounting_very_old(self):
        """Test temporal discounting with very old evidence."""
        calibrator = ConfidenceCalibrator()
        
        confidence = 0.8
        age_hours = 8760.0  # 1 year old
        
        discounted = calibrator.temporal_discounting(confidence, age_hours)
        
        assert discounted < confidence * 0.5  # Should be significantly discounted


class TestConfidenceCalibratorComposite:
    """Test composite confidence calculation."""
    
    def test_calculate_composite_confidence(self):
        """Test calculating composite confidence from multiple dimensions."""
        calibrator = ConfidenceCalibrator()
        
        metrics = ConfidenceMetrics(
            source_reliability={
                "tool_verification_score": 0.9,
                "memory_consistency_score": 0.85,
                "logical_validity_score": 0.8,
                "user_credibility_score": 0.95
            },
            temporal_stability={
                "verification_frequency": 0.1,
                "last_verification_age_hours": 24.0,
                "consistency_over_time": 0.9
            },
            cross_validation={
                "independent_verification_count": 3,
                "contradictory_evidence_count": 0,
                "consensus_strength": 0.95
            },
            contextual_factors={
                "domain_expertise_level": 0.8,
                "task_complexity_adjustment": 0.9,
                "environmental_stability": 0.85
            },
            overall_confidence=0.5  # Will be recalculated
        )
        
        composite = calibrator.calculate_composite_confidence(metrics)
        
        assert 0.0 <= composite <= 1.0
        assert composite > 0.5  # Should be higher given good metrics
    
    def test_update_confidence_with_evidence(self):
        """Test updating confidence metrics with new evidence."""
        calibrator = ConfidenceCalibrator()
        
        metrics = ConfidenceMetrics(overall_confidence=0.7)
        
        evidence = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="terminal",
            success_metrics={"success": True}
        )
        
        updated = calibrator.update_confidence_with_evidence(metrics, evidence, 0.8)
        
        assert updated.overall_confidence != metrics.overall_confidence
        assert 0.0 <= updated.overall_confidence <= 1.0


class TestConfidenceCalibratorCalibration:
    """Test calibration validation and tracking."""
    
    def test_track_calibration_error(self):
        """Test tracking calibration error."""
        calibrator = ConfidenceCalibrator()
        
        predicted_confidence = 0.8
        actual_outcome = True  # Knowledge was correct
        
        error = calibrator.track_calibration_error(predicted_confidence, actual_outcome)
        
        assert error >= 0.0
        # If prediction was accurate, error should be low
        if actual_outcome:
            assert error < 0.2
    
    def test_get_calibration_curve(self):
        """Test getting calibration curve."""
        calibrator = ConfidenceCalibrator()
        
        # Add some calibration data
        for i in range(10):
            confidence = i / 10.0
            outcome = i >= 5  # Higher confidence = more likely correct
            calibrator.track_calibration_error(confidence, outcome)
        
        curve = calibrator.get_calibration_curve()
        
        assert isinstance(curve, dict)
        assert len(curve) > 0

