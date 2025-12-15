"""
Tests for self-model updater.

Tests type validation, normalization, and update application.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from broca.self_model.model import SelfModel
from broca.self_model.updater import SelfModelUpdater
from broca.self_model.consistency import ConsistencyResult
from broca.self_model.epistemic.layer import EpistemicLayer


class TestSelfModelUpdater:
    """Test self-model updater functionality."""
    
    @pytest.fixture
    def updater(self):
        """Create a SelfModelUpdater instance."""
        return SelfModelUpdater()
    
    @pytest.fixture
    def base_model(self):
        """Create a base self-model for testing."""
        from broca.self_model.source import Source
        default_source = Source.system_default()
        return SelfModel(
            capabilities=[
                {"text": "Existing capability 1", "source": default_source.to_dict()},
                {"text": "Existing capability 2", "source": default_source.to_dict()},
            ],
            knowledge_boundaries={
                "existing_boundary": {"value": "value", "source": default_source.to_dict()}
            },
            constraints={
                "existing_constraint": {"value": "value", "source": default_source.to_dict()}
            },
            metadata={"version": 1},
        )
    
    def test_normalize_capabilities_strings(self, updater):
        """Test normalizing capabilities that are already strings."""
        from broca.self_model.source import Source
        capabilities = ["Capability 1", "Capability 2", "Capability 3"]
        normalized = updater._normalize_capabilities(capabilities)
        assert len(normalized) == 3
        assert all(isinstance(cap, dict) for cap in normalized)
        assert all("text" in cap and "source" in cap for cap in normalized)
        assert normalized[0]["text"] == "Capability 1"
        assert normalized[1]["text"] == "Capability 2"
        assert normalized[2]["text"] == "Capability 3"
    
    def test_normalize_capabilities_dicts_with_name(self, updater):
        """Test normalizing capabilities that are dicts with 'name' field."""
        capabilities = [
            {"name": "Capability 1", "description": "Desc 1"},
            {"name": "Capability 2"},
            {"name": "Capability 3", "extra": "data"},
        ]
        normalized = updater._normalize_capabilities(capabilities)
        assert len(normalized) == 3
        assert all(isinstance(cap, dict) for cap in normalized)
        assert normalized[0]["text"] == "Capability 1"
        assert normalized[1]["text"] == "Capability 2"
        assert normalized[2]["text"] == "Capability 3"
        assert all("source" in cap for cap in normalized)
    
    def test_normalize_capabilities_dicts_with_description(self, updater):
        """Test normalizing capabilities that are dicts with 'description' field."""
        capabilities = [
            {"description": "Capability 1 description"},
            {"description": "Capability 2 description", "other": "data"},
        ]
        normalized = updater._normalize_capabilities(capabilities)
        assert len(normalized) == 2
        assert all(isinstance(cap, dict) for cap in normalized)
        assert normalized[0]["text"] == "Capability 1 description"
        assert normalized[1]["text"] == "Capability 2 description"
        assert all("source" in cap for cap in normalized)
    
    def test_normalize_capabilities_dicts_without_name_or_description(self, updater):
        """Test normalizing capabilities that are dicts without name/description."""
        capabilities = [
            {"type": "capability", "data": "value"},
            {"key": "value"},
        ]
        normalized = updater._normalize_capabilities(capabilities)
        # Should be converted to dicts with text and source
        assert len(normalized) == 2
        assert all(isinstance(cap, dict) for cap in normalized)
        assert all("text" in cap and "source" in cap for cap in normalized)
        # Text should be string representation of the dict
        assert isinstance(normalized[0]["text"], str)
    
    def test_normalize_capabilities_mixed_types(self, updater):
        """Test normalizing capabilities with mixed types."""
        capabilities = [
            "String capability",
            {"name": "Dict capability"},
            {"description": "Description capability"},
            {"other": "data"},
            123,  # Should be converted to string
        ]
        normalized = updater._normalize_capabilities(capabilities)
        assert len(normalized) == 5
        assert all(isinstance(cap, dict) for cap in normalized)
        assert all("text" in cap and "source" in cap for cap in normalized)
        texts = [cap["text"] for cap in normalized]
        assert "String capability" in texts
        assert "Dict capability" in texts
        assert "Description capability" in texts
        assert "123" in texts
    
    def test_normalize_capabilities_empty_list(self, updater):
        """Test normalizing empty capabilities list."""
        normalized = updater._normalize_capabilities([])
        assert normalized == []
    
    def test_normalize_capabilities_invalid_type(self, updater):
        """Test normalizing capabilities with invalid type (not a list)."""
        normalized = updater._normalize_capabilities("not a list")
        assert normalized == []
    
    def test_validate_updates_capabilities_strings(self, updater):
        """Test validating updates with string capabilities."""
        updates = {
            "capabilities": ["New capability 1", "New capability 2"],
        }
        validated = updater._validate_updates(updates)
        assert "capabilities" in validated
        assert len(validated["capabilities"]) == 2
        assert all(isinstance(cap, dict) for cap in validated["capabilities"])
        assert validated["capabilities"][0]["text"] == "New capability 1"
        assert validated["capabilities"][1]["text"] == "New capability 2"
        assert all("source" in cap for cap in validated["capabilities"])
    
    def test_validate_updates_capabilities_dicts(self, updater):
        """Test validating updates with dict capabilities (should normalize)."""
        updates = {
            "capabilities": [
                {"name": "New capability 1"},
                {"description": "New capability 2"},
            ],
        }
        validated = updater._validate_updates(updates)
        assert "capabilities" in validated
        assert len(validated["capabilities"]) == 2
        assert validated["capabilities"][0]["text"] == "New capability 1"
        assert validated["capabilities"][1]["text"] == "New capability 2"
        assert all("source" in cap for cap in validated["capabilities"])
    
    def test_validate_updates_capabilities_invalid_type(self, updater):
        """Test validating updates with invalid capabilities type."""
        updates = {
            "capabilities": "not a list",
        }
        validated = updater._validate_updates(updates)
        assert "capabilities" not in validated
    
    def test_validate_updates_capabilities_none(self, updater):
        """Test validating updates with None capabilities."""
        updates = {
            "capabilities": None,
        }
        validated = updater._validate_updates(updates)
        assert "capabilities" not in validated
    
    # Preferences removed from self-model - tests removed
    
    def test_validate_updates_knowledge_boundaries(self, updater):
        """Test validating updates with knowledge boundaries."""
        updates = {
            "knowledge_boundaries": {"new_boundary": "value"},
        }
        validated = updater._validate_updates(updates)
        assert "knowledge_boundaries" in validated
        assert isinstance(validated["knowledge_boundaries"], dict)
        assert "new_boundary" in validated["knowledge_boundaries"]
        assert validated["knowledge_boundaries"]["new_boundary"]["value"] == "value"
        assert "source" in validated["knowledge_boundaries"]["new_boundary"]
    
    def test_validate_updates_constraints(self, updater):
        """Test validating updates with constraints."""
        updates = {
            "constraints": {"new_constraint": "value"},
        }
        validated = updater._validate_updates(updates)
        assert "constraints" in validated
        assert isinstance(validated["constraints"], dict)
        assert "new_constraint" in validated["constraints"]
        assert validated["constraints"]["new_constraint"]["value"] == "value"
        assert "source" in validated["constraints"]["new_constraint"]
    
    # Behavioral patterns removed from self-model - tests removed
    
    def test_validate_updates_all_fields(self, updater):
        """Test validating updates with all fields."""
        updates = {
            "capabilities": ["New capability"],
            "knowledge_boundaries": {"new_boundary": "value"},
            "constraints": {"new_constraint": "value"},
        }
        validated = updater._validate_updates(updates)
        assert len(validated) == 3
        assert all(key in validated for key in updates.keys())
    
    def test_apply_updates_capabilities_strings(self, updater, base_model):
        """Test applying updates with string capabilities."""
        updates = {
            "capabilities": ["New capability 1", "New capability 2"],
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert len(updated.capabilities) == 4  # 2 existing + 2 new
        texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "Existing capability 1" in texts
        assert "Existing capability 2" in texts
        assert "New capability 1" in texts
        assert "New capability 2" in texts
    
    def test_apply_updates_capabilities_dicts(self, updater, base_model):
        """Test applying updates with dict capabilities (should normalize)."""
        updates = {
            "capabilities": [
                {"name": "New capability 1"},
                {"description": "New capability 2"},
            ],
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert len(updated.capabilities) == 4  # 2 existing + 2 new
        texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "New capability 1" in texts
        assert "New capability 2" in texts
    
    def test_apply_updates_capabilities_duplicates(self, updater, base_model):
        """Test applying updates with duplicate capabilities (should not add duplicates)."""
        updates = {
            "capabilities": ["Existing capability 1", "New capability"],
        }
        updated = updater.apply_updates(base_model, updates)
        
        # Should not add duplicate (check by text)
        existing_texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "Existing capability 1" in existing_texts
        assert "New capability" in existing_texts
        assert len(updated.capabilities) == 3  # 2 existing (1 duplicate) + 1 new
    
    def test_apply_updates_capabilities_mixed_types(self, updater, base_model):
        """Test applying updates with mixed type capabilities."""
        updates = {
            "capabilities": [
                "String capability",
                {"name": "Dict capability"},
                {"description": "Description capability"},
            ],
        }
        updated = updater.apply_updates(base_model, updates)
        
        texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "String capability" in texts
        assert "Dict capability" in texts
        assert "Description capability" in texts
    
    def test_apply_updates_capabilities_invalid_type(self, updater, base_model):
        """Test applying updates with invalid capabilities type (should skip)."""
        updates = {
            "capabilities": "not a list",
        }
        updated = updater.apply_updates(base_model, updates)
        
        # Should remain unchanged
        assert updated.capabilities == base_model.capabilities
    
    # Preferences removed from self-model - test removed
    
    def test_apply_updates_knowledge_boundaries(self, updater, base_model):
        """Test applying updates with knowledge boundaries."""
        updates = {
            "knowledge_boundaries": {"new_boundary": "new_value"},
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert "existing_boundary" in updated.knowledge_boundaries
        assert updated.knowledge_boundaries["existing_boundary"]["value"] == "value"
        assert "new_boundary" in updated.knowledge_boundaries
        assert updated.knowledge_boundaries["new_boundary"]["value"] == "new_value"
        assert "source" in updated.knowledge_boundaries["new_boundary"]
    
    def test_apply_updates_constraints(self, updater, base_model):
        """Test applying updates with constraints."""
        updates = {
            "constraints": {"new_constraint": "new_value"},
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert "existing_constraint" in updated.constraints
        assert updated.constraints["existing_constraint"]["value"] == "value"
        assert "new_constraint" in updated.constraints
        assert updated.constraints["new_constraint"]["value"] == "new_value"
        assert "source" in updated.constraints["new_constraint"]
    
    # Behavioral patterns removed from self-model - test removed
    
    def test_apply_updates_all_fields(self, updater, base_model):
        """Test applying updates with all fields."""
        updates = {
            "capabilities": ["New capability"],
            "knowledge_boundaries": {"new_boundary": "value"},
            "constraints": {"new_constraint": "value"},
        }
        updated = updater.apply_updates(base_model, updates)
        
        texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "New capability" in texts
        assert "new_boundary" in updated.knowledge_boundaries
        assert updated.knowledge_boundaries["new_boundary"]["value"] == "value"
        assert "new_constraint" in updated.constraints
        assert updated.constraints["new_constraint"]["value"] == "value"
    
    def test_apply_updates_empty_updates(self, updater, base_model):
        """Test applying empty updates (should return unchanged model)."""
        updates = {}
        updated = updater.apply_updates(base_model, updates)
        
        assert updated.capabilities == base_model.capabilities
        assert updated.knowledge_boundaries == base_model.knowledge_boundaries
        assert updated.constraints == base_model.constraints
    
    def test_apply_updates_invalid_all_fields(self, updater, base_model):
        """Test applying updates with all invalid types (should skip all)."""
        updates = {
            "capabilities": "not a list",
            "knowledge_boundaries": "not a dict",
            "constraints": "not a dict",
        }
        updated = updater.apply_updates(base_model, updates)
        
        # Should remain unchanged
        assert updated.capabilities == base_model.capabilities
        assert updated.knowledge_boundaries == base_model.knowledge_boundaries
        assert updated.constraints == base_model.constraints
    
    def test_apply_updates_partial_valid(self, updater, base_model):
        """Test applying updates with some valid and some invalid fields."""
        updates = {
            "capabilities": ["Valid capability"],
            "constraints": {"valid_constraint": "value"},
        }
        updated = updater.apply_updates(base_model, updates)
        
        # Valid fields should be applied
        texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "Valid capability" in texts
        assert "valid_constraint" in updated.constraints
        assert updated.constraints["valid_constraint"]["value"] == "value"
    
    def test_apply_updates_preserves_metadata(self, updater, base_model):
        """Test that applying updates preserves existing metadata."""
        updates = {
            "capabilities": ["New capability"],
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert updated.metadata["version"] == base_model.metadata["version"]
        texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "New capability" in texts
    
    def test_apply_updates_preserves_epistemic_layer(self, updater):
        """Test that applying updates preserves epistemic layer."""
        epistemic_layer = EpistemicLayer()
        base_model = SelfModel(
            capabilities=["Existing capability"],
            epistemic_layer=epistemic_layer,
        )
        updates = {
            "capabilities": ["New capability"],
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert updated.epistemic_layer is epistemic_layer
        texts = {cap.get("text", str(cap)) for cap in updated.capabilities}
        assert "New capability" in texts
    
    # Tests for _normalize_to_dict method
    def test_normalize_to_dict_already_dict(self, updater):
        """Test normalizing a value that is already a dict."""
        value = {"key1": "value1", "key2": "value2"}
        normalized = updater._normalize_to_dict(value)
        assert normalized == value
    
    def test_normalize_to_dict_list_of_key_value_dicts(self, updater):
        """Test normalizing list of key-value pair dicts."""
        value = [
            {"key": "pref1", "value": "val1"},
            {"key": "pref2", "value": "val2"},
        ]
        normalized = updater._normalize_to_dict(value)
        assert normalized == {"pref1": "val1", "pref2": "val2"}
    
    def test_normalize_to_dict_list_of_name_value_dicts(self, updater):
        """Test normalizing list of name-value dicts."""
        value = [
            {"name": "constraint1", "value": "value1"},
            {"name": "constraint2", "value": "value2"},
        ]
        normalized = updater._normalize_to_dict(value)
        assert normalized == {"constraint1": "value1", "constraint2": "value2"}
    
    def test_normalize_to_dict_list_of_tuples(self, updater):
        """Test normalizing list of tuples."""
        value = [
            ("key1", "value1"),
            ("key2", "value2"),
        ]
        normalized = updater._normalize_to_dict(value)
        assert normalized == {"key1": "value1", "key2": "value2"}
    
    def test_normalize_to_dict_list_of_lists(self, updater):
        """Test normalizing list of two-item lists."""
        value = [
            ["key1", "value1"],
            ["key2", "value2"],
        ]
        normalized = updater._normalize_to_dict(value)
        assert normalized == {"key1": "value1", "key2": "value2"}
    
    def test_normalize_to_dict_list_of_strings_with_colon(self, updater):
        """Test normalizing list of strings with 'key: value' format."""
        value = [
            "key1: value1",
            "key2: value2",
        ]
        normalized = updater._normalize_to_dict(value)
        assert normalized == {"key1": "value1", "key2": "value2"}
    
    def test_normalize_to_dict_list_of_single_item_dicts(self, updater):
        """Test normalizing list of single-item dicts."""
        value = [
            {"key1": "value1"},
            {"key2": "value2"},
        ]
        normalized = updater._normalize_to_dict(value)
        assert normalized == {"key1": "value1", "key2": "value2"}
    
    def test_normalize_to_dict_empty_list(self, updater):
        """Test normalizing empty list."""
        normalized = updater._normalize_to_dict([])
        assert normalized == {}
    
    def test_normalize_to_dict_invalid_type(self, updater):
        """Test normalizing invalid type (not dict or list)."""
        normalized = updater._normalize_to_dict("not a dict or list")
        assert normalized == {}
    
    def test_normalize_to_dict_mixed_formats(self, updater):
        """Test normalizing list with mixed formats."""
        value = [
            {"key": "k1", "value": "v1"},
            ("k2", "v2"),
            {"k3": "v3"},
            "k4: v4",
        ]
        normalized = updater._normalize_to_dict(value)
        assert normalized == {"k1": "v1", "k2": "v2", "k3": "v3", "k4": "v4"}
    
    # Preferences removed from self-model - test removed
    
    def test_validate_updates_constraints_as_list(self, updater):
        """Test validating updates with constraints as list."""
        updates = {
            "constraints": [
                {"name": "constraint1", "value": "value1"},
                ("constraint2", "value2"),
            ],
        }
        validated = updater._validate_updates(updates)
        assert "constraints" in validated
        assert isinstance(validated["constraints"], dict)
        assert "constraint1" in validated["constraints"]
        assert validated["constraints"]["constraint1"]["value"] == "value1"
        assert "constraint2" in validated["constraints"]
        assert validated["constraints"]["constraint2"]["value"] == "value2"
        assert all("source" in v for v in validated["constraints"].values())
    
    def test_validate_updates_knowledge_boundaries_as_list(self, updater):
        """Test validating updates with knowledge_boundaries as list."""
        updates = {
            "knowledge_boundaries": [
                {"boundary1": "value1"},
                {"boundary2": "value2"},
            ],
        }
        validated = updater._validate_updates(updates)
        assert "knowledge_boundaries" in validated
        assert isinstance(validated["knowledge_boundaries"], dict)
        assert "boundary1" in validated["knowledge_boundaries"]
        assert validated["knowledge_boundaries"]["boundary1"]["value"] == "value1"
        assert "boundary2" in validated["knowledge_boundaries"]
        assert validated["knowledge_boundaries"]["boundary2"]["value"] == "value2"
        assert all("source" in v for v in validated["knowledge_boundaries"].values())
    
    # Preferences removed from self-model - test removed
    
    def test_apply_updates_constraints_as_list(self, updater, base_model):
        """Test applying updates with constraints as list."""
        updates = {
            "constraints": [
                {"name": "new_constraint", "value": "new_value"},
            ],
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert "existing_constraint" in updated.constraints
        assert updated.constraints["existing_constraint"]["value"] == "value"
        assert "new_constraint" in updated.constraints
        assert updated.constraints["new_constraint"]["value"] == "new_value"
        assert "source" in updated.constraints["new_constraint"]
    
    def test_apply_updates_knowledge_boundaries_as_list(self, updater, base_model):
        """Test applying updates with knowledge_boundaries as list."""
        updates = {
            "knowledge_boundaries": [
                {"new_boundary": "new_value"},
            ],
        }
        updated = updater.apply_updates(base_model, updates)
        
        assert "existing_boundary" in updated.knowledge_boundaries
        assert updated.knowledge_boundaries["existing_boundary"]["value"] == "value"
        assert "new_boundary" in updated.knowledge_boundaries
        assert updated.knowledge_boundaries["new_boundary"]["value"] == "new_value"
        assert "source" in updated.knowledge_boundaries["new_boundary"]

