"""
EpistemicLayer data structure for tracking epistemic metadata.

Contains mappings from knowledge IDs to sources, confidence metrics,
verification history, inference chains, and temporal dynamics.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime

from .models import (
    SourceMetadata,
    ConfidenceMetrics,
    InferenceNode,
    KnowledgeEvolution,
    VerificationRecord,
)
from .ids import KnowledgeID


class EpistemicLayer:
    """
    Epistemic metadata layer for second-order self-modeling.
    
    Tracks:
    - Knowledge sources: How knowledge was acquired
    - Confidence calibration: Confidence scores per knowledge item
    - Verification history: Records of verification events
    - Inference chains: Graph of knowledge dependencies
    - Temporal dynamics: Evolution of knowledge over time
    """
    
    def __init__(self) -> None:
        """Initialize an empty epistemic layer."""
        self.knowledge_sources: Dict[KnowledgeID, SourceMetadata] = {}
        self.confidence_calibration: Dict[KnowledgeID, ConfidenceMetrics] = {}
        self.verification_history: Dict[KnowledgeID, List[VerificationRecord]] = {}
        self.inference_chains: Dict[KnowledgeID, InferenceNode] = {}
        self.temporal_dynamics: Dict[KnowledgeID, KnowledgeEvolution] = {}
        # Memory ID to Knowledge ID mapping
        self.memory_knowledge_mapping: Dict[int, KnowledgeID] = {}
    
    def add_knowledge_source(self, knowledge_id: KnowledgeID, source: SourceMetadata) -> None:
        """Add or update knowledge source for a knowledge item."""
        self.knowledge_sources[knowledge_id] = source
    
    def get_knowledge_source(self, knowledge_id: KnowledgeID) -> Optional[SourceMetadata]:
        """Get knowledge source for a knowledge item."""
        return self.knowledge_sources.get(knowledge_id)
    
    def add_confidence_metrics(self, knowledge_id: KnowledgeID, metrics: ConfidenceMetrics) -> None:
        """Add or update confidence metrics for a knowledge item."""
        self.confidence_calibration[knowledge_id] = metrics
    
    def get_confidence_metrics(self, knowledge_id: KnowledgeID) -> Optional[ConfidenceMetrics]:
        """Get confidence metrics for a knowledge item."""
        return self.confidence_calibration.get(knowledge_id)
    
    def add_verification_record(self, knowledge_id: KnowledgeID, record: VerificationRecord) -> None:
        """Add a verification record to history."""
        if knowledge_id not in self.verification_history:
            self.verification_history[knowledge_id] = []
        self.verification_history[knowledge_id].append(record)
    
    def get_verification_history(self, knowledge_id: KnowledgeID) -> List[VerificationRecord]:
        """Get verification history for a knowledge item."""
        return self.verification_history.get(knowledge_id, [])
    
    def add_inference_node(self, node: InferenceNode) -> None:
        """Add or update an inference node."""
        self.inference_chains[node.knowledge_id] = node
    
    def get_inference_node(self, knowledge_id: KnowledgeID) -> Optional[InferenceNode]:
        """Get inference node for a knowledge item."""
        return self.inference_chains.get(knowledge_id)
    
    def add_knowledge_evolution(self, knowledge_id: KnowledgeID, evolution: KnowledgeEvolution) -> None:
        """Add or update knowledge evolution tracking."""
        self.temporal_dynamics[knowledge_id] = evolution
    
    def get_knowledge_evolution(self, knowledge_id: KnowledgeID) -> Optional[KnowledgeEvolution]:
        """Get knowledge evolution for a knowledge item."""
        return self.temporal_dynamics.get(knowledge_id)
    
    def add_memory_knowledge_mapping(self, memory_id: int, knowledge_id: KnowledgeID) -> None:
        """Add or update mapping from memory ID to knowledge ID."""
        self.memory_knowledge_mapping[memory_id] = knowledge_id
    
    def get_knowledge_id_for_memory(self, memory_id: int) -> Optional[KnowledgeID]:
        """Get knowledge ID for a memory ID."""
        return self.memory_knowledge_mapping.get(memory_id)
    
    def get_memory_ids_for_knowledge(self, knowledge_id: KnowledgeID) -> List[int]:
        """Get all memory IDs associated with a knowledge ID."""
        return [mid for mid, kid in self.memory_knowledge_mapping.items() if kid == knowledge_id]
    
    def has_knowledge(self, knowledge_id: KnowledgeID) -> bool:
        """Check if knowledge item exists in any tracking structure."""
        return (
            knowledge_id in self.knowledge_sources or
            knowledge_id in self.confidence_calibration or
            knowledge_id in self.verification_history or
            knowledge_id in self.inference_chains or
            knowledge_id in self.temporal_dynamics
        )
    
    def to_dict(self) -> Dict:
        """Convert epistemic layer to dictionary for serialization."""
        import json
        from datetime import datetime
        
        def serialize_value(value):
            """Recursively serialize values, converting datetime to ISO strings."""
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            elif hasattr(value, 'model_dump'):
                # Use Pydantic's model_dump with mode='json' to handle datetime
                try:
                    return value.model_dump(mode='json')
                except TypeError:
                    # Fallback to regular model_dump if mode not supported
                    return serialize_value(value.model_dump())
            else:
                return value
        
        return {
            "knowledge_sources": {
                kid: serialize_value(source)
                for kid, source in self.knowledge_sources.items()
            },
            "confidence_calibration": {
                kid: serialize_value(metrics)
                for kid, metrics in self.confidence_calibration.items()
            },
            "verification_history": {
                kid: [serialize_value(record) for record in records]
                for kid, records in self.verification_history.items()
            },
            "inference_chains": {
                kid: serialize_value(node)
                for kid, node in self.inference_chains.items()
            },
            "temporal_dynamics": {
                kid: serialize_value(evolution)
                for kid, evolution in self.temporal_dynamics.items()
            },
            "memory_knowledge_mapping": self.memory_knowledge_mapping,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EpistemicLayer":
        """Create epistemic layer from dictionary."""
        layer = cls()
        
        # Reconstruct knowledge sources
        for kid, source_data in data.get("knowledge_sources", {}).items():
            if isinstance(source_data, dict):
                layer.knowledge_sources[kid] = SourceMetadata(**source_data)
            else:
                layer.knowledge_sources[kid] = source_data
        
        # Reconstruct confidence calibration
        for kid, metrics_data in data.get("confidence_calibration", {}).items():
            if isinstance(metrics_data, dict):
                layer.confidence_calibration[kid] = ConfidenceMetrics(**metrics_data)
            else:
                layer.confidence_calibration[kid] = metrics_data
        
        # Reconstruct verification history
        for kid, records_data in data.get("verification_history", {}).items():
            layer.verification_history[kid] = []
            for record_data in records_data:
                if isinstance(record_data, dict):
                    # Handle datetime conversion
                    if "timestamp" in record_data and isinstance(record_data["timestamp"], str):
                        record_data["timestamp"] = datetime.fromisoformat(record_data["timestamp"])
                    layer.verification_history[kid].append(VerificationRecord(**record_data))
                else:
                    layer.verification_history[kid].append(record_data)
        
        # Reconstruct inference chains
        for kid, node_data in data.get("inference_chains", {}).items():
            if isinstance(node_data, dict):
                # Handle nested InferenceNodes in dependencies/dependents
                if "dependencies" in node_data:
                    deps = []
                    for dep_data in node_data["dependencies"]:
                        if isinstance(dep_data, dict):
                            deps.append(InferenceNode(**dep_data))
                        else:
                            deps.append(dep_data)
                    node_data["dependencies"] = deps
                if "dependents" in node_data:
                    deps = []
                    for dep_data in node_data["dependents"]:
                        if isinstance(dep_data, dict):
                            deps.append(InferenceNode(**dep_data))
                        else:
                            deps.append(dep_data)
                    node_data["dependents"] = deps
                layer.inference_chains[kid] = InferenceNode(**node_data)
            else:
                layer.inference_chains[kid] = node_data
        
        # Reconstruct temporal dynamics
        for kid, evolution_data in data.get("temporal_dynamics", {}).items():
            if isinstance(evolution_data, dict):
                # Handle datetime in creation_event
                if "creation_event" in evolution_data and "timestamp" in evolution_data["creation_event"]:
                    ts = evolution_data["creation_event"]["timestamp"]
                    if isinstance(ts, str):
                        evolution_data["creation_event"]["timestamp"] = datetime.fromisoformat(ts)
                # Handle verification history in evolution
                if "verification_history" in evolution_data:
                    vh = []
                    for record_data in evolution_data["verification_history"]:
                        if isinstance(record_data, dict):
                            if "timestamp" in record_data and isinstance(record_data["timestamp"], str):
                                # datetime is already imported at module level
                                record_data["timestamp"] = datetime.fromisoformat(record_data["timestamp"])
                            vh.append(VerificationRecord(**record_data))
                        else:
                            vh.append(record_data)
                    evolution_data["verification_history"] = vh
                layer.temporal_dynamics[kid] = KnowledgeEvolution(**evolution_data)
            else:
                layer.temporal_dynamics[kid] = evolution_data
        
        # Reconstruct memory-knowledge mapping
        mapping_data = data.get("memory_knowledge_mapping", {})
        if isinstance(mapping_data, dict):
            # Convert string keys to int if needed (JSON serialization)
            for key, value in mapping_data.items():
                memory_id = int(key) if isinstance(key, str) else key
                layer.memory_knowledge_mapping[memory_id] = value
        
        return layer

