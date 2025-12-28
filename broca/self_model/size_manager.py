"""
Self-Model Size Management.

Implements size limits and pruning strategies using metadata-to-artifacts pattern
to prevent unbounded growth of the self-model.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

from .model import SelfModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .epistemic.engine import MetacognitiveEngine

logger = logging.getLogger(__name__)


class PruningStrategy(Enum):
    """Strategies for pruning self-model entries when limits are exceeded."""
    LOWEST_CONFIDENCE = "lowest_confidence"
    LEAST_RECENT = "least_recent"
    LOWEST_EPISTEMIC_CONFIDENCE = "lowest_epistemic_confidence"
    COMBINED_SCORE = "combined_score"


@dataclass
class SizeLimits:
    """Size limits for self-model aspects."""
    max_capabilities: int = 50
    max_knowledge_boundaries: int = 30
    max_constraints: int = 30
    
    # Soft limits (warn when exceeded)
    soft_capabilities: int = 40
    soft_knowledge_boundaries: int = 25
    soft_constraints: int = 25


class SelfModelSizeManager:
    """
    Manages size limits and pruning for self-model.
    
    Uses metadata-to-artifacts pattern: self-model stores lightweight metadata,
    detailed information can be stored in separate artifact storage.
    """
    
    def __init__(
        self,
        limits: Optional[SizeLimits] = None,
        pruning_strategy: PruningStrategy = PruningStrategy.COMBINED_SCORE,
        epistemic_engine: Optional["MetacognitiveEngine"] = None
    ):
        """
        Initialize size manager.
        
        Args:
            limits: Size limits configuration
            pruning_strategy: Strategy for selecting entries to prune
            epistemic_engine: Optional epistemic engine for confidence metrics
        """
        self.limits = limits or SizeLimits()
        self.pruning_strategy = pruning_strategy
        self.epistemic_engine = epistemic_engine
        
        logger.info(
            f"Initialized SelfModelSizeManager "
            f"(limits: cap={self.limits.max_capabilities}, "
            f"kb={self.limits.max_knowledge_boundaries}, "
            f"const={self.limits.max_constraints})"
        )
    
    def check_size(
        self,
        self_model: SelfModel
    ) -> Dict[str, Any]:
        """
        Check current size against limits.
        
        Args:
            self_model: Self-model to check
            
        Returns:
            Dictionary with size status and recommendations
        """
        capabilities_count = len(self_model.capabilities)
        kb_count = len(self_model.knowledge_boundaries)
        constraints_count = len(self_model.constraints)
        
        status = {
            "capabilities": {
                "count": capabilities_count,
                "limit": self.limits.max_capabilities,
                "soft_limit": self.limits.soft_capabilities,
                "exceeds_soft": capabilities_count > self.limits.soft_capabilities,
                "exceeds_hard": capabilities_count > self.limits.max_capabilities
            },
            "knowledge_boundaries": {
                "count": kb_count,
                "limit": self.limits.max_knowledge_boundaries,
                "soft_limit": self.limits.soft_knowledge_boundaries,
                "exceeds_soft": kb_count > self.limits.soft_knowledge_boundaries,
                "exceeds_hard": kb_count > self.limits.max_knowledge_boundaries
            },
            "constraints": {
                "count": constraints_count,
                "limit": self.limits.max_constraints,
                "soft_limit": self.limits.soft_constraints,
                "exceeds_soft": constraints_count > self.limits.soft_constraints,
                "exceeds_hard": constraints_count > self.limits.max_constraints
            }
        }
        
        # Overall status
        any_exceeds_hard = (
            status["capabilities"]["exceeds_hard"] or
            status["knowledge_boundaries"]["exceeds_hard"] or
            status["constraints"]["exceeds_hard"]
        )
        any_exceeds_soft = (
            status["capabilities"]["exceeds_soft"] or
            status["knowledge_boundaries"]["exceeds_soft"] or
            status["constraints"]["exceeds_soft"]
        )
        
        status["needs_pruning"] = any_exceeds_hard
        status["warn_size"] = any_exceeds_soft and not any_exceeds_hard
        
        return status
    
    def prune_if_needed(
        self,
        self_model: SelfModel
    ) -> Tuple[SelfModel, Dict[str, int]]:
        """
        Prune self-model if size limits exceeded.
        
        Args:
            self_model: Current self-model
            
        Returns:
            Tuple of (pruned_model, pruning_stats) - if no pruning needed, returns original model
        """
        size_status = self.check_size(self_model)
        
        if not size_status["needs_pruning"]:
            return self_model, {}
        
        pruning_stats = {}
        pruned_model = self_model
        
        # Prune capabilities if needed
        if size_status["capabilities"]["exceeds_hard"]:
            excess = size_status["capabilities"]["count"] - self.limits.max_capabilities
            pruned_caps, pruned_count = self._prune_capabilities(
                self_model.capabilities,
                excess
            )
            if pruned_count > 0:
                from .model import SelfModel
                pruned_model = SelfModel(
                    capabilities=pruned_caps,
                    knowledge_boundaries=self_model.knowledge_boundaries,
                    constraints=self_model.constraints,
                    metadata=self_model.metadata.copy(),
                    epistemic_layer=self_model.epistemic_layer
                )
                pruning_stats["capabilities"] = pruned_count
        
        # Prune knowledge boundaries if needed
        if size_status["knowledge_boundaries"]["exceeds_hard"]:
            excess = size_status["knowledge_boundaries"]["count"] - self.limits.max_knowledge_boundaries
            pruned_kb, pruned_count = self._prune_knowledge_boundaries(
                self_model.knowledge_boundaries,
                excess
            )
            if pruned_count > 0:
                from .model import SelfModel
                pruned_model = SelfModel(
                    capabilities=pruned_model.capabilities,
                    knowledge_boundaries=pruned_kb,
                    constraints=pruned_model.constraints,
                    metadata=pruned_model.metadata.copy(),
                    epistemic_layer=pruned_model.epistemic_layer
                )
                pruning_stats["knowledge_boundaries"] = pruned_count
        
        # Prune constraints if needed
        if size_status["constraints"]["exceeds_hard"]:
            excess = size_status["constraints"]["count"] - self.limits.max_constraints
            pruned_constraints, pruned_count = self._prune_constraints(
                self_model.constraints,
                excess
            )
            if pruned_count > 0:
                from .model import SelfModel
                pruned_model = SelfModel(
                    capabilities=pruned_model.capabilities,
                    knowledge_boundaries=pruned_model.knowledge_boundaries,
                    constraints=pruned_constraints,
                    metadata=pruned_model.metadata.copy(),
                    epistemic_layer=pruned_model.epistemic_layer
                )
                pruning_stats["constraints"] = pruned_count
        
        # Update metadata
        if pruning_stats:
            pruned_model.metadata["version"] = self_model.metadata.get("version", 1) + 1
            pruned_model.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
            pruned_model.metadata["update_reason"] = "size_management_pruning"
            pruned_model.metadata["pruning_stats"] = pruning_stats
            logger.info(f"Pruned self-model: {pruning_stats}")
        
        return pruned_model, pruning_stats
    
    def _prune_capabilities(
        self,
        capabilities: List[Dict[str, Any]],
        count_to_prune: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Prune capabilities based on strategy."""
        if len(capabilities) <= count_to_prune:
            return [], len(capabilities)
        
        # Score entries for pruning
        scored = []
        for cap in capabilities:
            score = self._score_entry_for_pruning(cap, "capability")
            scored.append((score, cap))
        
        # Sort by score (lower = more likely to prune)
        scored.sort(key=lambda x: x[0])
        
        # Keep the best ones
        kept = [cap for _, cap in scored[:-count_to_prune]]
        pruned_count = count_to_prune
        
        return kept, pruned_count
    
    def _prune_knowledge_boundaries(
        self,
        knowledge_boundaries: Dict[str, Dict[str, Any]],
        count_to_prune: int
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        """Prune knowledge boundaries based on strategy."""
        if len(knowledge_boundaries) <= count_to_prune:
            return {}, len(knowledge_boundaries)
        
        # Score entries for pruning
        scored = []
        for key, value_dict in knowledge_boundaries.items():
            score = self._score_entry_for_pruning(value_dict, "knowledge_boundary", key)
            scored.append((score, key, value_dict))
        
        # Sort by score
        scored.sort(key=lambda x: x[0])
        
        # Keep the best ones
        kept = {key: value_dict for _, key, value_dict in scored[:-count_to_prune]}
        pruned_count = count_to_prune
        
        return kept, pruned_count
    
    def _prune_constraints(
        self,
        constraints: Dict[str, Dict[str, Any]],
        count_to_prune: int
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        """Prune constraints based on strategy."""
        if len(constraints) <= count_to_prune:
            return {}, len(constraints)
        
        # Score entries for pruning
        scored = []
        for key, value_dict in constraints.items():
            score = self._score_entry_for_pruning(value_dict, "constraint", key)
            scored.append((score, key, value_dict))
        
        # Sort by score
        scored.sort(key=lambda x: x[0])
        
        # Keep the best ones
        kept = {key: value_dict for _, key, value_dict in scored[:-count_to_prune]}
        pruned_count = count_to_prune
        
        return kept, pruned_count
    
    def _score_entry_for_pruning(
        self,
        entry: Dict[str, Any],
        aspect: str,
        key: Optional[str] = None
    ) -> float:
        """
        Score an entry for pruning priority (lower score = more likely to prune).
        
        Args:
            entry: Entry dictionary
            aspect: Aspect type (capability, knowledge_boundary, constraint)
            key: Optional key for dict-based aspects
            
        Returns:
            Score (lower = prune first)
        """
        if self.pruning_strategy == PruningStrategy.LOWEST_CONFIDENCE:
            # Use confidence from metadata if available
            confidence = entry.get("confidence", 0.5)
            return -confidence  # Lower confidence -> lower score -> prune first
        
        elif self.pruning_strategy == PruningStrategy.LEAST_RECENT:
            # Use timestamp from source or metadata
            source = entry.get("source", {})
            timestamp_str = source.get("timestamp") or entry.get("timestamp")
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = timestamp_str
                    # Older entries have lower score
                    age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
                    return age_seconds  # Older = higher age = prune first
                except Exception:
                    pass
            return 0.0  # No timestamp, default score
        
        elif self.pruning_strategy == PruningStrategy.LOWEST_EPISTEMIC_CONFIDENCE:
            # Use epistemic confidence if available
            if self.epistemic_engine and key:
                try:
                    from .epistemic.ids import (
                        generate_capability_id,
                        generate_constraint_id,
                        generate_knowledge_boundary_id
                    )
                    
                    if aspect == "capability":
                        text = entry.get("text", str(entry))
                        kid = generate_capability_id(text)
                    elif aspect == "knowledge_boundary":
                        value = entry.get("value", str(entry))
                        kid = generate_knowledge_boundary_id(key, value)
                    elif aspect == "constraint":
                        value = entry.get("value", str(entry))
                        kid = generate_constraint_id(key, value)
                    else:
                        return 0.5
                    
                    context = self.epistemic_engine.get_epistemic_context(kid)
                    if context and context.get("confidence_metrics"):
                        confidence = context["confidence_metrics"].get("overall_confidence", 0.5)
                        return -confidence
                except Exception as e:
                    logger.debug(f"Error getting epistemic confidence: {e}")
            return 0.5  # Default
        
        else:  # COMBINED_SCORE
            # Combine multiple factors
            score = 0.0
            
            # Confidence factor (if available)
            confidence = entry.get("confidence", 0.5)
            score += confidence * 0.4  # Higher confidence = higher score = keep
            
            # Recency factor
            source = entry.get("source", {})
            timestamp_str = source.get("timestamp") or entry.get("timestamp")
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = timestamp_str
                    age_days = (datetime.now(timezone.utc) - timestamp).total_seconds() / 86400
                    recency = max(0.0, 1.0 - (age_days / 365.0))  # Normalize to 0-1 over a year
                    score += recency * 0.3
                except Exception:
                    pass
            
            # Epistemic confidence factor
            if self.epistemic_engine and key:
                try:
                    from .epistemic.ids import (
                        generate_capability_id,
                        generate_constraint_id,
                        generate_knowledge_boundary_id
                    )
                    
                    if aspect == "capability":
                        text = entry.get("text", str(entry))
                        kid = generate_capability_id(text)
                    elif aspect == "knowledge_boundary":
                        value = entry.get("value", str(entry))
                        kid = generate_knowledge_boundary_id(key, value)
                    elif aspect == "constraint":
                        value = entry.get("value", str(entry))
                        kid = generate_constraint_id(key, value)
                    else:
                        pass
                    
                    context = self.epistemic_engine.get_epistemic_context(kid)
                    if context and context.get("confidence_metrics"):
                        ep_confidence = context["confidence_metrics"].get("overall_confidence", 0.5)
                        score += ep_confidence * 0.3
                except Exception:
                    pass
            
            return -score  # Lower score = prune first
    
    def get_metadata_only_representation(
        self,
        self_model: SelfModel
    ) -> Dict[str, Any]:
        """
        Get metadata-only representation (for world state, size-limited contexts).
        
        Args:
            self_model: Self-model to represent
            
        Returns:
            Dictionary with metadata-only representation (references, not full data)
        """
        # Create lightweight representation
        metadata = {
            "version": self_model.metadata.get("version", 1),
            "last_updated": self_model.metadata.get("last_updated"),
            "capabilities_count": len(self_model.capabilities),
            "knowledge_boundaries_count": len(self_model.knowledge_boundaries),
            "constraints_count": len(self_model.constraints),
            "capabilities_summary": [cap.get("text", str(cap))[:50] for cap in self_model.capabilities[:5]],
            "knowledge_boundaries_keys": list(self_model.knowledge_boundaries.keys())[:5],
            "constraints_keys": list(self_model.constraints.keys())[:5]
        }
        
        return metadata

