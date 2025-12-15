"""
EpistemicStorage for detailed epistemic history.

Uses JSON storage for detailed verification history and knowledge evolution
(hybrid approach: basic metadata in self_model.json, detailed history here).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
import logging

from .models import VerificationRecord, KnowledgeEvolution
from .ids import KnowledgeID

logger = logging.getLogger(__name__)


class EpistemicStorage:
    """
    Storage for detailed epistemic history.
    
    Stores verification history and knowledge evolution in JSON format.
    Basic metadata is stored in self_model.json (hybrid approach).
    """
    
    def __init__(self, storage_path: str = "epistemic_history.json", auto_save: bool = False) -> None:
        """
        Initialize epistemic storage.
        
        Args:
            storage_path: Path to JSON file for storing detailed history
            auto_save: If True, automatically save on every change
        """
        self.storage_path = Path(storage_path)
        self.auto_save = auto_save
        self._verification_history: Dict[KnowledgeID, List[VerificationRecord]] = {}
        self._knowledge_evolution: Dict[KnowledgeID, KnowledgeEvolution] = {}
        
        # Create parent directory if needed
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data if file exists
        if self.storage_path.exists():
            self._load()
        else:
            # Create empty file
            self.save()
            logger.info(f"Initialized EpistemicStorage at {self.storage_path.absolute()}")
    
    def _load(self) -> None:
        """Load data from storage file."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load verification history
            self._verification_history = {}
            for kid, records_data in data.get("verification_history", {}).items():
                self._verification_history[kid] = []
                for record_data in records_data:
                    # Convert timestamp string to datetime
                    if "timestamp" in record_data and isinstance(record_data["timestamp"], str):
                        record_data["timestamp"] = datetime.fromisoformat(record_data["timestamp"])
                    # Convert new_evidence
                    if "new_evidence" in record_data:
                        from .models import SourceMetadata
                        evidence = []
                        for ev_data in record_data["new_evidence"]:
                            evidence.append(SourceMetadata(**ev_data))
                        record_data["new_evidence"] = evidence
                    self._verification_history[kid].append(VerificationRecord(**record_data))
            
            # Load knowledge evolution
            self._knowledge_evolution = {}
            for kid, evolution_data in data.get("knowledge_evolution", {}).items():
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
                                record_data["timestamp"] = datetime.fromisoformat(record_data["timestamp"])
                            if "new_evidence" in record_data:
                                from .models import SourceMetadata
                                evidence = []
                                for ev_data in record_data["new_evidence"]:
                                    evidence.append(SourceMetadata(**ev_data))
                                record_data["new_evidence"] = evidence
                            vh.append(VerificationRecord(**record_data))
                        else:
                            vh.append(record_data)
                    evolution_data["verification_history"] = vh
                self._knowledge_evolution[kid] = KnowledgeEvolution(**evolution_data)
            
            logger.debug(f"Loaded epistemic storage from {self.storage_path}")
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load epistemic storage: {e}", exc_info=True)
            # Start with empty data
            self._verification_history = {}
            self._knowledge_evolution = {}
    
    def save(self) -> None:
        """Save data to storage file."""
        try:
            # Prepare data structure
            data = {
                "verification_history": {
                    kid: [record.model_dump() for record in records]
                    for kid, records in self._verification_history.items()
                },
                "knowledge_evolution": {
                    kid: evolution.model_dump()
                    for kid, evolution in self._knowledge_evolution.items()
                },
                "last_saved": datetime.now().isoformat(),
            }
            
            # Atomic write
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.storage_path.parent,
                delete=False,
                suffix='.tmp'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False, default=str)
                tmp_path = tmp_file.name
            
            # Atomic rename
            os.replace(tmp_path, self.storage_path)
            
            logger.debug(f"Saved epistemic storage to {self.storage_path}")
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to save epistemic storage: {e}", exc_info=True)
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise
    
    def add_verification_record(self, knowledge_id: KnowledgeID, record: VerificationRecord) -> None:
        """Add a verification record to history."""
        if knowledge_id not in self._verification_history:
            self._verification_history[knowledge_id] = []
        self._verification_history[knowledge_id].append(record)
        
        if self.auto_save:
            self.save()
    
    def get_verification_history(self, knowledge_id: KnowledgeID) -> List[VerificationRecord]:
        """Get verification history for a knowledge item."""
        return self._verification_history.get(knowledge_id, [])
    
    def get_verification_count(self, knowledge_id: KnowledgeID) -> int:
        """Get count of verification records for a knowledge item."""
        return len(self._verification_history.get(knowledge_id, []))
    
    def add_knowledge_evolution(self, knowledge_id: KnowledgeID, evolution: KnowledgeEvolution) -> None:
        """Add or update knowledge evolution tracking."""
        self._knowledge_evolution[knowledge_id] = evolution
        
        if self.auto_save:
            self.save()
    
    def get_knowledge_evolution(self, knowledge_id: KnowledgeID) -> Optional[KnowledgeEvolution]:
        """Get knowledge evolution for a knowledge item."""
        return self._knowledge_evolution.get(knowledge_id)
    
    def get_all_knowledge_ids(self) -> Set[KnowledgeID]:
        """Get all knowledge IDs that have epistemic data."""
        ids: Set[KnowledgeID] = set()
        ids.update(self._verification_history.keys())
        ids.update(self._knowledge_evolution.keys())
        return ids
    
    def clear(self) -> None:
        """Clear all stored data."""
        self._verification_history = {}
        self._knowledge_evolution = {}
        
        if self.auto_save:
            self.save()

