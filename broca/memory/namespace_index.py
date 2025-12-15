"""
Namespace index generator for memory system.

Generates and maintains a markdown index file mapping the memory namespace hierarchy.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Any, Set

from .storage import MemoryStorage

logger = logging.getLogger(__name__)


class NamespaceIndexGenerator:
    """
    Generates and maintains a markdown index of memory namespaces.
    
    Creates a hierarchical tree structure from flat namespace strings and
    generates a markdown file for easy navigation of the memory hierarchy.
    """
    
    def __init__(self, storage: MemoryStorage) -> None:
        """
        Initialize namespace index generator.
        
        Args:
            storage: MemoryStorage instance to query for namespaces
        """
        self.storage = storage
        self._cached_namespaces: Set[str] = set()
    
    def get_all_namespaces(self) -> List[str]:
        """
        Get all unique namespaces from storage.
        
        Returns:
            List of unique namespace strings, sorted alphabetically
        """
        try:
            namespaces = self.storage.get_all_namespaces()
            self._cached_namespaces = set(namespaces)
            return namespaces
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}", exc_info=True)
            return []
    
    def build_namespace_tree(self, namespaces: List[str]) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from flat namespace list.
        
        Args:
            namespaces: List of namespace strings (e.g., ["math.sage.api", "math.numpy"])
            
        Returns:
            Nested dictionary representing the namespace tree
        """
        tree: Dict[str, Any] = {}
        
        for namespace in namespaces:
            if not namespace or not namespace.strip():
                continue
            
            parts = namespace.split('.')
            current = tree
            
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                
                if part not in current:
                    current[part] = {
                        "children": {},
                        "is_leaf": False
                    }
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def generate_markdown(self, tree: Dict[str, Any]) -> str:
        """
        Generate markdown content from namespace tree.
        
        Args:
            tree: Namespace tree structure from build_namespace_tree
            
        Returns:
            Markdown string representing the namespace hierarchy
        """
        lines = [
            "# Memory Namespace Index",
            "",
            "Auto-generated index of memory namespaces. This file is automatically updated when new namespaces are created.",
            "",
            "## Namespace Hierarchy",
            ""
        ]
        
        def render_tree(node: Dict[str, Any], indent: int = 0) -> List[str]:
            """Recursively render tree nodes."""
            result = []
            prefix = "  " * indent + "- "
            
            # Sort keys alphabetically for consistent output
            sorted_keys = sorted(node.keys())
            
            for key in sorted_keys:
                node_data = node[key]
                result.append(f"{prefix}{key}")
                
                # Render children if any
                if node_data["children"]:
                    result.extend(render_tree(node_data["children"], indent + 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def get_index_path(self) -> Path:
        """
        Get path to the index file.
        
        Returns:
            Path object pointing to the index markdown file
        """
        # Index file is in the same directory as the database
        db_path = Path(self.storage.db_path)
        return db_path.parent / "memory_namespaces_index.md"
    
    def update_index(self) -> None:
        """
        Update or create the namespace index file.
        
        Queries all namespaces from storage, builds the tree, and writes
        the markdown file.
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            markdown = self.generate_markdown(tree)
            
            index_path = self.get_index_path()
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def is_namespace_new(self, namespace: str) -> bool:
        """
        Check if a namespace is new (not in cached namespaces).
        
        Note: This is a simple check based on cached namespaces. For accurate
        results, call get_all_namespaces() first to refresh the cache.
        
        Args:
            namespace: Namespace string to check
            
        Returns:
            True if namespace is not in cache, False otherwise
        """
        return namespace not in self._cached_namespaces

