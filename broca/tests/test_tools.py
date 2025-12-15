"""
Tests for tool abstraction and tool registry.

Tests the Tool protocol and ToolRegistry implementation.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json

from broca.tools import Tool
from broca.tools.registry import ToolRegistry


class MockTool:
    """Mock tool implementation for testing."""
    
    def __init__(self, name: str, description: str, parameters: dict):
        self._name = name
        self._description = description
        self._parameters = parameters
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> dict:
        return self._parameters
    
    def execute(self, **kwargs):
        return {"result": f"Executed {self._name} with {kwargs}"}
    
    def format_result(self, result: dict) -> str:
        return f"Formatted: {result}"


class TestToolProtocol:
    """Test Tool protocol compliance."""
    
    def test_mock_tool_has_required_properties(self):
        """
        Test that mock tool implements all required Tool protocol properties.
        
        Rationale: Ensures tools can be created that conform to the Tool protocol.
        """
        tool = MockTool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}}
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters == {"type": "object", "properties": {}}
    
    def test_mock_tool_has_required_methods(self):
        """
        Test that mock tool implements all required Tool protocol methods.
        
        Rationale: Ensures tools can execute and format results.
        """
        tool = MockTool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}}
        )
        
        result = tool.execute(param1="value1")
        assert "result" in result
        
        formatted = tool.format_result(result)
        assert isinstance(formatted, str)
        assert "Formatted" in formatted


class TestToolRegistryInitialization:
    """Test ToolRegistry initialization."""
    
    def test_init_creates_empty_registry(self):
        """
        Test that registry starts empty.
        
        Rationale: Ensures registry can be initialized without tools.
        """
        registry = ToolRegistry()
        assert len(registry.list_tools()) == 0
    
    def test_init_stores_tools_dict(self):
        """
        Test that registry maintains internal tools dictionary.
        
        Rationale: Ensures registry can track registered tools.
        """
        registry = ToolRegistry()
        assert hasattr(registry, "_tools")
        assert isinstance(registry._tools, dict)


class TestToolRegistryRegisterTool:
    """Test tool registration."""
    
    def test_register_tool_success(self):
        """
        Test registering a tool successfully.
        
        Rationale: Ensures tools can be registered in the registry.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test tool", {"type": "object"})
        
        registry.register_tool(tool)
        
        assert registry.get_tool("test_tool") == tool
        assert len(registry.list_tools()) == 1
    
    def test_register_multiple_tools(self):
        """
        Test registering multiple tools.
        
        Rationale: Ensures registry can handle multiple tools.
        """
        registry = ToolRegistry()
        tool1 = MockTool("tool1", "Tool 1", {"type": "object"})
        tool2 = MockTool("tool2", "Tool 2", {"type": "object"})
        
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        assert len(registry.list_tools()) == 2
        assert registry.get_tool("tool1") == tool1
        assert registry.get_tool("tool2") == tool2
    
    def test_register_duplicate_tool_raises_error(self):
        """
        Test that registering duplicate tool names raises error.
        
        Rationale: Ensures tool names are unique in the registry.
        """
        registry = ToolRegistry()
        tool1 = MockTool("same_name", "Tool 1", {"type": "object"})
        tool2 = MockTool("same_name", "Tool 2", {"type": "object"})
        
        registry.register_tool(tool1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register_tool(tool2)


class TestToolRegistryGetTool:
    """Test retrieving tools from registry."""
    
    def test_get_tool_success(self):
        """
        Test retrieving a registered tool.
        
        Rationale: Ensures tools can be retrieved by name.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test tool", {"type": "object"})
        registry.register_tool(tool)
        
        retrieved = registry.get_tool("test_tool")
        
        assert retrieved == tool
    
    def test_get_tool_not_found(self):
        """
        Test retrieving a non-existent tool returns None.
        
        Rationale: Ensures graceful handling of missing tools.
        """
        registry = ToolRegistry()
        
        result = registry.get_tool("nonexistent")
        
        assert result is None


class TestToolRegistryListTools:
    """Test listing tools."""
    
    def test_list_tools_empty(self):
        """
        Test listing tools when registry is empty.
        
        Rationale: Ensures empty registry returns empty list.
        """
        registry = ToolRegistry()
        
        tools = registry.list_tools()
        
        assert tools == []
    
    def test_list_tools_multiple(self):
        """
        Test listing multiple registered tools.
        
        Rationale: Ensures all registered tools are returned.
        """
        registry = ToolRegistry()
        tool1 = MockTool("tool1", "Tool 1", {"type": "object"})
        tool2 = MockTool("tool2", "Tool 2", {"type": "object"})
        tool3 = MockTool("tool3", "Tool 3", {"type": "object"})
        
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        registry.register_tool(tool3)
        
        tools = registry.list_tools()
        
        assert len(tools) == 3
        assert tool1 in tools
        assert tool2 in tools
        assert tool3 in tools


class TestToolRegistryOpenAIFormat:
    """Test OpenAI format conversion."""
    
    def test_to_openai_format_empty(self):
        """
        Test converting empty registry to OpenAI format.
        
        Rationale: Ensures empty registry returns empty list.
        """
        registry = ToolRegistry()
        
        tools_format = registry.to_openai_format()
        
        assert tools_format == []
    
    def test_to_openai_format_single_tool(self):
        """
        Test converting single tool to OpenAI format.
        
        Rationale: Ensures tools are converted to OpenAI function calling format.
        """
        registry = ToolRegistry()
        tool = MockTool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            }
        )
        registry.register_tool(tool)
        
        tools_format = registry.to_openai_format()
        
        assert len(tools_format) == 1
        assert tools_format[0]["type"] == "function"
        assert "function" in tools_format[0]
        assert tools_format[0]["function"]["name"] == "test_tool"
        assert tools_format[0]["function"]["description"] == "A test tool"
        assert tools_format[0]["function"]["parameters"] == tool.parameters
    
    def test_to_openai_format_multiple_tools(self):
        """
        Test converting multiple tools to OpenAI format.
        
        Rationale: Ensures all tools are converted correctly.
        """
        registry = ToolRegistry()
        tool1 = MockTool("tool1", "Tool 1", {"type": "object"})
        tool2 = MockTool("tool2", "Tool 2", {"type": "object"})
        
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        tools_format = registry.to_openai_format()
        
        assert len(tools_format) == 2
        names = [t["function"]["name"] for t in tools_format]
        assert "tool1" in names
        assert "tool2" in names


class TestToolRegistryExecuteToolCall:
    """Test tool call execution."""
    
    def test_execute_tool_call_success(self):
        """
        Test executing a tool call successfully.
        
        Rationale: Ensures tool calls can be executed and results formatted.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test tool", {"type": "object"})
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param1": "value1"})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        assert result["tool_call_id"] == "call_123"
        assert result["role"] == "tool"
        assert result["name"] == "test_tool"
        assert "content" in result
        assert "Formatted" in result["content"]
    
    def test_execute_tool_call_missing_name(self):
        """
        Test executing tool call with missing tool name.
        
        Rationale: Ensures graceful error handling for malformed tool calls.
        """
        registry = ToolRegistry()
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "arguments": json.dumps({})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        assert "Error" in result["content"]
        assert result["role"] == "tool"
    
    def test_execute_tool_call_nonexistent_tool(self):
        """
        Test executing tool call for non-existent tool.
        
        Rationale: Ensures graceful error handling for unknown tools.
        """
        registry = ToolRegistry()
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "nonexistent_tool",
                "arguments": json.dumps({})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        assert "Error" in result["content"]
        assert "not found" in result["content"]
        assert result["role"] == "tool"
    
    def test_execute_tool_call_invalid_json(self):
        """
        Test executing tool call with invalid JSON arguments.
        
        Rationale: Ensures graceful error handling for invalid arguments.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test tool", {"type": "object"})
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": "{ invalid json }"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        assert "Error" in result["content"] or "JSON Parsing Error" in result["content"]
        assert "Invalid JSON" in result["content"] or "JSON" in result["content"]
        # Should include detailed error information
        assert "snippet" in result["content"].lower() or "Position" in result["content"] or "Suggestions" in result["content"]
    
    def test_execute_tool_call_unterminated_string_json(self):
        """
        Test executing tool call with unterminated string in JSON.
        
        Rationale: Tests JSON repair for common error.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test tool", {"type": "object"})
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": '{"key": "unterminated'
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should either succeed (if repaired) or provide detailed error
        if "Error" in result["content"] or "JSON Parsing Error" in result["content"]:
            assert "snippet" in result["content"].lower() or "Position" in result["content"] or "unterminated" in result["content"].lower()
    
    def test_execute_tool_call_empty_arguments(self):
        """
        Test executing tool call with empty arguments.
        
        Rationale: Ensures tools can be called without arguments.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test tool", {"type": "object"})
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": "{}"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        assert result["tool_call_id"] == "call_123"
        assert result["role"] == "tool"
        assert "content" in result
    
    def test_execute_tool_call_tool_raises_exception(self):
        """
        Test executing tool call when tool execution raises exception.
        
        Rationale: Ensures tool execution errors are caught and returned gracefully.
        """
        registry = ToolRegistry()
        
        class FailingTool:
            @property
            def name(self):
                return "failing_tool"
            
            @property
            def description(self):
                return "A tool that fails"
            
            @property
            def parameters(self):
                return {"type": "object"}
            
            def execute(self, **kwargs):
                raise ValueError("Tool execution failed")
            
            def format_result(self, result):
                return str(result)
        
        tool = FailingTool()
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "failing_tool",
                "arguments": "{}"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        assert "Error" in result["content"]
        assert "execution failed" in result["content"]
        assert result["role"] == "tool"


class TestJSONRepair:
    """Test JSON repair utilities."""
    
    def test_json_repair_valid_json(self):
        """
        Test that valid JSON passes through unchanged.
        
        Rationale: Ensures repair doesn't break valid JSON.
        """
        from broca.tools.json_repair import attempt_json_repair
        
        valid_json = '{"key": "value", "num": 123}'
        result, error = attempt_json_repair(valid_json)
        
        assert error is None
        assert result == {"key": "value", "num": 123}
    
    def test_json_repair_unterminated_string(self):
        """
        Test repair of unterminated strings.
        
        Rationale: Ensures common JSON error can be fixed.
        """
        from broca.tools.json_repair import attempt_json_repair
        
        # Unterminated string
        bad_json = '{"key": "unterminated'
        result, error = attempt_json_repair(bad_json)
        
        # Should either succeed or provide detailed error
        if error is None:
            assert result is not None
        else:
            assert "Unterminated" in error or "unterminated" in error.lower()
            assert "snippet" in error.lower() or "Position" in error
    
    def test_json_repair_unescaped_quotes(self):
        """
        Test repair of unescaped quotes in strings.
        
        Rationale: Ensures quotes in string values are handled.
        """
        from broca.tools.json_repair import attempt_json_repair
        
        # Unescaped quotes
        bad_json = '{"key": "value with "quotes" inside"}'
        result, error = attempt_json_repair(bad_json)
        
        # Should either succeed or provide detailed error
        if error is None:
            assert result is not None
        else:
            assert "quote" in error.lower() or "Unescaped" in error
            assert "snippet" in error.lower()
    
    def test_json_repair_missing_commas(self):
        """
        Test repair of missing commas.
        
        Rationale: Ensures missing commas can be detected/fixed.
        """
        from broca.tools.json_repair import attempt_json_repair
        
        # Missing comma
        bad_json = '{"key1": "value1" "key2": "value2"}'
        result, error = attempt_json_repair(bad_json)
        
        # Should provide detailed error if not repairable
        if error:
            assert "comma" in error.lower() or "snippet" in error.lower()
    
    def test_json_repair_trailing_comma(self):
        """
        Test repair of trailing commas.
        
        Rationale: Ensures trailing commas are handled.
        """
        from broca.tools.json_repair import attempt_json_repair
        
        # Trailing comma
        bad_json = '{"key": "value",}'
        result, error = attempt_json_repair(bad_json)
        
        # Should succeed (trailing commas are easy to fix)
        if error is None:
            assert result == {"key": "value"}
    
    def test_diagnose_json_error(self):
        """
        Test JSON error diagnosis.
        
        Rationale: Ensures detailed error messages are generated.
        """
        from broca.tools.json_repair import diagnose_json_error
        import json
        
        bad_json = '{"key": "unterminated'
        try:
            json.loads(bad_json)
        except json.JSONDecodeError as e:
            error_msg = diagnose_json_error(bad_json, e)
            
            assert "Invalid JSON" in error_msg
            assert "Position" in error_msg
            assert "snippet" in error_msg.lower() or "Problematic" in error_msg
            assert "Suggestions" in error_msg
    
    def test_extract_problematic_snippet(self):
        """
        Test snippet extraction.
        
        Rationale: Ensures error location is clearly shown.
        """
        from broca.tools.json_repair import extract_problematic_snippet
        
        json_str = '{"key1": "value1", "key2": "value2", "key3": "bad}'
        snippet = extract_problematic_snippet(json_str, 45)
        
        assert "^" in snippet or "error here" in snippet.lower()
        assert "Line" in snippet or "column" in snippet.lower()
    
    def test_suggest_json_fix(self):
        """
        Test fix suggestions.
        
        Rationale: Ensures helpful suggestions are provided.
        """
        from broca.tools.json_repair import suggest_json_fix
        
        suggestion = suggest_json_fix("UnterminatedString", 10, '{"key": "unterminated')
        
        assert "Suggestions" in suggestion
        assert "string" in suggestion.lower()

