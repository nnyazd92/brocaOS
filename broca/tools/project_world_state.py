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
    - File structures (first few lines/headers)
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
            "file tree, and file headers (first few lines) for structure overview. "
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
            max_header_lines: Maximum number of header lines to extract
            
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
                        except OSError:
                            file_size = 0
                        
                        # Get relative path
                        try:
                            file_rel_path = str(item.relative_to(self._project_root))
                        except ValueError:
                            file_rel_path = str(item)
                        
                        # Only read headers from text files that are within size limit
                        headers: List[str] = []
                        if self._should_read_file_headers(item, file_size, ext):
                            headers = self._get_file_header(item, max_header_lines)
                        
                        file_info: Dict[str, Any] = {
                            "path": file_rel_path,
                            "name": item.name,
                            "size": file_size,
                            "extension": ext,
                            "headers": headers
                        }
                        
                        files.append(file_info)
                
                except (OSError, PermissionError) as e:
                    logger.debug(f"Error accessing {item}: {e}")
                    continue
        
        except (OSError, PermissionError) as e:
            logger.warning(f"Error scanning directory {path}: {e}")
        
        return files, directories
    
    def _should_read_file_headers(self, file_path: Path, file_size: int, extension: str) -> bool:
        """
        Determine if file headers should be read for this file.
        
        Args:
            file_path: Path to the file
            file_size: Size of the file in bytes
            extension: File extension (lowercase)
            
        Returns:
            True if headers should be read, False otherwise
        """
        # Skip binary file extensions
        if extension in self.BINARY_EXTENSIONS:
            return False
        
        # Skip files that are too large
        if file_size > self._max_file_size:
            logger.debug(f"Skipping large file {file_path} (size: {file_size} bytes)")
            return False
        
        # Skip zero-byte files
        if file_size == 0:
            return False
        
        # Additional binary detection: check first few bytes for null bytes
        # or attempt to decode as UTF-8
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(min(512, file_size))
                if len(sample) == 0:
                    return False
                
                # Check for null bytes (strong indicator of binary)
                if b'\x00' in sample:
                    logger.debug(f"Skipping binary file {file_path} (contains null bytes)")
                    return False
                
                # Try to decode as UTF-8 to check if it's valid text
                # This handles Unicode properly, not just ASCII
                try:
                    decoded = sample.decode('utf-8')
                    # Check if decoded content has reasonable text character ratio
                    # Count printable characters (including Unicode) and whitespace
                    text_chars = sum(1 for c in decoded if c.isprintable() or c.isspace())
                    if len(decoded) > 0:
                        text_ratio = text_chars / len(decoded)
                        # If less than 70% are printable/whitespace, likely binary
                        # Lower threshold to allow for valid UTF-8 with various characters
                        if text_ratio < 0.7:
                            logger.debug(f"Skipping likely binary file {file_path} (text ratio: {text_ratio:.2%})")
                            return False
                except UnicodeDecodeError:
                    # Can't decode as UTF-8, likely binary
                    logger.debug(f"Skipping binary file {file_path} (not valid UTF-8)")
                    return False
        except (OSError, PermissionError) as e:
            logger.debug(f"Could not check file {file_path} for binary detection: {e}")
            return False
        
        return True
    
    def _get_file_header(self, file_path: Path, max_lines: int) -> List[str]:
        """
        Extract first N lines from a text file.
        
        This method should only be called after _should_read_file_headers
        has verified the file is safe to read.
        
        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to extract
            
        Returns:
            List of header lines (empty list if file can't be read)
        """
        headers: List[str] = []
        
        try:
            # Read file line by line to avoid loading entire file into memory
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    # Strip line endings but preserve content
                    headers.append(line.rstrip('\n\r'))
                    
                    # Safety check: if we've read a reasonable amount, stop
                    # This prevents issues with files that have extremely long lines
                    if len(headers) > 0 and sum(len(h) for h in headers) > 100000:  # 100KB of headers max
                        logger.debug(f"Stopping header read for {file_path} (accumulated {sum(len(h) for h in headers)} bytes)")
                        break
        
        except (OSError, UnicodeDecodeError, PermissionError) as e:
            # File might have become unreadable or encoding issue
            logger.debug(f"Could not read headers from {file_path}: {e}")
        
        return headers
    
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
        
        Returns:
            True if state was loaded, False otherwise
        """
        if not self._state_file.exists():
            return False
        
        try:
            with open(self._state_file, 'r', encoding='utf-8') as f:
                self._state = json.load(f)
            logger.debug(f"Loaded world state from {self._state_file}")
            return True
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load world state from {self._state_file}: {e}")
            return False
    
    def _save_state(self) -> bool:
        """
        Save current state to JSON file.
        
        Returns:
            True if state was saved, False otherwise
        """
        if self._state is None:
            return False
        
        try:
            # Ensure parent directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first (atomic write)
            temp_file = self._state_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self._state_file)
            logger.debug(f"Saved world state to {self._state_file}")
            return True
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Failed to save world state to {self._state_file}: {e}")
            return False
    
    def build_world_state(self, project_root: Optional[str] = None, persist: bool = True) -> Dict[str, Any]:
        """
        Scan project and build initial world state.
        
        Args:
            project_root: Root directory to scan (defaults to tool's configured root)
            persist: Whether to save state to file
            
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
            
            # Persist if requested
            if persist:
                self._save_state()
            
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
        
        Returns:
            Result dictionary with success status and state information
        """
        if self._state is None:
            return {
                "success": False,
                "error": "World state has not been built yet. Use build_world_state first."
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
