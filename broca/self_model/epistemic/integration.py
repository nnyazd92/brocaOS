"""
KnowledgeIntegrator for conflict resolution and coherence maintenance.

Handles merging knowledge from multiple sources and maintaining consistency.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import logging

from .models import SourceMetadata, ConfidenceMetrics, SourceType
from .ids import KnowledgeID
from .calibration import ConfidenceCalibrator
from .validation import SourceValidator

logger = logging.getLogger(__name__)


class KnowledgeIntegrator:
    """
    Integrates knowledge from multiple sources and resolves conflicts.
    
    Provides:
    - Conflict resolution: Resolve conflicts using source hierarchy
    - Coherence maintenance: Consistency checking and pruning
    """
    
    def __init__(
        self,
        calibrator: Optional[ConfidenceCalibrator] = None,
        validator: Optional[SourceValidator] = None
    ) -> None:
        """
        Initialize knowledge integrator.
        
        Args:
            calibrator: Optional ConfidenceCalibrator instance
            validator: Optional SourceValidator instance
        """
        self.calibrator = calibrator or ConfidenceCalibrator()
        self.validator = validator or SourceValidator()
    
    def conflict_resolution(
        self,
        knowledge_id: KnowledgeID,
        sources: List[SourceMetadata],
        confidences: List[float]
    ) -> Tuple[SourceMetadata, float]:
        """
        Resolve conflicts between multiple sources.
        
        Uses source hierarchy: tool_verified > memory > inference > assumption
        
        Args:
            knowledge_id: ID of knowledge item
            sources: List of source metadata
            confidences: List of confidence scores
            
        Returns:
            Tuple of (selected_source, resolved_confidence)
        """
        if not sources:
            # Default source if none provided
            default_source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
            return default_source, 0.5
        
        if len(sources) == 1:
            return sources[0], confidences[0] if confidences else 0.5
        
        # Source hierarchy (higher number = higher priority)
        hierarchy = {
            SourceType.TOOL_MEDIATED_VERIFICATION: 4,
            SourceType.MEMORY_RETRIEVAL: 3,
            SourceType.LOGICAL_INFERENCE: 2,
            SourceType.USER_PROVIDED: 3,  # User provided is also high priority
            SourceType.EMERGENT_PATTERN: 1,
        }
        
        # Score each source
        scored_sources: List[Tuple[SourceMetadata, float, int]] = []
        for i, source in enumerate(sources):
            confidence = confidences[i] if i < len(confidences) else 0.5
            priority = hierarchy.get(source.source_type, 0)
            
            # Assess source reliability
            reliability = self.validator.assess_source_reliability(source)
            
            # Combined score: priority * reliability * confidence
            score = priority * reliability * confidence
            scored_sources.append((source, confidence, score))
        
        # Select highest scoring source
        scored_sources.sort(key=lambda x: x[2], reverse=True)
        selected_source, selected_confidence, _ = scored_sources[0]
        
        # If multiple high-quality sources agree, boost confidence
        if len(scored_sources) > 1:
            top_score = scored_sources[0][2]
            second_score = scored_sources[1][2]
            
            # If top two are close, consensus boosts confidence
            if top_score > 0 and second_score / top_score > 0.8:
                consensus_boost = 0.1
                selected_confidence = min(1.0, selected_confidence + consensus_boost)
        
        return selected_source, selected_confidence
    
    def coherence_maintenance(
        self,
        knowledge_items: Dict[KnowledgeID, Dict[str, any]]
    ) -> Dict[KnowledgeID, Dict[str, any]]:
        """
        Maintain coherence by checking consistency and pruning low-confidence items.
        
        Args:
            knowledge_items: Dictionary of knowledge items with their metadata
            
        Returns:
            Dictionary of knowledge items after coherence maintenance
        """
        # Remove low-confidence items
        threshold = 0.3
        pruned = {
            kid: data for kid, data in knowledge_items.items()
            if data.get("confidence", 0.5) >= threshold
        }
        
        # Check for contradictions
        contradictions: List[Tuple[KnowledgeID, KnowledgeID]] = []
        items_list = list(pruned.items())
        
        for i, (kid1, data1) in enumerate(items_list):
            for kid2, data2 in items_list[i+1:]:
                conf1 = data1.get("confidence", 0.5)
                conf2 = data2.get("confidence", 0.5)
                
                # Flag potential contradictions (simplified check)
                if conf1 > 0.7 and conf2 > 0.7 and abs(conf1 - conf2) > 0.6:
                    contradictions.append((kid1, kid2))
        
        # Log contradictions
        if contradictions:
            logger.warning(f"Found {len(contradictions)} potential contradictions")
            for kid1, kid2 in contradictions:
                logger.debug(f"Contradiction: {kid1} <-> {kid2}")
        
        return pruned
    
    def integrate_knowledge(
        self,
        knowledge_id: KnowledgeID,
        new_source: SourceMetadata,
        new_confidence: float,
        existing_source: Optional[SourceMetadata] = None,
        existing_confidence: Optional[float] = None
    ) -> Tuple[SourceMetadata, float]:
        """
        Integrate new knowledge with existing knowledge.
        
        Args:
            knowledge_id: ID of knowledge item
            new_source: New source metadata
            new_confidence: New confidence score
            existing_source: Optional existing source
            existing_confidence: Optional existing confidence
            
        Returns:
            Tuple of (integrated_source, integrated_confidence)
        """
        if existing_source is None:
            # No existing knowledge, use new
            return new_source, new_confidence
        
        # Resolve conflict between new and existing
        sources = [existing_source, new_source]
        confidences = [
            existing_confidence or 0.5,
            new_confidence
        ]
        
        return self.conflict_resolution(knowledge_id, sources, confidences)

