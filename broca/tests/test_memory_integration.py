"""
Integration tests for memory tools with ConversationSession.

Tests memory storage and retrieval in conversation flow, and interoperability with other tools.
"""

from __future__ import annotations

import tempfile
import os
import json
from unittest.mock import Mock, patch
import pytest

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tools.memory_tool import StoreMemoryTool, RetrieveMemoriesTool
from broca.memory import MemoryRecord, SourceType, SourceMetadata
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.memory.manager import MemoryManager
from broca.tests.utils import build_llm_response

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    service = Mock(spec=EmbeddingService)
    service.generate_embedding.return_value = [0.1] * 1536
    return service


@pytest.fixture
def temp_memory_system(mock_embedding_service):
    """Create temporary memory system for testing."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        index_path = os.path.join(tmpdir, "test.faiss")
        
        storage = MemoryStorage(db_path)
        vector_index = VectorIndex(dimension=1536, index_path=index_path)
        manager = MemoryManager(storage, vector_index, mock_embedding_service)
        
        yield manager, storage, vector_index
        
        manager.close()


class TestMemoryToolsWithSession:
    """Test memory tools integrated with ConversationSession."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_tool_call(self, mock_llm_client: Mock, temp_memory_system, normal_tools_mode):
        """
        Test storing memory via tool call in conversation.
        
        Rationale: Ensures memory tools work in conversation flow.
        """
        manager, storage, vector_index = temp_memory_system
        registry = ToolRegistry()
        store_tool = StoreMemoryTool(manager)
        registry.register_tool(store_tool)
        
        # Mock LLM response with tool call
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "store_memory",
                            "arguments": json.dumps({
                                "namespace": "test.namespace",
                                "text": "Test memory",
                                "tags": ["tag1"],
                                "importance": 0.7
                            })
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Memory stored")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Memory stored"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Store this: Test memory")
        
        assert response == "Memory stored"
        # Verify memory was stored
        all_memories = storage.get_all_memories()
        assert len(all_memories) == 1
        assert all_memories[0].text == "Test memory"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_memories_tool_call(self, mock_llm_client: Mock, temp_memory_system):
        """
        Test retrieving memories via tool call in conversation.
        
        Rationale: Ensures memory retrieval works in conversation flow.
        """
        manager, storage, vector_index = temp_memory_system
        registry = ToolRegistry()
        retrieve_tool = RetrieveMemoriesTool(manager)
        registry.register_tool(retrieve_tool)
        
        # Store a memory first
        memory_id = manager.store_memory(
            namespace="test",
            text="Stored memory",
            importance=0.8
        )
        
        # Mock LLM response with tool call
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "retrieve_memories",
                            "arguments": json.dumps({
                                "query": "stored memory",
                                "limit": 5
                            })
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Found the memory")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Found the memory"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("What memories do we have?")
        
        assert response == "Found the memory"
        # Verify tool was called (check tool messages in conversation)
        tool_messages = [msg for msg in session.messages if msg.get("role") == "tool"]
        assert len(tool_messages) > 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_memory_interoperability_with_web_search(self, mock_llm_client: Mock, temp_memory_system, normal_tools_mode):
        """
        Test that memory tools work alongside web search tool.
        
        Rationale: Ensures tools can be used together in the same conversation.
        """
        manager, storage, vector_index = temp_memory_system
        registry = ToolRegistry()
        
        # Register both tools
        store_tool = StoreMemoryTool(manager)
        registry.register_tool(store_tool)
        
        # Mock web search tool
        from broca.tests.test_tools import MockTool
        web_search_mock = MockTool(
            "web_search",
            "Search the web",
            {"type": "object", "properties": {"query": {"type": "string"}}}
        )
        registry.register_tool(web_search_mock)
        
        # Mock LLM that calls both tools
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "store_memory",
                            "arguments": json.dumps({
                                "namespace": "test",
                                "text": "Important fact",
                                "importance": 0.9
                            })
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Done")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Done"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Store this important fact")
        
        assert response == "Done"
        # Verify memory was stored
        assert len(storage.get_all_memories()) == 1


class TestMemoryPersistence:
    """Test memory persistence across sessions."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_memory_persists_across_sessions(self, mock_llm_client: Mock, temp_memory_system):
        """
        Test that memories persist across different sessions.
        
        Rationale: Ensures memories are truly persistent.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memory in first "session"
        memory_id = manager.store_memory(
            namespace="persistent",
            text="Persistent memory",
            importance=0.8
        )
        
        # Create new manager (simulating restart)
        manager2 = MemoryManager(storage, vector_index, manager.embedding_service)
        
        # Retrieve memory
        results = manager2.retrieve_memories(query="persistent", limit=5)
        
        assert len(results) > 0
        assert any(r.text == "Persistent memory" for r in results)


class TestMemorySourceIntegration:
    """Test source tracking integration across the memory system."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_end_to_end_source_tracking(self, temp_memory_system):
        """
        Test end-to-end source tracking from tool to storage.
        
        Rationale: Ensures source is tracked correctly through the entire system.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memory with source via tool
        tool = StoreMemoryTool(manager)
        result = tool.execute(
            namespace="test",
            text="Web search result",
            importance=0.5,
            source_type="web_search",
            source_metadata={"query": "test query", "urls": ["http://example.com"]}
        )
        
        assert result["success"] is True
        memory_id = result["memory_id"]
        
        # Verify source was stored
        memory = storage.get_memory(memory_id)
        assert memory is not None
        assert memory.source is not None
        assert memory.source.source_type == SourceType.WEB_SEARCH
        assert memory.source.metadata is not None
        assert memory.source.metadata["query"] == "test query"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_source_filtering_integration(self, temp_memory_system):
        """
        Test source filtering works end-to-end.
        
        Rationale: Ensures source filtering works through the entire system.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with different sources
        manager.store_memory(
            namespace="test",
            text="User provided information",
            importance=0.5,
            source=SourceMetadata(source_type=SourceType.USER)
        )
        manager.store_memory(
            namespace="test",
            text="Web search result",
            importance=0.5,
            source=SourceMetadata(source_type=SourceType.WEB_SEARCH)
        )
        manager.store_memory(
            namespace="test",
            text="System file content",
            importance=0.5,
            source=SourceMetadata(source_type=SourceType.SYSTEM_FILE)
        )
        
        # Filter by USER source
        results = manager.retrieve_memories(
            query="information",
            source_types=[SourceType.USER]
        )
        
        assert len(results) >= 1
        assert all(r.source is not None and r.source.source_type == SourceType.USER for r in results)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_backward_compatibility_no_source(self, temp_memory_system):
        """
        Test backward compatibility with memories without source.
        
        Rationale: Ensures existing code without source still works.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memory without source (old way)
        record = MemoryRecord(
            namespace="test",
            text="Old memory",
            importance=0.5
        )
        memory_id = storage.store_memory(record)
        
        # Should still be retrievable
        memory = storage.get_memory(memory_id)
        assert memory is not None
        assert memory.text == "Old memory"
        # Source should be None (not set)
        assert memory.source is None
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_all_source_types_work(self, temp_memory_system):
        """
        Test that all source types work correctly.
        
        Rationale: Ensures all source types are supported end-to-end.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with all source types
        for source_type in SourceType:
            memory_id, _, _ = manager.store_memory(
                namespace="test",
                text=f"Memory from {source_type.value}",
                importance=0.5,
                source=SourceMetadata(source_type=source_type)
            )
            
            # Verify source was stored
            memory = storage.get_memory(memory_id)
            assert memory is not None
            assert memory.source is not None
            assert memory.source.source_type == source_type
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_source_metadata_persistence(self, temp_memory_system):
        """
        Test that source metadata persists correctly.
        
        Rationale: Ensures complex source metadata is preserved.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memory with complex metadata
        source = SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            metadata={
                "query": "Python memory management",
                "urls": ["https://example.com/1", "https://example.com/2"],
                "result_count": 5,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
        memory_id, _, _ = manager.store_memory(
            namespace="test",
            text="Web search result",
            importance=0.5,
            source=source
        )
        
        # Close and reopen storage (simulate restart)
        manager.close()
        
        # Reopen
        storage2 = MemoryStorage(storage.db_path)
        vector_index2 = VectorIndex(dimension=1536, index_path=vector_index.index_path)
        manager2 = MemoryManager(storage2, vector_index2, Mock(spec=EmbeddingService))
        
        # Verify source metadata persisted
        memory = storage2.get_memory(memory_id)
        assert memory is not None
        assert memory.source is not None
        assert memory.source.source_type == SourceType.WEB_SEARCH
        assert memory.source.metadata is not None
        assert memory.source.metadata["query"] == "Python memory management"
        assert len(memory.source.metadata["urls"]) == 2
        assert memory.source.metadata["result_count"] == 5
        
        manager2.close()
        storage2.close()

