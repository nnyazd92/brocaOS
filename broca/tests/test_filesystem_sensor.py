"""
Tests for FileSystemSensor implementation.

Tests file system monitoring.
"""

from __future__ import annotations

import pytest
import tempfile
import os
from pathlib import Path

from broca.environment.sensors.filesystem_sensor import FileSystemSensor


class TestFileSystemSensorInitialization:
    """Test FileSystemSensor initialization."""
    
    def test_init_creates_sensor(self):
        """Test that filesystem sensor initializes."""
        sensor = FileSystemSensor()
        
        assert sensor is not None
        assert sensor.sensor_id is not None
        assert sensor.sensor_type == "filesystem"
    
    def test_init_with_monitored_path(self):
        """Test initialization with specific path to monitor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sensor = FileSystemSensor(monitored_path=tmpdir)
            
            assert sensor.monitored_path == tmpdir


class TestFileSystemSensorRead:
    """Test sensor reading functionality."""
    
    def test_read_file_changes(self):
        """Test reading file system changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sensor = FileSystemSensor(monitored_path=tmpdir)
            reading = sensor.read()
            
            assert reading is not None
            assert reading.sensor_type == "filesystem"
            assert 'file_changes' in reading.value or 'directory_structure' in reading.value
    
    def test_read_disk_usage(self):
        """Test reading disk usage."""
        sensor = FileSystemSensor()
        reading = sensor.read()
        
        assert 'disk_usage' in reading.value or 'directory_structure' in reading.value
    
    def test_read_directory_structure(self):
        """Test reading directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            (Path(tmpdir) / "test1.txt").write_text("test")
            (Path(tmpdir) / "test2.txt").write_text("test")
            
            sensor = FileSystemSensor(monitored_path=tmpdir)
            reading = sensor.read()
            
            assert reading is not None
            # Should detect files in directory
            assert 'directory_structure' in reading.value or 'file_count' in reading.value


class TestFileSystemSensorCapabilities:
    """Test sensor capabilities."""
    
    def test_get_capabilities(self):
        """Test getting sensor capabilities."""
        sensor = FileSystemSensor()
        capabilities = sensor.get_capabilities()
        
        assert capabilities.sensor_type == "filesystem"
        assert len(capabilities.metrics) > 0

