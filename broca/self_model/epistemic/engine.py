"""
MetacognitiveEngine orchestrating all epistemic processes.

Provides workflows for knowledge acquisition, confidence updates, and verification prioritization.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

from .layer import EpistemicLayer
from .models import (
    SourceMetadata,
    ConfidenceMetrics,
    VerificationRecord,
    KnowledgeEvolution,
    SourceType
)
from .ids import KnowledgeID
from .calibration import ConfidenceCalibrator
from .validation import SourceValidator
from .inference import InferenceTracker
from .integration import KnowledgeIntegrator
from .uncertainty import UncertaintyManager

logger = logging.getLogger(__name__)


class MetacognitiveEngine:
    """
    Main orchestrator for metacognitive processes.
    
    Coordinates:
    - Confidence calibration
    - Source validation
    - Inference tracking
    - Knowledge integration
    - Uncertainty management
    """
    
    def __init__(
        self,
        epistemic_layer: Optional[EpistemicLayer] = None,
        calibrator: Optional[ConfidenceCalibrator] = None,
        validator: Optional[SourceValidator] = None,
        tracker: Optional[InferenceTracker] = None,
        integrator: Optional[KnowledgeIntegrator] = None,
        uncertainty_manager: Optional[UncertaintyManager] = None
    ) -> None:
        """
        Initialize metacognitive engine.
        
        Args:
            epistemic_layer: EpistemicLayer instance
            calibrator: ConfidenceCalibrator instance
            validator: SourceValidator instance
            tracker: InferenceTracker instance
            integrator: KnowledgeIntegrator instance
            uncertainty_manager: UncertaintyManager instance
        """
        self.epistemic_layer = epistemic_layer or EpistemicLayer()
        self.calibrator = calibrator or ConfidenceCalibrator()
        self.validator = validator or SourceValidator()
        self.tracker = tracker or InferenceTracker()
        self.integrator = integrator or KnowledgeIntegrator(calibrator, validator)
        self.uncertainty_manager = uncertainty_manager or UncertaintyManager(calibrator)
    
    def knowledge_acquisition_workflow(
        self,
        knowledge_id: KnowledgeID,
        source: SourceMetadata,
        initial_confidence: float = 0.5
    ) -> ConfidenceMetrics:
        """
        Process new knowledge acquisition.
        
        Args:
            knowledge_id: ID of knowledge item
            source: Source metadata
            initial_confidence: Initial confidence score
            
        Returns:
            ConfidenceMetrics for the knowledge
        """
        # Assess source reliability
        source_reliability = self.validator.assess_source_reliability(source)
        
        # Calculate initial confidence based on source
        if source_reliability > 0.7:
            initial_confidence = max(initial_confidence, 0.7)
        elif source_reliability < 0.3:
            initial_confidence = min(initial_confidence, 0.3)
        
        # Initialize source reliability scores based on source type
        source_reliability_scores = {
            "tool_verification_score": 0.0,
            "memory_consistency_score": 0.0,
            "logical_validity_score": 0.0,
            "user_credibility_score": 0.0,
        }
        
        # Set appropriate source reliability score based on source type
        if source.source_type == SourceType.TOOL_MEDIATED_VERIFICATION:
            source_reliability_scores["tool_verification_score"] = source_reliability
        elif source.source_type == SourceType.MEMORY_RETRIEVAL:
            source_reliability_scores["memory_consistency_score"] = source_reliability
        elif source.source_type == SourceType.LOGICAL_INFERENCE:
            source_reliability_scores["logical_validity_score"] = source_reliability
        elif source.source_type == SourceType.USER_PROVIDED:
            source_reliability_scores["user_credibility_score"] = source_reliability
        elif source.source_type == SourceType.EXTERNAL_SOURCE:
            source_reliability_scores["tool_verification_score"] = source_reliability
        
        # Create confidence metrics
        metrics = ConfidenceMetrics(
            source_reliability=source_reliability_scores,
            overall_confidence=initial_confidence
        )
        
        # Update based on source type (this will refine the scores and recalculate composite)
        # During initialization, preserve initial_confidence exactly as specified
        updated_metrics = self.calibrator.update_confidence_with_evidence(
            metrics,
            source,
            source_reliability
        )
        
        # Preserve initial confidence during initialization
        # Use updated source reliability scores but keep the initial overall_confidence
        metrics = ConfidenceMetrics(
            source_reliability=updated_metrics.source_reliability,
            temporal_stability=updated_metrics.temporal_stability,
            cross_validation=updated_metrics.cross_validation,
            contextual_factors=updated_metrics.contextual_factors,
            overall_confidence=initial_confidence,  # Preserve initial confidence exactly
            confidence_calibration_error=updated_metrics.confidence_calibration_error
        )
        
        # Store in epistemic layer
        self.epistemic_layer.add_knowledge_source(knowledge_id, source)
        self.epistemic_layer.add_confidence_metrics(knowledge_id, metrics)
        
        # Initialize knowledge evolution
        evolution = KnowledgeEvolution(
            creation_event={
                "timestamp": datetime.now(timezone.utc),
                "initial_confidence": initial_confidence,
                "initial_source": source
            }
        )
        self.epistemic_layer.add_knowledge_evolution(knowledge_id, evolution)
        
        logger.info(f"Acquired knowledge {knowledge_id} with confidence {metrics.overall_confidence:.2f}")
        
        return metrics
    
    def confidence_update_workflow(
        self,
        knowledge_id: KnowledgeID,
        new_evidence: SourceMetadata,
        evidence_strength: float
    ) -> ConfidenceMetrics:
        """
        Update confidence based on new evidence.
        
        Args:
            knowledge_id: ID of knowledge item
            new_evidence: New evidence source
            evidence_strength: Strength of evidence (0-1)
            
        Returns:
            Updated ConfidenceMetrics
        """
        # Get current metrics
        current_metrics = self.epistemic_layer.get_confidence_metrics(knowledge_id)
        if not current_metrics:
            # No existing metrics, treat as new acquisition
            # Use assessed source reliability instead of passing evidence_strength directly
            source_reliability = self.validator.assess_source_reliability(new_evidence)
            return self.knowledge_acquisition_workflow(knowledge_id, new_evidence, source_reliability)
        
        # Update confidence with new evidence
        updated_metrics = self.calibrator.update_confidence_with_evidence(
            current_metrics,
            new_evidence,
            evidence_strength
        )
        
        # Record verification
        verification = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="evidence_update",
            result="confirmed" if evidence_strength > 0.5 else "modified",
            confidence_delta=updated_metrics.overall_confidence - current_metrics.overall_confidence,
            new_evidence=[new_evidence]
        )
        self.epistemic_layer.add_verification_record(knowledge_id, verification)
        
        # Update stored metrics
        self.epistemic_layer.add_confidence_metrics(knowledge_id, updated_metrics)
        
        # Update knowledge evolution
        evolution = self.epistemic_layer.get_knowledge_evolution(knowledge_id)
        if evolution:
            evolution.verification_history.append(verification)
        
        # Propagate through inference graph
        self.tracker.dependency_propagation(knowledge_id, updated_metrics.overall_confidence)
        
        logger.info(
            f"Updated confidence for {knowledge_id}: "
            f"{current_metrics.overall_confidence:.2f} -> {updated_metrics.overall_confidence:.2f}"
        )
        
        return updated_metrics
    
    def verification_prioritization_workflow(
        self,
        knowledge_items: Dict[KnowledgeID, Dict[str, Any]]
    ) -> List[KnowledgeID]:
        """
        Identify knowledge items that need verification.
        
        Args:
            knowledge_items: Dictionary of knowledge items with metadata
            
        Returns:
            List of knowledge IDs prioritized for verification
        """
        # Use uncertainty manager to calculate information gain
        prioritized = self.uncertainty_manager.prioritize_verification(knowledge_items)
        
        # Also check for low confidence items
        low_confidence = [
            kid for kid, data in knowledge_items.items()
            if data.get("confidence", 0.5) < 0.5
        ]
        
        # Combine and deduplicate
        all_priorities = list(dict.fromkeys(prioritized + low_confidence))
        
        return all_priorities[:20]  # Return top 20
    
    def get_epistemic_context(
        self,
        knowledge_id: KnowledgeID
    ) -> Dict[str, Any]:
        """
        Get full epistemic context for a knowledge item.
        
        Args:
            knowledge_id: ID of knowledge item
            
        Returns:
            Dictionary with epistemic context
        """
        source = self.epistemic_layer.get_knowledge_source(knowledge_id)
        metrics = self.epistemic_layer.get_confidence_metrics(knowledge_id)
        history = self.epistemic_layer.get_verification_history(knowledge_id)
        evolution = self.epistemic_layer.get_knowledge_evolution(knowledge_id)
        
        # Calculate uncertainty
        uncertainty = {}
        if metrics:
            uncertainty = self.uncertainty_manager.uncertainty_quantification(
                metrics.overall_confidence,
                source_count=len(history) + 1,
                contradictory_count=sum(1 for h in history if h.result == "refuted")
            )
        
        return {
            "knowledge_id": knowledge_id,
            "source": source.model_dump() if source else None,
            "confidence_metrics": metrics.model_dump() if metrics else None,
            "verification_count": len(history),
            "uncertainty": uncertainty,
            "has_evolution": evolution is not None
        }

