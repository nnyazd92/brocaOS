"""
Project World State Tool.

Allows the LLM to build, get, and update a project world state representing
directory structure, file tree, and file headers for structure overview.
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from . import Tool
from ..config import config

logger = logging.getLogger(__name__)


class ProjectWorldStateTool:
    """
    Tool for managing project world state.
    
    Maintains a structured representation of the project including:
    - Directory structure (tree representation)
    - File tree (all files with metadata)
    - File metadata (creation date, last modified, size)
    """
    
    # Allowed file extensions that should be included in world state
    ALLOWED_EXTENSIONS = {'.py', '.txt', '.json', '.md', '.sh'}
    
    # Binary file extensions that should not be read
    BINARY_EXTENSIONS = {
        '.bin', '.exe', '.so', '.dll', '.dylib', '.a', '.lib',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.webp',
        '.pdf', '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
        '.db', '.sqlite', '.sqlite3', '.faiss', '.index',
        '.pyc', '.pyo', '.pyd', '.class',
        '.o', '.obj', '.elf',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.woff', '.woff2', '.ttf', '.otf',
    }
    
    def __init__(
        self,
        project_root: Optional[str] = None,
        state_file: Optional[str] = None,
        max_header_lines: int = 10,
        max_file_size: Optional[int] = None
    ) -> None:
        """
        Initialize the project world state tool.
        
        Args:
            project_root: Root directory of the project (defaults to current directory)
            state_file: Path to JSON file for state persistence (defaults to config or "project_world_state.json")
            max_header_lines: Maximum number of header lines to extract from files (default: 10)
            max_file_size: Maximum file size in bytes to read headers from (defaults to config or 1MB)
        """
        # Determine project root: use provided, then config, then current directory
        if project_root:
            self._project_root = Path(project_root)
        elif config.tools.project_world_state_path:
            self._project_root = Path(config.tools.project_world_state_path)
        else:
            self._project_root = Path.cwd()
        
        # Use provided max_header_lines or config default
        if max_header_lines == 10:
            self._max_header_lines = config.tools.project_world_state_header_lines
        else:
            self._max_header_lines = max_header_lines
        
        # Use provided max_file_size or config default
        if max_file_size is None:
            self._max_file_size = config.tools.project_world_state_max_file_size
        else:
            self._max_file_size = max_file_size
        
        self._state: Optional[Dict[str, Any]] = None
        
        # Determine state file location
        if state_file:
            self._state_file = Path(state_file)
        else:
            self._state_file = Path(config.tools.project_world_state_file)
        
        # Try to load existing state
        self._load_state()
        
        logger.info(f"Initialized ProjectWorldStateTool with root: {self._project_root}")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "project_world_state"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Build, get, and update project world state containing directory structure, "
            "file tree, and file metadata (creation date, last modified, size) for structure overview. "
            "Use this tool to understand the current project structure, track changes, "
            "and maintain awareness of the codebase layout."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["build_world_state", "get_world_state", "update_world_state"],
                    "description": "Operation to perform: build (scan and create), get (retrieve current), or update (rescan and update)"
                },
                "project_root": {
                    "type": "string",
                    "description": "Root directory of the project to scan (defaults to tool's configured root)"
                },
                "persist": {
                    "type": "boolean",
                    "description": "Whether to persist state to JSON file (default: true)",
                    "default": True
                }
            },
            "required": ["operation"]
        }
    
    def _scan_directory(self, path: Path, max_header_lines: int = 10) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Recursively scan directory and collect file information.
        
        Args:
            path: Directory path to scan
            max_header_lines: Deprecated parameter (kept for compatibility, not used)
            
        Returns:
            Tuple of (files list, directories list)
        """
        files: List[Dict[str, Any]] = []
        directories: List[str] = []
        
        try:
            # Get relative path from project root
            try:
                rel_path = path.relative_to(self._project_root)
                if rel_path == Path('.'):
                    base_path = ""
                else:
                    base_path = str(rel_path) + os.sep
            except ValueError:
                # Path is outside project root
                base_path = ""
            
            for item in sorted(path.iterdir()):
                try:
                    if item.is_dir():
                        # Skip .venv directories completely
                        if item.name == '.venv':
                            continue
                        
                        # Add directory to list
                        dir_rel_path = str(Path(base_path) / item.name) if base_path else item.name
                        directories.append(dir_rel_path)
                        
                        # Recursively scan subdirectory
                        sub_files, sub_dirs = self._scan_directory(item, max_header_lines)
                        files.extend(sub_files)
                        directories.extend(sub_dirs)
                    
                    elif item.is_file():
                        # Extract file extension
                        ext = item.suffix.lower()
                        
                        # Only process allowed file types (.py, .txt, .json, .md)
                        if ext not in self.ALLOWED_EXTENSIONS:
                            continue
                        
                        # Get file metadata
                        try:
                            stat = item.stat()
                            file_size = stat.st_size
                            # Get timestamps - use st_ctime for creation (or st_birthtime if available)
                            try:
                                creation_timestamp = stat.st_birthtime
                            except AttributeError:
                                # Fallback to st_ctime on systems without birthtime
                                creation_timestamp = stat.st_ctime
                            last_modified_timestamp = stat.st_mtime
                            
                            # Convert to ISO format timestamps
                            creation_date = datetime.fromtimestamp(creation_timestamp, tz=timezone.utc).isoformat()
                            last_modified = datetime.fromtimestamp(last_modified_timestamp, tz=timezone.utc).isoformat()
                        except OSError:
                            file_size = 0
                            creation_date = datetime.now(timezone.utc).isoformat()
                            last_modified = datetime.now(timezone.utc).isoformat()
                        
                        # Get relative path
                        try:
                            file_rel_path = str(item.relative_to(self._project_root))
                        except ValueError:
                            file_rel_path = str(item)
                        
                        # Build metadata dictionary
                        metadata = {
                            "creation_date": creation_date,
                            "last_modified": last_modified,
                            "file_size": file_size
                        }
                        
                        file_info: Dict[str, Any] = {
                            "path": file_rel_path,
                            "name": item.name,
                            "size": file_size,
                            "extension": ext,
                            "metadata": metadata
                        }
                        
                        files.append(file_info)
                
                except (OSError, PermissionError) as e:
                    logger.debug(f"Error accessing {item}: {e}")
                    continue
        
        except (OSError, PermissionError) as e:
            logger.warning(f"Error scanning directory {path}: {e}")
        
        return files, directories
    
    def _build_directory_tree(self, files: List[Dict[str, Any]], directories: List[str]) -> Dict[str, Any]:
        """
        Build tree structure representation from files and directories.
        
        Args:
            files: List of file dictionaries
            directories: List of directory paths
            
        Returns:
            Tree structure dictionary
        """
        tree: Dict[str, Any] = {}
        
        # Process directories
        for dir_path in sorted(directories):
            parts = dir_path.split(os.sep)
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        # Process files
        for file_info in files:
            file_path = file_info["path"]
            parts = file_path.split(os.sep)
            if len(parts) > 1:
                # File in subdirectory
                dir_parts = parts[:-1]
                filename = parts[-1]
                current = tree
                for part in dir_parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                if "_files" not in current:
                    current["_files"] = []
                current["_files"].append(filename)
            else:
                # File in root
                if "_files" not in tree:
                    tree["_files"] = []
                tree["_files"].append(file_info["name"])
        
        return tree
    
    def _load_state(self) -> bool:
        """
        Load state from JSON file if it exists.
        
        Note: This method is now a no-op as state is routed through world state aggregator.
        
        Returns:
            False (state is not loaded from file)
        """
        # No-op: state is now routed through world state aggregator, not persisted to file
        return False
    
    def _save_state(self) -> bool:
        """
        Save current state to JSON file.
        
        Note: This method is now a no-op as state is routed through world state aggregator.
        
        Returns:
            False (state is not saved to file)
        """
        # No-op: state is now routed through world state aggregator, not persisted to file
        return False
    
    def build_world_state(self, project_root: Optional[str] = None, persist: bool = True) -> Dict[str, Any]:
        """
        Scan project and build initial world state.
        
        Args:
            project_root: Root directory to scan (defaults to tool's configured root)
            persist: Deprecated parameter (kept for compatibility, no longer used)
            
        Returns:
            Result dictionary with success status and state information
        """
        try:
            root_path = Path(project_root) if project_root else self._project_root
            
            if not root_path.exists():
                return {
                    "success": False,
                    "error": f"Project root does not exist: {root_path}"
                }
            
            if not root_path.is_dir():
                return {
                    "success": False,
                    "error": f"Project root is not a directory: {root_path}"
                }
            
            logger.info(f"Building world state for project: {root_path}")
            
            # Scan directory
            files, directories = self._scan_directory(root_path, self._max_header_lines)
            
            # Build directory tree
            directory_tree = self._build_directory_tree(files, directories)
            
            # Calculate statistics
            total_size = sum(f.get("size", 0) for f in files)
            
            # Build state
            self._state = {
                "project_root": str(root_path.absolute()),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "directory_tree": directory_tree,
                "files": files,
                "statistics": {
                    "total_files": len(files),
                    "total_directories": len(directories),
                    "total_size": total_size
                }
            }
            
            # State is now routed through world state aggregator, not persisted to file
            # (persist parameter kept for backward compatibility but ignored)
            
            return {
                "success": True,
                **self._state
            }
        
        except Exception as e:
            logger.error(f"Error building world state: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_world_state(self) -> Dict[str, Any]:
        """
        Retrieve current cached world state.
        
        If state hasn't been built yet, automatically builds it.
        
        Returns:
            Result dictionary with success status and state information
        """
        if self._state is None:
            # Auto-build state if it hasn't been built yet
            logger.info("World state not built yet, building automatically")
            build_result = self.build_world_state(project_root=None, persist=False)
            if not build_result.get("success"):
                return {
                    "success": False,
                    "error": build_result.get("error", "Failed to build world state")
                }
            # State is now built, return it
            return {
                "success": True,
                **self._state
            }
        
        return {
            "success": True,
            **self._state
        }
    
    def update_world_state(self, project_root: Optional[str] = None, persist: bool = True) -> Dict[str, Any]:
        """
        Rescan project and update world state.
        
        Args:
            project_root: Root directory to scan (defaults to tool's configured root)
            persist: Whether to save state to file
            
        Returns:
            Result dictionary with success status and updated state information
        """
        # Update is essentially a rebuild
        return self.build_world_state(project_root=project_root, persist=persist)
    
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute tool operation.
        
        Args:
            **kwargs: Tool parameters (operation, project_root, persist)
            
        Returns:
            Tool execution result
        """
        operation = kwargs.get("operation")
        project_root = kwargs.get("project_root")
        persist = kwargs.get("persist", True)
        
        if operation == "build_world_state":
            return self.build_world_state(project_root=project_root, persist=persist)
        elif operation == "get_world_state":
            return self.get_world_state()
        elif operation == "update_world_state":
            return self.update_world_state(project_root=project_root, persist=persist)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Must be one of: build_world_state, get_world_state, update_world_state"
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            return f"Error: {result.get('error', 'Unknown error')}"
        
        lines = ["Project World State:"]
        lines.append(f"  Project Root: {result.get('project_root', 'N/A')}")
        lines.append(f"  Last Updated: {result.get('last_updated', 'N/A')}")
        
        stats = result.get("statistics", {})
        lines.append(f"  Statistics:")
        lines.append(f"    Total Files: {stats.get('total_files', 0)}")
        lines.append(f"    Total Directories: {stats.get('total_directories', 0)}")
        lines.append(f"    Total Size: {stats.get('total_size', 0)} bytes")
        
        files = result.get("files", [])
        if files:
            lines.append(f"  Files ({len(files)} total):")
            # Show first 10 files as preview
            for file_info in files[:10]:
                lines.append(f"    - {file_info['path']} ({file_info.get('size', 0)} bytes)")
            if len(files) > 10:
                lines.append(f"    ... and {len(files) - 10} more files")
        
        return "\n".join(lines)
