"""
World state formatter that converts aggregated state to JSON.

Formats world state data as pretty-printed JSON for inclusion in LLM system prompts.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class WorldStateFormatter:
    """
    Formats world state data as JSON for system prompts.
    
    Converts structured world state data into pretty-printed JSON
    suitable for inclusion in LLM system prompts.
    """
    
    def __init__(self, max_length: Optional[int] = None) -> None:
        """
        Initialize formatter.
        
        Args:
            max_length: Optional maximum length for formatted output (None = no limit)
        """
        self.max_length = max_length
        logger.debug(f"Initialized WorldStateFormatter (max_length={max_length})")
    
    def format(self, world_state: Dict[str, Any]) -> str:
        """
        Format world state as pretty-printed JSON for system prompt.
        
        Args:
            world_state: Aggregated world state dictionary (clean hierarchical structure)
            
        Returns:
            Pretty-printed JSON string for system prompt
        """
        # Convert to JSON with pretty printing
        json_str = json.dumps(world_state, indent=2, ensure_ascii=False, sort_keys=False)
        
        # Apply length limit if specified
        if self.max_length and len(json_str) > self.max_length:
            # For very small limits, just return a minimal message
            if self.max_length < 50:
                json_str = '{"_truncated": true, "_message": "World state too large"}'
                logger.warning(f"World state JSON truncated to minimal message (limit: {self.max_length})")
            else:
                # Try to truncate at a reasonable point (end of a complete JSON structure)
                # Find the last complete key-value pair before the limit
                truncation_msg = ',\n  "_truncated": true\n}'
                max_content_length = self.max_length - len(truncation_msg)
                
                # Find last complete line that ends with a comma or closing brace
                truncated = json_str[:max_content_length]
                # Look backwards for a line ending with ',' or '}' or ']'
                lines = truncated.split('\n')
                # Remove incomplete last line
                if lines:
                    lines.pop()
                # Reconstruct, ensuring we end properly
                truncated = '\n'.join(lines)
                # Remove trailing comma if present (but keep structure intact)
                truncated = truncated.rstrip()
                if truncated.endswith(','):
                    truncated = truncated[:-1].rstrip()
                # Ensure we close any open structures properly
                if not truncated.endswith('}'):
                    # Count open braces to close them
                    open_braces = truncated.count('{') - truncated.count('}')
                    truncated = truncated.rstrip().rstrip(',')
                    truncated += '\n' + '  ' * (open_braces - 1) + '}'
                # Add truncation marker
                json_str = truncated + truncation_msg
                
                logger.warning(f"World state JSON truncated to {self.max_length} characters")
        
        return json_str

