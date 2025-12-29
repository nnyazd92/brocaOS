"""
Cognitive state monitoring for internal sensing.

Monitors cognitive states including confidence, coherence, attention,
processing depth, and uncertainty.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional, Union
from collections import deque, defaultdict
from .response_analyzer import ResponseAnalyzer

# Import data quality utilities
try:
    from .data_quality import (
        DataQuality,
        assess_data_quality,
        uncertainty_for_missing_data,
        confidence_for_missing_data,
        create_metric_with_quality,
    )
    HAS_DATA_QUALITY = True
except ImportError:
    HAS_DATA_QUALITY = False

logger = logging.getLogger(__name__)


class CognitiveStateMonitor:
    """
    Monitor cognitive states.
    
    Tracks:
    - Confidence level: Certainty in responses
    - Conceptual coherence: Logical consistency
    - Attention allocation: Focus distribution
    - Processing depth: Depth of analysis
    - Uncertainty tracking: Awareness of unknowns
    """
    
    def __init__(self, history_window: int = 60) -> None:
        """
        Initialize cognitive state monitor.
        
        Args:
            history_window: Number of samples to keep in history
        """
        self.states: Dict[str, Any] = {
            "confidence_level": 0.5,  # Default moderate confidence
            "confidence_calibration": {
                "ece": None,  # Expected Calibration Error
                "brier_score": None,  # Brier score
                "reliability": None,  # Overall reliability
            },
            "confidence_intervals": {
                "mean": 0.5,
                "std": 0.0,
                "min": 0.5,
                "max": 0.5,
            },
            "domain_confidence": {},  # Domain-specific confidence
            "meta_confidence": 0.5,  # Confidence in confidence estimates
            "conceptual_coherence": 0.5,  # Default moderate coherence
            "coherence_semantic": None,  # Semantic coherence from embeddings
            "coherence_temporal": 0.5,  # Temporal coherence
            "coherence_local": 0.5,  # Local (step-to-step) coherence
            "coherence_global": 0.5,  # Global (overall) coherence
            "attention_allocation": {},
            "processing_depth": 1.0,  # Default minimal processing depth
            "uncertainty_tracking": 0.0,  # Default no uncertainty
            "uncertainty_epistemic": 0.0,  # Reducible uncertainty
            "uncertainty_aleatoric": 0.0,  # Irreducible uncertainty
            "uncertainty_sources": {
                "knowledge_gaps": 0.0,
                "ambiguity": 0.0,
                "noise": 0.0,
            },
        }
        
        self.history_window = history_window
        self._history: deque = deque(maxlen=history_window)
        self._confidence_history: deque = deque(maxlen=20)
        self._confidence_outcomes: Dict[str, bool] = {}
        self._confidence_by_domain: Dict[str, deque] = {}  # Domain-specific confidence tracking
        self._reasoning_steps: List[Dict[str, Any]] = []
        self._attention_levels: Dict[str, float] = {}
        self._processing_depths: deque = deque(maxlen=20)
        self._uncertainty_history: deque = deque(maxlen=20)
        self._uncertainty_epistemic_history: deque = deque(maxlen=20)
        self._uncertainty_aleatoric_history: deque = deque(maxlen=20)
        self._reasoning_patterns: List[Dict[str, str]] = []
        self._coherence_history: deque = deque(maxlen=20)  # For temporal coherence
        
        # Embedding service for semantic coherence (optional)
        self._embedding_service: Optional[Any] = None
        
        # Epistemic bridge for second-order metacognition (optional)
        self._epistemic_bridge: Optional[Any] = None
        
        # Signal manager for damping (optional)
        self._signal_manager: Optional[Any] = None
        
        # DO NOT initialize moving averages with baseline values
        # This was causing values to get "stuck" at baseline when real values matched baseline
        # Instead, let moving averages build naturally from actual recorded data
        # The state dictionaries still have defaults (0.5, 0.0) which will be used until data is recorded
        
        logger.info("Initialized CognitiveStateMonitor")
    
    def set_embedding_service(self, embedding_service: Optional[Any]) -> None:
        """
        Set embedding service for semantic coherence analysis.
        
        Args:
            embedding_service: Embedding service with generate_embedding method
        """
        self._embedding_service = embedding_service
    
    def set_epistemic_bridge(self, epistemic_bridge: Optional[Any]) -> None:
        """
        Set epistemic bridge for second-order metacognition integration.
        
        Args:
            epistemic_bridge: EpistemicBridge instance
        """
        self._epistemic_bridge = epistemic_bridge
        logger.info("Set epistemic bridge for CognitiveStateMonitor")
    
    def set_signal_manager(self, signal_manager: Optional[Any]) -> None:
        """
        Set signal manager for damping uncertainty signals.
        
        Args:
            signal_manager: SignalManager instance
        """
        self._signal_manager = signal_manager
        logger.info("Set signal manager for CognitiveStateMonitor")
    
    def record_confidence(self, response_id: str, confidence: float) -> None:
        """
        Record confidence level for a response.
        
        Args:
            response_id: Unique identifier for the response
            confidence: Confidence level (0.0-1.0)
        """
        confidence = max(0.0, min(1.0, confidence))
        logger.debug(f"record_confidence called: response_id={response_id}, confidence={confidence:.3f}")
        self._confidence_history.append({
            "response_id": response_id,
            "confidence": confidence,
            "timestamp": time.time(),
        })
        self._update_confidence_level()
    
    def record_confidence_outcome(self, response_id: str, correct: bool) -> None:
        """
        Record the actual outcome for a confidence prediction.
        
        Args:
            response_id: Unique identifier for the response
            correct: Whether the response was correct
        """
        self._confidence_outcomes[response_id] = correct
    
    def _update_confidence_level(self) -> None:
        """Update average confidence level and calibration metrics."""
        # Compute from moving average history (builds naturally from recorded data)
        if len(self._confidence_history) > 0:
            avg = sum(entry["confidence"] for entry in self._confidence_history) / len(self._confidence_history)
            old_value = self.states["confidence_level"]
            self.states["confidence_level"] = avg
            logger.debug(f"Updated confidence_level: {old_value:.3f} -> {avg:.3f} (from {len(self._confidence_history)} samples, moving_avg)")
            
            # Update calibration metrics
            ece = self._calculate_ece()
            brier = self._calculate_brier_score()
            calibration = self._calculate_calibration()
            
            self.states["confidence_calibration"]["ece"] = ece
            self.states["confidence_calibration"]["brier_score"] = brier
            self.states["confidence_calibration"]["reliability"] = calibration
            
            # Update confidence intervals
            self._update_confidence_intervals()
            
            # Update meta-confidence
            self._update_meta_confidence()
            
            # Mark as having high quality data
            if HAS_DATA_QUALITY:
                if "data_quality" not in self.states:
                    self.states["data_quality"] = {}
                # Determine quality based on sample size
                sample_size = len(self._confidence_history)
                if sample_size >= 20:
                    self.states["data_quality"]["confidence_level"] = DataQuality.HIGH.value
                elif sample_size >= 10:
                    self.states["data_quality"]["confidence_level"] = DataQuality.MEDIUM.value
                elif sample_size >= 5:
                    self.states["data_quality"]["confidence_level"] = DataQuality.LOW.value
                else:
                    self.states["data_quality"]["confidence_level"] = DataQuality.INSUFFICIENT.value
        else:
            # No data yet: use prior with high uncertainty instead of default
            if HAS_DATA_QUALITY:
                conf_mean, _ = confidence_for_missing_data()
                self.states["confidence_level"] = conf_mean
                # Mark as having missing data
                if "data_quality" not in self.states:
                    self.states["data_quality"] = {}
                self.states["data_quality"]["confidence_level"] = DataQuality.MISSING.value
            else:
                self.states["confidence_level"] = 0.5
            logger.debug("Confidence level using prior (no history yet)")
    
    def _calculate_average_confidence(self) -> Optional[float]:
        """
        Calculate average confidence from history.
        
        Returns:
            Average confidence level (0.0-1.0), or None if no history available
        """
        if len(self._confidence_history) == 0:
            return None
        
        return sum(entry["confidence"] for entry in self._confidence_history) / len(self._confidence_history)
    
    def _calculate_calibration(self) -> Optional[float]:
        """
        Calculate confidence calibration accuracy.
        
        Returns:
            Calibration score (0.0-1.0), higher = better calibrated, or None if no data available
        """
        if len(self._confidence_history) == 0:
            return None
        
        # Calculate calibration: how well confidence predicts correctness
        calibration_scores = []
        
        for entry in self._confidence_history:
            response_id = entry["response_id"]
            confidence = entry["confidence"]
            
            if response_id in self._confidence_outcomes:
                correct = self._confidence_outcomes[response_id]
                # Perfect calibration: high confidence when correct, low when incorrect
                if correct:
                    # Higher confidence is better when correct
                    score = confidence
                else:
                    # Lower confidence is better when incorrect
                    score = 1.0 - confidence
                
                calibration_scores.append(score)
        
        if len(calibration_scores) == 0:
            return None  # No outcomes recorded yet
        
        return sum(calibration_scores) / len(calibration_scores)
    
    def _calculate_ece(self, n_bins: int = 10, min_samples: int = 10) -> Optional[float]:
        """
        Calculate Expected Calibration Error (ECE).
        
        Args:
            n_bins: Number of bins for calibration calculation
            min_samples: Minimum number of samples required (default: 10)
            
        Returns:
            ECE score (0.0-1.0), lower = better calibrated, or None if insufficient data
        """
        if len(self._confidence_history) == 0:
            return None
        
        # Group predictions into bins
        bins = [[] for _ in range(n_bins)]
        
        for entry in self._confidence_history:
            response_id = entry["response_id"]
            confidence = entry["confidence"]
            
            if response_id in self._confidence_outcomes:
                bin_idx = min(int(confidence * n_bins), n_bins - 1)
                bins[bin_idx].append({
                    "confidence": confidence,
                    "correct": self._confidence_outcomes[response_id]
                })
        
        # Calculate ECE: weighted average of |accuracy - confidence| per bin
        total_samples = sum(len(bin_data) for bin_data in bins)
        if total_samples == 0 or total_samples < min_samples:
            return None  # Insufficient data
        
        ece = 0.0
        for bin_data in bins:
            if len(bin_data) == 0:
                continue
            
            bin_size = len(bin_data)
            bin_weight = bin_size / total_samples
            
            # Average confidence in this bin
            avg_confidence = sum(item["confidence"] for item in bin_data) / bin_size
            
            # Accuracy in this bin
            accuracy = sum(1 for item in bin_data if item["correct"]) / bin_size
            
            # Calibration error for this bin
            bin_error = abs(accuracy - avg_confidence)
            ece += bin_weight * bin_error
        
        return ece
    
    def _calculate_brier_score(self, min_samples: int = 10) -> Optional[float]:
        """
        Calculate Brier score (mean squared error of probability predictions).
        
        Args:
            min_samples: Minimum number of samples required (default: 10)
        
        Returns:
            Brier score (0.0-1.0), lower = better, or None if insufficient data
        """
        if len(self._confidence_history) == 0:
            return None
        
        squared_errors = []
        for entry in self._confidence_history:
            response_id = entry["response_id"]
            confidence = entry["confidence"]
            
            if response_id in self._confidence_outcomes:
                actual = 1.0 if self._confidence_outcomes[response_id] else 0.0
                squared_error = (confidence - actual) ** 2
                squared_errors.append(squared_error)
        
        if len(squared_errors) == 0 or len(squared_errors) < min_samples:
            return None  # Insufficient data
        
        return sum(squared_errors) / len(squared_errors)
    
    def update_calibration_from_epistemic(self,
                                        ece: Optional[float] = None,
                                        brier_score: Optional[float] = None,
                                        calibration_error: Optional[float] = None) -> None:
        """
        Update calibration metrics from epistemic engine.
        
        Args:
            ece: Expected Calibration Error from epistemic engine
            brier_score: Brier score from epistemic engine
            calibration_error: Overall calibration error from epistemic engine
        """
        # If epistemic provides calibration metrics, use them to enhance our own
        if ece is not None:
            # Blend epistemic ECE with our own (weighted average)
            current_ece = self.states["confidence_calibration"]["ece"]
            if current_ece is not None:
                # Weight: 60% epistemic (more reliable), 40% internal
                blended_ece = (ece * 0.6) + (current_ece * 0.4)
                self.states["confidence_calibration"]["ece"] = blended_ece
            else:
                # Use epistemic ECE if we don't have our own
                self.states["confidence_calibration"]["ece"] = ece
        
        if brier_score is not None:
            # Blend epistemic Brier score with our own
            current_brier = self.states["confidence_calibration"]["brier_score"]
            if current_brier is not None:
                blended_brier = (brier_score * 0.6) + (current_brier * 0.4)
                self.states["confidence_calibration"]["brier_score"] = blended_brier
            else:
                self.states["confidence_calibration"]["brier_score"] = brier_score
        
        if calibration_error is not None:
            # Use epistemic calibration error to update reliability
            reliability = 1.0 - min(calibration_error, 1.0)
            current_reliability = self.states["confidence_calibration"]["reliability"]
            if current_reliability is not None:
                # Blend: 60% epistemic, 40% internal
                blended_reliability = (reliability * 0.6) + (current_reliability * 0.4)
                self.states["confidence_calibration"]["reliability"] = blended_reliability
            else:
                self.states["confidence_calibration"]["reliability"] = reliability
    
    def update_from_epistemic(self) -> None:
        """
        Update cognitive state from epistemic engine via bridge.
        
        This method should be called periodically to sync with epistemic metrics.
        """
        if not self._epistemic_bridge:
            return
        
        try:
            # Get aggregated uncertainty from epistemic
            epistemic_uncertainty = self._epistemic_bridge.get_aggregated_uncertainty()
            
            # Update uncertainty tracking with epistemic breakdown
            if epistemic_uncertainty:
                total_uncertainty = epistemic_uncertainty.get("total", 0.0)
                epistemic = epistemic_uncertainty.get("epistemic", 0.0)
                aleatoric = epistemic_uncertainty.get("aleatoric", 0.0)
                knowledge_gaps = epistemic_uncertainty.get("knowledge_gaps", 0.0)
                ambiguity = epistemic_uncertainty.get("ambiguity", 0.0)
                noise = epistemic_uncertainty.get("noise", 0.0)
                
                # Record uncertainty with epistemic breakdown
                question_id = f"epistemic_sync_{int(time.time())}"
                self.record_uncertainty(
                    question_id=question_id,
                    uncertainty=total_uncertainty,
                    epistemic=epistemic,
                    aleatoric=aleatoric,
                    knowledge_gaps=knowledge_gaps,
                    ambiguity=ambiguity,
                    noise=noise,
                )
            
            # Get aggregated confidence from epistemic
            epistemic_confidence = self._epistemic_bridge.get_aggregated_confidence()
            
            # Update calibration metrics from epistemic
            if epistemic_confidence:
                self.update_calibration_from_epistemic(
                    ece=epistemic_confidence.get("ece"),
                    brier_score=epistemic_confidence.get("brier_score"),
                    calibration_error=epistemic_confidence.get("calibration_error"),
                )
                
                # Use epistemic confidence to inform our confidence level
                epistemic_conf = epistemic_confidence.get("overall_confidence")
                if epistemic_conf is not None:
                    # Blend epistemic confidence with our own (weighted average)
                    current_conf = self.states["confidence_level"]
                    blended_conf = (epistemic_conf * 0.3) + (current_conf * 0.7)
                    self.states["confidence_level"] = max(0.0, min(1.0, blended_conf))
            
            # Get source reliability for domain-specific confidence
            source_reliability = self._epistemic_bridge.get_source_reliability()
            if source_reliability:
                # Update domain confidence based on tool reliability
                for source_key, reliability in source_reliability.items():
                    if source_key.startswith("tool:"):
                        domain = source_key.split(":", 1)[1]
                        # Use tool reliability as domain confidence indicator
                        if domain not in self.states["domain_confidence"]:
                            self.states["domain_confidence"][domain] = reliability
                        else:
                            # Blend with existing domain confidence
                            current = self.states["domain_confidence"][domain]
                            self.states["domain_confidence"][domain] = (reliability * 0.4) + (current * 0.6)
            
        except Exception as e:
            logger.warning(f"Error updating from epistemic: {e}", exc_info=True)
    
    def _update_confidence_intervals(self) -> None:
        """Update confidence distribution statistics."""
        if len(self._confidence_history) == 0:
            return
        
        confidences = [entry["confidence"] for entry in self._confidence_history]
        mean_conf = sum(confidences) / len(confidences)
        
        # Calculate standard deviation
        variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
        std_conf = variance ** 0.5
        
        min_conf = min(confidences)
        max_conf = max(confidences)
        
        self.states["confidence_intervals"] = {
            "mean": mean_conf,
            "std": std_conf,
            "min": min_conf,
            "max": max_conf,
        }
    
    def record_confidence_by_domain(self, domain: str, response_id: str, confidence: float) -> None:
        """
        Record confidence for a specific domain.
        
        Args:
            domain: Domain identifier (e.g., "programming", "science")
            response_id: Unique identifier for the response
            confidence: Confidence level (0.0-1.0)
        """
        if domain not in self._confidence_by_domain:
            self._confidence_by_domain[domain] = deque(maxlen=20)
        
        self._confidence_by_domain[domain].append({
            "response_id": response_id,
            "confidence": max(0.0, min(1.0, confidence)),
            "timestamp": time.time(),
        })
        
        # Update domain-specific confidence
        domain_confidences = [entry["confidence"] for entry in self._confidence_by_domain[domain]]
        if len(domain_confidences) > 0:
            self.states["domain_confidence"][domain] = sum(domain_confidences) / len(domain_confidences)
    
    def _update_meta_confidence(self) -> None:
        """Update meta-confidence (confidence in confidence estimates) based on calibration."""
        ece = self._calculate_ece()
        brier = self._calculate_brier_score()
        
        if ece is None or brier is None:
            # Default to moderate meta-confidence if no calibration data
            self.states["meta_confidence"] = 0.5
            return
        
        # Meta-confidence is inverse of calibration errors
        # Lower ECE and Brier = higher meta-confidence
        ece_component = 1.0 - min(ece, 1.0)  # ECE: lower is better
        brier_component = 1.0 - min(brier, 1.0)  # Brier: lower is better
        
        # Weighted combination
        meta_conf = (ece_component * 0.6) + (brier_component * 0.4)
        self.states["meta_confidence"] = max(0.0, min(1.0, meta_conf))
    
    def record_reasoning_step(self, step_id: str, step_data: Dict[str, Any]) -> None:
        """
        Record a reasoning step.
        
        Args:
            step_id: Unique identifier for the step
            step_data: Dictionary containing premise, conclusion, etc.
        """
        self._reasoning_steps.append({
            "step_id": step_id,
            **step_data,
            "timestamp": time.time(),
        })
        # Keep only recent steps
        if len(self._reasoning_steps) > 50:
            self._reasoning_steps = self._reasoning_steps[-50:]
        
        # Update coherence (will use default if insufficient steps)
        self._update_coherence()
    
    
    def _compute_semantic_coherence(self) -> Optional[float]:
        """
        Compute semantic coherence from reasoning steps using embeddings.
        
        Returns:
            Semantic coherence score (0.0-1.0) or None if unavailable
        """
        if not self._embedding_service or len(self._reasoning_steps) < 2:
            return None
        
        try:
            from .response_analyzer import ResponseAnalyzer
            
            # Get embeddings for recent reasoning steps
            step_texts = []
            for step in self._reasoning_steps[-5:]:  # Last 5 steps
                conclusion = step.get("conclusion", "")
                if conclusion:
                    step_texts.append(conclusion)
            
            if len(step_texts) < 2:
                return None
            
            # Compute pairwise similarities
            similarities = []
            embeddings = []
            for text in step_texts:
                try:
                    emb = self._embedding_service.generate_embedding(text)
                    if emb:
                        embeddings.append(emb)
                except Exception:
                    pass
            
            if len(embeddings) < 2:
                return None
            
            # Compute average pairwise similarity
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    distance = ResponseAnalyzer.calculate_semantic_distance(embeddings[i], embeddings[j])
                    similarity = 1.0 - distance  # Convert distance to similarity
                    similarities.append(similarity)
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                return max(0.0, min(1.0, avg_similarity))
            
            return None
        except Exception as e:
            logger.debug(f"Error computing semantic coherence: {e}")
            return None
    
    def _update_coherence(self) -> None:
        """Update conceptual coherence with multi-level and semantic analysis."""
        if len(self._reasoning_steps) < 2:
            # Use default when insufficient reasoning steps
            self.states["conceptual_coherence"] = 0.5
            self.states["coherence_local"] = 0.5
            self.states["coherence_global"] = 0.5
            # Mark as missing data
            if HAS_DATA_QUALITY:
                if "data_quality" not in self.states:
                    self.states["data_quality"] = {}
                self.states["data_quality"]["conceptual_coherence"] = DataQuality.MISSING.value
                self.states["data_quality"]["coherence_local"] = DataQuality.MISSING.value
                self.states["data_quality"]["coherence_global"] = DataQuality.MISSING.value
            return
        
        # 1. Local coherence: step-to-step consistency
        local_coherences = []
        for i in range(len(self._reasoning_steps) - 1):
            step1 = self._reasoning_steps[i]
            step2 = self._reasoning_steps[i + 1]
            
            # Check for contradictions between adjacent steps
            if (step1.get("premise") == step2.get("premise") and
                step1.get("conclusion") != step2.get("conclusion")):
                local_coherences.append(0.0)
            else:
                local_coherences.append(1.0)
        
        local_coherence = sum(local_coherences) / len(local_coherences) if local_coherences else 1.0
        self.states["coherence_local"] = local_coherence
        
        # 2. Global coherence: overall consistency
        contradictions = 0
        total_comparisons = 0
        for i, step1 in enumerate(self._reasoning_steps):
            for step2 in self._reasoning_steps[i+1:]:
                total_comparisons += 1
                if (step1.get("premise") == step2.get("premise") and
                    step1.get("conclusion") != step2.get("conclusion")):
                    contradictions += 1
        
        global_coherence = 1.0 - (contradictions / total_comparisons) if total_comparisons > 0 else 1.0
        self.states["coherence_global"] = global_coherence
        
        # 3. Check for logical reversals
        latest_conclusion = self._reasoning_steps[-1].get("conclusion", "")
        reversal_score = ResponseAnalyzer.detect_logical_reversals(latest_conclusion)
        
        # 4. Semantic coherence (if available)
        semantic_coherence = self._compute_semantic_coherence()
        if semantic_coherence is not None:
            self.states["coherence_semantic"] = semantic_coherence
        
        # 5. Temporal coherence: consistency over time
        current_coherence = (local_coherence * 0.4) + (global_coherence * 0.6)
        self._coherence_history.append(current_coherence)
        if len(self._coherence_history) >= 2:
            # Check variance in coherence over time (lower variance = better temporal coherence)
            coherence_values = list(self._coherence_history)
            mean_coherence = sum(coherence_values) / len(coherence_values)
            variance = sum((c - mean_coherence) ** 2 for c in coherence_values) / len(coherence_values)
            # Temporal coherence is inverse of variance (normalized)
            temporal_coherence = 1.0 - min(variance, 1.0)
            self.states["coherence_temporal"] = max(0.0, min(1.0, temporal_coherence))
        
        # Combine all coherence measures
        base_coherence = (local_coherence * 0.3) + (global_coherence * 0.4)
        
        # Add semantic coherence if available
        if semantic_coherence is not None:
            base_coherence = (base_coherence * 0.7) + (semantic_coherence * 0.3)
        
        # Reduce by reversals
        final_coherence = base_coherence * (1.0 - (reversal_score * 0.5))
        
        self.states["conceptual_coherence"] = max(0.0, min(1.0, final_coherence))
        
        # Mark data quality based on reasoning steps available
        if HAS_DATA_QUALITY:
            if "data_quality" not in self.states:
                self.states["data_quality"] = {}
            step_count = len(self._reasoning_steps)
            if step_count >= 10:
                self.states["data_quality"]["conceptual_coherence"] = DataQuality.HIGH.value
                self.states["data_quality"]["coherence_local"] = DataQuality.HIGH.value
                self.states["data_quality"]["coherence_global"] = DataQuality.HIGH.value
            elif step_count >= 5:
                self.states["data_quality"]["conceptual_coherence"] = DataQuality.MEDIUM.value
                self.states["data_quality"]["coherence_local"] = DataQuality.MEDIUM.value
                self.states["data_quality"]["coherence_global"] = DataQuality.MEDIUM.value
            elif step_count >= 2:
                self.states["data_quality"]["conceptual_coherence"] = DataQuality.LOW.value
                self.states["data_quality"]["coherence_local"] = DataQuality.LOW.value
                self.states["data_quality"]["coherence_global"] = DataQuality.LOW.value

    
    def _calculate_coherence(self) -> Optional[float]:
        """
        Calculate conceptual coherence from reasoning steps.
        
        Returns:
            Coherence score (0.0-1.0), or None if insufficient data
        """
        return self.states["conceptual_coherence"]
    
    def record_attention(self, topic: str, level: float) -> None:
        """
        Record attention level for a topic.
        
        Args:
            topic: Topic identifier
            level: Attention level (0.0-1.0)
        """
        level = max(0.0, min(1.0, level))
        self._attention_levels[topic] = level
        
        # Normalize attention allocation
        total = sum(self._attention_levels.values())
        if total > 1.0:
            # Normalize to sum to 1.0
            for key in self._attention_levels:
                self._attention_levels[key] /= total
        
        self.states["attention_allocation"] = self._attention_levels.copy()
    
    def record_processing_depth(self, operation_id: str, depth: int) -> None:
        """
        Record processing depth for an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            depth: Processing depth (number of levels)
        """
        self._processing_depths.append({
            "operation_id": operation_id,
            "depth": depth,
            "timestamp": time.time(),
        })
        self._update_processing_depth()
    
    def _update_processing_depth(self) -> None:
        """Update average processing depth using moving average."""
        # Compute from moving average history (builds naturally from recorded data)
        if len(self._processing_depths) > 0:
            avg = sum(entry["depth"] for entry in self._processing_depths) / len(self._processing_depths)
            self.states["processing_depth"] = avg
            logger.debug(f"Updated processing_depth: {avg:.3f} (from {len(self._processing_depths)} samples, moving_avg)")
        else:
            # Use default when no data recorded yet (will be replaced once data is recorded)
            self.states["processing_depth"] = 1.0
            logger.debug("Processing depth using default (no history yet)")
    
    def _calculate_average_depth(self) -> Optional[float]:
        """
        Calculate average processing depth.
        
        Returns:
            Average depth, or None if no operations recorded
        """
        if len(self._processing_depths) == 0:
            return None
        
        return sum(entry["depth"] for entry in self._processing_depths) / len(self._processing_depths)
    
    def _normalize_depth(self, depth: int, max_depth: int = 20) -> float:
        """
        Normalize processing depth to 0-1 range.
        
        Args:
            depth: Processing depth
            max_depth: Maximum expected depth
            
        Returns:
            Normalized depth (0.0-1.0)
        """
        return min(depth / max_depth, 1.0)
    
    def record_uncertainty(self, question_id: str, uncertainty: float,
                          epistemic: Optional[float] = None,
                          aleatoric: Optional[float] = None,
                          knowledge_gaps: Optional[float] = None,
                          ambiguity: Optional[float] = None,
                          noise: Optional[float] = None) -> None:
        """
        Record uncertainty level with decomposition.
        
        Args:
            question_id: Unique identifier for the question
            uncertainty: Total uncertainty level (0.0-1.0)
            epistemic: Optional epistemic (reducible) uncertainty (0.0-1.0)
            aleatoric: Optional aleatoric (irreducible) uncertainty (0.0-1.0)
            knowledge_gaps: Optional uncertainty from knowledge gaps (0.0-1.0)
            ambiguity: Optional uncertainty from ambiguity (0.0-1.0)
            noise: Optional uncertainty from noise (0.0-1.0)
        """
        uncertainty = max(0.0, min(1.0, uncertainty))
        logger.debug(f"record_uncertainty called: question_id={question_id}, uncertainty={uncertainty:.3f}")
        
        self._uncertainty_history.append({
            "question_id": question_id,
            "uncertainty": uncertainty,
            "timestamp": time.time(),
        })
        
        # Record epistemic uncertainty if provided
        if epistemic is not None:
            epistemic = max(0.0, min(1.0, epistemic))
            self._uncertainty_epistemic_history.append(epistemic)
        
        # Record aleatoric uncertainty if provided
        if aleatoric is not None:
            aleatoric = max(0.0, min(1.0, aleatoric))
            self._uncertainty_aleatoric_history.append(aleatoric)
        
        # If epistemic/aleatoric not provided, estimate from total uncertainty
        # Assume 70% epistemic (reducible) and 30% aleatoric (irreducible) by default
        if epistemic is None and aleatoric is None:
            estimated_epistemic = uncertainty * 0.7
            estimated_aleatoric = uncertainty * 0.3
            self._uncertainty_epistemic_history.append(estimated_epistemic)
            self._uncertainty_aleatoric_history.append(estimated_aleatoric)
        
        # Update uncertainty sources
        if knowledge_gaps is not None:
            self.states["uncertainty_sources"]["knowledge_gaps"] = max(0.0, min(1.0, knowledge_gaps))
        if ambiguity is not None:
            self.states["uncertainty_sources"]["ambiguity"] = max(0.0, min(1.0, ambiguity))
        if noise is not None:
            self.states["uncertainty_sources"]["noise"] = max(0.0, min(1.0, noise))
        
        self._update_uncertainty()
    
    def _update_uncertainty(self) -> None:
        """Update average uncertainty from history with decomposition."""
        # Compute from moving average history (builds naturally from recorded data)
        if len(self._uncertainty_history) > 0:
            avg = sum(entry["uncertainty"] for entry in self._uncertainty_history) / len(self._uncertainty_history)
            old_value = self.states["uncertainty_tracking"]
            # Update through SignalManager if available (hybrid approach)
            if self._signal_manager:
                try:
                    avg = self._signal_manager.update("self_model.uncertainty", avg)
                except Exception as e:
                    logger.debug(f"Error updating uncertainty signal through SignalManager: {e}")
            self.states["uncertainty_tracking"] = avg
            logger.debug(f"Updated uncertainty_tracking: {old_value:.3f} -> {avg:.3f} (from {len(self._uncertainty_history)} samples, moving_avg)")
        else:
            # No data yet: use high uncertainty instead of default 0.0
            if HAS_DATA_QUALITY:
                self.states["uncertainty_tracking"] = uncertainty_for_missing_data()
                if "data_quality" not in self.states:
                    self.states["data_quality"] = {}
                self.states["data_quality"]["uncertainty"] = DataQuality.MISSING.value
            else:
                self.states["uncertainty_tracking"] = 0.0
            logger.debug("Uncertainty tracking using high uncertainty (no history yet)")
        
        # Update epistemic uncertainty
        if len(self._uncertainty_epistemic_history) > 0:
            avg_epistemic = sum(self._uncertainty_epistemic_history) / len(self._uncertainty_epistemic_history)
            self.states["uncertainty_epistemic"] = avg_epistemic
        else:
            self.states["uncertainty_epistemic"] = 0.0
        
        # Update aleatoric uncertainty
        if len(self._uncertainty_aleatoric_history) > 0:
            avg_aleatoric = sum(self._uncertainty_aleatoric_history) / len(self._uncertainty_aleatoric_history)
            self.states["uncertainty_aleatoric"] = avg_aleatoric
        else:
            self.states["uncertainty_aleatoric"] = 0.0
    
    def _calculate_average_uncertainty(self) -> Optional[float]:
        """
        Calculate average uncertainty from history.
        
        Returns:
            Average uncertainty (0.0-1.0), or None if no uncertainties recorded
        """
        if len(self._uncertainty_history) == 0:
            return None
        
        return sum(entry["uncertainty"] for entry in self._uncertainty_history) / len(self._uncertainty_history)
    
    def record_reasoning_pattern(self, pattern_type: str, pattern_name: str) -> None:
        """
        Record a reasoning pattern.
        
        Args:
            pattern_type: Type of pattern (e.g., "heuristic", "algorithm")
            pattern_name: Name of the pattern
        """
        self._reasoning_patterns.append({
            "type": pattern_type,
            "name": pattern_name,
            "timestamp": time.time(),
        })
        # Keep only recent patterns
        if len(self._reasoning_patterns) > 100:
            self._reasoning_patterns = self._reasoning_patterns[-100:]
    
    def _get_reasoning_patterns(self) -> List[Dict[str, str]]:
        """
        Get recent reasoning patterns.
        
        Returns:
            List of pattern dictionaries
        """
        return self._reasoning_patterns.copy()
    
    def sample_cognitive_state(self) -> Dict[str, Any]:
        """
        Sample complete cognitive state.
        
        Returns:
            Dictionary containing all cognitive states with timestamp.
            All values are computed from moving averages, ensuring they reflect
            smoothed historical data rather than raw defaults.
        """
        # Update all states from moving averages before sampling
        # This guarantees we return moving average values, not stale defaults
        self._update_confidence_level()
        self._update_coherence()
        self._update_processing_depth()
        self._update_uncertainty()
        
        # Create sample with timestamp
        # self.states now contains moving average values from the update methods above
        sample = {
            **self.states,
            "timestamp": time.time(),
        }
        
        # Add to history
        self._history.append(sample)
        
        return sample
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get history of cognitive state samples.
        
        Returns:
            List of sample dictionaries
        """
        return list(self._history)
    
    def serialize_histories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Serialize moving average histories for persistence.
        
        Returns:
            Dictionary mapping history names to lists of entries
        """
        return {
            "confidence_history": list(self._confidence_history),
            "uncertainty_history": list(self._uncertainty_history),
            "processing_depths": list(self._processing_depths),
        }
    
    def deserialize_histories(self, histories: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Deserialize moving average histories from persistence.
        
        Args:
            histories: Dictionary mapping history names to lists of entries
        """
        # Restore confidence history
        if "confidence_history" in histories:
            self._confidence_history.clear()
            for entry in histories["confidence_history"]:
                self._confidence_history.append(entry)
            # Update state from restored history
            self._update_confidence_level()
            logger.debug(f"Restored {len(self._confidence_history)} confidence history entries")
        
        # Restore uncertainty history
        if "uncertainty_history" in histories:
            self._uncertainty_history.clear()
            for entry in histories["uncertainty_history"]:
                self._uncertainty_history.append(entry)
            # Update state from restored history
            self._update_uncertainty()
            logger.debug(f"Restored {len(self._uncertainty_history)} uncertainty history entries")
        
        # Restore processing depths
        if "processing_depths" in histories:
            self._processing_depths.clear()
            for entry in histories["processing_depths"]:
                self._processing_depths.append(entry)
            # Update state from restored history
            self._update_processing_depth()
            logger.debug(f"Restored {len(self._processing_depths)} processing depth entries")

