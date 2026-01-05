"""
World state formatter that converts aggregated state to JSON.

Formats world state data as compact JSON for inclusion in LLM system prompts.
Optimized for token efficiency - uses minimal whitespace.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class WorldStateFormatter:
    """
    Formats world state data as JSON for system prompts.
    
    Converts structured world state data into compact JSON
    suitable for inclusion in LLM system prompts.
    Optimized for token efficiency by removing unnecessary whitespace.
    """
    
    def __init__(self, max_length: Optional[int] = None) -> None:
        """
        Initialize formatter.
        
        Args:
            max_length: Optional maximum length for formatted output.
                       If None, uses config.storage.max_world_state_size
        """
        if max_length is None:
            from ..config import config
            max_length = config.storage.max_world_state_size
        self.max_length = max_length
        logger.debug(f"Initialized WorldStateFormatter (max_length={max_length})")
    
    def format(self, world_state: Dict[str, Any]) -> str:
        """
        Format world state as compact JSON for system prompt.
        
        Args:
            world_state: Aggregated world state dictionary (clean hierarchical structure)
            
        Returns:
            Compact JSON string for system prompt (optimized for token efficiency)
        """
        # Convert to JSON with compact formatting (no whitespace)
        json_str = json.dumps(world_state, separators=(',', ':'), ensure_ascii=False, sort_keys=False)
        
        # Apply length limit if specified
        if self.max_length and len(json_str) > self.max_length:
            # For very small limits, just return a minimal message
            if self.max_length < 50:
                json_str = '{"_truncated":true,"_message":"World state too large"}'
                logger.warning(f"World state JSON truncated to minimal message (limit: {self.max_length})")
            else:
                # For compact JSON, truncate and close with truncation marker
                truncation_msg = ',"_truncated":true}'
                max_content_length = self.max_length - len(truncation_msg)
                
                # Find a safe truncation point (after a comma)
                truncated = json_str[:max_content_length]
                # Look for last comma to truncate cleanly
                last_comma = truncated.rfind(',')
                if last_comma > 0:
                    truncated = truncated[:last_comma]
                
                # Count braces/brackets to close properly
                open_braces = truncated.count('{') - truncated.count('}')
                open_brackets = truncated.count('[') - truncated.count(']')
                
                # Close any open structures
                closing = ']' * open_brackets + '}' * max(0, open_braces - 1)  # -1 because truncation_msg adds one
                json_str = truncated + closing + truncation_msg
                
                logger.warning(f"World state JSON truncated to {self.max_length} characters")
        
        return json_str
