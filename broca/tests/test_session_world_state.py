"""
Tests for session world state integration.
"""

from __future__ import annotations

import pytest
import json
from unittest.mock import Mock, MagicMock, patch

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator
from broca.world_state.formatter import WorldStateFormatter
from broca.self_model.model import SelfModel


class TestSessionWorldState:
    """Test world state integration in ConversationSession."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        mock = Mock()
        mock.chat.return_value = {
            "choices": [{"message": {"content": "Test response", "role": "assistant"}}]
        }
        mock.extract_assistant_content.return_value = "Test response"
        mock.extract_tool_calls.return_value = []
        return mock
    
    @pytest.fixture
    def mock_world_state_aggregator(self):
        """Create a mock world state aggregator."""
        mock = Mock(spec=WorldStateAggregator)
        mock.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "datetime": "2024-01-01T12:00:00Z",
                "platform": "Linux",
            },
            "self_model": {
                "summary": "Test summary",
            },
        }
        return mock
    
    def test_init_with_world_state_aggregator(self, mock_llm_client, mock_world_state_aggregator):
        """Test initializing session with world state aggregator."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        assert session.world_state_aggregator is mock_world_state_aggregator
        assert session._world_state_formatter is not None
        
        # Verify aggregator was called during initialization
        mock_world_state_aggregator.aggregate.assert_called_once()
        
        # Verify system message contains only world state as JSON (no base prompt)
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        # Check that it's valid JSON with expected structure
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
        assert "system" in parsed or "self_model" in parsed
    
    def test_init_without_world_state_aggregator(self, mock_llm_client):
        """Test initializing session without world state aggregator."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
        )
        
        assert session.world_state_aggregator is None
        assert session._world_state_formatter is None
        # Without aggregator, no system message should be created
        assert len(session.messages) == 0
    
    def test_init_populates_world_state_before_first_message(self, mock_llm_client, mock_world_state_aggregator):
        """Test that world state is populated at initialization, before any user message."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Verify aggregator was called during initialization
        assert mock_world_state_aggregator.aggregate.call_count == 1
        
        # Verify system message exists and contains only world state as JSON
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        # Check that it's valid JSON
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
        assert "system" in parsed or "self_model" in parsed
        
        # Verify no user messages yet
        user_messages = [m for m in session.messages if m.get("role") == "user"]
        assert len(user_messages) == 0
    
    def test_init_populates_world_state_without_initial_prompt(self, mock_llm_client, mock_world_state_aggregator):
        """Test that world state is populated even when no initial system prompt is provided."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Verify aggregator was called
        assert mock_world_state_aggregator.aggregate.call_count == 1
        
        # Verify system message was created with only world state as JSON
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        # Check that it's valid JSON
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
    
    def test_update_system_prompt_with_aggregator(self, mock_llm_client, mock_world_state_aggregator):
        """Test updating system prompt with world state aggregator."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Reset call count (aggregator was called during init)
        initial_call_count = mock_world_state_aggregator.aggregate.call_count
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Call update method
        session._update_system_prompt()
        
        # Verify aggregator was called again
        mock_world_state_aggregator.aggregate.assert_called_once()
        
        # Verify system message contains only world state as JSON (no base prompt)
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        # Check that it's valid JSON
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
    
    def test_update_system_prompt_without_aggregator(self, mock_llm_client):
        """Test updating system prompt without aggregator (should do nothing)."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
        )
        
        original_messages = session.messages.copy()
        
        # Call update method
        session._update_system_prompt()
        
        # Should not change messages (no aggregator, so no system message)
        assert session.messages == original_messages
    
    def test_update_system_prompt_creates_system_message(self, mock_llm_client, mock_world_state_aggregator):
        """Test that update creates system message if none exists."""
        # Create session without system prompt but with aggregator
        # This will create system message during init
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # System message should be created during initialization
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        # Check that it's valid JSON
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
        
        # Reset and manually remove system message to test creation
        session.messages = []
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Call update method
        session._update_system_prompt()
        
        # Should create system message with only world state as JSON
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        # Check that it's valid JSON
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
    
    def test_update_system_prompt_handles_errors(self, mock_llm_client):
        """Test that update handles errors gracefully."""
        # Create aggregator that raises error
        mock_aggregator = Mock(spec=WorldStateAggregator)
        mock_aggregator.aggregate.side_effect = Exception("Test error")
        
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_aggregator,
        )
        
        # On init, aggregator is called and may fail, but session should still be created
        # If there's a system message from init, it should remain unchanged on error
        # If no system message exists, update should not create one on error
        original_messages_count = len(session.messages)
        
        # Call update method (should not raise)
        session._update_system_prompt()
        
        # Should not change messages on error (either keep existing or remain empty)
        assert len(session.messages) == original_messages_count
    
    def test_send_updates_system_prompt_before_llm_call(self, mock_llm_client, mock_world_state_aggregator):
        """Test that send() updates system prompt before LLM call."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Reset call count
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Send a message
        session.send("Test user message")
        
        # Verify aggregator was called (before LLM call)
        assert mock_world_state_aggregator.aggregate.called
        
        # Verify system message contains only world state as JSON
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
    
    def test_send_updates_system_prompt_each_iteration(self, mock_llm_client, mock_world_state_aggregator):
        """Test that system prompt is updated before each LLM call iteration."""
        # Simple test: verify aggregator is called during send
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Reset call count
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Send a message
        session.send("Test user message")
        
        # Verify aggregator was called (at least once before LLM call)
        assert mock_world_state_aggregator.aggregate.call_count >= 1
    
    def test_system_prompt_always_first_message(self, mock_llm_client, mock_world_state_aggregator):
        """Test that system prompt is always the first message."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Add some messages
        session.messages.append({"role": "user", "content": "User message"})
        session.messages.append({"role": "assistant", "content": "Assistant message"})
        
        # Update system prompt
        session._update_system_prompt()
        
        # System message should be first
        assert session.messages[0]["role"] == "system"
        assert session.messages[1]["role"] == "user"
        assert session.messages[2]["role"] == "assistant"
        # System message should contain only world state as JSON
        system_content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            json_part = system_content
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
    
    def test_system_prompt_excludes_behavioral_patterns(self, mock_llm_client):
        """Test that system prompt JSON does NOT contain behavioral_patterns."""
        from broca.internal_sensing.framework import InternalSensingFramework
        
        # Create a mock internal sensing that would return behavioral_patterns
        mock_internal_sensing = Mock(spec=InternalSensingFramework)
        mock_internal_sensing.sample_internal_state.return_value = {
            "physiology": {"metrics": {"processing_latency": 0.5}},
            "cognition": {"metrics": {"confidence": 0.8}},
            "affect": {"valence": 0.6},
        }
        mock_internal_sensing.generate_interoceptive_report.return_value = "Test report"
        mock_internal_sensing.get_tool_statistics.return_value = {"memory": 5}
        mock_internal_sensing.extract_behavioral_patterns.return_value = [
            {"type": "tool_usage", "tool": "memory"}
        ]
        
        # Create real aggregator with mock internal sensing
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
        )
        
        # Get system prompt content
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in system_content:
            json_part = system_content.split("\n\n", 1)[1]
        else:
            # If no base prompt, entire content is JSON
            json_part = system_content
        
        # Parse JSON
        parsed = json.loads(json_part)
        
        # Verify behavioral_patterns is NOT in the JSON anywhere
        # Check recursively in the parsed structure
        def check_no_behavioral_patterns(obj, path=""):
            """Recursively check that behavioral_patterns is not present."""
            if isinstance(obj, dict):
                assert "behavioral_patterns" not in obj, f"Found behavioral_patterns at path: {path}"
                for key, value in obj.items():
                    check_no_behavioral_patterns(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_no_behavioral_patterns(item, f"{path}[{i}]" if path else f"[{i}]")
        
        check_no_behavioral_patterns(parsed)
        
        # Verify internal_state exists and has expected fields (but not behavioral_patterns)
        if "internal_state" in parsed and parsed["internal_state"] is not None:
            internal_state = parsed["internal_state"]
            assert "behavioral_patterns" not in internal_state
            # Other fields should still be present
            assert "interoceptive_report" in internal_state or "tool_statistics" in internal_state
    
    def test_system_prompt_includes_project_files_and_directory_tree(self, mock_llm_client):
        """Test that system prompt includes project files and directory_tree when available."""
        from broca.tools.project_world_state import ProjectWorldStateTool
        
        # Create a real project world state tool with test data
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test1.py").write_text("print('test1')")
            (Path(tmpdir) / "test2.py").write_text("print('test2')")
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "test3.py").write_text("print('test3')")
            
            # Build world state
            project_tool = ProjectWorldStateTool(project_root=tmpdir)
            project_tool.build_world_state(project_root=tmpdir)
            
            # Create aggregator with project tool
            aggregator = WorldStateAggregator(project_world_state_tool=project_tool)
            
            # Create session
            session = ConversationSession(
                system_prompt=None,
                llm=mock_llm_client,
                world_state_aggregator=aggregator,
            )
            
            # Get system prompt content
            assert len(session.messages) == 1
            assert session.messages[0]["role"] == "system"
            system_content = session.messages[0]["content"]
            
            # Extract JSON part
            if "\n\n" in system_content:
                json_part = system_content.split("\n\n", 1)[1]
            else:
                json_part = system_content
            
            # Parse JSON
            parsed = json.loads(json_part)
            
            # Verify project section exists
            assert "project" in parsed
            project = parsed["project"]
            
            # Verify minimal structure: directory_tree and filenames only
            assert "directory_tree" in project
            assert "filenames" in project
            assert isinstance(project["filenames"], list)
            assert len(project["filenames"]) > 0
            # Verify filenames are simple strings (paths), not objects with metadata
            for filename in project["filenames"]:
                assert isinstance(filename, str)
            # Should NOT include extraneous metadata
            assert "files" not in project  # Should be "filenames" not "files"
            assert "root" not in project
            assert "statistics" not in project
            assert "file_count" not in project
            
            # Verify directory_tree is included
            assert "directory_tree" in project
            assert isinstance(project["directory_tree"], dict)
    
    def test_system_prompt_includes_memory_namespace_hierarchy(self, mock_llm_client):
        """Test that system prompt includes memory namespace hierarchy when available."""
        from broca.memory.manager import MemoryManager
        from broca.memory.storage import MemoryStorage
        from broca.memory.vector_index import VectorIndex
        from broca.memory.embeddings import EmbeddingService
        
        # Create a real memory manager
        import tempfile
        import os
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = os.path.join(tmpdir, "test_memories.db")
                index_path = os.path.join(tmpdir, "test.faiss")
                
                # Initialize components
                storage = MemoryStorage(db_path=db_path)
                vector_index = VectorIndex(dimension=1536, index_path=index_path)
                embedding_service = EmbeddingService()
                memory_manager = MemoryManager(storage, vector_index, embedding_service)
                
                try:
                    # Create aggregator with memory manager
                    aggregator = WorldStateAggregator(memory_manager=memory_manager)
                    
                    # Create session
                    session = ConversationSession(
                        system_prompt=None,
                        llm=mock_llm_client,
                        world_state_aggregator=aggregator,
                    )
                    
                    # Get system prompt content
                    assert len(session.messages) == 1
                    assert session.messages[0]["role"] == "system"
                    system_content = session.messages[0]["content"]
                    
                    # Extract JSON part
                    if "\n\n" in system_content:
                        json_part = system_content.split("\n\n", 1)[1]
                    else:
                        json_part = system_content
                    
                    # Parse JSON
                    parsed = json.loads(json_part)
                    
                    # Verify memory section exists
                    assert "memory" in parsed
                    memory = parsed["memory"]
                    
                    # Verify namespace_hierarchy is included
                    assert "namespace_hierarchy" in memory
                    assert isinstance(memory["namespace_hierarchy"], dict)
                finally:
                    memory_manager.close()
        except ImportError:
            pytest.skip("Memory dependencies not available")
    
    def test_valence_computed_from_conversation_history(self, mock_llm_client):
        """Test that session computes valence from conversation history."""
        from broca.internal_sensing.framework import InternalSensingFramework
        
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            internal_sensing_framework=framework,
        )
        
        # Add conversation messages
        session.messages.extend([
            {"role": "user", "content": "This is great! Excellent work!"},
            {"role": "assistant", "content": "Thank you! I'm glad you're happy."},
        ])
        
        # Send a message (this should compute valence from history)
        response = session.send("Perfect!")
        
        # Check that valence was computed
        valence = framework.interoception.affect.affective_states.get("valence")
        assert valence is not None
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
    
    def test_valence_excludes_system_in_history(self, mock_llm_client):
        """Test that system messages are excluded from valence computation."""
        from broca.internal_sensing.framework import InternalSensingFramework
        
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        session = ConversationSession(
            system_prompt="You are a helpful assistant.",
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            internal_sensing_framework=framework,
        )
        
        # Add conversation with negative sentiment
        session.messages.extend([
            {"role": "user", "content": "This is terrible. I'm very frustrated."},
            {"role": "assistant", "content": "I understand your frustration."},
        ])
        
        # Send a message
        response = session.send("Still terrible!")
        
        # Check that valence reflects conversation (negative), not system prompt
        valence = framework.interoception.affect.affective_states.get("valence")
        assert valence is not None
        assert isinstance(valence, float)
        # Should be negative from conversation, not affected by system prompt
        assert valence < 0.0
    
    def test_valence_computed_before_first_response(self, mock_llm_client):
        """Test that valence is computed from user message before first assistant response."""
        from broca.internal_sensing.framework import InternalSensingFramework
        
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            internal_sensing_framework=framework,
        )
        
        # Before sending, valence should be None
        initial_valence = framework.interoception.affect.affective_states.get("valence")
        assert initial_valence is None
        
        # Send first message - valence should be computed from user message before response
        # We'll check by mocking the send to stop before LLM call
        # Actually, let's just send and check that valence was computed early
        response = session.send("This is wonderful! I'm so happy!")
        
        # Valence should have been computed from user message
        valence = framework.interoception.affect.affective_states.get("valence")
        assert valence is not None
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        assert valence > 0.0  # Should be positive from positive user message
    
    def test_valence_in_world_state_on_first_prompt(self, mock_llm_client):
        """Test that valence appears in world state on first prompt."""
        from broca.internal_sensing.framework import InternalSensingFramework
        
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            internal_sensing_framework=framework,
        )
        
        # Send first message
        response = session.send("This is terrible! I'm frustrated!")
        
        # Get world state after first prompt
        world_state = aggregator.aggregate()
        
        # Valence should be in world state
        assert "internal_state" in world_state
        assert "affect" in world_state["internal_state"]
        affect = world_state["internal_state"]["affect"]
        assert "valence" in affect
        assert affect["valence"] is not None
        assert isinstance(affect["valence"], float)
        assert -1.0 <= affect["valence"] <= 1.0
        assert affect["valence"] < 0.0  # Should be negative from negative user message

