"""
Tests for world state formatter.
"""

from __future__ import annotations

import pytest
import json

from broca.world_state.formatter import WorldStateFormatter


class TestWorldStateFormatter:
    """Test world state formatter functionality."""
    
    @pytest.fixture
    def sample_world_state(self):
        """Create a sample world state dictionary with clean hierarchical structure."""
        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "datetime": "2024-01-01T12:00:00Z",
                "platform": "Linux",
                "platform_release": "6.0",
                "working_directory": "/test/project",
            },
            "self_model": {
                "summary": "Self-Model Summary:\nVersion: 1\nCapabilities:\n  - Test capability",
                "capabilities": ["Test capability 1", "Test capability 2"],
                "preferences": {"test_pref": "value"},
                "constraints": {"test_constraint": "value"},
            },
            "internal_state": {
                "interoceptive_report": "Current state: stable",
                "tool_statistics": {"memory": 5, "terminal": 3},
                "physiology": {"health": {"cpu_load": 0.09, "mem_pressure": 0.59, "latency_ms": 11}},
                "cognition": {"metrics": {"confidence": 0.8, "uncertainty": 0.2}},
            },
            "project": {
                "root": "/test/project",
                "last_updated": "2024-01-01T00:00:00Z",
                "statistics": {
                    "total_files": 10,
                    "total_directories": 5,
                    "total_size": 1024,
                },
            },
            "tools_registry": {
                "version": "v12345678",
                "hash": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "refresh_on_change": True
            },
            "tools": {
                "count": 2,
                "names": ["memory", "terminal"],
            },
        }
    
    def test_init_default(self):
        """Test initializing formatter with default settings."""
        formatter = WorldStateFormatter()
        
        assert formatter.max_length is None
    
    def test_init_with_max_length(self):
        """Test initializing formatter with max length."""
        formatter = WorldStateFormatter(max_length=1000)
        
        assert formatter.max_length == 1000
    
    def test_format_complete_world_state(self, sample_world_state):
        """Test formatting complete world state as JSON."""
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(sample_world_state)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert isinstance(parsed, dict)
        
        # Should have clean hierarchical structure
        assert "timestamp" in parsed
        assert "system" in parsed
        assert "self_model" in parsed
        assert "internal_state" in parsed
        assert "project" in parsed
        assert "tools" in parsed
        
        # Verify content
        assert parsed["system"]["platform"] == "Linux"
        assert "Test capability" in parsed["self_model"]["summary"]
        assert parsed["tools"]["count"] == 2
    
    def test_format_with_missing_sections(self):
        """Test formatting world state with missing sections (only system)."""
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "datetime": "2024-01-01T12:00:00Z",
                "platform": "Linux",
            },
        }
        
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(world_state)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert isinstance(parsed, dict)
        
        # Should only have system, not other sections
        assert "system" in parsed
        assert "self_model" not in parsed
        assert "internal_state" not in parsed
        assert "project" not in parsed
        assert "tools" not in parsed
    
    def test_format_system_info(self):
        """Test formatting system information section as JSON."""
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "datetime": "2024-01-01T12:00:00Z",
                "platform": "Linux",
                "platform_release": "6.0",
                "working_directory": "/test/project",
            },
        }
        
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(world_state)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed["system"]["datetime"] == "2024-01-01T12:00:00Z"
        assert parsed["system"]["platform"] == "Linux"
        assert parsed["system"]["working_directory"] == "/test/project"
    
    def test_format_self_model_with_summary(self):
        """Test formatting self-model with summary as JSON."""
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
            "self_model": {
                "summary": "Self-Model Summary:\nVersion: 1\nCapabilities:\n  - Test",
            },
        }
        
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(world_state)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert "Self-Model Summary" in parsed["self_model"]["summary"]
    
    def test_format_self_model_without_summary(self):
        """Test formatting self-model without summary as JSON."""
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
            "self_model": {
                "capabilities": ["Capability 1", "Capability 2"],
                "constraints": {"constraint1": "value1", "constraint2": "value2"},
            },
        }
        
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(world_state)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert "Capability 1" in parsed["self_model"]["capabilities"]
        assert "Capability 2" in parsed["self_model"]["capabilities"]
    
    def test_format_internal_sensing(self):
        """Test formatting internal sensing section as JSON."""
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
            "internal_state": {
                "interoceptive_report": "Current state: stable",
                "tool_statistics": {"memory": 5, "terminal": 3},
                "physiology": {"health": {"cpu_load": 0.09, "mem_pressure": 0.59, "latency_ms": 11}},
                "cognition": {"metrics": {"confidence": 0.8}},
            },
        }
        
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(world_state)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed["internal_state"]["interoceptive_report"] == "Current state: stable"
        assert parsed["internal_state"]["tool_statistics"]["memory"] == 5
        assert parsed["internal_state"]["physiology"]["health"]["latency_ms"] == 11
    
    def test_format_tools(self):
        """Test formatting tools section as JSON."""
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
            "tools_registry": {
                "version": "v12345678",
                "hash": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "refresh_on_change": True
            },
            "tools_registry": {
                "version": "v12345678",
                "hash": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "refresh_on_change": True
            },
            "tools": {
                "count": 2,
                "names": ["memory", "terminal"],
            },
        }
        
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(world_state)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert "tools_registry" in parsed
        assert parsed["tools_registry"]["version"] == "v12345678"
        assert parsed["tools"]["count"] == 2
        assert "memory" in parsed["tools"]["names"]
        assert "terminal" in parsed["tools"]["names"]
    
    def test_format_with_max_length(self, sample_world_state):
        """Test formatting with max length limit."""
        formatter = WorldStateFormatter(max_length=100)
        
        formatted = formatter.format(sample_world_state)
        
        assert len(formatted) <= 100
        # Should still be valid JSON (truncation should maintain JSON validity)
        parsed = json.loads(formatted)
        assert isinstance(parsed, dict)
        # Should have truncation marker if truncated
        if len(formatted) < len(json.dumps(sample_world_state, indent=2)):
            assert "_truncated" in parsed
    
    def test_format_empty_world_state(self):
        """Test formatting empty world state."""
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
        }
        
        formatter = WorldStateFormatter()
        
        formatted = formatter.format(world_state)
        
        # Should be valid JSON with just timestamp
        parsed = json.loads(formatted)
        assert isinstance(parsed, dict)
        assert "timestamp" in parsed
        assert len(parsed) == 1

