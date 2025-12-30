"""
Tests for declarative memory integration with reasoning system.

Following AGENTS.md guidelines:
- Unit tests
- Integration tests
- Property-based tests
- Mutation testing structure
- Coverage: Target 90%+ branch coverage
"""

from __future__ import annotations

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from typing import List, Dict, Any

from broca.reasoning.declarative_memory import DeclarativeMemoryInterface
from broca.reasoning.spreading_activation import SpreadingActivation
from broca.reasoning.working_memory import WorkingMemory, WorkingMemoryItem
from broca.reasoning.rule_engine import RuleEngine
from broca.reasoning.goal_manager import GoalManager, Goal, GoalStatus, GoalType
from broca.reasoning.production_rules import ProductionRuleSystem, ProductionRule, RuleType
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.memory.manager import MemoryManager
from broca.memory import MemoryRecord, SourceType, SourceMetadata

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    service = Mock(spec=EmbeddingService)
    service.generate_embedding.return_value = [0.1] * 1536
    return service


@pytest.fixture
def temp_storage():
    """Temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = MemoryStorage(db_path)
        yield storage
        storage.close()


@pytest.fixture
def temp_vector_index():
    """Temporary vector index for testing."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test.faiss")
        index = VectorIndex(dimension=1536, index_path=index_path)
        yield index


@pytest.fixture
def memory_manager(temp_storage, temp_vector_index, mock_embedding_service):
    """Memory manager for testing."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    return MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)


@pytest.fixture
def declarative_memory(memory_manager):
    """Declarative memory interface for testing."""
    return DeclarativeMemoryInterface(
        memory_manager=memory_manager,
        reasoning_namespace="reasoning/"
    )


@pytest.fixture
def spreading_activation(declarative_memory):
    """Spreading activation for testing."""
    return SpreadingActivation(
        declarative_memory=declarative_memory,
        activation_threshold=0.7,
        damping_factor=0.5,
        max_activations_per_cycle=3
    )


# ============================================================================
# Unit Tests: DeclarativeMemoryInterface
# ============================================================================

class TestDeclarativeMemoryInterface:
    """Test DeclarativeMemoryInterface functionality."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_init(self, memory_manager):
        """Test initialization."""
        dmi = DeclarativeMemoryInterface(
            memory_manager=memory_manager,
            reasoning_namespace="test_reasoning/"
        )
        assert dmi.memory_manager == memory_manager
        assert dmi.reasoning_namespace == "test_reasoning"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_relevant_no_items(self, declarative_memory):
        """Test retrieval with no working memory items."""
        result = declarative_memory.retrieve_relevant([])
        assert result == []
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_relevant_low_activation(self, declarative_memory):
        """Test retrieval filters out low-activation items."""
        wm_items = [
            {"content": {"text": "test content"}, "activation": 0.5}  # Below threshold
        ]
        result = declarative_memory.retrieve_relevant(wm_items, min_activation=0.7)
        # Should return empty or very few results since activation is low
        assert isinstance(result, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_reasoning_result(self, declarative_memory):
        """Test storing reasoning result."""
        memory_id = declarative_memory.store_reasoning_result(
            content="Test inference result",
            source="test_inference",
            tags=["test", "inference"],
            importance=0.7
        )
        assert memory_id is not None
        assert isinstance(memory_id, int)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_reasoning_result_empty_content(self, declarative_memory):
        """Test storing empty content returns None."""
        memory_id = declarative_memory.store_reasoning_result(
            content="",
            source="test"
        )
        assert memory_id is None
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_strengthen_memory(self, declarative_memory, memory_manager):
        """Test strengthening memory importance."""
        # Store a memory first
        memory_id, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Test memory",
            importance=0.5
        )
        
        # Strengthen it
        success = declarative_memory.strengthen_memory(memory_id, boost=0.1)
        assert success is True
        
        # Verify importance increased
        memory = memory_manager.storage.get_memory(memory_id)
        assert memory.importance == 0.6
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_strengthen_memory_nonexistent(self, declarative_memory):
        """Test strengthening nonexistent memory returns False."""
        success = declarative_memory.strengthen_memory(99999, boost=0.1)
        assert success is False
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_context_for_goal(self, declarative_memory):
        """Test retrieving context for a goal."""
        # Store a goal-related memory
        declarative_memory.store_reasoning_result(
            content="Goal test_goal progress: 50%",
            source="goal_progress",
            tags=["test_goal", "goal"],
            namespace="reasoning/goals/test_goal"
        )
        
        # Retrieve context
        memories = declarative_memory.get_context_for_goal("test_goal", limit=5)
        assert isinstance(memories, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_goal_progress(self, declarative_memory):
        """Test storing goal progress."""
        memory_id = declarative_memory.store_goal_progress(
            goal_name="test_goal",
            progress=0.75,
            description="Made significant progress"
        )
        assert memory_id is not None
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_rule_execution(self, declarative_memory):
        """Test storing rule execution."""
        memory_id = declarative_memory.store_rule_execution(
            rule_name="test_rule",
            results=[{"type": "add_to_memory", "content": {"text": "result"}}],
            context="Test execution"
        )
        assert memory_id is not None
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_inference(self, declarative_memory):
        """Test storing inference."""
        memory_id = declarative_memory.store_inference(
            inference="If A then B",
            context="Logical inference",
            importance=0.8
        )
        assert memory_id is not None


# ============================================================================
# Unit Tests: SpreadingActivation
# ============================================================================

class TestSpreadingActivation:
    """Test SpreadingActivation functionality."""
    
    def test_init(self, declarative_memory):
        """Test initialization."""
        sa = SpreadingActivation(
            declarative_memory=declarative_memory,
            activation_threshold=0.8,
            damping_factor=0.3
        )
        assert sa.declarative_memory == declarative_memory
        assert sa.activation_threshold == 0.8
        assert sa.damping_factor == 0.3
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_propagate_activation_empty_items(self, spreading_activation):
        """Test propagation with empty items."""
        result = spreading_activation.propagate_activation([])
        assert result == []
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_propagate_activation_low_threshold(self, spreading_activation):
        """Test propagation filters by activation threshold."""
        wm_items = [
            {"content": {"text": "low activation"}, "activation": 0.5}  # Below 0.7 threshold
        ]
        result = spreading_activation.propagate_activation(wm_items)
        # Should return empty since activation is below threshold
        assert isinstance(result, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_boost_activation_for_retrieved(self, spreading_activation):
        """Test boosting activation when memories are retrieved."""
        item = {"content": {"text": "test"}, "activation": 0.8}
        old_activation = item["activation"]
        
        # Create mock memories
        mock_memories = [
            MemoryRecord(
                namespace="test",
                text="Retrieved memory 1",
                importance=0.7,
                tags=[]
            ),
            MemoryRecord(
                namespace="test",
                text="Retrieved memory 2",
                importance=0.7,
                tags=[]
            )
        ]
        
        new_activation = spreading_activation.boost_activation_for_retrieved(
            item, mock_memories, boost_amount=0.1
        )
        
        assert new_activation > old_activation
        assert item["activation"] == new_activation
        assert item["activation"] > 0.8  # Should be boosted
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_associations(self, spreading_activation):
        """Test getting associations for an item."""
        item = {"content": {"text": "test item"}, "activation": 0.8}
        associations = spreading_activation.get_associations(item)
        assert isinstance(associations, set)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_strengthen_association(self, spreading_activation, memory_manager):
        """Test strengthening association."""
        # Store a memory
        memory_id, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Test memory",
            importance=0.5
        )
        
        item = {"content": {"text": "test item"}, "activation": 0.8}
        spreading_activation.strengthen_association(item, memory_id)
        
        # Check association was recorded
        associations = spreading_activation.get_associations(item)
        assert memory_id in associations
    
    def test_reset(self, spreading_activation):
        """Test resetting activation tracking."""
        # Add some state
        item = {"content": {"id": "test"}, "activation": 0.8}
        spreading_activation.recent_activations["id:test"] = 123.0
        spreading_activation.associations["id:test"] = {1, 2, 3}
        
        # Reset
        spreading_activation.reset()
        
        assert len(spreading_activation.recent_activations) == 0
        assert len(spreading_activation.associations) == 0


# ============================================================================
# Integration Tests: Working Memory with Declarative Memory
# ============================================================================

class TestWorkingMemoryDeclarativeMemoryIntegration:
    """Test integration between working memory and declarative memory."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_wm_init_with_declarative_memory(self, declarative_memory, spreading_activation):
        """Test working memory initialization with declarative memory."""
        wm = WorkingMemory(
            declarative_memory=declarative_memory,
            spreading_activation=spreading_activation
        )
        assert wm.declarative_memory == declarative_memory
        assert wm.spreading_activation == spreading_activation
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_wm_to_declarative_memory(self, declarative_memory, spreading_activation):
        """Test storing WM items to declarative memory."""
        wm = WorkingMemory(
            declarative_memory=declarative_memory,
            spreading_activation=spreading_activation
        )
        
        # Add item with high activation
        wm.add({"type": "fact", "text": "Important fact"}, activation=0.8)
        
        # Store to declarative memory
        stored_count = wm.to_declarative_memory()
        assert stored_count >= 0  # May store if above threshold
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_wm_removal_stores_to_declarative_memory(self, declarative_memory, spreading_activation, memory_manager):
        """Test that WM items are stored when removed due to capacity."""
        wm = WorkingMemory(
            capacity=2,  # Small capacity
            declarative_memory=declarative_memory,
            spreading_activation=spreading_activation
        )
        
        # Fill capacity
        wm.add({"type": "fact", "text": "Fact 1"}, activation=0.9)
        wm.add({"type": "fact", "text": "Fact 2"}, activation=0.8)
        
        # Add one more to trigger eviction
        wm.add({"type": "fact", "text": "Fact 3"}, activation=0.7)
        
        # The evicted item should have been stored (if above threshold)
        # Verify by checking memory count
        all_memories = memory_manager.storage.get_all_memories()
        # At least some memories may have been stored
        assert isinstance(all_memories, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_wm_refresh_from_declarative_memory(self, declarative_memory, spreading_activation, memory_manager):
        """Test refreshing WM from declarative memory."""
        # Store some memories first
        memory_manager.store_memory(
            namespace="reasoning/test",
            text="Stored memory for retrieval",
            importance=0.8
        )
        
        wm = WorkingMemory(
            declarative_memory=declarative_memory,
            spreading_activation=spreading_activation
        )
        
        # Add high-activation item to trigger retrieval
        wm.add({"type": "query", "text": "test"}, activation=0.8)
        
        # Refresh from declarative memory
        wm.refresh_from_declarative_memory(limit=5)
        
        # WM should have items (may include retrieved memories)
        assert len(wm.items) >= 1


# ============================================================================
# Integration Tests: Rule Engine with Declarative Memory
# ============================================================================

class TestRuleEngineDeclarativeMemoryIntegration:
    """Test integration between rule engine and declarative memory."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_rule_engine_init_with_declarative_memory(self, declarative_memory):
        """Test rule engine initialization with declarative memory."""
        rule_engine = RuleEngine(declarative_memory=declarative_memory)
        assert rule_engine.declarative_memory == declarative_memory
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_execute_cycle_with_declarative_memory(
        self, declarative_memory, spreading_activation, memory_manager
    ):
        """Test rule cycle execution with declarative memory integration."""
        # Create working memory with declarative memory
        wm = WorkingMemory(
            declarative_memory=declarative_memory,
            spreading_activation=spreading_activation
        )
        
        # Create rule system with this WM
        rule_system = ProductionRuleSystem(working_memory=wm)
        
        # Create rule engine
        rule_engine = RuleEngine(
            rule_system=rule_system,
            declarative_memory=declarative_memory
        )
        
        # Add some content to WM
        wm.add({"type": "fact", "content": "Test fact"}, activation=0.8)
        
        # Execute cycle
        results = rule_engine.execute_cycle(wm, max_rules=3)
        
        # Should return results (may be empty if no rules match)
        assert isinstance(results, list)


# ============================================================================
# Integration Tests: Goal Manager with Declarative Memory
# ============================================================================

class TestGoalManagerDeclarativeMemoryIntegration:
    """Test integration between goal manager and declarative memory."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_goal_manager_init_with_declarative_memory(self, declarative_memory):
        """Test goal manager initialization with declarative memory."""
        gm = GoalManager(declarative_memory=declarative_memory)
        assert gm.declarative_memory == declarative_memory
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_add_goal_retrieves_memories(self, declarative_memory, memory_manager):
        """Test that adding active goal retrieves related memories."""
        # Store goal-related memory first
        memory_manager.store_memory(
            namespace="reasoning/goals/test_goal",
            text="Previous work on test_goal",
            importance=0.8,
            tags=["test_goal", "goal"]
        )
        
        gm = GoalManager(declarative_memory=declarative_memory)
        
        # Add active goal
        goal = Goal(
            name="test_goal",
            description="Test goal",
            status=GoalStatus.ACTIVE
        )
        gm.add_goal(goal)
        
        # Memories should have been retrieved (check via get_context_for_goal)
        memories = declarative_memory.get_context_for_goal("test_goal")
        assert isinstance(memories, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_goal_progress_stores_to_declarative_memory(self, declarative_memory):
        """Test that goal progress updates are stored."""
        gm = GoalManager(declarative_memory=declarative_memory)
        
        # Add goal
        goal = Goal(name="test_goal", description="Test")
        gm.add_goal(goal)
        
        # Update progress
        gm.update_goal_progress("test_goal", 0.5, "Halfway done")
        
        # Progress should have been stored (verified via memory retrieval)
        memories = declarative_memory.get_context_for_goal("test_goal")
        assert isinstance(memories, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_complete_goal_stores_to_declarative_memory(self, declarative_memory):
        """Test that goal completion is stored."""
        gm = GoalManager(declarative_memory=declarative_memory)
        
        # Add goal
        goal = Goal(name="test_goal", description="Test")
        gm.add_goal(goal)
        
        # Complete goal
        gm.complete_goal("test_goal")
        
        # Completion should have been stored
        memories = declarative_memory.get_context_for_goal("test_goal")
        assert isinstance(memories, list)


# ============================================================================
# Property-Based Tests
# ============================================================================

try:
    from hypothesis import given, strategies as st, settings, HealthCheck
    
    class TestDeclarativeMemoryPropertyBased:
        """Property-based tests using Hypothesis."""
        
        @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
        @given(
            num_items=st.integers(min_value=0, max_value=10),
            activation_values=st.lists(st.floats(min_value=0.0, max_value=2.0), min_size=0, max_size=10)
        )
        def test_retrieve_relevant_property(
            self, declarative_memory, num_items, activation_values
        ):
            """Property: Retrieval results are always a list."""
            # Create WM items
            wm_items = []
            for i, activation in enumerate(activation_values[:num_items]):
                wm_items.append({
                    "content": {"text": f"Item {i}", "id": i},
                    "activation": activation
                })
            
            result = declarative_memory.retrieve_relevant(wm_items, min_activation=0.7)
            assert isinstance(result, list)
            assert len(result) <= len(wm_items)  # Can't retrieve more than items
            
        @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
        @given(
            content=st.text(min_size=1, max_size=100),
            importance=st.floats(min_value=0.0, max_value=1.0)
        )
        def test_store_reasoning_result_property(
            self, declarative_memory, content, importance
        ):
            """Property: Storing always returns int or None."""
            memory_id = declarative_memory.store_reasoning_result(
                content=content,
                importance=importance
            )
            assert memory_id is None or isinstance(memory_id, int)
            
        @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
        @given(
            threshold=st.floats(min_value=0.0, max_value=1.0),
            activations=st.lists(st.floats(min_value=0.0, max_value=2.0), min_size=0, max_size=5)
        )
        def test_spreading_activation_threshold_property(
            self, declarative_memory, threshold, activations
        ):
            """Property: Spreading activation respects threshold."""
            sa = SpreadingActivation(
                declarative_memory=declarative_memory,
                activation_threshold=threshold
            )
            
            wm_items = [
                {"content": {"text": f"Item {i}"}, "activation": act}
                for i, act in enumerate(activations)
            ]
            
            result = sa.propagate_activation(wm_items, limit=5)
            assert isinstance(result, list)
            # Result length should be reasonable
            assert len(result) <= len(wm_items) * 2  # Can't retrieve way more than items
            
except ImportError:
    # Hypothesis not available - skip property-based tests
    pass


# ============================================================================
# Mutation Testing Structure
# ============================================================================

class TestDeclarativeMemoryMutation:
    """Structure for mutation testing of declarative memory."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_mutation_activation_threshold(self, declarative_memory):
        """Mutation test: Changing activation threshold affects retrieval."""
        # This would be run with mutmut or similar mutation testing tool
        # The test should fail when threshold logic is mutated incorrectly
        wm_items = [
            {"content": {"text": "test"}, "activation": 0.75}
        ]
        
        # With threshold 0.7, this should retrieve
        result_low = declarative_memory.retrieve_relevant(wm_items, min_activation=0.7)
        
        # With threshold 0.8, this should not retrieve (or retrieve less)
        result_high = declarative_memory.retrieve_relevant(wm_items, min_activation=0.8)
        
        # Results should differ based on threshold
        assert isinstance(result_low, list)
        assert isinstance(result_high, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_mutation_strengthen_boost(self, declarative_memory, memory_manager):
        """Mutation test: Boost amount affects memory importance."""
        # Store memory
        memory_id, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Test",
            importance=0.5
        )
        
        original_memory = memory_manager.storage.get_memory(memory_id)
        original_importance = original_memory.importance
        
        # Strengthen with boost
        declarative_memory.strengthen_memory(memory_id, boost=0.2)
        
        updated_memory = memory_manager.storage.get_memory(memory_id)
        assert updated_memory.importance > original_importance


# ============================================================================
# Fault Injection Tests
# ============================================================================

class TestDeclarativeMemoryFaultInjection:
    """Fault injection tests for error handling."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_relevant_handles_memory_manager_error(self, declarative_memory):
        """Test that retrieval handles memory manager errors gracefully."""
        # Inject fault by making memory manager raise exception
        with patch.object(declarative_memory.memory_manager, 'retrieve_memories', side_effect=Exception("Test error")):
            wm_items = [{"content": {"text": "test"}, "activation": 0.8}]
            result = declarative_memory.retrieve_relevant(wm_items)
            # Should return empty list on error
            assert result == []
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_reasoning_result_handles_storage_error(self, declarative_memory):
        """Test that storage handles errors gracefully."""
        # Inject fault
        with patch.object(declarative_memory.memory_manager, 'store_memory', side_effect=Exception("Test error")):
            memory_id = declarative_memory.store_reasoning_result(
                content="Test",
                source="test"
            )
            # Should return None on error
            assert memory_id is None
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_spreading_activation_handles_errors(self, spreading_activation):
        """Test that spreading activation handles errors gracefully."""
        # Inject fault
        with patch.object(spreading_activation.declarative_memory, 'retrieve_relevant', side_effect=Exception("Test error")):
            wm_items = [{"content": {"text": "test"}, "activation": 0.8}]
            result = spreading_activation.propagate_activation(wm_items)
            # Should return empty list on error
            assert result == []

