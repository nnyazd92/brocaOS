"""
ConfidenceCalibrator for calculating and updating confidence scores.

Implements Bayesian updating, frequentist calibration, ensemble weighting,
and temporal discounting methods.
"""

from __future__ import annotations

import math
from typing import Dict, Any, List
from collections import defaultdict
import logging

from .models import ConfidenceMetrics, SourceMetadata, SourceType

logger = logging.getLogger(__name__)


class ConfidenceCalibrator:
    """
    Calibrates confidence scores using multiple methods.
    
    Provides:
    - Bayesian updating: Update confidence based on evidence
    - Frequentist calibration: Calibrate based on success rates
    - Ensemble weighting: Combine multiple confidence sources
    - Temporal discounting: Adjust confidence based on age of evidence
    """
    
    def __init__(self) -> None:
        """Initialize confidence calibrator."""
        # Track calibration errors for validation
        self._calibration_data: List[Dict[str, Any]] = []
    
    def bayesian_updating(
        self,
        prior: float,
        evidence_strength: float,
        prior_weight: float = 0.5
    ) -> float:
        """
        Update confidence using Bayesian updating.
        
        Uses a simplified Bayesian approach where:
        posterior = (prior * prior_weight + evidence * (1 - prior_weight)) / normalization
        
        Args:
            prior: Prior confidence (0-1)
            evidence_strength: Strength of new evidence (0-1)
            prior_weight: Weight given to prior vs evidence (0-1)
            
        Returns:
            Updated confidence (0-1)
        """
        # Ensure inputs are in valid range
        prior = max(0.0, min(1.0, prior))
        evidence_strength = max(0.0, min(1.0, evidence_strength))
        prior_weight = max(0.0, min(1.0, prior_weight))
        
        # Weighted average with normalization
        # If evidence is strong (high), increase confidence
        # If evidence is weak (low), decrease confidence
        evidence_weight = 1.0 - prior_weight
        
        # Calculate posterior
        posterior = (prior * prior_weight + evidence_strength * evidence_weight)
        
        # Normalize to ensure we stay in [0, 1]
        posterior = max(0.0, min(1.0, posterior))
        
        return posterior
    
    def frequentist_calibration(
        self,
        success_rate: float,
        sample_size: int,
        prior_belief: float = 0.5
    ) -> float:
        """
        Calibrate confidence using frequentist approach.
        
        Adjusts confidence based on success rate and sample size.
        Larger samples provide more reliable estimates.
        
        Args:
            success_rate: Observed success rate (0-1)
            sample_size: Number of observations
            prior_belief: Prior belief before observations (0-1)
            
        Returns:
            Calibrated confidence (0-1)
        """
        if sample_size <= 0:
            return prior_belief
        
        # Use Bayesian approach with uniform prior
        # As sample size increases, we trust the observed rate more
        # For small samples, we shrink toward prior
        
        # Effective sample size for prior (controls shrinkage)
        prior_sample_size = 10
        
        # Calculate weighted average
        total_samples = sample_size + prior_sample_size
        weighted_success = (success_rate * sample_size + prior_belief * prior_sample_size)
        
        calibrated = weighted_success / total_samples
        
        # Adjust for sample size uncertainty
        # Smaller samples have more uncertainty
        uncertainty_factor = 1.0 / (1.0 + math.sqrt(sample_size))
        calibrated = calibrated * (1.0 - uncertainty_factor * 0.1) + prior_belief * (uncertainty_factor * 0.1)
        
        return max(0.0, min(1.0, calibrated))
    
    def ensemble_weighting(
        self,
        sources: List[Dict[str, float]]
    ) -> float:
        """
        Combine multiple confidence sources using weighted average.
        
        Args:
            sources: List of dicts with "confidence" and "weight" keys
            
        Returns:
            Weighted average confidence (0-1)
        """
        if not sources:
            return 0.5  # Default if no sources
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for source in sources:
            confidence = max(0.0, min(1.0, source.get("confidence", 0.5)))
            weight = max(0.0, source.get("weight", 1.0))
            
            weighted_sum += confidence * weight
            total_weight += weight
        
        if total_weight == 0.0:
            return 0.5
        
        return max(0.0, min(1.0, weighted_sum / total_weight))
    
    def temporal_discounting(
        self,
        confidence: float,
        age_hours: float,
        half_life_hours: float = 720.0  # 30 days default
    ) -> float:
        """
        Discount confidence based on age of evidence.
        
        Uses exponential decay: confidence * exp(-age / half_life)
        
        Args:
            confidence: Original confidence (0-1)
            age_hours: Age of evidence in hours
            half_life_hours: Hours for confidence to decay to half (default: 30 days)
            
        Returns:
            Discounted confidence (0-1)
        """
        if age_hours <= 0:
            return confidence
        
        if half_life_hours <= 0:
            return confidence
        
        # Exponential decay
        decay_factor = math.exp(-age_hours / half_life_hours)
        
        # Discount toward a minimum (don't go to zero)
        min_confidence = 0.1
        discounted = confidence * decay_factor + min_confidence * (1.0 - decay_factor)
        
        return max(0.0, min(1.0, discounted))
    
    def calculate_composite_confidence(self, metrics: ConfidenceMetrics) -> float:
        """
        Calculate composite confidence from multi-dimensional metrics.
        
        Combines source reliability, temporal stability, cross-validation,
        and contextual factors into overall confidence.
        
        Args:
            metrics: ConfidenceMetrics instance
            
        Returns:
            Composite confidence score (0-1)
        """
        # Weight different dimensions
        source_weight = 0.4
        temporal_weight = 0.2
        cross_validation_weight = 0.3
        contextual_weight = 0.1
        
        # Source reliability (average of scores)
        source_scores = metrics.source_reliability.values()
        source_avg = sum(source_scores) / len(source_scores) if source_scores else 0.5
        
        # Check if all source reliability scores are zero (initialization case)
        all_zeros = all(score == 0.0 for score in source_scores) if source_scores else True
        
        # Temporal stability (weighted by consistency)
        temporal_consistency = metrics.temporal_stability.get("consistency_over_time", 0.5)
        temporal_age_hours = metrics.temporal_stability.get("last_verification_age_hours", float("inf"))
        
        # Discount by age
        temporal_score = temporal_consistency
        if temporal_age_hours < float("inf"):
            temporal_score = self.temporal_discounting(temporal_consistency, temporal_age_hours)
        
        # Cross-validation (consensus strength, adjusted by contradictory evidence)
        consensus = metrics.cross_validation.get("consensus_strength", 0.5)
        contradictions = metrics.cross_validation.get("contradictory_evidence_count", 0)
        
        # Reduce confidence if there are contradictions
        contradiction_penalty = min(0.3, contradictions * 0.1)
        cross_validation_score = consensus * (1.0 - contradiction_penalty)
        
        # Contextual factors (average)
        contextual_scores = metrics.contextual_factors.values()
        contextual_avg = sum(contextual_scores) / len(contextual_scores) if contextual_scores else 0.5
        
        # Weighted combination
        composite = (
            source_avg * source_weight +
            temporal_score * temporal_weight +
            cross_validation_score * cross_validation_weight +
            contextual_avg * contextual_weight
        )
        
        # If all source reliability scores are zero and we have an existing overall_confidence,
        # blend the calculated composite with the existing confidence to preserve initial values
        if all_zeros and metrics.overall_confidence > 0.0:
            # Use 70% existing confidence, 30% calculated composite
            # This preserves initial confidence while allowing gradual updates
            composite = metrics.overall_confidence * 0.7 + composite * 0.3
        elif metrics.overall_confidence > composite * 1.5:
            # If existing confidence is significantly higher than calculated, preserve it more
            # This handles initialization cases where we set a high initial confidence
            composite = metrics.overall_confidence * 0.8 + composite * 0.2
        
        return max(0.0, min(1.0, composite))
    
    def update_confidence_with_evidence(
        self,
        current_metrics: ConfidenceMetrics,
        evidence: SourceMetadata,
        evidence_strength: float
    ) -> ConfidenceMetrics:
        """
        Update confidence metrics with new evidence.
        
        Args:
            current_metrics: Current confidence metrics
            evidence: New evidence source
            evidence_strength: Strength of evidence (0-1)
            
        Returns:
            Updated ConfidenceMetrics
        """
        # Create updated metrics
        updated = ConfidenceMetrics(
            source_reliability=current_metrics.source_reliability.copy(),
            temporal_stability=current_metrics.temporal_stability.copy(),
            cross_validation=current_metrics.cross_validation.copy(),
            contextual_factors=current_metrics.contextual_factors.copy(),
            overall_confidence=current_metrics.overall_confidence,
            confidence_calibration_error=current_metrics.confidence_calibration_error
        )
        
        # Update based on source type
        # Use evidence_strength for overall confidence update when source-specific fields aren't available
        source_specific_update = False
        
        if evidence.source_type == SourceType.TOOL_MEDIATED_VERIFICATION:
            # Update tool verification score
            tool_score = evidence.success_metrics.get("success", False) if evidence.success_metrics else False
            if tool_score:
                updated.source_reliability["tool_verification_score"] = self.bayesian_updating(
                    updated.source_reliability["tool_verification_score"],
                    evidence_strength
                )
                source_specific_update = True
            else:
                # Use evidence_strength directly if no success metrics
                updated.source_reliability["tool_verification_score"] = self.bayesian_updating(
                    updated.source_reliability["tool_verification_score"],
                    evidence_strength
                )
                source_specific_update = True
        elif evidence.source_type == SourceType.MEMORY_RETRIEVAL:
            # Update memory consistency score
            if evidence.retrieval_confidence is not None:
                updated.source_reliability["memory_consistency_score"] = self.bayesian_updating(
                    updated.source_reliability["memory_consistency_score"],
                    evidence.retrieval_confidence
                )
                source_specific_update = True
            else:
                # Use evidence_strength if retrieval_confidence not provided
                updated.source_reliability["memory_consistency_score"] = self.bayesian_updating(
                    updated.source_reliability["memory_consistency_score"],
                    evidence_strength
                )
                source_specific_update = True
        elif evidence.source_type == SourceType.LOGICAL_INFERENCE:
            # Update logical validity score
            if evidence.logical_strength is not None:
                updated.source_reliability["logical_validity_score"] = self.bayesian_updating(
                    updated.source_reliability["logical_validity_score"],
                    evidence.logical_strength
                )
                source_specific_update = True
            else:
                # Use evidence_strength if logical_strength not provided
                updated.source_reliability["logical_validity_score"] = self.bayesian_updating(
                    updated.source_reliability["logical_validity_score"],
                    evidence_strength
                )
                source_specific_update = True
        elif evidence.source_type == SourceType.USER_PROVIDED:
            # Update user credibility score
            updated.source_reliability["user_credibility_score"] = self.bayesian_updating(
                updated.source_reliability["user_credibility_score"],
                evidence_strength
            )
            source_specific_update = True
        elif evidence.source_type == SourceType.EXTERNAL_SOURCE:
            # For external sources, update tool verification score as fallback
            updated.source_reliability["tool_verification_score"] = self.bayesian_updating(
                updated.source_reliability["tool_verification_score"],
                evidence_strength
            )
            source_specific_update = True
        
        # Update overall confidence
        # If source-specific update happened, recalculate composite
        # Otherwise, use Bayesian updating directly on overall confidence
        if source_specific_update:
            calculated_composite = self.calculate_composite_confidence(updated)
            # For contradictions (low evidence_strength < 0.5), ensure confidence decreases
            # For confirmations (high evidence_strength >= 0.5), allow increase
            if evidence_strength < 0.5:
                # Contradiction: use Bayesian updating to decrease confidence
                # Use (1 - evidence_strength) as the signal to decrease
                updated.overall_confidence = self.bayesian_updating(
                    current_metrics.overall_confidence,
                    1.0 - evidence_strength,  # Invert: low evidence_strength -> high decrease signal
                    prior_weight=0.7  # Give more weight to prior to ensure decrease
                )
                # Ensure it actually decreased
                if updated.overall_confidence >= current_metrics.overall_confidence:
                    # Force decrease by using a lower value
                    updated.overall_confidence = current_metrics.overall_confidence * (1.0 - (0.5 - evidence_strength))
            else:
                # Confirmation: use calculated composite or Bayesian update, whichever is higher
                bayesian_updated = self.bayesian_updating(
                    current_metrics.overall_confidence,
                    evidence_strength,
                    prior_weight=0.6
                )
                updated.overall_confidence = max(calculated_composite, bayesian_updated)
        else:
            # Fallback: update overall confidence directly using evidence_strength
            if evidence_strength < 0.5:
                # Contradiction: decrease confidence
                updated.overall_confidence = self.bayesian_updating(
                    current_metrics.overall_confidence,
                    1.0 - evidence_strength,
                    prior_weight=0.7
                )
                # Ensure it decreased
                if updated.overall_confidence >= current_metrics.overall_confidence:
                    updated.overall_confidence = current_metrics.overall_confidence * (1.0 - (0.5 - evidence_strength))
            else:
                # Confirmation: increase confidence
                updated.overall_confidence = self.bayesian_updating(
                    current_metrics.overall_confidence,
                    evidence_strength,
                    prior_weight=0.6
                )
        
        return updated
    
    def track_calibration_error(
        self,
        predicted_confidence: float,
        actual_outcome: bool
    ) -> float:
        """
        Track calibration error (difference between predicted and actual).
        
        Args:
            predicted_confidence: Predicted confidence (0-1)
            actual_outcome: Whether knowledge was actually correct
            
        Returns:
            Calibration error (0-1)
        """
        actual_confidence = 1.0 if actual_outcome else 0.0
        error = abs(predicted_confidence - actual_confidence)
        
        # Store for calibration curve
        self._calibration_data.append({
            "predicted": predicted_confidence,
            "actual": actual_confidence,
            "error": error
        })
        
        return error
    
    def get_calibration_curve(self, bins: int = 10) -> Dict[str, Any]:
        """
        Get calibration curve showing predicted vs actual confidence.
        
        Args:
            bins: Number of bins for calibration curve
            
        Returns:
            Dictionary with calibration curve data
        """
        if not self._calibration_data:
            return {}
        
        # Bin predictions
        bin_counts = defaultdict(lambda: {"predicted_sum": 0.0, "actual_sum": 0.0, "count": 0})
        
        for data in self._calibration_data:
            predicted = data["predicted"]
            actual = data["actual"]
            
            # Determine bin
            bin_idx = min(int(predicted * bins), bins - 1)
            bin_key = f"bin_{bin_idx}"
            
            bin_counts[bin_key]["predicted_sum"] += predicted
            bin_counts[bin_key]["actual_sum"] += actual
            bin_counts[bin_key]["count"] += 1
        
        # Calculate averages per bin
        curve = {}
        for bin_key, counts in bin_counts.items():
            if counts["count"] > 0:
                curve[bin_key] = {
                    "predicted_avg": counts["predicted_sum"] / counts["count"],
                    "actual_avg": counts["actual_sum"] / counts["count"],
                    "count": counts["count"]
                }
        
        return curve

