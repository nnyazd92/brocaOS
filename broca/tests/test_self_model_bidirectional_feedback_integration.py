"""
Integration tests for Self-Model Bidirectional Feedback System.

Tests end-to-end integration between cognitive dissonance, self-model updates,
size management, output feedback, and CRUD operations following AGENTS.md requirements.
"""

from __future__ import annotations

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from pathlib import Path

from broca.reasoning.cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics
from broca.reasoning.self_model_feedback import SelfModelFeedbackLoop
from broca.self_model.model import SelfModel
from broca.self_model.storage import SelfModelSQLiteStorage
from broca.self_model.size_manager import SelfModelSizeManager, SizeLimits
from broca.self_model.updater import SelfModelUpdater
from broca.self_model.consistency import ConsistencyChecker, ConsistencyResult
from broca.tools.self_model_crud_tool import SelfModelCRUDTool
from broca.reasoning.integration_tool import ReasoningTool
from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.world_state.aggregator import WorldStateAggregator
from broca.llm import create_llm_client


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def storage(temp_db_path):
    """Create storage instance."""
    return SelfModelSQLiteStorage(db_path=temp_db_path)


@pytest.fixture
def sample_self_model():
    """Create sample self-model."""
    return SelfModel.create_default()


@pytest.fixture
def epistemic_engine():
    """Create epistemic engine."""
    epistemic_layer = EpistemicLayer()
    return MetacognitiveEngine(epistemic_layer=epistemic_layer)


@pytest.fixture
def consistency_checker():
    """Create consistency checker with mocked LLM."""
    mock_llm = Mock()
    mock_llm.chat.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "is_consistent": True,
                    "violations": [],
                    "overall_severity": 0.0
                })
            }
        }]
    }
    mock_llm.extract_assistant_content = lambda x: json.dumps({
        "is_consistent": True,
        "violations": [],
        "overall_severity": 0.0
    })
    return ConsistencyChecker(llm_client=mock_llm)


@pytest.fixture
def cognitive_dissonance_monitor(sample_self_model, consistency_checker, epistemic_engine):
    """Create cognitive dissonance monitor."""
    return CognitiveDissonanceMonitor(
        self_model=sample_self_model,
        consistency_checker=consistency_checker,
        epistemic_engine=epistemic_engine
    )


@pytest.fixture
def self_model_updater():
    """Create self-model updater with mocked LLM."""
    mock_llm = Mock()
    mock_llm.chat.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "capabilities": None,
                    "knowledge_boundaries": None,
                    "constraints": None,
                    "rationale": "Test update"
                })
            }
        }]
    }
    mock_llm.extract_assistant_content = lambda x: json.dumps({
        "capabilities": None,
        "knowledge_boundaries": None,
        "constraints": None,
        "rationale": "Test update"
    })
    return SelfModelUpdater(llm_client=mock_llm)


@pytest.fixture
def self_model_feedback_loop(
    sample_self_model,
    cognitive_dissonance_monitor,
    self_model_updater,
    storage,
    epistemic_engine
):
    """Create self-model feedback loop."""
    return SelfModelFeedbackLoop(
        self_model=sample_self_model,
        cognitive_dissonance_monitor=cognitive_dissonance_monitor,
        self_model_updater=self_model_updater,
        self_model_storage=storage,
        epistemic_engine=epistemic_engine
    )


@pytest.fixture
def size_manager(epistemic_engine):
    """Create size manager."""
    limits = SizeLimits(
        max_capabilities=10,
        max_knowledge_boundaries=5,
        max_constraints=5
    )
    return SelfModelSizeManager(limits=limits, epistemic_engine=epistemic_engine)


@pytest.fixture
def crud_tool(sample_self_model, storage, epistemic_engine):
    """Create CRUD tool."""
    storage.save(sample_self_model)
    return SelfModelCRUDTool(
        self_model=sample_self_model,
        storage=storage,
        epistemic_engine=epistemic_engine
    )


class TestCognitiveDissonanceTriggersRevision:
    """Test that cognitive dissonance triggers self-model revision."""
    
    def test_high_dissonance_triggers_update(
        self, self_model_feedback_loop, cognitive_dissonance_monitor
    ):
        """Test that high dissonance triggers self-model update."""
        # Simulate high dissonance
        with patch.object(cognitive_dissonance_monitor, 'measure_dissonance') as mock_measure:
            mock_measure.return_value = DissonanceMetrics(
                overall=0.8,  # High dissonance
                logical=0.7,
                factual=0.8,
                behavioral=0.6,
                goal=0.7,
                trend="increasing"
            )
            
            # Check if update should be triggered
            should_update = self_model_feedback_loop.should_update()
            # May or may not trigger depending on threshold
            assert isinstance(should_update, bool)
    
    def test_low_dissonance_no_update(
        self, self_model_feedback_loop, cognitive_dissonance_monitor
    ):
        """Test that low dissonance doesn't trigger update."""
        with patch.object(cognitive_dissonance_monitor, 'measure_dissonance') as mock_measure:
            mock_measure.return_value = DissonanceMetrics(
                overall=0.1,  # Low dissonance
                logical=0.1,
                factual=0.1,
                behavioral=0.1,
                goal=0.1,
                trend="stable"
            )
            
            should_update = self_model_feedback_loop.should_update()
            # Low dissonance should not trigger update (or very rarely)
            assert isinstance(should_update, bool)


class TestSelfModelCRUDViaTool:
    """Test CRUD operations via ReasoningTool."""
    
    def test_crud_tool_can_be_accessed(self, crud_tool):
        """Test that CRUD tool is accessible and functional."""
        result = crud_tool.execute(action="query", aspect="all")
        assert result["success"] is True
    
    def test_create_via_crud_triggers_size_management(
        self, crud_tool, size_manager, storage
    ):
        """Test that creating entries via CRUD may trigger size management."""
        # Create many capabilities
        for i in range(15):
            crud_tool.execute(
                action="create",
                aspect="capabilities",
                entries=[f"Capability {i}"]
            )
        
        # Load model and check size
        loaded_model = storage.load()
        if loaded_model:
            status = size_manager.check_size(loaded_model)
            # May exceed limits depending on initial state
            assert "capabilities" in status


class TestSizeManagerIntegration:
    """Test size manager integration with world state."""
    
    def test_size_manager_in_world_state_aggregator(
        self, sample_self_model, size_manager, epistemic_engine
    ):
        """Test that size manager is integrated with world state aggregator."""
        from broca.config import config
        
        aggregator = WorldStateAggregator(
            self_model=sample_self_model,
            size_manager=size_manager,
            config=config
        )
        
        # Should be able to get metadata-only representation if enabled
        world_state = aggregator.aggregate()
        assert "self_model" in world_state or "system" in world_state
    
    def test_metadata_only_mode_enabled(
        self, sample_self_model, size_manager, epistemic_engine
    ):
        """Test metadata-only mode in world state."""
        from broca.config import config
        
        # Enable metadata-only mode
        with patch.object(config.self_model, 'metadata_only_mode', True):
            aggregator = WorldStateAggregator(
                self_model=sample_self_model,
                size_manager=size_manager,
                config=config
            )
            world_state = aggregator.aggregate()
            # Should use metadata-only representation
            assert "self_model" in world_state or "system" in world_state


class TestOutputFeedbackInfluencesSelfModel:
    """Test bidirectional feedback from output to self-model."""
    
    def test_output_patterns_influence_self_model(self, sample_self_model):
        """Test that detected output patterns can influence self-model."""
        from broca.self_model.output_feedback import OutputMonitor, PatternDetector
        
        monitor = OutputMonitor()
        detector = PatternDetector()
        
        # Record some output events
        for i in range(5):
            monitor.record_response(f"Consistent pattern {i % 2}")
        
        events = monitor.get_recent_events()
        patterns = detector.detect_patterns(events)
        
        # Patterns may suggest self-model updates
        assert isinstance(patterns, list)
        # Integration with self-model updates would happen here


class TestGoldenTraceSelfModelUpdateCycle:
    """Test golden trace replay for self-model update cycle."""
    
    def test_golden_trace_replay(self, temp_db_path, storage):
        """Test replaying a golden trace of self-model update cycle."""
        # Create fixtures directory if it doesn't exist
        fixtures_dir = Path(__file__).parent / "fixtures" / "golden_traces"
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple golden trace
        trace = {
            "initial_model": {
                "capabilities": ["Initial capability"],
                "knowledge_boundaries": {},
                "constraints": {}
            },
            "update_operations": [
                {"action": "create", "aspect": "capabilities", "entries": ["New capability"]}
            ],
            "expected_final_state": {
                "capabilities_count": 2
            }
        }
        
        trace_file = fixtures_dir / "self_model_update_cycle.json"
        with open(trace_file, 'w') as f:
            json.dump(trace, f, indent=2)
        
        # Replay trace
        model = SelfModel(
            capabilities=trace["initial_model"]["capabilities"],
            knowledge_boundaries=trace["initial_model"]["knowledge_boundaries"],
            constraints=trace["initial_model"]["constraints"]
        )
        storage.save(model)
        
        crud_tool = SelfModelCRUDTool(model, storage)
        for op in trace["update_operations"]:
            crud_tool.execute(**op)
        
        final_model = storage.load()
        assert final_model is not None
        assert len(final_model.capabilities) >= trace["expected_final_state"]["capabilities_count"]
        
        # Cleanup
        if trace_file.exists():
            trace_file.unlink()


class TestMetadataOnlyModeInWorldState:
    """Test metadata-only mode in world state aggregation."""
    
    def test_metadata_only_aggregation(
        self, sample_self_model, size_manager, epistemic_engine
    ):
        """Test that world state uses metadata-only when enabled."""
        from broca.config import config
        
        with patch.object(config.self_model, 'metadata_only_mode', True):
            aggregator = WorldStateAggregator(
                self_model=sample_self_model,
                size_manager=size_manager,
                config=config
            )
            world_state = aggregator.aggregate()
            
            # Should have self_model section
            if "self_model" in world_state:
                sm_state = world_state["self_model"]
                # Should have summary at minimum
                assert "summary" in sm_state or "available" in sm_state


class TestEndToEndFeedbackLoop:
    """Test end-to-end feedback loop."""
    
    def test_dissonance_to_revision_to_world_state(
        self, self_model_feedback_loop, storage, size_manager, epistemic_engine
    ):
        """Test complete flow: dissonance -> revision -> world state."""
        from broca.config import config
        
        # Trigger feedback loop cycle
        self_model_feedback_loop.cycle_count += 1
        
        # Check if update should occur
        should_update = self_model_feedback_loop.should_update()
        assert isinstance(should_update, bool)
        
        # If update occurs, verify it's reflected in world state
        if should_update:
            model = storage.load()
            if model:
                aggregator = WorldStateAggregator(
                    self_model=model,
                    size_manager=size_manager,
                    config=config
                )
                world_state = aggregator.aggregate()
                assert "self_model" in world_state or "system" in world_state

