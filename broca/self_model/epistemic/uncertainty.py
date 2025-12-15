"""
UncertaintyManager for uncertainty quantification and propagation.

Handles epistemic, aleatoric, and model uncertainty, and calculates information gain.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import math
import logging

from .models import ConfidenceMetrics, SourceMetadata
from .ids import KnowledgeID
from .calibration import ConfidenceCalibrator

logger = logging.getLogger(__name__)


class UncertaintyManager:
    """
    Manages uncertainty quantification and propagation.
    
    Provides:
    - Uncertainty quantification: Epistemic, aleatoric, model uncertainty
    - Uncertainty propagation: Through inference chains
    - Information gain calculation: What would reduce uncertainty most
    """
    
    def __init__(self, calibrator: Optional[ConfidenceCalibrator] = None) -> None:
        """
        Initialize uncertainty manager.
        
        Args:
            calibrator: Optional ConfidenceCalibrator instance
        """
        self.calibrator = calibrator or ConfidenceCalibrator()
    
    def uncertainty_quantification(
        self,
        confidence: float,
        source_count: int = 1,
        contradictory_count: int = 0
    ) -> Dict[str, float]:
        """
        Quantify different types of uncertainty.
        
        Args:
            confidence: Confidence score (0-1)
            source_count: Number of independent sources
            contradictory_count: Number of contradictory sources
            
        Returns:
            Dictionary with uncertainty breakdown
        """
        # Epistemic uncertainty: from incomplete knowledge
        # Lower confidence = higher epistemic uncertainty
        epistemic = 1.0 - confidence
        
        # Aleatoric uncertainty: from inherent randomness/noise
        # Based on contradictory evidence
        aleatoric = min(0.5, contradictory_count * 0.1)
        
        # Model uncertainty: from self-model limitations
        # Based on number of sources (fewer sources = more model uncertainty)
        model_uncertainty = max(0.0, 0.3 - (source_count - 1) * 0.05)
        model_uncertainty = min(0.3, model_uncertainty)
        
        # Total uncertainty
        total = min(1.0, epistemic + aleatoric + model_uncertainty)
        
        return {
            "epistemic": epistemic,
            "aleatoric": aleatoric,
            "model": model_uncertainty,
            "total": total
        }
    
    def uncertainty_propagation(
        self,
        uncertainties: Dict[KnowledgeID, float],
        dependencies: Dict[KnowledgeID, List[KnowledgeID]]
    ) -> Dict[KnowledgeID, float]:
        """
        Propagate uncertainty through inference chains.
        
        Args:
            uncertainties: Dictionary of knowledge ID to uncertainty
            dependencies: Dictionary of knowledge ID to list of dependencies
            
        Returns:
            Dictionary of propagated uncertainties
        """
        propagated = uncertainties.copy()
        
        # Propagate uncertainty from dependencies to dependents
        for knowledge_id, deps in dependencies.items():
            if not deps:
                continue
            
            # Calculate propagated uncertainty
            # Use maximum of dependency uncertainties (worst case)
            dep_uncertainties = [uncertainties.get(dep, 0.5) for dep in deps]
            if dep_uncertainties:
                max_dep_uncertainty = max(dep_uncertainties)
                # Combine with current uncertainty
                current_uncertainty = propagated.get(knowledge_id, 0.5)
                propagated[knowledge_id] = max(current_uncertainty, max_dep_uncertainty * 0.8)
        
        return propagated
    
    def information_gain_calculation(
        self,
        knowledge_items: Dict[KnowledgeID, Dict[str, any]]
    ) -> List[Tuple[KnowledgeID, float]]:
        """
        Calculate information gain for verifying different knowledge items.
        
        Args:
            knowledge_items: Dictionary of knowledge items with metadata
            
        Returns:
            List of tuples (knowledge_id, information_gain) sorted by gain
        """
        gains: List[Tuple[KnowledgeID, float]] = []
        
        for knowledge_id, data in knowledge_items.items():
            confidence = data.get("confidence", 0.5)
            importance = data.get("importance", 0.5)
            usage_frequency = data.get("usage_frequency", 0.0)
            
            # Information gain = importance * (1 - confidence) * usage_frequency
            # Higher importance, lower confidence, higher usage = more gain
            uncertainty = 1.0 - confidence
            gain = importance * uncertainty * (1.0 + usage_frequency)
            
            gains.append((knowledge_id, gain))
        
        # Sort by gain (highest first)
        gains.sort(key=lambda x: x[1], reverse=True)
        
        return gains
    
    def calculate_uncertainty_reduction(
        self,
        current_uncertainty: float,
        new_confidence: float
    ) -> float:
        """
        Calculate how much uncertainty would be reduced by new evidence.
        
        Args:
            current_uncertainty: Current uncertainty (0-1)
            new_confidence: Confidence from new evidence (0-1)
            
        Returns:
            Uncertainty reduction (0-1)
        """
        new_uncertainty = 1.0 - new_confidence
        reduction = current_uncertainty - new_uncertainty
        
        return max(0.0, reduction)
    
    def prioritize_verification(
        self,
        knowledge_items: Dict[KnowledgeID, Dict[str, any]],
        limit: int = 10
    ) -> List[KnowledgeID]:
        """
        Prioritize knowledge items for verification.
        
        Args:
            knowledge_items: Dictionary of knowledge items
            limit: Maximum number of items to return
            
        Returns:
            List of knowledge IDs prioritized for verification
        """
        gains = self.information_gain_calculation(knowledge_items)
        
        # Return top items
        return [kid for kid, _ in gains[:limit]]

