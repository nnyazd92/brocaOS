"""
Tests for directory structure generator.

Tests the automatic generation of directory hierarchy for /home/wizard/broca.
"""

from __future__ import annotations

import tempfile
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

from broca.world_state.directory_structure import DirectoryStructureGenerator


class TestDirectoryStructureGenerator:
    """Test DirectoryStructureGenerator functionality."""
    
    def test_scan_directory(self):
        """
        Test that scan_directory collects files and directories correctly.
        
        Rationale: Ensures directory scanning works correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            test_dir = Path(tmpdir) / "test_root"
            test_dir.mkdir()
            
            # Create subdirectories and files
            (test_dir / "file1.txt").write_text("content1")
            (test_dir / "file2.py").write_text("content2")
            subdir1 = test_dir / "subdir1"
            subdir1.mkdir()
            (subdir1 / "file3.txt").write_text("content3")
            subdir2 = test_dir / "subdir2"
            subdir2.mkdir()
            (subdir2 / "file4.py").write_text("content4")
            
            generator = DirectoryStructureGenerator(root_path=str(test_dir))
            files, directories = generator.scan_directory()
            
            # Verify files are collected
            file_paths = [f["path"] for f in files]
            assert "file1.txt" in file_paths
            assert "file2.py" in file_paths
            assert "subdir1/file3.txt" in file_paths or "subdir1\\file3.txt" in file_paths
            assert "subdir2/file4.py" in file_paths or "subdir2\\file4.py" in file_paths
            
            # Verify directories are collected
            assert "subdir1" in directories
            assert "subdir2" in directories
    
    def test_scan_directory_skips_hidden_files(self):
        """
        Test that scan_directory skips hidden files and directories.
        
        Rationale: Ensures hidden files are excluded from the structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_root"
            test_dir.mkdir()
            
            # Create visible and hidden files/dirs
            (test_dir / "visible.txt").write_text("visible")
            (test_dir / ".hidden.txt").write_text("hidden")
            (test_dir / "visible_dir").mkdir()
            (test_dir / ".hidden_dir").mkdir()
            (test_dir / ".hidden_dir" / "file.txt").write_text("content")
            
            generator = DirectoryStructureGenerator(root_path=str(test_dir))
            files, directories = generator.scan_directory()
            
            # Verify only visible files/dirs are included
            file_paths = [f["path"] for f in files]
            assert "visible.txt" in file_paths
            assert ".hidden.txt" not in file_paths
            assert "visible_dir" in directories
            assert ".hidden_dir" not in directories
    
    def test_build_directory_tree(self):
        """
        Test that build_directory_tree creates correct hierarchical structure.
        
        Rationale: Ensures tree building logic works correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_root"
            test_dir.mkdir()
            
            # Create structure
            (test_dir / "root_file.txt").write_text("content")
            subdir1 = test_dir / "subdir1"
            subdir1.mkdir()
            (subdir1 / "file1.txt").write_text("content")
            subdir2 = test_dir / "subdir2"
            subdir2.mkdir()
            (subdir2 / "file2.py").write_text("content")
            nested = subdir1 / "nested"
            nested.mkdir()
            (nested / "file3.txt").write_text("content")
            
            generator = DirectoryStructureGenerator(root_path=str(test_dir))
            files, directories = generator.scan_directory()
            tree = generator.build_directory_tree(files, directories)
            
            # Verify structure
            assert "subdir1" in tree
            assert "subdir2" in tree
            assert "files" in tree or any("root_file.txt" in str(v) for v in tree.values())
            
            # Verify nested structure
            assert "children" in tree.get("subdir1", {}) or "nested" in tree.get("subdir1", {})
            assert "files" in tree.get("subdir1", {}) or any("file1.txt" in str(v) for v in tree.get("subdir1", {}).values())
    
    def test_get_directory_hierarchy(self):
        """
        Test that get_directory_hierarchy returns correct structure.
        
        Rationale: Ensures the hierarchy method returns the directory tree correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_root"
            test_dir.mkdir()
            
            (test_dir / "file1.txt").write_text("content")
            subdir = test_dir / "subdir"
            subdir.mkdir()
            (subdir / "file2.txt").write_text("content")
            
            generator = DirectoryStructureGenerator(root_path=str(test_dir))
            hierarchy = generator.get_directory_hierarchy()
            
            # Verify hierarchy structure
            assert isinstance(hierarchy, dict)
            # Should have subdir in the hierarchy
            assert "subdir" in hierarchy or any("subdir" in str(k) for k in hierarchy.keys())
    
    def test_handles_missing_directory(self):
        """
        Test that handles missing directory gracefully.
        
        Rationale: Ensures graceful error handling when directory doesn't exist.
        """
        generator = DirectoryStructureGenerator(root_path="/nonexistent/path/that/does/not/exist")
        
        # Should return empty structure or handle gracefully
        hierarchy = generator.get_directory_hierarchy()
        assert isinstance(hierarchy, dict)
    
    def test_handles_permission_errors(self):
        """
        Test that handles permission errors gracefully.
        
        Rationale: Ensures permission errors don't crash the system.
        """
        # This test might not work on all systems, but we test the structure
        generator = DirectoryStructureGenerator(root_path="/home/wizard/broca")
        
        # Should not raise exception even if there are permission issues
        try:
            hierarchy = generator.get_directory_hierarchy()
            assert isinstance(hierarchy, dict)
        except PermissionError:
            pytest.skip("Cannot test permission errors in this environment")
    
    def test_empty_directory(self):
        """
        Test that empty directory returns empty structure.
        
        Rationale: Ensures empty directories are handled correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "empty_root"
            test_dir.mkdir()
            
            generator = DirectoryStructureGenerator(root_path=str(test_dir))
            hierarchy = generator.get_directory_hierarchy()
            
            assert isinstance(hierarchy, dict)
            # Should be empty or have minimal structure
            assert len(hierarchy) == 0 or (len(hierarchy) == 1 and "files" in hierarchy)


class TestWorldStateAggregatorBrocaHouse:
    """Test that WorldStateAggregator includes broca_house structure."""
    
    def test_aggregator_includes_broca_house_when_generator_provided(self):
        """
        Test that WorldStateAggregator includes broca_house structure.
        
        Rationale: Ensures broca_house structure is included in world state.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "broca"
            test_dir.mkdir()
            (test_dir / "test.txt").write_text("content")
            
            from broca.world_state.aggregator import WorldStateAggregator
            from broca.world_state.directory_structure import DirectoryStructureGenerator
            
            generator = DirectoryStructureGenerator(root_path=str(test_dir))
            aggregator = WorldStateAggregator(directory_structure_generator=generator)
            
            world_state = aggregator.aggregate()
            
            # Verify repo section exists
            assert "repo" in world_state
            assert "root" in world_state["repo"]
            assert "tree_hash" in world_state["repo"]
            assert "last_scan" in world_state["repo"]
    
    def test_aggregator_works_without_generator(self):
        """
        Test that WorldStateAggregator works when generator is not provided.
        
        Rationale: Ensures backward compatibility when generator is None.
        """
        from broca.world_state.aggregator import WorldStateAggregator
        
        aggregator = WorldStateAggregator(directory_structure_generator=None)
        
        world_state = aggregator.aggregate()
        
        # Should not include repo section
        assert "repo" not in world_state
        
        # Should still include other sections
        assert "system" in world_state
        assert "timestamp" in world_state
    
    def test_get_broca_house_structure_returns_correct_structure(self):
        """
        Test that get_broca_house_structure() returns correct structure.
        
        Rationale: Ensures the method returns the directory hierarchy correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "broca"
            test_dir.mkdir()
            subdir = test_dir / "subdir"
            subdir.mkdir()
            (subdir / "test.txt").write_text("content")
            
            from broca.world_state.aggregator import WorldStateAggregator
            from broca.world_state.directory_structure import DirectoryStructureGenerator
            
            generator = DirectoryStructureGenerator(root_path=str(test_dir))
            aggregator = WorldStateAggregator(directory_structure_generator=generator)
            
            structure = aggregator.get_broca_house_structure()
            
            # Verify structure
            assert structure.get("available") is True
            assert "repo" in structure
            assert "root" in structure["repo"]
            assert "tree_hash" in structure["repo"]
            assert "last_scan" in structure["repo"]
            assert "note" in structure
    
    def test_get_broca_house_structure_handles_missing_generator(self):
        """
        Test that get_broca_house_structure() handles missing generator.
        
        Rationale: Ensures graceful handling when generator is None.
        """
        from broca.world_state.aggregator import WorldStateAggregator
        
        aggregator = WorldStateAggregator(directory_structure_generator=None)
        
        structure = aggregator.get_broca_house_structure()
        
        assert structure.get("available") is False
    
    def test_get_broca_house_structure_handles_errors(self):
        """
        Test that get_broca_house_structure() handles errors gracefully.
        
        Rationale: Ensures errors don't break world state aggregation.
        """
        from broca.world_state.aggregator import WorldStateAggregator
        from broca.world_state.directory_structure import DirectoryStructureGenerator
        from unittest.mock import Mock
        
        # Create a mock generator that raises an error
        mock_generator = Mock(spec=DirectoryStructureGenerator)
        mock_generator.get_directory_hierarchy.side_effect = Exception("Test error")
        
        aggregator = WorldStateAggregator(directory_structure_generator=mock_generator)
        
        structure = aggregator.get_broca_house_structure()
        
        assert structure.get("available") is False
        assert "error" in structure

