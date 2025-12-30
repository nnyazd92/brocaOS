"""
Epistemic bridge for integrating epistemic self-modeling with internal sensing.

Provides unified interface between MetacognitiveEngine and InternalSensingFramework,
enabling bidirectional flow of uncertainty, confidence, and source reliability metrics.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from .data_quality import (
    DataQuality,
    uncertainty_for_missing_data,
    confidence_for_missing_data,
    assess_data_quality,
    create_metric_with_quality,
    propagate_uncertainty,
)

logger = logging.getLogger(__name__)


class EpistemicBridge:
    """
    Bridge between epistemic self-modeling and internal sensing.
    
    Aggregates epistemic metrics (uncertainty, confidence, source reliability)
    into formats usable by internal sensing, and feeds internal sensing insights
    back to the epistemic engine.
    """
    
    def __init__(self, epistemic_engine: Optional[Any] = None) -> None:
        """
        Initialize epistemic bridge.
        
        Args:
            epistemic_engine: Optional MetacognitiveEngine instance
        """
        self.epistemic_engine = epistemic_engine
        self._recent_knowledge_items: Dict[str, Dict[str, Any]] = {}
        self._aggregated_uncertainty_cache: Optional[Dict[str, float]] = None
        self._aggregated_confidence_cache: Optional[float] = None
        
        logger.info("Initialized EpistemicBridge" + (" with epistemic engine" if epistemic_engine else " (no epistemic engine)"))
    
    def get_aggregated_uncertainty(self, 
                                   recent_knowledge_count: int = 20) -> Dict[str, float]:
        """
        Get aggregated uncertainty metrics from epistemic engine.
        
        Args:
            recent_knowledge_count: Number of recent knowledge items to aggregate
            
        Returns:
            Dictionary with aggregated uncertainty breakdown:
            - epistemic: Average epistemic uncertainty
            - aleatoric: Average aleatoric uncertainty
            - model: Average model uncertainty
            - total: Average total uncertainty
            - knowledge_gaps: Uncertainty from knowledge gaps
            - ambiguity: Uncertainty from ambiguity
            - noise: Uncertainty from noise
        """
        if not self.epistemic_engine:
            # Missing epistemic engine should return explicit "missing" uncertainty
            # rather than zeros (zeros look like "perfect certainty" and pollute downstream).
            return self._get_default_uncertainty()
        
        try:
            # Get recent knowledge items from epistemic layer
            epistemic_layer = self.epistemic_engine.epistemic_layer
            
            # Get knowledge IDs from knowledge_sources dict (all tracked knowledge)
            knowledge_ids = list(epistemic_layer.knowledge_sources.keys())
            if not knowledge_ids:
                return self._get_default_uncertainty()
            
            # Get recent knowledge items (limit to recent_knowledge_count)
            recent_ids = knowledge_ids[-recent_knowledge_count:]
            
            uncertainties = {
                "epistemic": [],
                "aleatoric": [],
                "model": [],
                "total": [],
            }
            
            source_breakdown = {
                "knowledge_gaps": [],
                "ambiguity": [],
                "noise": [],
            }
            
            for knowledge_id in recent_ids:
                try:
                    # Get epistemic context
                    context = self.epistemic_engine.get_epistemic_context(knowledge_id)
                    uncertainty = context.get("uncertainty", {})
                    
                    if uncertainty:
                        uncertainties["epistemic"].append(uncertainty.get("epistemic", 0.0))
                        uncertainties["aleatoric"].append(uncertainty.get("aleatoric", 0.0))
                        uncertainties["model"].append(uncertainty.get("model", 0.0))
                        uncertainties["total"].append(uncertainty.get("total", 0.0))
                    
                    # Estimate uncertainty sources from confidence metrics
                    metrics = context.get("confidence_metrics")
                    if metrics:
                        overall_conf = metrics.get("overall_confidence", 0.5)
                        # Knowledge gaps: inversely related to confidence and source count
                        source_count = context.get("verification_count", 0) + 1
                        knowledge_gaps = (1.0 - overall_conf) * (1.0 / max(source_count, 1))
                        source_breakdown["knowledge_gaps"].append(knowledge_gaps)
                        
                        # Ambiguity: related to contradictory evidence
                        cross_val = metrics.get("cross_validation", {})
                        contradictions = cross_val.get("contradictory_evidence_count", 0)
                        ambiguity = min(1.0, contradictions * 0.2)
                        source_breakdown["ambiguity"].append(ambiguity)
                        
                        # Noise: related to calibration error
                        calibration_error = metrics.get("confidence_calibration_error", 0.0)
                        noise = min(1.0, calibration_error * 2.0)
                        source_breakdown["noise"].append(noise)
                        
                except Exception as e:
                    logger.debug(f"Error getting uncertainty for {knowledge_id}: {e}")
                    continue
            
            # Calculate averages with data quality tracking
            aggregated = {}
            total_samples = len(recent_ids)
            
            for key, values in uncertainties.items():
                if values:
                    aggregated[key] = sum(values) / len(values)
                else:
                    # Missing data: use high uncertainty
                    aggregated[key] = uncertainty_for_missing_data()
            
            for key, values in source_breakdown.items():
                if values:
                    aggregated[key] = sum(values) / len(values)
                else:
                    # Missing data: use high uncertainty
                    aggregated[key] = uncertainty_for_missing_data()
            
            # Add data quality metadata
            data_quality = assess_data_quality(total_samples)
            aggregated["data_quality"] = data_quality.value
            aggregated["sample_size"] = total_samples
            aggregated["has_data"] = total_samples > 0
            
            # Cache result
            self._aggregated_uncertainty_cache = aggregated
            
            return aggregated
            
        except Exception as e:
            logger.warning(f"Error aggregating epistemic uncertainty: {e}", exc_info=True)
            return self._get_default_uncertainty()
    
    def _get_default_uncertainty(self) -> Dict[str, Any]:
        """
        Return high uncertainty values when data is missing.
        
        Uses high uncertainty (0.9) to indicate missing data rather than
        neutral defaults that could be mistaken for real measurements.
        """
        missing_uncertainty = uncertainty_for_missing_data()
        return {
            "epistemic": missing_uncertainty,
            "aleatoric": missing_uncertainty * 0.3,  # Some aleatoric uncertainty even when missing
            "model": missing_uncertainty * 0.5,  # Model uncertainty when no data
            "total": missing_uncertainty,
            "knowledge_gaps": missing_uncertainty,
            "ambiguity": missing_uncertainty * 0.7,
            "noise": missing_uncertainty * 0.2,
            "data_quality": DataQuality.MISSING.value,
            "sample_size": 0,
            "has_data": False,
        }
    
    def get_aggregated_confidence(self, 
                                 recent_knowledge_count: int = 20) -> Dict[str, Any]:
        """
        Get aggregated confidence metrics from epistemic engine.
        
        Args:
            recent_knowledge_count: Number of recent knowledge items to aggregate
            
        Returns:
            Dictionary with aggregated confidence metrics:
            - overall_confidence: Average overall confidence
            - calibration_error: Average calibration error
            - ece: Expected Calibration Error (if available)
            - brier_score: Brier score (if available)
            - reliability: Overall reliability
        """
        if not self.epistemic_engine:
            # No epistemic engine: return high uncertainty with wide confidence interval
            conf_mean, conf_interval = confidence_for_missing_data()
            return {
                "overall_confidence": conf_mean,
                "confidence_interval": conf_interval,
                "calibration_error": None,  # Cannot compute without data
                "ece": None,
                "brier_score": None,
                "reliability": None,  # Cannot compute without data
                "data_quality": DataQuality.MISSING.value,
                "sample_size": 0,
                "has_data": False,
                "uncertainty": uncertainty_for_missing_data(),
            }
        
        try:
            # Get recent knowledge items from epistemic layer
            epistemic_layer = self.epistemic_engine.epistemic_layer
            
            # Get knowledge IDs from knowledge_sources dict (all tracked knowledge)
            knowledge_ids = list(epistemic_layer.knowledge_sources.keys())
            if not knowledge_ids:
                return self._get_default_confidence()
            
            recent_ids = knowledge_ids[-recent_knowledge_count:]
            
            confidences = []
            calibration_errors = []
            
            for knowledge_id in recent_ids:
                try:
                    context = self.epistemic_engine.get_epistemic_context(knowledge_id)
                    metrics = context.get("confidence_metrics")
                    
                    if metrics:
                        conf = metrics.get("overall_confidence")
                        if conf is not None:
                            confidences.append(conf)
                        cal_err = metrics.get("confidence_calibration_error")
                        if cal_err is not None:
                            calibration_errors.append(cal_err)
                        
                except Exception as e:
                    logger.debug(f"Error getting confidence for {knowledge_id}: {e}")
                    continue
            
            sample_size = len(confidences)
            data_quality = assess_data_quality(sample_size)
            
            # Use Bayesian prior if insufficient data
            if sample_size == 0:
                return self._get_default_confidence()
            
            # Calculate averages with uncertainty propagation
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                # Calculate confidence interval based on sample size
                from .data_quality import wilson_score_interval
                # Convert confidence to success rate for interval calculation
                # Use average as point estimate
                std_dev = (sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)) ** 0.5 if len(confidences) > 1 else 0.1
                # Approximate confidence interval
                z_score = 1.96  # 95% confidence
                margin = z_score * std_dev / (len(confidences) ** 0.5) if len(confidences) > 1 else 0.4
                conf_interval = (max(0.0, avg_confidence - margin), min(1.0, avg_confidence + margin))
            else:
                # Fallback to prior
                avg_confidence, conf_interval = confidence_for_missing_data()
            
            if calibration_errors:
                avg_calibration_error = sum(calibration_errors) / len(calibration_errors)
            else:
                avg_calibration_error = None
            
            # Get calibration metrics from calibrator if available
            ece = None
            brier_score = None
            if hasattr(self.epistemic_engine, 'calibrator'):
                calibrator = self.epistemic_engine.calibrator
                # Try to get calibration curve (which includes ECE calculation)
                # Note: This would need to be implemented in ConfidenceCalibrator
                # For now, use average calibration error as proxy
            
            # Calculate uncertainty from confidence interval width
            interval_width = conf_interval[1] - conf_interval[0]
            uncertainty = min(1.0, interval_width)
            
            aggregated = {
                "overall_confidence": avg_confidence,
                "confidence_interval": conf_interval,
                "calibration_error": avg_calibration_error,
                "ece": ece,
                "brier_score": brier_score,
                "reliability": 1.0 - avg_calibration_error if avg_calibration_error is not None else None,
                "data_quality": data_quality.value,
                "sample_size": sample_size,
                "has_data": sample_size > 0,
                "uncertainty": uncertainty,
            }
            
            # Cache result
            self._aggregated_confidence_cache = aggregated
            
            return aggregated
            
        except Exception as e:
            logger.warning(f"Error aggregating epistemic confidence: {e}", exc_info=True)
            return self._get_default_confidence()
    
    def _get_default_confidence(self) -> Dict[str, Any]:
        """
        Return high uncertainty confidence values when data is missing.
        
        Uses uniform prior (Beta(1,1)) which gives mean 0.5 with wide
        confidence interval to indicate missing data.
        """
        conf_mean, conf_interval = confidence_for_missing_data()
        interval_width = conf_interval[1] - conf_interval[0]
        uncertainty = min(1.0, interval_width)
        
        return {
            "overall_confidence": conf_mean,
            "confidence_interval": conf_interval,
            "calibration_error": None,  # Cannot compute without data
            "ece": None,
            "brier_score": None,
            "reliability": None,  # Cannot compute without data
            "data_quality": DataQuality.MISSING.value,
            "sample_size": 0,
            "has_data": False,
            "uncertainty": uncertainty,
        }
    
    def get_source_reliability(self, source_type: Optional[str] = None) -> Dict[str, float]:
        """
        Get source reliability scores from epistemic validator.
        
        Args:
            source_type: Optional source type to filter by (e.g., "tool", "memory")
            
        Returns:
            Dictionary mapping source identifiers to reliability scores (0.0-1.0)
        """
        if not self.epistemic_engine or not hasattr(self.epistemic_engine, 'validator'):
            return {}
        
        try:
            validator = self.epistemic_engine.validator
            reliability_scores = {}
            
            # Get tool reliability scores
            if hasattr(validator, '_tool_executions'):
                for tool_type, executions in validator._tool_executions.items():
                    if source_type is None or source_type == "tool":
                        reliability = validator.assess_tool_reliability(tool_type)
                        reliability_scores[f"tool:{tool_type}"] = reliability
            
            # Get memory quality scores
            if hasattr(validator, '_memory_retrievals'):
                for memory_id, retrievals in validator._memory_retrievals.items():
                    if source_type is None or source_type == "memory":
                        quality = validator.assess_memory_quality(memory_id)
                        reliability_scores[f"memory:{memory_id}"] = quality
            
            return reliability_scores
            
        except Exception as e:
            logger.warning(f"Error getting source reliability: {e}", exc_info=True)
            return {}
    
    def get_tool_reliability(self, tool_name: str) -> Optional[float]:
        """
        Get reliability score for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Reliability score (0.0-1.0) or None if unavailable
        """
        if not self.epistemic_engine or not hasattr(self.epistemic_engine, 'validator'):
            return None
        
        try:
            return self.epistemic_engine.validator.assess_tool_reliability(tool_name)
        except Exception as e:
            logger.debug(f"Error getting tool reliability for {tool_name}: {e}")
            return None
    
    def get_information_gain(self, knowledge_items: Optional[Dict[str, Dict[str, Any]]] = None) -> float:
        """
        Calculate information gain from epistemic uncertainty manager.
        
        Args:
            knowledge_items: Optional knowledge items dict (if None, uses recent items)
            
        Returns:
            Information gain score (0.0-1.0)
        """
        # Delegate to metadata-returning method to avoid hard-coded placeholder inputs.
        info = self.get_information_gain_info(knowledge_items)
        try:
            return max(0.0, min(1.0, float(info.get("value", 0.0))))
        except Exception:
            return 0.0

    def get_information_gain_info(self, knowledge_items: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Information gain with metadata to avoid silent placeholders.

        Returns:
            Dict with:
            - value: float in [0,1]
            - has_data: bool
            - sample_size: int
            - estimator: str ("measured" | "missing_engine" | "error" | "estimated_inputs")
        """
        if not self.epistemic_engine or not hasattr(self.epistemic_engine, 'uncertainty_manager'):
            return {"value": 0.0, "has_data": False, "sample_size": 0, "estimator": "missing_engine"}

        try:
            # If caller doesn't supply, attempt to build from recent knowledge items
            estimated_inputs = False
            if knowledge_items is None:
                epistemic_layer = self.epistemic_engine.epistemic_layer
                knowledge_ids = list(epistemic_layer.knowledge_sources.keys())
                knowledge_items = {}
                for kid in knowledge_ids[-20:]:
                    try:
                        context = self.epistemic_engine.get_epistemic_context(kid)
                        metrics = context.get("confidence_metrics", {})
                        conf_val = metrics.get("overall_confidence") if metrics else None
                        if conf_val is None:
                            conf_mean, _interval = confidence_for_missing_data()
                            conf_val = conf_mean
                            estimated_inputs = True

                        # importance/usage_frequency are currently not tracked in epistemic layer;
                        # keep conservative defaults but mark as estimated inputs.
                        knowledge_items[kid] = {
                            "confidence": float(conf_val),
                            "importance": 0.25,
                            "usage_frequency": 0.0,
                        }
                        estimated_inputs = True
                    except Exception:
                        continue

            if not knowledge_items:
                return {"value": 0.0, "has_data": False, "sample_size": 0, "estimator": "measured"}

            uncertainty_manager = self.epistemic_engine.uncertainty_manager
            gains = uncertainty_manager.information_gain_calculation(knowledge_items)

            if gains:
                avg_gain = sum(gain for _, gain in gains) / len(gains)
                return {
                    "value": min(1.0, float(avg_gain)),
                    "has_data": True,
                    "sample_size": len(gains),
                    "estimator": "estimated_inputs" if estimated_inputs else "measured",
                }

            return {"value": 0.0, "has_data": False, "sample_size": 0, "estimator": "measured"}
        except Exception as e:
            logger.debug(f"Error calculating information gain (info): {e}", exc_info=True)
            return {"value": 0.0, "has_data": False, "sample_size": 0, "estimator": "error"}
    
    def update_from_epistemic(self, 
                              cognitive_monitor: Any,
                              affective_monitor: Any) -> None:
        """
        Update internal sensing monitors from epistemic engine state.
        
        Args:
            cognitive_monitor: CognitiveStateMonitor instance
            affective_monitor: ComputationalAffectMonitor instance
        """
        if not self.epistemic_engine:
            return
        
        try:
            # Get aggregated uncertainty
            uncertainty = self.get_aggregated_uncertainty()
            
            # Update cognitive monitor with epistemic uncertainty
            if hasattr(cognitive_monitor, 'record_uncertainty'):
                cognitive_monitor.record_uncertainty(
                    question_id=f"epistemic_aggregate_{int(__import__('time').time())}",
                    uncertainty=uncertainty.get("total", 0.0),
                    epistemic=uncertainty.get("epistemic", 0.0),
                    aleatoric=uncertainty.get("aleatoric", 0.0),
                    knowledge_gaps=uncertainty.get("knowledge_gaps", 0.0),
                    ambiguity=uncertainty.get("ambiguity", 0.0),
                    noise=uncertainty.get("noise", 0.0),
                )
            
            # Get aggregated confidence
            confidence = self.get_aggregated_confidence()
            
            # Update cognitive monitor with epistemic confidence calibration
            if hasattr(cognitive_monitor, '_update_confidence_level'):
                # The _update_confidence_level will use calibration metrics if available
                # We'll set them via a method that accepts calibration data
                if hasattr(cognitive_monitor, 'update_calibration_from_epistemic'):
                    cognitive_monitor.update_calibration_from_epistemic(
                        ece=confidence.get("ece"),
                        brier_score=confidence.get("brier_score"),
                        calibration_error=confidence.get("calibration_error"),
                    )
            
            # Update affective monitor with epistemic metrics
            if hasattr(affective_monitor, 'update_certainty_affect'):
                # Use epistemic confidence for certainty affect
                epistemic_conf = confidence.get("overall_confidence", 0.5)
                calibration_error = confidence.get("calibration_error")
                reliability = confidence.get("reliability")
                
                affective_monitor.update_certainty_affect(
                    confidence=epistemic_conf,
                    calibration_error=calibration_error,
                    confidence_accuracy_correlation=reliability,
                )
            
            # Update curiosity drive with information gain
            if hasattr(affective_monitor, 'compute_curiosity_drive'):
                information_gain = self.get_information_gain()
                # Get current uncertainty for curiosity calculation
                current_uncertainty = uncertainty.get("total", 0.0)
                # Use attention as proxy for interest (would need to get from cognitive)
                interest = 0.5  # Default
                if hasattr(cognitive_monitor, 'states'):
                    attention = cognitive_monitor.states.get("attention_allocation", {})
                    interest = min(1.0, sum(attention.values())) if attention else 0.5
                
                affective_monitor.compute_curiosity_drive(
                    uncertainty=current_uncertainty,
                    interest=interest,
                    information_gain=information_gain,
                )
            
        except Exception as e:
            logger.warning(f"Error updating internal sensing from epistemic: {e}", exc_info=True)
    
    def update_epistemic_from_internal(self,
                                       response_id: str,
                                       confidence: float,
                                       uncertainty: float,
                                       correct: Optional[bool] = None) -> None:
        """
        Feed internal sensing insights back to epistemic engine.
        
        Args:
            response_id: Identifier for the response
            confidence: Confidence level from internal sensing (0.0-1.0)
            uncertainty: Uncertainty level from internal sensing (0.0-1.0)
            correct: Optional correctness indicator for calibration
        """
        if not self.epistemic_engine:
            return
        
        try:
            # Create a knowledge ID for this response
            from ..self_model.epistemic.ids import generate_knowledge_id
            knowledge_id = generate_knowledge_id("internal_sensing", response_id)
            
            # Create source metadata for internal sensing
            from ..self_model.epistemic.models import SourceMetadata, SourceType
            from datetime import datetime, timezone
            
            source = SourceMetadata(
                source_type=SourceType.EMERGENT_PATTERN,
                pattern_type="internal_sensing_confidence",
                timestamp=datetime.now(timezone.utc),
                statistical_significance=confidence,
                predictive_accuracy=1.0 - uncertainty if uncertainty else None,
            )
            
            # Update epistemic engine with internal sensing confidence
            # Use confidence as evidence strength
            self.epistemic_engine.confidence_update_workflow(
                knowledge_id=knowledge_id,
                new_evidence=source,
                evidence_strength=confidence,
            )
            
            # Record outcome if available for calibration
            if correct is not None and hasattr(self.epistemic_engine, 'calibrator'):
                self.epistemic_engine.calibrator.track_calibration_error(
                    predicted_confidence=confidence,
                    actual_outcome=correct,
                )
            
        except Exception as e:
            logger.debug(f"Error updating epistemic from internal sensing: {e}", exc_info=True)
    
    def get_epistemic_valence_context(self) -> Dict[str, float]:
        """
        Get epistemic context for valence calculation.
        
        Returns:
            Dictionary with:
            - tool_success_rate: Average tool success rate
            - memory_consistency: Average memory consistency
            - knowledge_confidence: Average knowledge confidence
        """
        if not self.epistemic_engine:
            return {
                "tool_success_rate": 0.5,
                "memory_consistency": 0.5,
                "knowledge_confidence": 0.5,
            }
        
        try:
            # Get tool reliability scores
            tool_reliabilities = []
            if hasattr(self.epistemic_engine, 'validator'):
                validator = self.epistemic_engine.validator
                if hasattr(validator, '_tool_executions'):
                    for tool_type in validator._tool_executions.keys():
                        reliability = validator.assess_tool_reliability(tool_type)
                        tool_reliabilities.append(reliability)
            
            tool_success_rate = sum(tool_reliabilities) / len(tool_reliabilities) if tool_reliabilities else 0.5
            
            # Get memory consistency
            memory_consistencies = []
            if hasattr(self.epistemic_engine, 'validator'):
                validator = self.epistemic_engine.validator
                if hasattr(validator, '_memory_retrievals'):
                    for memory_id in validator._memory_retrievals.keys():
                        quality = validator.assess_memory_quality(memory_id)
                        memory_consistencies.append(quality)
            
            memory_consistency = sum(memory_consistencies) / len(memory_consistencies) if memory_consistencies else 0.5
            
            # Get average knowledge confidence
            confidence = self.get_aggregated_confidence()
            knowledge_confidence = confidence.get("overall_confidence", 0.5)
            
            return {
                "tool_success_rate": tool_success_rate,
                "memory_consistency": memory_consistency,
                "knowledge_confidence": knowledge_confidence,
            }
            
        except Exception as e:
            logger.debug(f"Error getting epistemic valence context: {e}")
            return {
                "tool_success_rate": 0.5,
                "memory_consistency": 0.5,
                "knowledge_confidence": 0.5,
            }

