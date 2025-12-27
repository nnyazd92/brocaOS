"""
Storage for internal sensing state persistence.

Handles saving and loading of moving average histories to/from disk.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class InternalSensingStorage:
    """
    Storage for internal sensing state.
    
    Persists moving average histories to disk so they survive restarts.
    """
    
    def __init__(self, state_path: str) -> None:
        """
        Initialize storage.
        
        Args:
            state_path: Path to state file (JSON)
        """
        self.state_path = Path(state_path)
        # Ensure parent directory exists
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized InternalSensingStorage with path: {self.state_path}")
    
    def save_state(
        self,
        cognitive_histories: Dict[str, List[Dict[str, Any]]],
        affective_histories: Dict[str, List[float]],
        physiology_histories: Dict[str, List[float]],
    ) -> None:
        """
        Save moving average histories to disk.
        
        Args:
            cognitive_histories: Dict mapping history names to lists of entries
            affective_histories: Dict mapping history names to lists of float values
            physiology_histories: Dict mapping history names to lists of float values
        """
        try:
            # Prepare data structure
            data = {
                "cognitive": cognitive_histories,
                "affective": affective_histories,
                "physiology": physiology_histories,
                "last_saved": datetime.utcnow().isoformat() + "Z",
            }
            
            # Atomic write: write to temp file, then rename
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.state_path.parent,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False, default=str)
                tmp_path = Path(tmp_file.name)
            
            # Atomic rename
            tmp_path.replace(self.state_path)
            
            logger.debug(f"Saved internal sensing state to {self.state_path}")
            
        except Exception as e:
            logger.error(f"Failed to save internal sensing state: {e}", exc_info=True)
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise
    
    def load_state(
        self,
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Load moving average histories from disk.
        
        Returns:
            Dictionary with keys "cognitive", "affective", "physiology", each containing
            history dictionaries, or None if file doesn't exist or is corrupted
        """
        if not self.state_path.exists():
            logger.debug(f"Internal sensing state file not found: {self.state_path}")
            return None
        
        try:
            with open(self.state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if not isinstance(data, dict):
                logger.warning(f"Invalid state file format: expected dict, got {type(data)}")
                return None
            
            # Ensure all required keys exist
            result = {
                "cognitive": data.get("cognitive", {}),
                "affective": data.get("affective", {}),
                "physiology": data.get("physiology", {}),
            }
            
            logger.info(f"Loaded internal sensing state from {self.state_path}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse internal sensing state file: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to load internal sensing state: {e}", exc_info=True)
            return None
    
    def clear_state(self) -> None:
        """
        Clear persisted state (delete file).
        """
        try:
            if self.state_path.exists():
                self.state_path.unlink()
                logger.info(f"Cleared internal sensing state file: {self.state_path}")
        except Exception as e:
            logger.warning(f"Failed to clear internal sensing state: {e}", exc_info=True)

