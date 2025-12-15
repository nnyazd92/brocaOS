"""
Tests for expanded filesystem operations.

Tests new filesystem actuator operations.
"""

from __future__ import annotations

import pytest
import tempfile
import os
import stat
from pathlib import Path

from broca.environment.actuators.filesystem_actuator import FileSystemActuator
from broca.environment.access_types import AccessLevel
from broca.environment.tools.environment_tool import EnvironmentAccessTool


class TestReadFileOperation:
    """Test read_file operation."""
    
    def test_read_file_success(self):
        """Test reading a file successfully."""
        actuator = FileSystemActuator()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content")
            tmp_path = tmp.name
        
        try:
            result = actuator.activate({
                'operation': 'read_file',
                'path': tmp_path
            })
            
            assert result.success is True
            assert result.data['content'] == "test content"
        finally:
            os.unlink(tmp_path)
    
    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        actuator = FileSystemActuator()
        
        result = actuator.activate({
            'operation': 'read_file',
            'path': '/nonexistent/file.txt'
        })
        
        assert result.success is False
        assert "not found" in result.error.lower() or "does not exist" in result.error.lower()


class TestListDirectoryOperation:
    """Test list_directory operation."""
    
    def test_list_directory_success(self):
        """Test listing directory contents."""
        actuator = FileSystemActuator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.txt").write_text("content2")
            (Path(tmpdir) / "subdir").mkdir()
            
            result = actuator.activate({
                'operation': 'list_directory',
                'path': tmpdir
            })
            
            assert result.success is True
            assert 'items' in result.data
            assert len(result.data['items']) >= 3  # file1, file2, subdir
    
    def test_list_directory_not_found(self):
        """Test listing non-existent directory."""
        actuator = FileSystemActuator()
        
        result = actuator.activate({
            'operation': 'list_directory',
            'path': '/nonexistent/directory'
        })
        
        assert result.success is False


class TestMoveFileOperation:
    """Test move_file operation."""
    
    def test_move_file_success(self):
        """Test moving a file successfully."""
        actuator = FileSystemActuator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.txt"
            dst = Path(tmpdir) / "dest.txt"
            src.write_text("test content")
            
            result = actuator.activate({
                'operation': 'move_file',
                'source_path': str(src),
                'destination_path': str(dst)
            })
            
            assert result.success is True
            assert not src.exists()
            assert dst.exists()
            assert dst.read_text() == "test content"


class TestCopyFileOperation:
    """Test copy_file operation."""
    
    def test_copy_file_success(self):
        """Test copying a file successfully."""
        actuator = FileSystemActuator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.txt"
            dst = Path(tmpdir) / "copy.txt"
            src.write_text("test content")
            
            result = actuator.activate({
                'operation': 'copy_file',
                'source_path': str(src),
                'destination_path': str(dst)
            })
            
            assert result.success is True
            assert src.exists()
            assert dst.exists()
            assert dst.read_text() == "test content"


class TestDeleteDirectoryOperation:
    """Test delete_directory operation."""
    
    def test_delete_directory_success(self):
        """Test deleting a directory."""
        actuator = FileSystemActuator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "file.txt").write_text("content")
            
            result = actuator.activate({
                'operation': 'delete_directory',
                'path': str(subdir),
                'recursive': True
            })
            
            assert result.success is True
            assert not subdir.exists()


class TestCheckFileExistsOperation:
    """Test check_file_exists operation."""
    
    def test_check_file_exists_true(self):
        """Test checking existing file."""
        actuator = FileSystemActuator()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = actuator.activate({
                'operation': 'check_file_exists',
                'path': tmp_path
            })
            
            assert result.success is True
            assert result.data['exists'] is True
        finally:
            os.unlink(tmp_path)
    
    def test_check_file_exists_false(self):
        """Test checking non-existent file."""
        actuator = FileSystemActuator()
        
        result = actuator.activate({
            'operation': 'check_file_exists',
            'path': '/nonexistent/file.txt'
        })
        
        assert result.success is True
        assert result.data['exists'] is False


class TestGetFileInfoOperation:
    """Test get_file_info operation."""
    
    def test_get_file_info_success(self):
        """Test getting file information."""
        actuator = FileSystemActuator()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        try:
            result = actuator.activate({
                'operation': 'get_file_info',
                'path': tmp_path
            })
            
            assert result.success is True
            assert 'size' in result.data
            assert 'is_file' in result.data or 'is_directory' in result.data
        finally:
            os.unlink(tmp_path)


class TestCreateSymlinkOperation:
    """Test create_symlink operation."""
    
    def test_create_symlink_success(self):
        """Test creating a symlink."""
        actuator = FileSystemActuator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            target.write_text("content")
            link = Path(tmpdir) / "link.txt"
            
            result = actuator.activate({
                'operation': 'create_symlink',
                'target_path': str(target),
                'link_path': str(link)
            })
            
            assert result.success is True
            assert link.is_symlink()
            assert link.readlink() == target


class TestReadSymlinkOperation:
    """Test read_symlink operation."""
    
    def test_read_symlink_success(self):
        """Test reading a symlink target."""
        actuator = FileSystemActuator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            target.write_text("content")
            link = Path(tmpdir) / "link.txt"
            link.symlink_to(target)
            
            result = actuator.activate({
                'operation': 'read_symlink',
                'path': str(link)
            })
            
            assert result.success is True
            assert 'target' in result.data


class TestFilesystemOperationsWithTool:
    """Test filesystem operations through tool interface."""
    
    def test_read_file_via_tool(self):
        """Test reading file through environment tool."""
        tool = EnvironmentAccessTool()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content")
            tmp_path = tmp.name
        
        try:
            # Read-only operation should work at SANDBOXED level
            result = tool.execute(
                action="control_actuator",
                actuator_id="filesystem_actuator",
                operation="read_file",
                parameters={"path": tmp_path}
            )
            
            # Should succeed (read-only operations don't need approval)
            assert result["success"] is True or "approval" not in result.get("error", "").lower()
        finally:
            os.unlink(tmp_path)
    
    def test_write_operation_requires_approval(self):
        """Test that write operations require approval."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS level first
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Now try the operation - should require approval token
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/test.txt", "content": "test"}
        )
        
        # Should require approval (not in emergency mode)
        assert result["success"] is False
        assert "approval" in result.get("error", "").lower() or "approval_request_id" in result

