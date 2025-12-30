"""
Action Map for RL Policy.

Maps tool names to action IDs for reinforcement learning.
"""

import json
import os
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ActionMap:
    """Maps tool names to action IDs."""
    
    def __init__(self):
        self.tool_to_id: Dict[str, int] = {}
        self.id_to_tool: Dict[int, str] = {}
        self.next_id: int = 0
        
    def add_tool(self, tool_name: str) -> int:
        """Add a tool to the action map."""
        if tool_name in self.tool_to_id:
            return self.tool_to_id[tool_name]
            
        action_id = self.next_id
        self.tool_to_id[tool_name] = action_id
        self.id_to_tool[action_id] = tool_name
        self.next_id += 1
        
        logger.debug(f"Added tool '{tool_name}' with action_id {action_id}")
        return action_id
    
    def get_action_id(self, tool_name: str) -> Optional[int]:
        """Get action ID for a tool name."""
        return self.tool_to_id.get(tool_name)
    
    def get_tool_name(self, action_id: int) -> Optional[str]:
        """Get tool name for an action ID."""
        return self.id_to_tool.get(action_id)
    
    def get_all_tools(self) -> List[str]:
        """Get all tool names."""
        return list(self.tool_to_id.keys())
    
    def get_all_action_ids(self) -> List[int]:
        """Get all action IDs."""
        return list(self.id_to_tool.keys())
    
    def size(self) -> int:
        """Get the size of the action map."""
        return len(self.tool_to_id)
    
    def save_to_file(self, filepath: str) -> bool:
        """Save action map to JSON file."""
        try:
            data = {
                "tool_to_id": self.tool_to_id,
                "id_to_tool": {str(k): v for k, v in self.id_to_tool.items()},
                "next_id": self.next_id
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved action map to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save action map: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """Load action map from JSON file."""
        try:
            if not os.path.exists(filepath):
                logger.error(f"Action map file not found: {filepath}")
                return False
                
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.tool_to_id = data.get("tool_to_id", {})
            self.id_to_tool = {int(k): v for k, v in data.get("id_to_tool", {}).items()}
            self.next_id = data.get("next_id", 0)
            
            logger.info(f"Loaded action map from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load action map: {e}")
            return False
    
    def load_from_dict(self, data: Dict[str, Any]) -> bool:
        """Load action map from dictionary."""
        try:
            self.tool_to_id = data.get("tool_to_id", {})
            self.id_to_tool = {int(k): v for k, v in data.get("id_to_tool", {}).items()}
            self.next_id = data.get("next_id", 0)
            
            logger.info("Loaded action map from dictionary")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load action map from dict: {e}")
            return False
    
    def load_from_csv(self, csv_path: str) -> bool:
        """Load action map from CSV file."""
        try:
            import csv
            
            if not os.path.exists(csv_path):
                logger.error(f"CSV file not found: {csv_path}")
                return False
                
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tool_name = row.get('tool_name')
                    action_id = int(row.get('action_id', 0))
                    
                    if tool_name:
                        self.tool_to_id[tool_name] = action_id
                        self.id_to_tool[action_id] = tool_name
                        self.next_id = max(self.next_id, action_id + 1)
            
            logger.info(f"Loaded action map from CSV: {csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load action map from CSV: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action map to dictionary."""
        return {
            "tool_to_id": self.tool_to_id,
            "id_to_tool": {str(k): v for k, v in self.id_to_tool.items()},
            "next_id": self.next_id
        }
    
    def __str__(self) -> str:
        """String representation of action map."""
        lines = ["ActionMap:"]
        for tool_name, action_id in sorted(self.tool_to_id.items()):
            lines.append(f"  {tool_name}: {action_id}")
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """Representation of action map."""
        return f"ActionMap(size={self.size()})"
