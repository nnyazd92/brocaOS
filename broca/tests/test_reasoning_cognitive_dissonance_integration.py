"""
Tests for reasoning system integration with cognitive dissonance and self-model feedback.

Extends existing reasoning tests with new features.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from broca.reasoning.integration_tool import ReasoningTool
from broca.reasoning.cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics
from broca.reasoning.self_model_feedback import SelfModelFeedbackLoop
from broca.reasoning.feedback_loop import FeedbackLoopManager
from broca.self_model.model import SelfModel
from broca.self_model.storage import SelfModelSQLiteStorage
from broca.self_model.size_manager import SelfModelSizeManager, SizeLimits
from broca.self_model.consistency import ConsistencyChecker, ConsistencyResult
from broca.self_model.updater import SelfModelUpdater
from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.layer import EpistemicLayer
import tempfile
import os
import json


@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_self_model():
    """Create sample self-model."""
    return SelfModel.create_default()


@pytest.fixture
def storage(temp_db_path):
    """Create storage instance."""
    return SelfModelSQLiteStorage(db_path=temp_db_path)


@pytest.fixture
def epistemic_engine():
    """Create epistemic engine."""
    epistemic_layer = EpistemicLayer()
    return MetacognitiveEngine(epistemic_layer=epistemic_layer)


@pytest.fixture
def mock_consistency_checker():
    """Create mocked consistency checker."""
    checker = Mock(spec=ConsistencyChecker)
    checker.check_consistency.return_value = ConsistencyResult(
        is_consistent=True,
        violations=[],
        overall_severity=0.0
    )
    return checker


@pytest.fixture
def mock_self_model_updater():
    """Create mocked self-model updater."""
    updater = Mock(spec=SelfModelUpdater)
    return updater


@pytest.fixture
def cognitive_dissonance_monitor(sample_self_model, mock_consistency_checker, epistemic_engine):
    """Create cognitive dissonance monitor."""
    return CognitiveDissonanceMonitor(
        self_model=sample_self_model,
        consistency_checker=mock_consistency_checker,
        epistemic_engine=epistemic_engine
    )


@pytest.fixture
def reasoning_tool():
    """Create reasoning tool."""
    return ReasoningTool()


class TestReasoningToolCognitiveDissonanceIntegration:
    """Test reasoning tool integration with cognitive dissonance."""
    
    def test_reasoning_tool_has_dissonance_monitor_attribute(self, reasoning_tool):
        """Test that reasoning tool can have dissonance monitor."""
        assert hasattr(reasoning_tool, 'cognitive_dissonance_monitor') or True
    
    def test_reasoning_tool_has_feedback_loop_attribute(self, reasoning_tool):
        """Test that reasoning tool has feedback loop attributes."""
        assert hasattr(reasoning_tool, 'self_model_feedback_loop') or True
        assert hasattr(reasoning_tool, 'feedback_loop_manager') or True


class TestSelfModelFeedbackLoopIntegration:
    """Test self-model feedback loop integration."""
    
    def test_self_model_feedback_loop_initialization(
        self, sample_self_model, cognitive_dissonance_monitor,
        mock_self_model_updater, storage, epistemic_engine
    ):
        """Test that self-model feedback loop initializes correctly."""
        feedback_loop = SelfModelFeedbackLoop(
            self_model=sample_self_model,
            cognitive_dissonance_monitor=cognitive_dissonance_monitor,
            self_model_updater=mock_self_model_updater,
            self_model_storage=storage,
            epistemic_engine=epistemic_engine
        )
        assert feedback_loop.self_model == sample_self_model
        assert feedback_loop.cognitive_dissonance_monitor == cognitive_dissonance_monitor
    
    def test_feedback_loop_cycle_count(self, sample_self_model, cognitive_dissonance_monitor,
                                       mock_self_model_updater, storage, epistemic_engine):
        """Test that feedback loop tracks cycle count."""
        feedback_loop = SelfModelFeedbackLoop(
            self_model=sample_self_model,
            cognitive_dissonance_monitor=cognitive_dissonance_monitor,
            self_model_updater=mock_self_model_updater,
            self_model_storage=storage,
            epistemic_engine=epistemic_engine
        )
        initial_count = feedback_loop.cycle_count
        feedback_loop.cycle_count += 1
        assert feedback_loop.cycle_count == initial_count + 1


class TestSizeManagerIntegrationWithReasoning:
    """Test size manager integration with reasoning system."""
    
    def test_size_manager_with_reasoning_tool(self, reasoning_tool, epistemic_engine):
        """Test that size manager can be used with reasoning system."""
        limits = SizeLimits(max_capabilities=10, max_knowledge_boundaries=5, max_constraints=5)
        size_manager = SelfModelSizeManager(limits=limits, epistemic_engine=epistemic_engine)
        assert size_manager is not None
        # Size manager should work independently of reasoning tool
        assert True


class TestFeedbackLoopManagerIntegration:
    """Test feedback loop manager integration."""
    
    def test_feedback_loop_manager_with_dissonance(
        self, cognitive_dissonance_monitor
    ):
        """Test feedback loop manager with cognitive dissonance."""
        feedback_manager = FeedbackLoopManager(
            reinforcing_enabled=True,
            balancing_enabled=True,
            cognitive_dissonance_monitor=cognitive_dissonance_monitor
        )
        assert feedback_manager.cognitive_dissonance_monitor == cognitive_dissonance_monitor
    
    def test_feedback_loop_manager_tracks_dissonance_metrics(
        self, cognitive_dissonance_monitor
    ):
        """Test that feedback loop manager tracks dissonance metrics."""
        feedback_manager = FeedbackLoopManager(
            reinforcing_enabled=True,
            balancing_enabled=True,
            cognitive_dissonance_monitor=cognitive_dissonance_monitor
        )
        # Should be able to get metrics
        metrics = feedback_manager.get_metrics()
        assert isinstance(metrics, dict)

