"""
InferenceTracker for tracking inference chains and dependencies.

Handles dependency propagation, contradiction detection, and assumption sensitivity.
"""

from __future__ import annotations

from typing import Dict, List, Set, Optional
import logging

from .models import InferenceNode, SourceMetadata, SourceType
from .ids import KnowledgeID

logger = logging.getLogger(__name__)


class InferenceTracker:
    """
    Tracks inference chains and propagates confidence changes.
    
    Provides:
    - Dependency propagation: Propagate confidence through inference graph
    - Contradiction detection: Identify conflicting knowledge
    - Assumption sensitivity: Measure impact of assumption changes
    """
    
    def __init__(self) -> None:
        """Initialize inference tracker."""
        self._inference_graph: Dict[KnowledgeID, InferenceNode] = {}
    
    def add_node(self, node: InferenceNode) -> None:
        """Add or update an inference node."""
        self._inference_graph[node.knowledge_id] = node
    
    def get_node(self, knowledge_id: KnowledgeID) -> Optional[InferenceNode]:
        """Get an inference node."""
        return self._inference_graph.get(knowledge_id)
    
    def dependency_propagation(
        self,
        knowledge_id: KnowledgeID,
        new_confidence: float
    ) -> Dict[KnowledgeID, float]:
        """
        Propagate confidence changes through dependency graph.
        
        Args:
            knowledge_id: ID of knowledge item that changed
            new_confidence: New confidence value
            
        Returns:
            Dictionary mapping affected knowledge IDs to new confidence values
        """
        affected: Dict[KnowledgeID, float] = {}
        
        node = self._inference_graph.get(knowledge_id)
        if not node:
            return affected
        
        # Update this node's confidence
        old_confidence = node.confidence
        node.confidence = new_confidence
        affected[knowledge_id] = new_confidence
        
        # Propagate to dependents
        for dependent in node.dependents:
            if dependent.knowledge_id not in affected:
                # Calculate new confidence based on dependency strength
                strength = dependent.logical_relationship.get("strength", 0.5)
                confidence_delta = (new_confidence - old_confidence) * strength
                new_dependent_confidence = max(0.0, min(1.0, dependent.confidence + confidence_delta))
                
                # Recursively propagate
                sub_affected = self.dependency_propagation(dependent.knowledge_id, new_dependent_confidence)
                affected.update(sub_affected)
        
        return affected
    
    def contradiction_detection(
        self,
        knowledge_id: KnowledgeID,
        new_knowledge: str,
        confidence: float
    ) -> List[Dict[str, any]]:
        """
        Detect contradictions with existing knowledge.
        
        Args:
            knowledge_id: ID of knowledge item to check
            new_knowledge: New knowledge content
            confidence: Confidence in new knowledge
            
        Returns:
            List of contradiction records
        """
        contradictions: List[Dict[str, any]] = []
        
        # Check against all other nodes
        for other_id, other_node in self._inference_graph.items():
            if other_id == knowledge_id:
                continue
            
            # Simple heuristic: if both have high confidence and are semantically opposite
            # This is a simplified check - in practice would use semantic similarity
            if other_node.confidence > 0.7 and confidence > 0.7:
                # Check if knowledge items might contradict
                # For now, we'll flag potential contradictions based on confidence
                if abs(other_node.confidence - confidence) > 0.5:
                    contradictions.append({
                        "knowledge_id": knowledge_id,
                        "contradicts_with": other_id,
                        "confidence_difference": abs(other_node.confidence - confidence),
                        "severity": "medium"
                    })
        
        return contradictions
    
    def assumption_sensitivity(
        self,
        assumption_id: KnowledgeID,
        new_confidence: float
    ) -> Dict[str, any]:
        """
        Measure impact of changing an assumption's confidence.
        
        Args:
            assumption_id: ID of assumption to change
            new_confidence: New confidence value
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        node = self._inference_graph.get(assumption_id)
        if not node or node.node_type != "assumption":
            return {"impact": "none", "affected_count": 0}
        
        old_confidence = node.confidence
        
        # Propagate change and count affected nodes
        affected = self.dependency_propagation(assumption_id, new_confidence)
        
        # Calculate average confidence change
        if affected:
            avg_change = sum(abs(v - self._inference_graph.get(kid, InferenceNode(
                knowledge_id=kid,
                node_type="assumption",
                confidence=0.5,
                source=SourceMetadata(source_type=SourceType.LOGICAL_INFERENCE)
            )).confidence) for kid, v in affected.items()) / len(affected)
        else:
            avg_change = 0.0
        
        return {
            "impact": "high" if len(affected) > 5 else "medium" if len(affected) > 0 else "low",
            "affected_count": len(affected),
            "average_confidence_change": avg_change,
            "affected_nodes": list(affected.keys())
        }
    
    def get_dependencies(self, knowledge_id: KnowledgeID) -> List[KnowledgeID]:
        """Get all dependencies for a knowledge item."""
        node = self._inference_graph.get(knowledge_id)
        if not node:
            return []
        
        deps: List[KnowledgeID] = []
        for dep in node.dependencies:
            deps.append(dep.knowledge_id)
            # Recursively get dependencies
            deps.extend(self.get_dependencies(dep.knowledge_id))
        
        return list(set(deps))  # Remove duplicates
    
    def get_dependents(self, knowledge_id: KnowledgeID) -> List[KnowledgeID]:
        """Get all dependents for a knowledge item."""
        node = self._inference_graph.get(knowledge_id)
        if not node:
            return []
        
        dependents: List[KnowledgeID] = []
        for dep in node.dependents:
            dependents.append(dep.knowledge_id)
            # Recursively get dependents
            dependents.extend(self.get_dependents(dep.knowledge_id))
        
        return list(set(dependents))  # Remove duplicates
    
    def track_inference(
        self,
        node: InferenceNode,
        epistemic_layer: "EpistemicLayer"
    ) -> None:
        """
        Track an inference node in the epistemic layer.
        
        Args:
            node: Inference node to track
            epistemic_layer: EpistemicLayer to store the node in
        """
        from .layer import EpistemicLayer
        epistemic_layer.add_inference_node(node)
        self.add_node(node)

