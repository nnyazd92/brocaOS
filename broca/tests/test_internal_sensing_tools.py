"""
Tests for internal sensing tools.

Tests tools that allow LLM to query and access internal sensing data.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest

from broca.tools.internal_sensing_tool import QueryInternalStateTool, GetInteroceptiveReportTool
from broca.internal_sensing.framework import InternalSensingFramework


class TestQueryInternalStateTool:
    """Test QueryInternalStateTool."""
    
    def test_tool_properties(self):
        """
        Test that tool has required properties.
        
        Rationale: Ensures tool conforms to Tool protocol.
        """
        framework = InternalSensingFramework()
        tool = QueryInternalStateTool(framework)
        
        assert tool.name == "query_internal_state"
        assert isinstance(tool.description, str)
        assert isinstance(tool.parameters, dict)
    
    def test_query_internal_state_tool(self):
        """
        Test that tool queries current internal state.
        
        Rationale: Ensures tool can retrieve internal state.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        tool = QueryInternalStateTool(framework)
        result = tool.execute()
        
        assert result["success"] is True
        assert "state" in result
    
    def test_query_internal_state_aspect(self):
        """
        Test that tool can query specific aspects.
        
        Rationale: Ensures tool supports filtering.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        tool = QueryInternalStateTool(framework)
        result = tool.execute(aspect="computational")
        
        assert result["success"] is True
        assert "computational" in result.get("state", {}) or "state" in result


class TestGetInteroceptiveReportTool:
    """Test GetInteroceptiveReportTool."""
    
    def test_tool_properties(self):
        """
        Test that tool has required properties.
        
        Rationale: Ensures tool conforms to Tool protocol.
        """
        framework = InternalSensingFramework()
        tool = GetInteroceptiveReportTool(framework)
        
        assert tool.name == "get_interoceptive_report"
        assert isinstance(tool.description, str)
        assert isinstance(tool.parameters, dict)
    
    def test_get_interoceptive_report_tool(self):
        """
        Test that tool generates reports.
        
        Rationale: Ensures tool can generate interoceptive reports.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        tool = GetInteroceptiveReportTool(framework)
        result = tool.execute()
        
        assert result["success"] is True
        assert "report" in result
        assert isinstance(result["report"], str)


class TestToolProtocolCompliance:
    """Test tool protocol compliance."""
    
    def test_tool_protocol_compliance(self):
        """
        Test that tools follow Tool protocol.
        
        Rationale: Ensures tools integrate with tool registry.
        """
        framework = InternalSensingFramework()
        query_tool = QueryInternalStateTool(framework)
        report_tool = GetInteroceptiveReportTool(framework)
        
        # Check all required properties
        assert hasattr(query_tool, "name")
        assert hasattr(query_tool, "description")
        assert hasattr(query_tool, "parameters")
        assert hasattr(query_tool, "execute")
        assert hasattr(query_tool, "format_result")
        
        assert hasattr(report_tool, "name")
        assert hasattr(report_tool, "description")
        assert hasattr(report_tool, "parameters")
        assert hasattr(report_tool, "execute")
        assert hasattr(report_tool, "format_result")
    
    def test_tool_integration(self):
        """
        Test that tools integrate with tool registry.
        
        Rationale: Ensures tools can be registered.
        """
        from broca.tools.registry import ToolRegistry
        
        framework = InternalSensingFramework()
        query_tool = QueryInternalStateTool(framework)
        report_tool = GetInteroceptiveReportTool(framework)
        
        registry = ToolRegistry()
        registry.register_tool(query_tool)
        registry.register_tool(report_tool)
        
        assert registry.get_tool("query_internal_state") is not None
        assert registry.get_tool("get_interoceptive_report") is not None

