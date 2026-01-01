"""
Directory structure generator for tracking file system hierarchy.

Generates and maintains a hierarchical tree structure representing the directory
structure of a specified root path (e.g., /home/wizard/broca).
"""

from __future__ import annotations

import logging
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import threading
import time

logger = logging.getLogger(__name__)


class DirectoryStructureGenerator:
    """
    Generates and maintains a hierarchical tree structure of directory contents.
    
    Scans a directory recursively and builds a tree structure representing
    files and subdirectories for inclusion in world state.
    """
    
    def __init__(self, root_path: str = "/home/wizard/broca") -> None:
        """
        Initialize directory structure generator.
        
        Args:
            root_path: Root directory path to scan (default: /home/wizard/broca)
        """
        self.root_path = Path(root_path)
        self._last_scan: Optional[datetime] = None
        self._cached_tree_hash: Optional[str] = None
        self._cached_tree_hash_at: Optional[float] = None
        self._cache_lock = threading.Lock()
        self._scan_inflight: bool = False
        # Default ignore patterns for directories and files to avoid scanning
        # common build/artifact and binary directories.
        self.ignore_dirs = set([
            "__pycache__", ".git", "build", "dist", "artifacts",  # Existing
            ".venv", "venv", "env", ".env",  # Virtual environments
            ".pytest_cache", ".mypy_cache",  # Python caches
            "node_modules",  # Node.js dependencies
            ".tox", ".coverage", "htmlcov",  # Build artifacts
            ".idea", ".vscode",  # IDE directories
        ])
        # Optional flag to include hidden files if explicitly requested
        self.include_hidden = False
        # Maximum file size (bytes) to consider for prompt-sized outputs; larger
        # files will be skipped when producing prompt-ready file lists.
        self.max_text_file_size = 10 * 1024 * 1024  # 10 MB
        logger.debug(f"Initialized DirectoryStructureGenerator with root: {root_path}")

        # Cache TTL for expensive scans/hash computation.
        # Keep this fairly long; it's meant as a cache key input, not a live file watcher.
        self.tree_hash_ttl_seconds: float = float(
            os.getenv("BROCA_DIRECTORY_TREE_HASH_TTL_SECONDS", "600.0")
        )
    
    def scan_directory(self) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Recursively scan directory and collect file and directory information.
        
        Returns:
            Tuple of (files list, directories list)
            - files: List of dicts with "path" (relative) and "name" (filename)
            - directories: List of relative directory path strings
            
        Note:
            Skips hidden files and directories (starting with '.').
        """
        files: List[Dict[str, str]] = []
        directories: List[str] = []
        
        if not self.root_path.exists() or not self.root_path.is_dir():
            logger.warning(f"Root path does not exist or is not a directory: {self.root_path}")
            return files, directories
        
        try:
            self._scan_directory_recursive(self.root_path, files, directories, Path(""))
        except (OSError, PermissionError) as e:
            logger.warning(f"Error scanning directory {self.root_path}: {e}", exc_info=True)
        
        return files, directories
    
    def _scan_directory_recursive(
        self,
        current_path: Path,
        files: List[Dict[str, str]],
        directories: List[str],
        rel_path: Path
    ) -> None:
        """Recursively scan a directory."""
        try:
            for item in sorted(current_path.iterdir()):
                try:
                    item_rel_path = rel_path / item.name if rel_path else Path(item.name)
                    
                    if item.is_dir():
                        # Skip ignored directories (e.g., .venv, .git, node_modules) completely
                        if item.name in self.ignore_dirs:
                            continue
                        
                        # Skip hidden directories (starting with '.') unless include_hidden is True
                        if item.name.startswith('.') and not self.include_hidden:
                            continue
                        # Add directory to list
                        directories.append(str(item_rel_path).replace('\\', '/'))
                        # Recursively scan subdirectory
                        self._scan_directory_recursive(item, files, directories, item_rel_path)
                    elif item.is_file():
                        # Skip hidden files (starting with '.') unless include_hidden is True
                        if item.name.startswith('.') and not self.include_hidden:
                            continue
                        # Add file to list
                        files.append({
                            "path": str(item_rel_path).replace('\\', '/'),
                            "name": item.name
                        })
                
                except (OSError, PermissionError) as e:
                    logger.debug(f"Error accessing {item}: {e}")
                    continue
        
        except (OSError, PermissionError) as e:
            logger.debug(f"Error scanning directory {current_path}: {e}")
    
    def build_directory_tree(
        self,
        files: List[Dict[str, str]],
        directories: List[str]
    ) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from files and directories.
        
        Args:
            files: List of file dictionaries with "path" and "name" keys
            directories: List of relative directory path strings
            
        Returns:
            Nested dictionary representing the directory tree with format:
            {
                "dir_name": {
                    "children": {...},  # subdirectories
                    "files": [...]      # files in this directory
                }
            }
            Root-level files are stored under a special "__files__" key at the root.
        """
        tree: Dict[str, Any] = {}
        root_files: List[str] = []
        
        # Process directories first to build the structure
        for dir_path in sorted(directories):
            parts = [p for p in dir_path.replace('\\', '/').split('/') if p]
            if parts:
                current = tree
                for part in parts:
                    if part not in current:
                        current[part] = {
                            "children": {},
                            "files": []
                        }
                    current = current[part]["children"]
        
        # Process files - add them to the appropriate directory
        for file_info in files:
            file_path = file_info["path"]
            parts = [p for p in file_path.replace('\\', '/').split('/') if p]
            
            if len(parts) > 1:
                # File in subdirectory: parts = [dir1, dir2, ..., filename]
                dir_parts = parts[:-1]
                filename = parts[-1]
                
                # Navigate to the parent directory node
                current = tree
                for i, part in enumerate(dir_parts):
                    if part not in current:
                        current[part] = {
                            "children": {},
                            "files": []
                        }
                    # If this is the last directory, we want to add the file to it
                    if i == len(dir_parts) - 1:
                        current[part]["files"].append(filename)
                    else:
                        # Continue navigating into children
                        current = current[part]["children"]
            else:
                # File in root
                root_files.append(file_info["name"])
        
        # Add root files if any
        if root_files:
            tree["__files__"] = sorted(root_files)
        
        return tree
    
    def get_directory_hierarchy(self) -> Dict[str, Any]:
        """
        Get the directory hierarchy as a tree data structure.
        
        This method scans the directory and returns a tree structure that can
        be included in world state.
        
        Returns:
            Dictionary representing the directory tree structure with format:
            {
                "dir_name": {
                    "children": {...},  # subdirectories
                    "files": [...]      # files in this directory
                }
            }
            Root-level files are stored under "__files__" key.
            Returns empty dict on error.
        """
        try:
            files, directories = self.scan_directory()
            tree = self.build_directory_tree(files, directories)
            self._last_scan = datetime.now(timezone.utc)
            return tree
        except Exception as e:
            logger.error(f"Error getting directory hierarchy: {e}", exc_info=True)
            return {}
    
    def get_directory_tree_hash(self) -> str:
        """
        Compute hash of directory tree structure.
        
        Returns:
            SHA256 hex digest of the JSON-serialized directory tree
        """
        tree = self.get_directory_hierarchy()
        tree_json = json.dumps(tree, sort_keys=True)
        hash_obj = hashlib.sha256(tree_json.encode())
        return hash_obj.hexdigest()

    def get_directory_tree_hash_cached(self, *, allow_scan: bool = False) -> Optional[str]:
        """Return a cached directory tree hash without forcing a scan unless allowed."""
        now = time.time()
        with self._cache_lock:
            if self._cached_tree_hash is not None and self._cached_tree_hash_at is not None:
                age = now - self._cached_tree_hash_at
                if age < self.tree_hash_ttl_seconds:
                    return self._cached_tree_hash

            if not allow_scan:
                return self._cached_tree_hash

        # Compute outside lock to avoid blocking other readers.
        try:
            tree_hash = self.get_directory_tree_hash()
        except Exception:
            return None

        with self._cache_lock:
            self._cached_tree_hash = tree_hash
            self._cached_tree_hash_at = now
        return tree_hash

    def warm_tree_hash_async(self) -> None:
        """Best-effort background warm of the cached tree hash."""
        with self._cache_lock:
            if self._scan_inflight:
                return
            self._scan_inflight = True

        def _run() -> None:
            try:
                self.get_directory_tree_hash_cached(allow_scan=True)
            finally:
                with self._cache_lock:
                    self._scan_inflight = False

        threading.Thread(target=_run, daemon=True, name="broca-dir-tree-hash").start()
    
    def get_last_scan(self) -> Optional[str]:
        """
        Get last scan timestamp in ISO format.
        
        Returns:
            ISO format timestamp string, or None if never scanned
        """
        if self._last_scan:
            return self._last_scan.isoformat()
        return None
