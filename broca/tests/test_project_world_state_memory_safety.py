"""
Tests for Project World State Tool memory safety.

Tests to ensure the tool doesn't cause memory leaks by reading
binary files, huge files, or loading entire files into memory.
"""

from __future__ import annotations

import tempfile
import os
from pathlib import Path
import pytest

from broca.tools.project_world_state import ProjectWorldStateTool


class TestMemorySafety:
    """Test memory safety features."""
    
    def test_skip_binary_files(self):
        """
        Test that binary files are excluded from scanning.
        
        Rationale: Binary files should not be included in world state (only allowed extensions).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a binary file (won't be included since it's not .py)
            binary_file = Path(tmpdir) / "binary.bin"
            binary_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe\xfd' * 1000)
            
            # Create a Python file for comparison
            py_file = Path(tmpdir) / "text.py"
            py_file.write_text("Line 1\nLine 2\nLine 3")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            
            # Find the files in results
            binary_info = next((f for f in result["files"] if f["path"] == "binary.bin"), None)
            py_info = next((f for f in result["files"] if f["path"] == "text.py"), None)
            
            # Binary file should not be in results (not .py extension)
            assert binary_info is None
            
            # Python file should have metadata
            assert py_info is not None
            assert "metadata" in py_info
            assert "creation_date" in py_info["metadata"]
            assert "last_modified" in py_info["metadata"]
            assert "file_size" in py_info["metadata"]
    
    def test_handle_large_files(self):
        """
        Test that large files are handled correctly (metadata only, no content reading).
        
        Rationale: Large files should have metadata collected without reading contents.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a large Python file (simulate by checking size limit)
            large_file = Path(tmpdir) / "large.py"
            # Write enough data to exceed typical limits (e.g., 10MB)
            large_file.write_text("x" * (10 * 1024 * 1024 + 1))
            
            # Create a normal Python file
            normal_file = Path(tmpdir) / "normal.py"
            normal_file.write_text("Line 1\nLine 2")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            
            # Both files should be in results (we collect metadata for all files)
            large_info = next((f for f in result["files"] if f["path"] == "large.py"), None)
            normal_info = next((f for f in result["files"] if f["path"] == "normal.py"), None)
            
            assert large_info is not None
            # Large file should have metadata (we don't read contents, just get stats)
            assert "metadata" in large_info
            assert large_info["metadata"]["file_size"] > 10 * 1024 * 1024  # Should be > 10MB
            
            # Normal file should have metadata
            assert normal_info is not None
            assert "metadata" in normal_info
            assert normal_info["metadata"]["file_size"] < 100  # Should be small
    
    def test_only_collect_metadata_not_contents(self):
        """
        Test that we only collect file metadata, not file contents.
        
        Rationale: We should never load file contents into memory, only collect metadata.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file with many lines
            large_file = Path(tmpdir) / "many_lines.py"
            with open(large_file, 'w') as f:
                for i in range(10000):
                    f.write(f"Line {i}\n")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            
            file_info = next((f for f in result["files"] if f["path"] == "many_lines.py"), None)
            assert file_info is not None
            # Should have metadata, not file contents
            assert "metadata" in file_info
            assert "headers" not in file_info  # No headers field anymore
            # File size should reflect the actual file size
            assert file_info["metadata"]["file_size"] > 0
    
    def test_skip_common_binary_extensions(self):
        """
        Test that common binary file extensions are excluded.
        
        Rationale: Non-.py files should not be included at all.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with binary extensions (won't be included)
            extensions = ['.bin', '.exe', '.so', '.dll', '.dylib', '.jpg', '.png', '.pdf', '.zip', '.tar', '.gz']
            
            for ext in extensions:
                binary_file = Path(tmpdir) / f"test{ext}"
                binary_file.write_bytes(b'\x00\x01\x02' * 100)
            
            # Create a Python file
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("text content")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            
            # All binary files should not be in results (not .py extension)
            for ext in extensions:
                file_info = next((f for f in result["files"] if f["path"] == f"test{ext}"), None)
                assert file_info is None
            
            # Python file should have metadata
            py_info = next((f for f in result["files"] if f["path"] == "test.py"), None)
            assert py_info is not None
            assert "metadata" in py_info
            assert "creation_date" in py_info["metadata"]
            assert "last_modified" in py_info["metadata"]
    
    def test_handle_unicode_files_safely(self):
        """
        Test that Unicode files are handled safely without memory issues.
        
        Rationale: Unicode files should be read safely with proper encoding.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Unicode Python file
            unicode_file = Path(tmpdir) / "unicode.py"
            unicode_file.write_text("测试 🎉\nLine 2\nLine 3", encoding='utf-8')
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            
            file_info = next((f for f in result["files"] if f["path"] == "unicode.py"), None)
            assert file_info is not None
            # Should have metadata (we don't read file contents anymore)
            assert "metadata" in file_info
            assert "creation_date" in file_info["metadata"]
            assert "last_modified" in file_info["metadata"]
            assert file_info["metadata"]["file_size"] > 0
    
    def test_skip_database_files(self):
        """
        Test that database files are excluded.
        
        Rationale: Non-.py files should not be included at all.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create database-like files (won't be included)
            db_files = ['test.db', 'test.sqlite', 'test.sqlite3', 'test.faiss']
            
            for db_file in db_files:
                db_path = Path(tmpdir) / db_file
                db_path.write_bytes(b'\x00' * 1000)
            
            # Create a Python file for comparison
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("import os")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            
            # All database files should not be in results (not .py extension)
            for db_file in db_files:
                file_info = next((f for f in result["files"] if f["path"] == db_file), None)
                assert file_info is None
            
            # Python file should be included
            py_info = next((f for f in result["files"] if f["path"] == "test.py"), None)
            assert py_info is not None
    
    def test_memory_efficient_scanning(self):
        """
        Test that scanning doesn't load all files into memory at once.
        
        Rationale: We should process files one at a time, not load all into memory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create many Python files
            for i in range(100):
                file_path = Path(tmpdir) / f"file_{i}.py"
                file_path.write_text(f"Content {i}\nLine 2\nLine 3")
            
            tool = ProjectWorldStateTool(project_root=tmpdir)
            result = tool.build_world_state(project_root=tmpdir)
            
            assert result["success"] is True
            assert len(result["files"]) == 100
            
            # All files should have metadata (we collect metadata for all files)
            for file_info in result["files"]:
                assert "metadata" in file_info
                assert "creation_date" in file_info["metadata"]
                assert "last_modified" in file_info["metadata"]
                assert "file_size" in file_info["metadata"]
                assert "headers" not in file_info  # No headers field anymore

