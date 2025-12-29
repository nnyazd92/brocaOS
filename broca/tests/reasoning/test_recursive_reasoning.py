"""
Unit tests for recursive reasoning engine.
"""

import pytest
from unittest.mock import Mock, MagicMock
from broca.reasoning.recursive_reasoning import RecursiveReasoningEngine, RecursiveReasoningTask


@pytest.fixture
def mock_rule_engine():
    """Create a mock rule engine."""
    engine = Mock()
    engine.execute_rule = Mock(return_value={"success": True})
    return engine


@pytest.fixture
def mock_working_memory():
    """Create a mock working memory."""
    memory = Mock()
    memory.add = Mock()
    memory.retrieve = Mock(return_value=[])
    return memory


@pytest.fixture
def recursive_reasoning_engine(mock_rule_engine, mock_working_memory):
    """Create a recursive reasoning engine instance."""
    return RecursiveReasoningEngine(
        max_depth=3,
        timeout_seconds=30.0,
        working_memory=mock_working_memory,
        rule_engine=mock_rule_engine
    )


class TestRecursiveReasoningEngine:
    """Unit tests for RecursiveReasoningEngine."""
    
    def test_init(self, recursive_reasoning_engine):
        """Test engine initialization."""
        assert recursive_reasoning_engine is not None
        assert recursive_reasoning_engine.max_depth == 3
        assert recursive_reasoning_engine.timeout_seconds == 30.0
    
    def test_reason_about_task(self, recursive_reasoning_engine):
        """Test reasoning about a task."""
        import uuid
        task = RecursiveReasoningTask(
            task_id=str(uuid.uuid4()),
            question="What should I do?",
            depth=0,
            max_depth=recursive_reasoning_engine.max_depth
        )
        
        result = recursive_reasoning_engine.reason_about(task)
        assert result is not None
        assert hasattr(result, 'state') or isinstance(result, dict)
    
    def test_respects_max_depth(self, recursive_reasoning_engine):
        """Test that max depth is respected."""
        import uuid
        task = RecursiveReasoningTask(
            task_id=str(uuid.uuid4()),
            question="Deep question",
            depth=recursive_reasoning_engine.max_depth,
            max_depth=recursive_reasoning_engine.max_depth
        )
        
        result = recursive_reasoning_engine.reason_about(task)
        # Should not exceed max depth
        if hasattr(result, 'depth'):
            assert result.depth <= recursive_reasoning_engine.max_depth
    
    def test_get_statistics(self, recursive_reasoning_engine):
        """Test statistics retrieval."""
        import uuid
        # Execute some reasoning tasks
        task1 = RecursiveReasoningTask(str(uuid.uuid4()), "Question 1", 0, recursive_reasoning_engine.max_depth)
        task2 = RecursiveReasoningTask(str(uuid.uuid4()), "Question 2", 0, recursive_reasoning_engine.max_depth)
        recursive_reasoning_engine.reason_about(task1)
        recursive_reasoning_engine.reason_about(task2)
        
        stats = recursive_reasoning_engine.get_statistics()
        assert stats["status"] != "no_data"
        assert "total_tasks" in stats
        assert stats["total_tasks"] >= 2
    
    def test_timeout_handling(self):
        """Test timeout handling."""
        import uuid
        engine = RecursiveReasoningEngine(
            max_depth=10,
            timeout_seconds=0.001,  # Very short timeout
            working_memory=None,
            rule_engine=None
        )
        
        task = RecursiveReasoningTask(str(uuid.uuid4()), "Slow question", 0, engine.max_depth)
        result = engine.reason_about(task)
        # Should handle timeout gracefully
        assert result is not None

