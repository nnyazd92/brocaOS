"""
Namespace index generator for memory system.

Generates and maintains a markdown index file mapping the memory namespace hierarchy.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timezone

from .storage import MemoryStorage

logger = logging.getLogger(__name__)
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class NamespaceIndexGenerator:
    """
    Generates and maintains a markdown index of memory namespaces.
    
    Creates a hierarchical tree structure from flat namespace strings and
    generates a markdown file for easy navigation of the memory hierarchy.
    """
    
    def xǁNamespaceIndexGeneratorǁ__init____mutmut_orig(self, storage: MemoryStorage) -> None:
        """
        Initialize namespace index generator.
        
        Args:
            storage: MemoryStorage instance to query for namespaces
        """
        self.storage = storage
        self._cached_namespaces: Set[str] = set()
        self._last_indexed: Optional[datetime] = None
    
    def xǁNamespaceIndexGeneratorǁ__init____mutmut_1(self, storage: MemoryStorage) -> None:
        """
        Initialize namespace index generator.
        
        Args:
            storage: MemoryStorage instance to query for namespaces
        """
        self.storage = None
        self._cached_namespaces: Set[str] = set()
        self._last_indexed: Optional[datetime] = None
    
    def xǁNamespaceIndexGeneratorǁ__init____mutmut_2(self, storage: MemoryStorage) -> None:
        """
        Initialize namespace index generator.
        
        Args:
            storage: MemoryStorage instance to query for namespaces
        """
        self.storage = storage
        self._cached_namespaces: Set[str] = None
        self._last_indexed: Optional[datetime] = None
    
    def xǁNamespaceIndexGeneratorǁ__init____mutmut_3(self, storage: MemoryStorage) -> None:
        """
        Initialize namespace index generator.
        
        Args:
            storage: MemoryStorage instance to query for namespaces
        """
        self.storage = storage
        self._cached_namespaces: Set[str] = set()
        self._last_indexed: Optional[datetime] = ""
    
    xǁNamespaceIndexGeneratorǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁ__init____mutmut_1': xǁNamespaceIndexGeneratorǁ__init____mutmut_1, 
        'xǁNamespaceIndexGeneratorǁ__init____mutmut_2': xǁNamespaceIndexGeneratorǁ__init____mutmut_2, 
        'xǁNamespaceIndexGeneratorǁ__init____mutmut_3': xǁNamespaceIndexGeneratorǁ__init____mutmut_3
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁ__init____mutmut_orig)
    xǁNamespaceIndexGeneratorǁ__init____mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁ__init__'
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_orig(self) -> List[str]:
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
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_1(self) -> List[str]:
        """
        Get all unique namespaces from storage.
        
        Returns:
            List of unique namespace strings, sorted alphabetically
        """
        try:
            namespaces = None
            self._cached_namespaces = set(namespaces)
            return namespaces
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}", exc_info=True)
            return []
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_2(self) -> List[str]:
        """
        Get all unique namespaces from storage.
        
        Returns:
            List of unique namespace strings, sorted alphabetically
        """
        try:
            namespaces = self.storage.get_all_namespaces()
            self._cached_namespaces = None
            return namespaces
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}", exc_info=True)
            return []
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_3(self) -> List[str]:
        """
        Get all unique namespaces from storage.
        
        Returns:
            List of unique namespace strings, sorted alphabetically
        """
        try:
            namespaces = self.storage.get_all_namespaces()
            self._cached_namespaces = set(None)
            return namespaces
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}", exc_info=True)
            return []
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_4(self) -> List[str]:
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
            logger.error(None, exc_info=True)
            return []
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_5(self) -> List[str]:
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
            logger.error(f"Error getting namespaces: {e}", exc_info=None)
            return []
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_6(self) -> List[str]:
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
            logger.error(exc_info=True)
            return []
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_7(self) -> List[str]:
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
            logger.error(f"Error getting namespaces: {e}", )
            return []
    
    def xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_8(self) -> List[str]:
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
            logger.error(f"Error getting namespaces: {e}", exc_info=False)
            return []
    
    xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_1': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_1, 
        'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_2': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_2, 
        'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_3': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_3, 
        'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_4': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_4, 
        'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_5': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_5, 
        'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_6': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_6, 
        'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_7': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_7, 
        'xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_8': xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_8
    }
    
    def get_all_namespaces(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_all_namespaces.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_orig)
    xǁNamespaceIndexGeneratorǁget_all_namespaces__mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁget_all_namespaces'
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_orig(self, namespaces: List[str]) -> Dict[str, Any]:
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_1(self, namespaces: List[str]) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from flat namespace list.
        
        Args:
            namespaces: List of namespace strings (e.g., ["math.sage.api", "math.numpy"])
            
        Returns:
            Nested dictionary representing the namespace tree
        """
        tree: Dict[str, Any] = None
        
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_2(self, namespaces: List[str]) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from flat namespace list.
        
        Args:
            namespaces: List of namespace strings (e.g., ["math.sage.api", "math.numpy"])
            
        Returns:
            Nested dictionary representing the namespace tree
        """
        tree: Dict[str, Any] = {}
        
        for namespace in namespaces:
            if not namespace and not namespace.strip():
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_3(self, namespaces: List[str]) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from flat namespace list.
        
        Args:
            namespaces: List of namespace strings (e.g., ["math.sage.api", "math.numpy"])
            
        Returns:
            Nested dictionary representing the namespace tree
        """
        tree: Dict[str, Any] = {}
        
        for namespace in namespaces:
            if namespace or not namespace.strip():
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_4(self, namespaces: List[str]) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from flat namespace list.
        
        Args:
            namespaces: List of namespace strings (e.g., ["math.sage.api", "math.numpy"])
            
        Returns:
            Nested dictionary representing the namespace tree
        """
        tree: Dict[str, Any] = {}
        
        for namespace in namespaces:
            if not namespace or namespace.strip():
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_5(self, namespaces: List[str]) -> Dict[str, Any]:
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
                break
            
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_6(self, namespaces: List[str]) -> Dict[str, Any]:
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
            
            parts = None
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_7(self, namespaces: List[str]) -> Dict[str, Any]:
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
            
            parts = namespace.split(None)
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_8(self, namespaces: List[str]) -> Dict[str, Any]:
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
            
            parts = namespace.split('XX.XX')
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_9(self, namespaces: List[str]) -> Dict[str, Any]:
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
            current = None
            
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_10(self, namespaces: List[str]) -> Dict[str, Any]:
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
            
            for i, part in enumerate(None):
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_11(self, namespaces: List[str]) -> Dict[str, Any]:
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
                part = None
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_12(self, namespaces: List[str]) -> Dict[str, Any]:
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
                if part:
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_13(self, namespaces: List[str]) -> Dict[str, Any]:
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
                    break
                
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
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_14(self, namespaces: List[str]) -> Dict[str, Any]:
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
                
                if part in current:
                    current[part] = {
                        "children": {},
                        "is_leaf": False
                    }
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_15(self, namespaces: List[str]) -> Dict[str, Any]:
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
                    current[part] = None
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_16(self, namespaces: List[str]) -> Dict[str, Any]:
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
                        "XXchildrenXX": {},
                        "is_leaf": False
                    }
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_17(self, namespaces: List[str]) -> Dict[str, Any]:
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
                        "CHILDREN": {},
                        "is_leaf": False
                    }
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_18(self, namespaces: List[str]) -> Dict[str, Any]:
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
                        "XXis_leafXX": False
                    }
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_19(self, namespaces: List[str]) -> Dict[str, Any]:
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
                        "IS_LEAF": False
                    }
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_20(self, namespaces: List[str]) -> Dict[str, Any]:
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
                        "is_leaf": True
                    }
                
                # Mark as leaf if this is the last part
                if i == len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_21(self, namespaces: List[str]) -> Dict[str, Any]:
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
                if i != len(parts) - 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_22(self, namespaces: List[str]) -> Dict[str, Any]:
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
                if i == len(parts) + 1:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_23(self, namespaces: List[str]) -> Dict[str, Any]:
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
                if i == len(parts) - 2:
                    current[part]["is_leaf"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_24(self, namespaces: List[str]) -> Dict[str, Any]:
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
                    current[part]["is_leaf"] = None
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_25(self, namespaces: List[str]) -> Dict[str, Any]:
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
                    current[part]["XXis_leafXX"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_26(self, namespaces: List[str]) -> Dict[str, Any]:
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
                    current[part]["IS_LEAF"] = True
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_27(self, namespaces: List[str]) -> Dict[str, Any]:
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
                    current[part]["is_leaf"] = False
                
                current = current[part]["children"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_28(self, namespaces: List[str]) -> Dict[str, Any]:
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
                
                current = None
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_29(self, namespaces: List[str]) -> Dict[str, Any]:
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
                
                current = current[part]["XXchildrenXX"]
        
        return tree
    
    def xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_30(self, namespaces: List[str]) -> Dict[str, Any]:
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
                
                current = current[part]["CHILDREN"]
        
        return tree
    
    xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_1': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_1, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_2': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_2, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_3': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_3, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_4': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_4, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_5': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_5, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_6': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_6, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_7': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_7, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_8': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_8, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_9': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_9, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_10': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_10, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_11': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_11, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_12': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_12, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_13': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_13, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_14': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_14, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_15': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_15, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_16': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_16, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_17': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_17, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_18': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_18, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_19': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_19, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_20': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_20, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_21': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_21, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_22': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_22, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_23': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_23, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_24': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_24, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_25': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_25, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_26': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_26, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_27': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_27, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_28': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_28, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_29': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_29, 
        'xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_30': xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_30
    }
    
    def build_namespace_tree(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_mutants"), args, kwargs, self)
        return result 
    
    build_namespace_tree.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_orig)
    xǁNamespaceIndexGeneratorǁbuild_namespace_tree__mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁbuild_namespace_tree'
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_orig(self, tree: Dict[str, Any]) -> str:
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_1(self, tree: Dict[str, Any]) -> str:
        """
        Generate markdown content from namespace tree.
        
        Args:
            tree: Namespace tree structure from build_namespace_tree
            
        Returns:
            Markdown string representing the namespace hierarchy
        """
        lines = None
        
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_2(self, tree: Dict[str, Any]) -> str:
        """
        Generate markdown content from namespace tree.
        
        Args:
            tree: Namespace tree structure from build_namespace_tree
            
        Returns:
            Markdown string representing the namespace hierarchy
        """
        lines = [
            "XX# Memory Namespace IndexXX",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_3(self, tree: Dict[str, Any]) -> str:
        """
        Generate markdown content from namespace tree.
        
        Args:
            tree: Namespace tree structure from build_namespace_tree
            
        Returns:
            Markdown string representing the namespace hierarchy
        """
        lines = [
            "# memory namespace index",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_4(self, tree: Dict[str, Any]) -> str:
        """
        Generate markdown content from namespace tree.
        
        Args:
            tree: Namespace tree structure from build_namespace_tree
            
        Returns:
            Markdown string representing the namespace hierarchy
        """
        lines = [
            "# MEMORY NAMESPACE INDEX",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_5(self, tree: Dict[str, Any]) -> str:
        """
        Generate markdown content from namespace tree.
        
        Args:
            tree: Namespace tree structure from build_namespace_tree
            
        Returns:
            Markdown string representing the namespace hierarchy
        """
        lines = [
            "# Memory Namespace Index",
            "XXXX",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_6(self, tree: Dict[str, Any]) -> str:
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
            "XXAuto-generated index of memory namespaces. This file is automatically updated when new namespaces are created.XX",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_7(self, tree: Dict[str, Any]) -> str:
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
            "auto-generated index of memory namespaces. this file is automatically updated when new namespaces are created.",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_8(self, tree: Dict[str, Any]) -> str:
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
            "AUTO-GENERATED INDEX OF MEMORY NAMESPACES. THIS FILE IS AUTOMATICALLY UPDATED WHEN NEW NAMESPACES ARE CREATED.",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_9(self, tree: Dict[str, Any]) -> str:
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
            "XXXX",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_10(self, tree: Dict[str, Any]) -> str:
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
            "XX## Namespace HierarchyXX",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_11(self, tree: Dict[str, Any]) -> str:
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
            "## namespace hierarchy",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_12(self, tree: Dict[str, Any]) -> str:
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
            "## NAMESPACE HIERARCHY",
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_13(self, tree: Dict[str, Any]) -> str:
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
            "XXXX"
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_14(self, tree: Dict[str, Any]) -> str:
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
        
        def render_tree(node: Dict[str, Any], indent: int = 1) -> List[str]:
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_15(self, tree: Dict[str, Any]) -> str:
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
            result = None
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_16(self, tree: Dict[str, Any]) -> str:
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
            prefix = None
            
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_17(self, tree: Dict[str, Any]) -> str:
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
            prefix = "  " * indent - "- "
            
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_18(self, tree: Dict[str, Any]) -> str:
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
            prefix = "  " / indent + "- "
            
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_19(self, tree: Dict[str, Any]) -> str:
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
            prefix = "XX  XX" * indent + "- "
            
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_20(self, tree: Dict[str, Any]) -> str:
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
            prefix = "  " * indent + "XX- XX"
            
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_21(self, tree: Dict[str, Any]) -> str:
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
            sorted_keys = None
            
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_22(self, tree: Dict[str, Any]) -> str:
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
            sorted_keys = sorted(None)
            
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_23(self, tree: Dict[str, Any]) -> str:
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
                node_data = None
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_24(self, tree: Dict[str, Any]) -> str:
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
                result.append(None)
                
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
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_25(self, tree: Dict[str, Any]) -> str:
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
                if node_data["XXchildrenXX"]:
                    result.extend(render_tree(node_data["children"], indent + 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_26(self, tree: Dict[str, Any]) -> str:
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
                if node_data["CHILDREN"]:
                    result.extend(render_tree(node_data["children"], indent + 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_27(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(None)
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_28(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(None, indent + 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_29(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(node_data["children"], None))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_30(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(indent + 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_31(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(node_data["children"], ))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_32(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(node_data["XXchildrenXX"], indent + 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_33(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(node_data["CHILDREN"], indent + 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_34(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(node_data["children"], indent - 1))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_35(self, tree: Dict[str, Any]) -> str:
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
                    result.extend(render_tree(node_data["children"], indent + 2))
            
            return result
        
        if tree:
            lines.extend(render_tree(tree))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_36(self, tree: Dict[str, Any]) -> str:
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
            lines.extend(None)
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_37(self, tree: Dict[str, Any]) -> str:
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
            lines.extend(render_tree(None))
        else:
            lines.append("(No namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_38(self, tree: Dict[str, Any]) -> str:
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
            lines.append(None)
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_39(self, tree: Dict[str, Any]) -> str:
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
            lines.append("XX(No namespaces found)XX")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_40(self, tree: Dict[str, Any]) -> str:
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
            lines.append("(no namespaces found)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_41(self, tree: Dict[str, Any]) -> str:
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
            lines.append("(NO NAMESPACES FOUND)")
        
        lines.append("")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_42(self, tree: Dict[str, Any]) -> str:
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
        
        lines.append(None)
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_43(self, tree: Dict[str, Any]) -> str:
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
        
        lines.append("XXXX")
        return "\n".join(lines)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_44(self, tree: Dict[str, Any]) -> str:
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
        return "\n".join(None)
    
    def xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_45(self, tree: Dict[str, Any]) -> str:
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
        return "XX\nXX".join(lines)
    
    xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_1': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_1, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_2': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_2, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_3': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_3, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_4': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_4, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_5': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_5, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_6': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_6, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_7': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_7, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_8': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_8, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_9': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_9, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_10': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_10, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_11': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_11, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_12': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_12, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_13': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_13, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_14': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_14, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_15': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_15, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_16': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_16, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_17': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_17, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_18': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_18, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_19': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_19, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_20': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_20, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_21': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_21, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_22': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_22, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_23': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_23, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_24': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_24, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_25': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_25, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_26': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_26, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_27': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_27, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_28': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_28, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_29': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_29, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_30': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_30, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_31': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_31, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_32': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_32, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_33': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_33, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_34': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_34, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_35': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_35, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_36': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_36, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_37': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_37, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_38': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_38, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_39': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_39, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_40': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_40, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_41': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_41, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_42': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_42, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_43': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_43, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_44': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_44, 
        'xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_45': xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_45
    }
    
    def generate_markdown(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_mutants"), args, kwargs, self)
        return result 
    
    generate_markdown.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_orig)
    xǁNamespaceIndexGeneratorǁgenerate_markdown__mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁgenerate_markdown'
    
    def xǁNamespaceIndexGeneratorǁget_index_path__mutmut_orig(self) -> Path:
        """
        Get path to the index file.
        
        Returns:
            Path object pointing to the index markdown file
        """
        # Index file is in the same directory as the database
        db_path = Path(self.storage.db_path)
        return db_path.parent / "memory_namespaces_index.md"
    
    def xǁNamespaceIndexGeneratorǁget_index_path__mutmut_1(self) -> Path:
        """
        Get path to the index file.
        
        Returns:
            Path object pointing to the index markdown file
        """
        # Index file is in the same directory as the database
        db_path = None
        return db_path.parent / "memory_namespaces_index.md"
    
    def xǁNamespaceIndexGeneratorǁget_index_path__mutmut_2(self) -> Path:
        """
        Get path to the index file.
        
        Returns:
            Path object pointing to the index markdown file
        """
        # Index file is in the same directory as the database
        db_path = Path(None)
        return db_path.parent / "memory_namespaces_index.md"
    
    def xǁNamespaceIndexGeneratorǁget_index_path__mutmut_3(self) -> Path:
        """
        Get path to the index file.
        
        Returns:
            Path object pointing to the index markdown file
        """
        # Index file is in the same directory as the database
        db_path = Path(self.storage.db_path)
        return db_path.parent * "memory_namespaces_index.md"
    
    def xǁNamespaceIndexGeneratorǁget_index_path__mutmut_4(self) -> Path:
        """
        Get path to the index file.
        
        Returns:
            Path object pointing to the index markdown file
        """
        # Index file is in the same directory as the database
        db_path = Path(self.storage.db_path)
        return db_path.parent / "XXmemory_namespaces_index.mdXX"
    
    def xǁNamespaceIndexGeneratorǁget_index_path__mutmut_5(self) -> Path:
        """
        Get path to the index file.
        
        Returns:
            Path object pointing to the index markdown file
        """
        # Index file is in the same directory as the database
        db_path = Path(self.storage.db_path)
        return db_path.parent / "MEMORY_NAMESPACES_INDEX.MD"
    
    xǁNamespaceIndexGeneratorǁget_index_path__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁget_index_path__mutmut_1': xǁNamespaceIndexGeneratorǁget_index_path__mutmut_1, 
        'xǁNamespaceIndexGeneratorǁget_index_path__mutmut_2': xǁNamespaceIndexGeneratorǁget_index_path__mutmut_2, 
        'xǁNamespaceIndexGeneratorǁget_index_path__mutmut_3': xǁNamespaceIndexGeneratorǁget_index_path__mutmut_3, 
        'xǁNamespaceIndexGeneratorǁget_index_path__mutmut_4': xǁNamespaceIndexGeneratorǁget_index_path__mutmut_4, 
        'xǁNamespaceIndexGeneratorǁget_index_path__mutmut_5': xǁNamespaceIndexGeneratorǁget_index_path__mutmut_5
    }
    
    def get_index_path(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁget_index_path__mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁget_index_path__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_index_path.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁget_index_path__mutmut_orig)
    xǁNamespaceIndexGeneratorǁget_index_path__mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁget_index_path'
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_orig(self) -> None:
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
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_1(self) -> None:
        """
        Update or create the namespace index file.
        
        Queries all namespaces from storage, builds the tree, and writes
        the markdown file.
        """
        try:
            namespaces = None
            tree = self.build_namespace_tree(namespaces)
            markdown = self.generate_markdown(tree)
            
            index_path = self.get_index_path()
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_2(self) -> None:
        """
        Update or create the namespace index file.
        
        Queries all namespaces from storage, builds the tree, and writes
        the markdown file.
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = None
            markdown = self.generate_markdown(tree)
            
            index_path = self.get_index_path()
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_3(self) -> None:
        """
        Update or create the namespace index file.
        
        Queries all namespaces from storage, builds the tree, and writes
        the markdown file.
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(None)
            markdown = self.generate_markdown(tree)
            
            index_path = self.get_index_path()
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_4(self) -> None:
        """
        Update or create the namespace index file.
        
        Queries all namespaces from storage, builds the tree, and writes
        the markdown file.
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            markdown = None
            
            index_path = self.get_index_path()
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_5(self) -> None:
        """
        Update or create the namespace index file.
        
        Queries all namespaces from storage, builds the tree, and writes
        the markdown file.
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            markdown = self.generate_markdown(None)
            
            index_path = self.get_index_path()
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_6(self) -> None:
        """
        Update or create the namespace index file.
        
        Queries all namespaces from storage, builds the tree, and writes
        the markdown file.
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            markdown = self.generate_markdown(tree)
            
            index_path = None
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_7(self) -> None:
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
            index_path.parent.mkdir(parents=None, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_8(self) -> None:
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
            index_path.parent.mkdir(parents=True, exist_ok=None)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_9(self) -> None:
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
            index_path.parent.mkdir(exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_10(self) -> None:
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
            index_path.parent.mkdir(parents=True, )
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_11(self) -> None:
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
            index_path.parent.mkdir(parents=False, exist_ok=True)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_12(self) -> None:
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
            index_path.parent.mkdir(parents=True, exist_ok=False)
            
            index_path.write_text(markdown, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_13(self) -> None:
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
            
            index_path.write_text(None, encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_14(self) -> None:
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
            
            index_path.write_text(markdown, encoding=None)
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_15(self) -> None:
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
            
            index_path.write_text(encoding='utf-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_16(self) -> None:
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
            
            index_path.write_text(markdown, )
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_17(self) -> None:
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
            
            index_path.write_text(markdown, encoding='XXutf-8XX')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_18(self) -> None:
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
            
            index_path.write_text(markdown, encoding='UTF-8')
            logger.info(f"Updated namespace index at {index_path}")
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_19(self) -> None:
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
            logger.info(None)
            
        except Exception as e:
            logger.error(f"Error updating namespace index: {e}", exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_20(self) -> None:
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
            logger.error(None, exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_21(self) -> None:
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
            logger.error(f"Error updating namespace index: {e}", exc_info=None)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_22(self) -> None:
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
            logger.error(exc_info=True)
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_23(self) -> None:
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
            logger.error(f"Error updating namespace index: {e}", )
            # Don't raise - index generation failure shouldn't break memory operations
    
    def xǁNamespaceIndexGeneratorǁupdate_index__mutmut_24(self) -> None:
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
            logger.error(f"Error updating namespace index: {e}", exc_info=False)
            # Don't raise - index generation failure shouldn't break memory operations
    
    xǁNamespaceIndexGeneratorǁupdate_index__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_1': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_1, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_2': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_2, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_3': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_3, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_4': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_4, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_5': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_5, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_6': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_6, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_7': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_7, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_8': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_8, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_9': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_9, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_10': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_10, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_11': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_11, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_12': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_12, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_13': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_13, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_14': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_14, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_15': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_15, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_16': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_16, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_17': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_17, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_18': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_18, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_19': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_19, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_20': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_20, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_21': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_21, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_22': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_22, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_23': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_23, 
        'xǁNamespaceIndexGeneratorǁupdate_index__mutmut_24': xǁNamespaceIndexGeneratorǁupdate_index__mutmut_24
    }
    
    def update_index(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁupdate_index__mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁupdate_index__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_index.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁupdate_index__mutmut_orig)
    xǁNamespaceIndexGeneratorǁupdate_index__mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁupdate_index'
    
    def xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_orig(self, namespace: str) -> bool:
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
    
    def xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_1(self, namespace: str) -> bool:
        """
        Check if a namespace is new (not in cached namespaces).
        
        Note: This is a simple check based on cached namespaces. For accurate
        results, call get_all_namespaces() first to refresh the cache.
        
        Args:
            namespace: Namespace string to check
            
        Returns:
            True if namespace is not in cache, False otherwise
        """
        return namespace in self._cached_namespaces
    
    xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_1': xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_1
    }
    
    def is_namespace_new(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_mutants"), args, kwargs, self)
        return result 
    
    is_namespace_new.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_orig)
    xǁNamespaceIndexGeneratorǁis_namespace_new__mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁis_namespace_new'
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_orig(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_1(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = None
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_2(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = None
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_3(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(None)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_4(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = None
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_5(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(None)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_6(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(None, exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_7(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=None)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_8(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(exc_info=True)
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_9(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", )
            return {}
    
    def xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_10(self) -> Dict[str, Any]:
        """
        Get the namespace hierarchy as a tree data structure.
        
        This method returns the same tree structure that is used to generate
        the markdown index, but as a dictionary that can be included in world state.
        
        Returns:
            Dictionary representing the namespace tree structure with format:
            {
                "namespace_name": {
                    "children": {...},
                    "is_leaf": bool
                }
            }
        """
        try:
            namespaces = self.get_all_namespaces()
            tree = self.build_namespace_tree(namespaces)
            self._last_indexed = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting namespace hierarchy: {e}", exc_info=False)
            return {}
    
    xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_1': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_1, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_2': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_2, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_3': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_3, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_4': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_4, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_5': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_5, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_6': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_6, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_7': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_7, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_8': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_8, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_9': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_9, 
        'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_10': xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_10
    }
    
    def get_namespace_hierarchy(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_orig"), object.__getattribute__(self, "xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_namespace_hierarchy.__signature__ = _mutmut_signature(xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_orig)
    xǁNamespaceIndexGeneratorǁget_namespace_hierarchy__mutmut_orig.__name__ = 'xǁNamespaceIndexGeneratorǁget_namespace_hierarchy'
    
    def get_last_indexed(self) -> Optional[str]:
        """
        Get last indexed timestamp in ISO format.
        
        Returns:
            ISO format timestamp string, or None if never indexed
        """
        if self._last_indexed:
            return self._last_indexed.isoformat()
        return None

