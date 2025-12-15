"""
Tests for minimal project world state.

Verifies that project world state only includes directory structure and filenames,
with no extraneous metadata (file sizes, timestamps, statistics, etc.).
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock
import tempfile
from pathlib import Path

from broca.world_state.aggregator import WorldStateAggregator
from broca.tools.project_world_state import ProjectWorldStateTool


class TestMinimalProjectWorldState:
    """Test that project world state is minimal (directory_tree + filenames only)."""
    
    def test_project_state_includes_only_directory_tree_and_filenames(self):
        """
        Test that project state only includes directory_tree and filenames.
        
        Rationale: Project state should be minimal to avoid overwhelming system prompt.
        """
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.py").write_text("print('test1')")
            (Path(tmpdir) / "file2.py").write_text("print('test2')")
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "file3.py").write_text("print('test3')")
            
            # Build world state
            project_tool = ProjectWorldStateTool(project_root=tmpdir)
            project_tool.build_world_state(project_root=tmpdir)
            
            # Create aggregator
            aggregator = WorldStateAggregator(project_world_state_tool=project_tool)
            
            # Get project state
            project_state = aggregator.get_project_state()
            
            assert project_state["available"] is True
            
            # Should only have directory_tree and filenames
            assert "directory_tree" in project_state
            assert "filenames" in project_state
            
            # Should NOT have extraneous fields
            assert "project_root" not in project_state
            assert "last_updated" not in project_state
            assert "statistics" not in project_state
            assert "files" not in project_state  # Should be "filenames" not "files"
            assert "file_count" not in project_state
            assert "directory_count" not in project_state
            
            # Verify filenames is a simple list of paths
            filenames = project_state["filenames"]
            assert isinstance(filenames, list)
            assert "file1.py" in filenames
            assert "file2.py" in filenames
            assert "subdir/file3.py" in filenames
            
            # Verify directory_tree structure
            directory_tree = project_state["directory_tree"]
            assert isinstance(directory_tree, dict)
            assert "_files" in directory_tree or "subdir" in directory_tree
    
    def test_aggregate_includes_only_minimal_project_state(self):
        """
        Test that aggregate() includes only minimal project state.
        
        Rationale: System prompt should not be overwhelmed with metadata.
        """
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test.py").write_text("print('test')")
            
            # Build world state
            project_tool = ProjectWorldStateTool(project_root=tmpdir)
            project_tool.build_world_state(project_root=tmpdir)
            
            # Create aggregator
            aggregator = WorldStateAggregator(project_world_state_tool=project_tool)
            
            # Aggregate world state
            world_state = aggregator.aggregate()
            
            # Verify project section exists
            assert "project" in world_state
            project = world_state["project"]
            
            # Should only have directory_tree and filenames
            assert "directory_tree" in project
            assert "filenames" in project
            
            # Should NOT have extraneous fields
            assert "root" not in project
            assert "last_updated" not in project
            assert "statistics" not in project
            assert "files" not in project  # Should be "filenames" not "files"
            assert "file_count" not in project
            assert "directory_count" not in project
            
            # Verify filenames is a simple list
            filenames = project["filenames"]
            assert isinstance(filenames, list)
            assert len(filenames) > 0
            # Should be simple strings (paths), not objects with metadata
            for filename in filenames:
                assert isinstance(filename, str)
    
    def test_filenames_are_simple_paths_no_metadata(self):
        """
        Test that filenames are simple path strings, not objects with metadata.
        
        Rationale: Filenames should be minimal - just the path strings.
        """
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.py").write_text("test1")
            (Path(tmpdir) / "file2.txt").write_text("test2")
            
            # Build world state
            project_tool = ProjectWorldStateTool(project_root=tmpdir)
            project_tool.build_world_state(project_root=tmpdir)
            
            # Create aggregator
            aggregator = WorldStateAggregator(project_world_state_tool=project_tool)
            
            # Get project state
            project_state = aggregator.get_project_state()
            
            filenames = project_state["filenames"]
            
            # Each filename should be a simple string
            for filename in filenames:
                assert isinstance(filename, str)
                # Should not be a dict with metadata
                assert not isinstance(filename, dict)
                # Should not have metadata fields
                assert "path" not in str(filename) if isinstance(filename, str) else True
                assert "size" not in str(filename) if isinstance(filename, str) else True
                assert "metadata" not in str(filename) if isinstance(filename, str) else True

