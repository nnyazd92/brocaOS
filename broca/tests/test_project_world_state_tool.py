"""
Tests for Project World State Tool.

Tests directory scanning, file header extraction, state management, and persistence.
"""

from __future__ import annotations

import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from broca.tools.project_world_state import ProjectWorldStateTool
from broca.tools.registry import ToolRegistry


class TestProjectWorldStateToolInitialization:
    """Test tool initialization."""
    
    def test_init_with_defaults(self):
        """
        Test initialization with default parameters.
        
        Rationale: Ensures tool initializes with sensible defaults.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a temporary state file that doesn't exist
            state_file = Path(tmpdir) / "nonexistent_state.json"
            tool = ProjectWorldStateTool(state_file=str(state_file))
            
            assert tool.name == "project_world_state"
            # State may be None if file doesn't exist, or loaded if it does
            assert tool._state_file == state_file
            # Check that max_header_lines is set (will use config default)
            assert tool._max_header_lines is not None
    
    def test_init_with_custom_path(self):
        """
        Test initialization with custom project root path.
        
        Rationale: Ensures tool can be configured with custom paths.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ProjectWorldStateTool(project_root=tmpdir)
            
            assert tool._project_root == Path(tmpdir)
    
    def test_init_with_custom_state_file(self):
        """
        Test initialization with custom state file path.
        
        Rationale: Ensures state file location is configurable.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "custom_state.json"
            tool = ProjectWorldStateTool(state_file=str(state_file))
            
            assert tool._state_file == state_file
    
    def test_init_with_custom_header_lines(self):
        """
        Test initialization with custom header lines count.
        
        Rationale: Ensures header line count is configurable.
        """
        tool = ProjectWorldStateTool(max_header_lines=20)
        
        assert tool._max_header_lines == 20


class TestDirectoryScanning:
    """Test directory scanning functionality."""
    
    def test_scan_empty_directory(self):
        """
        Test scanning an empty directory.
        
        Rationale: Ensures tool handles empty directories gracefully.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ProjectWorldStateTool(project_root=tmpdir)
            
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            assert files == []
            assert dirs == []
    
    def test_scan_directory_with_files(self):
        """
        Test scanning a directory with files.
        
        Rationale: Ensures files are discovered and metadata collected.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files (allowed file types will be included)
            (Path(tmpdir) / "file1.py").write_text("Line 1\nLine 2\nLine 3")
            (Path(tmpdir) / "file2.py").write_text("import os\nprint('hello')")
            (Path(tmpdir) / "file3.txt").write_text("text content")
            (Path(tmpdir) / "file4.json").write_text('{"key": "value"}')
            (Path(tmpdir) / "file5.md").write_text("# Markdown")
            (Path(tmpdir) / "file6.png").write_bytes(b'\x89PNG')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            # Allowed file types should be included
            assert len(files) == 5
            file_names = [f["path"] for f in files]
            assert "file1.py" in file_names
            assert "file2.py" in file_names
            assert "file3.txt" in file_names
            assert "file4.json" in file_names
            assert "file5.md" in file_names
            assert "file6.png" not in file_names  # Not an allowed type
            
            # Check metadata
            file1 = next(f for f in files if f["path"] == "file1.py")
            assert "size" in file1
            assert "extension" in file1
            assert file1["extension"] == ".py"
    
    def test_scan_directory_recursive(self):
        """
        Test recursive directory scanning.
        
        Rationale: Ensures subdirectories are scanned recursively.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure (allowed file types will be included)
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").write_text("nested content")
            (subdir / "data.txt").write_text("text data")
            (Path(tmpdir) / "root.py").write_text("root content")
            (Path(tmpdir) / "readme.md").write_text("# Readme")
            (Path(tmpdir) / "config.json").write_text('{"key": "value"}')
            (Path(tmpdir) / "ignored.png").write_bytes(b'\x89PNG')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            # Allowed file types should be included
            assert len(files) == 5
            file_paths = [f["path"] for f in files]
            assert "root.py" in file_paths
            assert "subdir/nested.py" in file_paths
            assert "subdir/data.txt" in file_paths
            assert "readme.md" in file_paths
            assert "config.json" in file_paths
            assert "ignored.png" not in file_paths  # Not an allowed type
    
    def test_scan_ignores_hidden_files(self):
        """
        Test that hidden files (starting with .) are handled appropriately.
        
        Rationale: Ensures tool handles hidden files correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".hidden.py").write_text("hidden")
            (Path(tmpdir) / "visible.py").write_text("visible")
            (Path(tmpdir) / ".hidden.txt").write_text("hidden text")
            (Path(tmpdir) / "visible.txt").write_text("visible text")
            (Path(tmpdir) / ".config.json").write_text('{"hidden": true}')
            (Path(tmpdir) / "config.json").write_text('{"visible": true}')
            (Path(tmpdir) / ".readme.md").write_text("# Hidden")
            (Path(tmpdir) / "readme.md").write_text("# Visible")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            # Allowed file types should be included (including hidden ones)
            file_names = [f["path"] for f in files]
            assert ".hidden.py" in file_names
            assert "visible.py" in file_names
            assert ".hidden.txt" in file_names
            assert "visible.txt" in file_names
            assert ".config.json" in file_names
            assert "config.json" in file_names
            assert ".readme.md" in file_names
            assert "readme.md" in file_names


class TestFileMetadataCollection:
    """Test file metadata collection."""
    
    def test_file_metadata_includes_creation_date(self):
        """
        Test that file metadata includes creation_date.
        
        Rationale: Ensures creation_date is collected for all files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("print('hello')")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            assert len(files) == 1
            file_info = files[0]
            assert "metadata" in file_info
            assert "creation_date" in file_info["metadata"]
            # Verify it's a valid ISO format timestamp
            from datetime import datetime
            datetime.fromisoformat(file_info["metadata"]["creation_date"].replace('Z', '+00:00'))
    
    def test_file_metadata_includes_last_modified(self):
        """
        Test that file metadata includes last_modified.
        
        Rationale: Ensures last_modified timestamp is collected for all files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("print('hello')")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            assert len(files) == 1
            file_info = files[0]
            assert "metadata" in file_info
            assert "last_modified" in file_info["metadata"]
            # Verify it's a valid ISO format timestamp
            from datetime import datetime
            datetime.fromisoformat(file_info["metadata"]["last_modified"].replace('Z', '+00:00'))
    
    def test_file_metadata_includes_file_size(self):
        """
        Test that file metadata includes file_size.
        
        Rationale: Ensures file_size is included in metadata structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            content = "print('hello')"
            file_path.write_text(content)
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            assert len(files) == 1
            file_info = files[0]
            assert "metadata" in file_info
            assert "file_size" in file_info["metadata"]
            assert file_info["metadata"]["file_size"] == len(content.encode('utf-8'))
    
    def test_file_metadata_structure(self):
        """
        Test that file metadata has correct structure.
        
        Rationale: Ensures metadata is properly structured with all required fields.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("print('hello')")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            assert len(files) == 1
            file_info = files[0]
            assert "metadata" in file_info
            metadata = file_info["metadata"]
            assert isinstance(metadata, dict)
            assert "creation_date" in metadata
            assert "last_modified" in metadata
            assert "file_size" in metadata
            # Verify timestamps are ISO format strings
            assert isinstance(metadata["creation_date"], str)
            assert isinstance(metadata["last_modified"], str)
            assert isinstance(metadata["file_size"], int)
    
    def test_file_metadata_no_headers_field(self):
        """
        Test that files no longer have headers field.
        
        Rationale: Ensures headers field has been removed in favor of metadata.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("print('hello')")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            assert len(files) == 1
            file_info = files[0]
            assert "headers" not in file_info
            assert "metadata" in file_info


class TestBuildWorldState:
    """Test building world state."""
    
    def test_build_world_state_empty_directory(self):
        """
        Test building world state for empty directory.
        
        Rationale: Ensures tool handles empty projects.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ProjectWorldStateTool(project_root=tmpdir)
            
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            assert result["project_root"] == tmpdir
            assert result["files"] == []
            assert "last_updated" in result
            assert "statistics" in result
            assert result["statistics"]["total_files"] == 0
    
    def test_build_world_state_with_files(self):
        """
        Test building world state with files.
        
        Rationale: Ensures state is built correctly with actual files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.py").write_text("Content 1\nLine 2")
            (Path(tmpdir) / "file2.py").write_text("import os\n# comment")
            (Path(tmpdir) / "file3.txt").write_text("text content")
            (Path(tmpdir) / "file4.json").write_text('{"key": "value"}')
            (Path(tmpdir) / "file5.md").write_text("# Markdown")
            (Path(tmpdir) / "file6.png").write_bytes(b'\x89PNG')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            # Allowed file types should be included
            assert len(result["files"]) == 5
            assert result["statistics"]["total_files"] == 5
            
            # Check file metadata
            file1 = next(f for f in result["files"] if "file1.py" in f["path"])
            assert "metadata" in file1
            assert "creation_date" in file1["metadata"]
            assert "last_modified" in file1["metadata"]
            assert "file_size" in file1["metadata"]
    
    def test_build_world_state_with_nested_structure(self):
        """
        Test building world state with nested directory structure.
        
        Rationale: Ensures nested structures are captured correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").write_text("nested")
            (subdir / "data.txt").write_text("data")
            (Path(tmpdir) / "root.py").write_text("root")
            (Path(tmpdir) / "readme.md").write_text("# Readme")
            (Path(tmpdir) / "config.json").write_text('{"key": "value"}')
            (Path(tmpdir) / "ignored.png").write_bytes(b'\x89PNG')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            # Allowed file types should be included
            assert len(result["files"]) == 5
            assert "directory_tree" in result


class TestGetWorldState:
    """Test getting world state."""
    
    def test_get_world_state_not_built(self):
        """
        Test getting world state when not yet built.
        
        Rationale: Ensures tool auto-builds state when it hasn't been built yet.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a temporary state file that doesn't exist
            state_file = Path(tmpdir) / "nonexistent_state.json"
            tool = ProjectWorldStateTool(state_file=str(state_file), project_root=tmpdir)
            
            # Clear any loaded state
            tool._state = None
            
            result = tool.get_world_state()
            
            # Tool should auto-build the state, so it should succeed
            assert result["success"] is True
            assert "project_root" in result
            assert "files" in result
    
    def test_get_world_state_after_build(self):
        """
        Test getting world state after building.
        
        Rationale: Ensures state can be retrieved after building.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("test")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            tool.build_world_state(project_root=tmpdir)
            
            result = tool.get_world_state()
            
            assert result["success"] is True
            assert result["project_root"] == tmpdir
            assert len(result["files"]) == 1


class TestUpdateWorldState:
    """Test updating world state."""
    
    def test_update_world_state_adds_files(self):
        """
        Test updating world state when files are added.
        
        Rationale: Ensures state reflects current directory structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.py").write_text("file1")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            tool.build_world_state(project_root=tmpdir)
            
            # Add new files
            (Path(tmpdir) / "file2.py").write_text("file2")
            (Path(tmpdir) / "file3.txt").write_text("text file")
            (Path(tmpdir) / "file4.json").write_text('{"key": "value"}')
            (Path(tmpdir) / "file5.png").write_bytes(b'\x89PNG')
            
            result = tool.update_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            # Allowed file types should be included
            assert len(result["files"]) == 4
    
    def test_update_world_state_removes_files(self):
        """
        Test updating world state when files are removed.
        
        Rationale: Ensures state reflects deletions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.py").write_text("file1")
            (Path(tmpdir) / "file2.py").write_text("file2")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            tool.build_world_state(project_root=tmpdir)
            
            # Remove file
            (Path(tmpdir) / "file1.py").unlink()
            
            result = tool.update_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            assert len(result["files"]) == 1


class TestPersistence:
    """Test that persistence is disabled (state routed through world state aggregator)."""
    
    def test_state_not_saved_to_file(self):
        """
        Test that state is not saved to JSON file.
        
        Rationale: Ensures state is routed through world state aggregator, not persisted to file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            (Path(tmpdir) / "test.py").write_text("test")
            
            tool = ProjectWorldStateTool(project_root=tmpdir, state_file=str(state_file))
            tool.build_world_state(project_root=tmpdir, persist=True)
            
            # State should not be saved to file (routed through aggregator instead)
            assert not state_file.exists()
            # But state should still be available in memory
            result = tool.get_world_state()
            assert result["success"] is True
            assert len(result["files"]) == 1
    
    def test_load_state_from_file_disabled(self):
        """
        Test that loading state from file is disabled.
        
        Rationale: Ensures persisted state is not loaded (state is built fresh each time).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            
            # Create a saved state file (should be ignored)
            saved_state = {
                "project_root": tmpdir,
                "last_updated": "2024-01-01T00:00:00",
                "files": [{"path": "test.py", "size": 4}],
                "statistics": {"total_files": 1}
            }
            with open(state_file, 'w') as f:
                json.dump(saved_state, f)
            
            tool = ProjectWorldStateTool(project_root=tmpdir, state_file=str(state_file))
            # _load_state should return False (no-op)
            result = tool._load_state()
            assert result is False
            # State should be None until build_world_state is called
            assert tool._state is None
    
    def test_build_creates_fresh_state(self):
        """
        Test that building creates fresh state (doesn't load from file).
        
        Rationale: Ensures tool builds state fresh each time, not from saved file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            (Path(tmpdir) / "test.py").write_text("test content")
            
            # Pre-create state file with old data (should be ignored)
            saved_state = {
                "project_root": tmpdir,
                "last_updated": "2024-01-01T00:00:00",
                "files": [{"path": "old.py", "size": 100}],
                "statistics": {"total_files": 1}
            }
            with open(state_file, 'w') as f:
                json.dump(saved_state, f)
            
            tool = ProjectWorldStateTool(project_root=tmpdir, state_file=str(state_file))
            result = tool.build_world_state(project_root=tmpdir)
            
            # Should build fresh state, not load from file
            assert result["success"] is True
            # Should include test.py and state.json (both are in the directory)
            file_paths = [f["path"] for f in result["files"]]
            assert "test.py" in file_paths
            # Old file from saved state should not be in state (proves we didn't load from file)
            assert "old.py" not in file_paths


class TestToolProtocol:
    """Test tool protocol compliance."""
    
    def test_tool_name(self):
        """
        Test tool name property.
        
        Rationale: Ensures tool implements protocol correctly.
        """
        tool = ProjectWorldStateTool()
        
        assert tool.name == "project_world_state"
    
    def test_tool_description(self):
        """
        Test tool description property.
        
        Rationale: Ensures LLM understands tool purpose.
        """
        tool = ProjectWorldStateTool()
        
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
    
    def test_tool_parameters(self):
        """
        Test tool parameters schema.
        
        Rationale: Ensures tool has valid parameter schema.
        """
        tool = ProjectWorldStateTool()
        
        params = tool.parameters
        assert "type" in params
        assert params["type"] == "object"
        assert "properties" in params
    
    def test_execute_build_world_state(self):
        """
        Test executing build_world_state operation.
        
        Rationale: Ensures tool execution works via protocol.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("test")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.execute(operation="build_world_state", project_root=tmpdir)
            
            assert "success" in result
            assert result["success"] is True
    
    def test_execute_get_world_state(self):
        """
        Test executing get_world_state operation.
        
        Rationale: Ensures get operation works via protocol.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ProjectWorldStateTool(project_root=tmpdir)
            
            # First build
            tool.execute(operation="build_world_state", project_root=tmpdir)
            
            # Then get
            result = tool.execute(operation="get_world_state")
            
            assert "success" in result
    
    def test_execute_update_world_state(self):
        """
        Test executing update_world_state operation.
        
        Rationale: Ensures update operation works via protocol.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ProjectWorldStateTool(project_root=tmpdir)
            
            # Build first
            tool.execute(operation="build_world_state", project_root=tmpdir)
            
            # Then update
            result = tool.execute(operation="update_world_state", project_root=tmpdir)
            
            assert "success" in result


class TestFileFiltering:
    """Test that .py, .txt, .json, and .md files are included."""
    
    def test_allowed_file_types_included(self):
        """
        Test that .py, .txt, .json, and .md files are included in world state.
        
        Rationale: Ensures allowed file types are included while others are excluded.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create various file types
            (Path(tmpdir) / "script.py").write_text("import os\nprint('hello')")
            (Path(tmpdir) / "data.txt").write_text("some text data")
            (Path(tmpdir) / "config.json").write_text('{"key": "value"}')
            (Path(tmpdir) / "readme.md").write_text("# Readme")
            (Path(tmpdir) / "image.png").write_bytes(b'\x89PNG\r\n')
            (Path(tmpdir) / "binary.bin").write_bytes(b'\x00\x01\x02')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            # Allowed file types should be included
            assert len(files) == 4
            file_paths = {f["path"]: f["extension"] for f in files}
            assert "script.py" in file_paths
            assert file_paths["script.py"] == ".py"
            assert "data.txt" in file_paths
            assert file_paths["data.txt"] == ".txt"
            assert "config.json" in file_paths
            assert file_paths["config.json"] == ".json"
            assert "readme.md" in file_paths
            assert file_paths["readme.md"] == ".md"
            # Other file types should be excluded
            assert "image.png" not in file_paths
            assert "binary.bin" not in file_paths
    
    def test_allowed_files_in_nested_directories_included(self):
        """
        Test that allowed file types in nested directories are included.
        
        Rationale: Ensures recursive scanning works for all allowed file types.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure with allowed and non-allowed files
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "module.py").write_text("def func(): pass")
            (subdir / "data.txt").write_text("data")
            (subdir / "config.json").write_text('{"key": "value"}')
            (subdir / "docs.md").write_text("# Docs")
            (subdir / "image.png").write_bytes(b'\x89PNG')
            (Path(tmpdir) / "main.py").write_text("import subdir.module")
            (Path(tmpdir) / "readme.txt").write_text("readme")
            (Path(tmpdir) / "settings.json").write_text('{"setting": true}')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            # Allowed file types should be included
            file_paths = [f["path"] for f in files]
            assert len(files) == 7
            assert "main.py" in file_paths
            assert "subdir/module.py" in file_paths
            assert "readme.txt" in file_paths
            assert "subdir/data.txt" in file_paths
            assert "settings.json" in file_paths
            assert "subdir/config.json" in file_paths
            assert "subdir/docs.md" in file_paths
            # Non-allowed files should be excluded
            assert "subdir/image.png" not in file_paths
    
    def test_build_world_state_includes_allowed_files(self):
        """
        Test that build_world_state includes .py, .txt, .json, and .md files.
        
        Rationale: Ensures high-level API respects file type filtering.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "module.py").write_text("def func(): pass")
            (Path(tmpdir) / "data.json").write_text('{"key": "value"}')
            (Path(tmpdir) / "readme.md").write_text("# Title")
            (Path(tmpdir) / "notes.txt").write_text("Some notes")
            (Path(tmpdir) / "image.png").write_bytes(b'\x89PNG')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            # All allowed file types should be included
            assert len(result["files"]) == 4
            assert result["statistics"]["total_files"] == 4
            file_paths = [f["path"] for f in result["files"]]
            assert "module.py" in file_paths
            assert "data.json" in file_paths
            assert "readme.md" in file_paths
            assert "notes.txt" in file_paths
            assert "image.png" not in file_paths


class TestDirectoryFiltering:
    """Test that .venv directories are completely ignored."""
    
    def test_venv_directory_ignored(self):
        """
        Test that .venv directory is completely ignored.
        
        Rationale: Ensures virtual environment directories are not scanned.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .venv directory with files
            venv_dir = Path(tmpdir) / ".venv"
            venv_dir.mkdir()
            (venv_dir / "python").write_text("python binary")
            (venv_dir / "lib").mkdir()
            (venv_dir / "lib" / "site-packages").mkdir()
            (venv_dir / "lib" / "site-packages" / "package.py").write_text("package code")
            
            # Create project files
            (Path(tmpdir) / "main.py").write_text("import os")
            (Path(tmpdir) / "utils.py").write_text("def helper(): pass")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            # .venv should not appear in directories list
            assert ".venv" not in dirs
            # Files in .venv should not be included
            file_paths = [f["path"] for f in files]
            assert "main.py" in file_paths
            assert "utils.py" in file_paths
            assert ".venv/python" not in file_paths
            assert ".venv/lib/site-packages/package.py" not in file_paths
            # Only project files (allowed types) should be present
            assert len(files) == 2
    
    def test_venv_nested_ignored(self):
        """
        Test that .venv subdirectories are also ignored.
        
        Rationale: Ensures entire .venv tree is skipped, not just top level.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested .venv structure
            venv_dir = Path(tmpdir) / ".venv"
            venv_dir.mkdir()
            lib_dir = venv_dir / "lib"
            lib_dir.mkdir()
            site_packages = lib_dir / "site-packages"
            site_packages.mkdir()
            (site_packages / "numpy.py").write_text("import numpy")
            (site_packages / "pandas.py").write_text("import pandas")
            
            # Create project file
            (Path(tmpdir) / "app.py").write_text("import numpy")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            files, dirs = tool._scan_directory(Path(tmpdir))
            
            # Only project files (allowed types) should be included
            assert len(files) == 1
            assert files[0]["path"] == "app.py"
            # .venv and its subdirectories should not be in dirs list
            assert ".venv" not in dirs
            assert "lib" not in dirs
            assert "site-packages" not in dirs
    
    def test_venv_with_py_files_ignored(self):
        """
        Test that .py files inside .venv are ignored.
        
        Rationale: Ensures even Python files in .venv are excluded.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .venv with .py files
            venv_dir = Path(tmpdir) / ".venv"
            venv_dir.mkdir()
            (venv_dir / "activate.py").write_text("def activate(): pass")
            (venv_dir / "setup.py").write_text("from setuptools import setup")
            
            # Create project .py files
            (Path(tmpdir) / "main.py").write_text("import os")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            assert len(result["files"]) == 1
            assert result["files"][0]["path"] == "main.py"
            assert ".venv" not in [d for d in result.get("directory_tree", {}).keys()]
            # .venv files should not be included even if they have allowed extensions
    
    def test_build_world_state_ignores_venv(self):
        """
        Test that build_world_state ignores .venv directory.
        
        Rationale: Ensures high-level API respects .venv exclusion.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .venv with various files
            venv_dir = Path(tmpdir) / ".venv"
            venv_dir.mkdir()
            (venv_dir / "python").write_text("binary")
            (venv_dir / "package.py").write_text("package")
            
            # Create project structure
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            (src_dir / "app.py").write_text("def main(): pass")
            (Path(tmpdir) / "main.py").write_text("from src.app import main")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            # Only project files (allowed types) should be included
            file_paths = [f["path"] for f in result["files"]]
            assert len(result["files"]) == 2
            assert "main.py" in file_paths
            assert "src/app.py" in file_paths
            # .venv should not appear anywhere
            assert ".venv" not in str(result.get("directory_tree", {}))


class TestToolIntegration:
    """Test tool registry integration."""
    
    def test_register_tool(self):
        """
        Test registering tool in registry.
        
        Rationale: Ensures tool can be used in tool registry.
        """
        registry = ToolRegistry()
        tool = ProjectWorldStateTool()
        
        registry.register_tool(tool)
        
        assert registry.get_tool("project_world_state") == tool
    
    def test_tool_format_result(self):
        """
        Test tool result formatting.
        
        Rationale: Ensures results are formatted for LLM consumption.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.execute(operation="build_world_state", project_root=tmpdir)
            
            formatted = tool.format_result(result)
            
            assert isinstance(formatted, str)
            assert len(formatted) > 0
