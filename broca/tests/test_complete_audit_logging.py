"""
Tests for complete audit logging.

Tests that ALL operations are logged to the audit trail.
"""

from __future__ import annotations

import pytest

from broca.environment.tools.environment_tool import EnvironmentAccessTool


class TestAuditLoggingAllOperations:
    """Test that all operations are logged."""
    
    def test_read_sensor_logged(self):
        """Test that read_sensor operations are logged."""
        tool = EnvironmentAccessTool()
        tool.access_system.discover_and_register_sensors()
        
        sensors = tool.access_system.sensor_registry.sensors
        if sensors:
            sensor_id = list(sensors.keys())[0]
            tool.execute(action="read_sensor", sensor_id=sensor_id)
            
            # Check audit log
            log_entries = tool.access_system.policy_manager.get_audit_log(operation="read_sensor")
            assert len(log_entries) > 0
            assert log_entries[-1]["operation"] == "read_sensor"
    
    def test_list_sensors_logged(self):
        """Test that list_sensors operations are logged."""
        tool = EnvironmentAccessTool()
        tool.execute(action="list_sensors")
        
        # Check audit log
        log_entries = tool.access_system.policy_manager.get_audit_log(operation="list_sensors")
        assert len(log_entries) > 0
        assert log_entries[-1]["operation"] == "list_sensors"
    
    def test_get_access_level_logged(self):
        """Test that get_access_level operations are logged."""
        tool = EnvironmentAccessTool()
        tool.execute(action="get_access_level")
        
        # Check audit log
        log_entries = tool.access_system.policy_manager.get_audit_log(operation="get_access_level")
        assert len(log_entries) > 0
        assert log_entries[-1]["operation"] == "get_access_level"
    
    def test_failed_operations_logged(self):
        """Test that failed operations are also logged."""
        tool = EnvironmentAccessTool()
        
        # Try invalid operation
        tool.execute(action="read_sensor", sensor_id="nonexistent")
        
        # Check audit log
        log_entries = tool.access_system.policy_manager.get_audit_log(operation="read_sensor")
        assert len(log_entries) > 0
        # Last entry should be the failed one
        last_entry = log_entries[-1]
        assert last_entry["operation"] == "read_sensor"
        assert last_entry["result"].get("success") is False
    
    def test_audit_log_contains_timestamps(self):
        """Test that all audit log entries contain timestamps."""
        tool = EnvironmentAccessTool()
        tool.execute(action="get_access_level")
        
        log_entries = tool.access_system.policy_manager.get_audit_log()
        assert len(log_entries) > 0
        
        for entry in log_entries:
            assert "timestamp" in entry
            assert entry["timestamp"] is not None
    
    def test_audit_log_contains_access_level(self):
        """Test that audit log entries contain access level."""
        tool = EnvironmentAccessTool()
        tool.execute(action="get_access_level")
        
        log_entries = tool.access_system.policy_manager.get_audit_log()
        assert len(log_entries) > 0
        
        for entry in log_entries:
            assert "access_level" in entry
            assert entry["access_level"] is not None

