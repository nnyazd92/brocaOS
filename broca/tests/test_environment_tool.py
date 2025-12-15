"""
Tests for EnvironmentAccessTool implementation.

Tests tool protocol compliance and integration with registry.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from broca.environment.tools.environment_tool import EnvironmentAccessTool
from broca.environment.access_system import EnvironmentAccessSystem
from broca.environment.access_types import AccessLevel


class TestEnvironmentAccessToolProtocol:
    """Test tool protocol compliance."""
    
    def test_tool_has_required_properties(self):
        """Test that tool has required properties."""
        tool = EnvironmentAccessTool()
        
        assert tool.name == "environment_access"
        assert isinstance(tool.description, str)
        assert isinstance(tool.parameters, dict)
        assert "type" in tool.parameters
        assert "properties" in tool.parameters
    
    def test_tool_name(self):
        """Test tool name property."""
        tool = EnvironmentAccessTool()
        assert tool.name == "environment_access"
    
    def test_tool_description(self):
        """Test tool description property."""
        tool = EnvironmentAccessTool()
        description = tool.description
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "sensor" in description.lower() or "environment" in description.lower()


class TestEnvironmentAccessToolExecute:
    """Test tool execution."""
    
    def test_execute_list_sensors(self):
        """Test listing sensors."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="list_sensors")
        
        assert result["success"] is True
        assert "sensors" in result
        assert "count" in result
    
    def test_execute_get_access_level(self):
        """Test getting access level."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="get_access_level")
        
        assert result["success"] is True
        assert result["access_level"] == "SANDBOXED"
        assert result["value"] == 0
    
    def test_execute_read_sensor_missing_id(self):
        """Test reading sensor without ID."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="read_sensor")
        
        assert result["success"] is False
        assert "sensor_id" in result["error"].lower() or "required" in result["error"].lower()
    
    def test_execute_request_escalation(self):
        """Test requesting escalation."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(
            action="request_escalation",
            target_level="SUPERVISED",
            rationale="Test escalation"
        )
        
        assert result["success"] is True
        assert "request_id" in result
        assert result["target_level"] == "SUPERVISED"
    
    def test_execute_unknown_action(self):
        """Test executing unknown action."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="unknown_action")
        
        assert result["success"] is False
        assert "unknown" in result["error"].lower()


class TestEnvironmentAccessToolFormatResult:
    """Test result formatting."""
    
    def test_format_result_success(self):
        """Test formatting successful result."""
        tool = EnvironmentAccessTool()
        
        result = {"success": True, "access_level": "SANDBOXED"}
        formatted = tool.format_result(result)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
    
    def test_format_result_error(self):
        """Test formatting error result."""
        tool = EnvironmentAccessTool()
        
        result = {"success": False, "error": "Test error"}
        formatted = tool.format_result(result)
        
        assert "error" in formatted.lower()
        assert "test error" in formatted.lower()

