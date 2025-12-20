"""
Integration tests for epistemic system.

Tests integration with memory, tools, and self-model systems.
"""

from __future__ import annotations

import pytest
import tempfile
import os
from datetime import datetime, timezone

from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata
from broca.self_model.model import SelfModel
from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.epistemic.ids import generate_capability_id


class TestEpistemicMemoryIntegration:
    """Test epistemic integration with memory system."""
    
    def test_memory_manager_retrieve_with_metadata(self):
        """Test MemoryManager.retrieve_with_metadata returns epistemic context."""
        # This is a basic integration test - full test would require MemoryManager setup
        # For now, we test that the method exists and returns expected structure
        from broca.memory.manager import MemoryManager
        
        # Check that method exists
        assert hasattr(MemoryManager, 'retrieve_with_metadata')
        assert hasattr(MemoryManager, 'store_memory_with_epistemic')


class TestEpistemicToolIntegration:
    """Test epistemic integration with tool system."""
    
    def test_tool_registry_epistemic_tracking(self):
        """Test ToolRegistry tracks epistemic metadata."""
        from broca.tools.registry import ToolRegistry
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        
        # Create epistemic engine
        epistemic_engine = MetacognitiveEngine()
        
        # Create registry with epistemic engine
        registry = ToolRegistry(epistemic_engine=epistemic_engine)
        
        # Check that epistemic_engine is set
        assert registry.epistemic_engine is not None
    
    def test_end_to_end_tool_execution_epistemic_tracking(self):
        """
        Test end-to-end tool execution → epistemic tracking flow.
        
        Rationale: Ensures tool executions properly trigger epistemic tracking workflow.
        """
        from broca.tools.registry import ToolRegistry
        from broca.tools import Tool
        
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        class TestTool(Tool):
            @property
            def name(self) -> str:
                return "test_tool"
            
            @property
            def description(self) -> str:
                return "A test tool"
            
            @property
            def parameters(self):
                return {"type": "object", "properties": {}, "required": []}
            
            def execute(self, **kwargs):
                return {"success": True, "data": "test_result"}
            
            def format_result(self, result):
                return str(result)
        
        tool = TestTool()
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_e2e",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": "{}"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Verify epistemic tracking occurred
        assert "_epistemic_impact" in result
        assert "confidence_metrics" in result["_epistemic_impact"]
        
        # Verify tool execution was recorded
        assert len(engine.validator._tool_executions.get("test_tool", [])) > 0
        assert engine.validator._tool_executions["test_tool"][-1] is True
    
    def test_epistemic_context_retrieval_after_tool_usage(self):
        """
        Test epistemic context retrieval after tool usage.
        
        Rationale: Ensures we can retrieve epistemic context for knowledge created from tool executions.
        """
        from broca.tools.registry import ToolRegistry
        from broca.tools import Tool
        
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        class ContextTool(Tool):
            @property
            def name(self) -> str:
                return "context_tool"
            
            @property
            def description(self) -> str:
                return "Tool for context testing"
            
            @property
            def parameters(self):
                return {"type": "object", "properties": {}, "required": []}
            
            def execute(self, **kwargs):
                return {"success": True, "context": "test"}
            
            def format_result(self, result):
                return str(result)
        
        tool = ContextTool()
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_context",
            "type": "function",
            "function": {
                "name": "context_tool",
                "arguments": "{}"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Verify epistemic impact contains confidence metrics
        assert "_epistemic_impact" in result
        impact = result["_epistemic_impact"]
        assert "confidence_metrics" in impact
        metrics = impact["confidence_metrics"]
        assert "tool_reliability_score" in metrics
        assert "execution_success" in metrics
        assert "evidence_strength" in metrics
    
    def test_confidence_calibration_across_different_tool_types(self):
        """
        Test confidence calibration works across different tool types.
        
        Rationale: Ensures different tools get appropriate confidence scores based on their reliability.
        """
        from broca.tools.registry import ToolRegistry
        from broca.tools import Tool
        
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        class ReliableTool(Tool):
            @property
            def name(self) -> str:
                return "reliable_tool"
            
            @property
            def description(self) -> str:
                return "A reliable tool"
            
            @property
            def parameters(self):
                return {"type": "object", "properties": {}, "required": []}
            
            def execute(self, **kwargs):
                return {"success": True}
            
            def format_result(self, result):
                return str(result)
        
        class UnreliableTool(Tool):
            @property
            def name(self) -> str:
                return "unreliable_tool"
            
            @property
            def description(self) -> str:
                return "An unreliable tool"
            
            @property
            def parameters(self):
                return {"type": "object", "properties": {}, "required": []}
            
            def execute(self, **kwargs):
                return {"success": False, "error": "failed"}
            
            def format_result(self, result):
                return str(result)
        
        reliable = ReliableTool()
        unreliable = UnreliableTool()
        
        registry.register_tool(reliable)
        registry.register_tool(unreliable)
        
        # Execute reliable tool multiple times
        for i in range(5):
            call = {
                "id": f"reliable_{i}",
                "type": "function",
                "function": {"name": "reliable_tool", "arguments": "{}"}
            }
            registry.execute_tool_call(call)
        
        # Execute unreliable tool
        call_unreliable = {
            "id": "unreliable_1",
            "type": "function",
            "function": {"name": "unreliable_tool", "arguments": "{}"}
        }
        registry.execute_tool_call(call_unreliable)
        
        # Check reliability scores differ
        reliable_score = engine.validator.assess_tool_reliability("reliable_tool")
        unreliable_score = engine.validator.assess_tool_reliability("unreliable_tool")
        
        assert reliable_score > unreliable_score
        assert reliable_score > 0.5  # Should be above neutral
        assert unreliable_score < 0.5  # Should be below neutral


class TestEpistemicSelfModelIntegration:
    """Test epistemic integration with self-model."""
    
    def test_query_self_model_with_epistemic(self):
        """Test QuerySelfModelTool returns epistemic context."""
        from broca.self_model.model import SelfModel
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.tools.self_model_tool import QuerySelfModelTool
        
        # Create self-model with epistemic layer
        epistemic = EpistemicLayer()
        self_model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic
        )
        
        # Add some epistemic metadata
        knowledge_id = generate_capability_id("Python programming")
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        epistemic.add_knowledge_source(knowledge_id, source)
        
        # Create tool directly with self_model and storage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SelfModelSQLiteStorage(db_path=os.path.join(tmpdir, "test.db"))
            storage.save(self_model)
            
            tool = QuerySelfModelTool(self_model, storage)
            
            # Query with epistemic aspect
            result = tool.execute(aspect="epistemic")
            
            assert result["success"] is True
            assert "epistemic_layer" in result
            assert result["epistemic_layer"] is not None


class TestEpistemicConsistencyIntegration:
    """Test epistemic integration (consistency layer removed)."""
    
    @pytest.mark.skip(reason="Consistency checking has been removed")
    def test_consistency_layer_records_violations(self):
        """Test ConsistencyLayer records violations as epistemic events."""
        # This test is skipped because consistency checking has been removed
        pass


class TestMetacognitiveEngineCreationAndSharing:
    """Test MetacognitiveEngine creation and sharing across components."""
    
    def test_metacognitive_engine_can_be_created(self):
        """
        Test that MetacognitiveEngine can be created.
        
        Rationale: Ensures the engine can be instantiated for use across components.
        """
        engine = MetacognitiveEngine()
        
        assert engine is not None
        assert engine.epistemic_layer is not None
        assert isinstance(engine.epistemic_layer, EpistemicLayer)
    
    def test_metacognitive_engine_can_share_epistemic_layer(self):
        """
        Test that MetacognitiveEngine can share an epistemic layer with SelfModel.
        
        Rationale: Ensures the engine can work with an existing epistemic layer from self-model.
        """
        # Create epistemic layer
        epistemic_layer = EpistemicLayer()
        
        # Create self-model with the layer
        self_model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic_layer
        )
        
        # Create engine with the same layer
        engine = MetacognitiveEngine(epistemic_layer=epistemic_layer)
        
        # Both should reference the same layer
        assert engine.epistemic_layer is epistemic_layer
        assert self_model.epistemic_layer is epistemic_layer
    
    def test_tool_registry_accepts_optional_epistemic_engine(self):
        """
        Test that ToolRegistry accepts optional epistemic_engine parameter.
        
        Rationale: Ensures backward compatibility - registry works with or without engine.
        """
        from broca.tools.registry import ToolRegistry
        
        # Test without epistemic engine (backward compatibility)
        registry1 = ToolRegistry()
        assert registry1.epistemic_engine is None
        
        # Test with epistemic engine
        engine = MetacognitiveEngine()
        registry2 = ToolRegistry(epistemic_engine=engine)
        assert registry2.epistemic_engine is engine
    
    def test_components_work_without_metacognitive_engine(self):
        """
        Test that components work without MetacognitiveEngine (backward compatibility).
        
        Rationale: Ensures existing code that doesn't use epistemic engine continues to work.
        """
        from broca.tools.registry import ToolRegistry
        
        # Create registry without engine
        registry = ToolRegistry()
        
        # Should work fine
        assert registry.epistemic_engine is None
        assert registry.list_tools() == []
        
        # Should be able to register tools
        from broca.tools import Tool
        
        class MockTool(Tool):
            @property
            def name(self) -> str:
                return "mock_tool"
            
            @property
            def description(self) -> str:
                return "A mock tool"
            
            @property
            def parameters(self):
                return {"type": "object", "properties": {}}
            
            def execute(self, **kwargs):
                return {"success": True}
            
            def format_result(self, result):
                return str(result)
        
        tool = MockTool()
        registry.register_tool(tool)
        assert len(registry.list_tools()) == 1
    
    def test_metacognitive_engine_can_be_shared_across_components(self):
        """
        Test that a single MetacognitiveEngine can be shared across multiple components.
        
        Rationale: Ensures we can create one engine and pass it to multiple components.
        """
        from broca.tools.registry import ToolRegistry
        
        # Create shared engine
        engine = MetacognitiveEngine()
        
        # Share with multiple registries (simulating multiple components)
        registry1 = ToolRegistry(epistemic_engine=engine)
        registry2 = ToolRegistry(epistemic_engine=engine)
        
        # Both should reference the same engine
        assert registry1.epistemic_engine is engine
        assert registry2.epistemic_engine is engine
        assert registry1.epistemic_engine is registry2.epistemic_engine

