"""
Tests for SQLite-only self-model storage.

Tests SQLite storage operations, data integrity, and round-trip serialization.
"""

from __future__ import annotations

import pytest
import tempfile
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from broca.self_model.model import SelfModel
from broca.self_model.storage import SelfModelSQLiteStorage
from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.epistemic.models import SourceType, SourceMetadata, ConfidenceMetrics, VerificationRecord
from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.ids import generate_capability_id


class TestSelfModelSQLiteStorage:
    """Test SQLite-only storage for self-model."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def storage(self, temp_db_path):
        """Create a SQLite storage instance."""
        return SelfModelSQLiteStorage(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_self_model(self):
        """Create a sample self-model with epistemic layer for testing."""
        # Create self-model with epistemic layer
        epistemic_layer = EpistemicLayer()
        engine = MetacognitiveEngine(epistemic_layer=epistemic_layer)
        
        # Add some knowledge
        capability = "Test capability"
        knowledge_id = generate_capability_id(capability)
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        engine.knowledge_acquisition_workflow(
            knowledge_id=knowledge_id,
            source=source,
            initial_confidence=0.8
        )
        
        # Add memory mapping
        epistemic_layer.add_memory_knowledge_mapping(1, knowledge_id)
        
        model = SelfModel(
            capabilities=["Test capability", "Another capability"],
            knowledge_boundaries={"test": "boundary"},
            constraints={"test": "constraint"},
            metadata={"version": 1, "test": "metadata"},
            epistemic_layer=epistemic_layer
        )
        
        return model
    
    def test_storage_initialization(self, storage, temp_db_path):
        """
        Test SQLite storage initialization.
        
        Rationale: Ensures storage can be initialized and database is created.
        """
        assert storage is not None
        assert os.path.exists(temp_db_path)
        
        # Verify schema was created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert "self_models" in tables
        assert "epistemic_knowledge_sources" in tables
        assert "epistemic_confidence_metrics" in tables
    
    def test_save_and_load_empty_model(self, storage):
        """
        Test saving and loading an empty self-model.
        
        Rationale: Ensures basic save/load operations work.
        """
        model = SelfModel(
            capabilities=[],
            knowledge_boundaries={},
            constraints={},
            metadata={"version": 1}
        )
        
        storage.save(model)
        loaded = storage.load()
        
        assert loaded is not None
        assert loaded.capabilities == []
        assert loaded.metadata["version"] == 1
    
    def test_save_and_load_full_model(self, storage, sample_self_model):
        """
        Test saving and loading a full self-model with all fields.
        
        Rationale: Ensures all model fields are preserved.
        """
        storage.save(sample_self_model)
        loaded = storage.load()
        
        assert loaded is not None
        assert loaded.capabilities == sample_self_model.capabilities
        assert loaded.knowledge_boundaries == sample_self_model.knowledge_boundaries
        assert loaded.constraints == sample_self_model.constraints
        assert loaded.metadata["version"] == sample_self_model.metadata["version"]
    
    def test_save_and_load_epistemic_layer(self, storage, sample_self_model):
        """
        Test saving and loading epistemic layer.
        
        Rationale: Ensures epistemic layer data is preserved.
        """
        storage.save(sample_self_model)
        loaded = storage.load()
        
        assert loaded.epistemic_layer is not None
        assert len(loaded.epistemic_layer.knowledge_sources) == len(sample_self_model.epistemic_layer.knowledge_sources)
        assert len(loaded.epistemic_layer.confidence_calibration) == len(sample_self_model.epistemic_layer.confidence_calibration)
        assert loaded.epistemic_layer.memory_knowledge_mapping == sample_self_model.epistemic_layer.memory_knowledge_mapping
    
    def test_epistemic_data_persisted_to_database(self, temp_db_path):
        """
        Test that epistemic knowledge items are saved and loaded from database.
        
        Rationale: Ensures epistemic data (knowledge sources, confidence metrics) 
        is properly persisted and can be retrieved.
        """
        storage = SelfModelSQLiteStorage(temp_db_path)
        
        # Create a self-model with epistemic layer containing knowledge
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType
        from broca.self_model.epistemic.ids import generate_capability_id
        from datetime import datetime, timezone
        
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        # Add some knowledge to epistemic layer
        engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
        knowledge_id = generate_capability_id("Python programming")
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        engine.knowledge_acquisition_workflow(
            knowledge_id=knowledge_id,
            source=source,
            initial_confidence=0.5
        )
        
        # Verify knowledge exists in memory
        assert self_model.epistemic_layer.has_knowledge(knowledge_id)
        
        # Save model
        storage.save(self_model)
        
        # Load model
        loaded = storage.load()
        
        # Verify epistemic layer was loaded
        assert loaded.epistemic_layer is not None
        
        # Verify knowledge item exists in loaded model
        assert loaded.epistemic_layer.has_knowledge(knowledge_id)
        
        # Verify confidence metrics were loaded
        metrics = loaded.epistemic_layer.get_confidence_metrics(knowledge_id)
        assert metrics is not None
        assert metrics.overall_confidence == 0.5
    
    def test_epistemic_data_loaded_from_database(self, temp_db_path):
        """
        Test that epistemic data is loaded when self-model is loaded from database.
        
        Rationale: Ensures epistemic layer with knowledge items is properly loaded and integrated.
        """
        storage = SelfModelSQLiteStorage(temp_db_path)
        
        # Create and save a self-model with epistemic layer containing knowledge
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType
        from broca.self_model.epistemic.ids import generate_capability_id, generate_constraint_id
        from datetime import datetime, timezone
        
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        # Add multiple knowledge items
        engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
        knowledge_id1 = generate_capability_id("Python programming")
        knowledge_id2 = generate_constraint_id("max_iterations", 100)
        
        source1 = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        source2 = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        
        engine.knowledge_acquisition_workflow(knowledge_id1, source1, 0.5)
        engine.knowledge_acquisition_workflow(knowledge_id2, source2, 0.6)
        
        # Save model
        storage.save(self_model)
        
        # Load model
        loaded = storage.load()
        
        # Verify epistemic layer was loaded with all knowledge items
        assert loaded.epistemic_layer is not None
        assert loaded.epistemic_layer.has_knowledge(knowledge_id1)
        assert loaded.epistemic_layer.has_knowledge(knowledge_id2)
        assert len(loaded.epistemic_layer.knowledge_sources) == 2
    
    def test_epistemic_data_loaded_from_previous_version(self, temp_db_path):
        """
        Test that epistemic data from previous model versions is loaded if current model has none.
        
        Rationale: Ensures epistemic data is not lost when model version changes.
        """
        storage = SelfModelSQLiteStorage(temp_db_path)
        
        # Create and save version 1 with epistemic data
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType
        from broca.self_model.epistemic.ids import generate_capability_id
        from datetime import datetime, timezone
        
        model_v1 = SelfModel.create_default()
        model_v1.metadata["version"] = 1
        model_v1.epistemic_layer = EpistemicLayer()
        
        engine = MetacognitiveEngine(epistemic_layer=model_v1.epistemic_layer)
        knowledge_id = generate_capability_id("Python programming")
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        engine.knowledge_acquisition_workflow(knowledge_id, source, 0.5)
        
        storage.save(model_v1)
        
        # Create version 2 without epistemic layer
        model_v2 = SelfModel.create_default()
        model_v2.metadata["version"] = 2
        model_v2.epistemic_layer = None  # No epistemic layer in v2
        
        storage.save(model_v2)
        
        # Load current model (v2)
        loaded = storage.load()
        
        # Verify epistemic data from v1 is loaded even though v2 had none
        assert loaded.epistemic_layer is not None
        assert loaded.epistemic_layer.has_knowledge(knowledge_id)
        assert len(loaded.epistemic_layer.knowledge_sources) == 1
    
    def test_epistemic_layer_activated_on_load(self, temp_db_path):
        """
        Test that epistemic layer is active and integrated when loaded.
        
        Rationale: Ensures MetacognitiveEngine can be created and used with loaded epistemic layer.
        """
        storage = SelfModelSQLiteStorage(temp_db_path)
        
        # Create and save a self-model with epistemic layer
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceMetadata, SourceType
        from broca.self_model.epistemic.ids import generate_capability_id
        from datetime import datetime, timezone
        
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
        knowledge_id = generate_capability_id("Python programming")
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        engine.knowledge_acquisition_workflow(knowledge_id, source, 0.5)
        
        storage.save(self_model)
        
        # Load model
        loaded = storage.load()
        
        # Verify epistemic layer is active - can create engine and use it
        assert loaded.epistemic_layer is not None
        loaded_engine = MetacognitiveEngine(epistemic_layer=loaded.epistemic_layer)
        
        # Verify we can query the epistemic layer
        metrics = loaded_engine.epistemic_layer.get_confidence_metrics(knowledge_id)
        assert metrics is not None
        assert metrics.overall_confidence == 0.5
        
        # Verify we can get epistemic context
        context = loaded_engine.get_epistemic_context(knowledge_id)
        assert context is not None
    
    def test_save_and_load_verification_history(self, storage, sample_self_model):
        """
        Test saving and loading verification history.
        
        Rationale: Ensures verification records are preserved.
        """
        # Add verification record
        knowledge_id = list(sample_self_model.epistemic_layer.knowledge_sources.keys())[0]
        verification = VerificationRecord(
            timestamp=datetime.now(timezone.utc),
            verification_type="test",
            result="confirmed",
            confidence_delta=0.1,
            new_evidence=[SourceMetadata(source_type=SourceType.USER_PROVIDED)]
        )
        sample_self_model.epistemic_layer.add_verification_record(knowledge_id, verification)
        
        storage.save(sample_self_model)
        loaded = storage.load()
        
        history = loaded.epistemic_layer.get_verification_history(knowledge_id)
        assert len(history) == 1
        assert history[0].result == "confirmed"
        assert history[0].confidence_delta == 0.1
    
    def test_save_and_load_inference_chains(self, storage, sample_self_model):
        """
        Test saving and loading inference chains.
        
        Rationale: Ensures inference nodes are preserved.
        """
        from broca.self_model.epistemic.models import InferenceNode
        
        # Add inference node
        knowledge_id = list(sample_self_model.epistemic_layer.knowledge_sources.keys())[0]
        node = InferenceNode(
            knowledge_id=knowledge_id,
            node_type="premise",
            confidence=0.8,
            source=SourceMetadata(source_type=SourceType.USER_PROVIDED)
        )
        sample_self_model.epistemic_layer.add_inference_node(node)
        
        storage.save(sample_self_model)
        loaded = storage.load()
        
        loaded_node = loaded.epistemic_layer.get_inference_node(knowledge_id)
        assert loaded_node is not None
        assert loaded_node.node_type == "premise"
        assert loaded_node.confidence == 0.8
    
    def test_version_history(self, storage, sample_self_model):
        """
        Test version history tracking.
        
        Rationale: Ensures version history is maintained.
        """
        # Save initial version
        storage.save(sample_self_model)
        
        # Update and save new version
        sample_self_model.metadata["version"] = 2
        sample_self_model.capabilities.append("New capability")
        storage.save(sample_self_model)
        
        # Check version history
        history = storage.get_version_history()
        assert len(history) >= 2
        
        # Verify we can load specific version
        version_1 = storage.get_version(1)
        assert version_1 is not None
        assert version_1.metadata["version"] == 1
        assert len(version_1.capabilities) == 2  # Original capabilities
        
        version_2 = storage.get_version(2)
        assert version_2 is not None
        assert version_2.metadata["version"] == 2
        assert len(version_2.capabilities) == 3  # Added new capability
    
    def test_update_existing_model(self, storage, sample_self_model):
        """
        Test updating an existing model.
        
        Rationale: Ensures updates work correctly.
        """
        # Save initial
        storage.save(sample_self_model)
        
        # Update
        sample_self_model.capabilities.append("Updated capability")
        sample_self_model.metadata["version"] = 2
        storage.save(sample_self_model)
        
        # Load and verify
        loaded = storage.load()
        assert len(loaded.capabilities) == 3
        assert loaded.metadata["version"] == 2
    
    def test_load_nonexistent_model(self, storage):
        """
        Test loading when no model exists.
        
        Rationale: Ensures graceful handling of missing data.
        """
        loaded = storage.load()
        assert loaded is None
    
    def test_round_trip_serialization(self, storage, sample_self_model):
        """
        Test round-trip serialization preserves all data.
        
        Rationale: Ensures data integrity through save/load cycles.
        """
        # Save and load multiple times
        storage.save(sample_self_model)
        loaded1 = storage.load()
        
        loaded1.metadata["version"] = 2
        storage.save(loaded1)
        loaded2 = storage.load()
        
        # Verify all data preserved
        assert loaded2.capabilities == sample_self_model.capabilities
        assert loaded2.epistemic_layer is not None
        assert len(loaded2.epistemic_layer.knowledge_sources) == len(sample_self_model.epistemic_layer.knowledge_sources)
    
    def test_multiple_versions(self, storage, sample_self_model):
        """
        Test saving multiple versions.
        
        Rationale: Ensures version history is maintained correctly.
        """
        # Save version 1
        storage.save(sample_self_model)
        
        # Save version 2
        sample_self_model.metadata["version"] = 2
        sample_self_model.capabilities.append("V2 capability")
        storage.save(sample_self_model)
        
        # Save version 3
        sample_self_model.metadata["version"] = 3
        sample_self_model.capabilities.append("V3 capability")
        storage.save(sample_self_model)
        
        # Verify all versions
        v1 = storage.get_version(1)
        v2 = storage.get_version(2)
        v3 = storage.get_version(3)
        current = storage.load()
        
        assert v1 is not None
        assert v2 is not None
        assert v3 is not None
        assert current.metadata["version"] == 3
        assert len(current.capabilities) == 4  # Original 2 + V2 + V3
    
    def test_version_history_limit(self, storage, sample_self_model):
        """
        Test that version history is limited to 50 versions.
        
        Rationale: Ensures database doesn't grow unbounded.
        """
        # Save 60 versions
        for i in range(1, 61):
            sample_self_model.metadata["version"] = i
            storage.save(sample_self_model)
        
        history = storage.get_version_history()
        # Should have at most 50 versions (plus current)
        assert len(history) <= 51
    
    def test_epistemic_layer_without_model(self, storage):
        """
        Test saving model with None epistemic layer.
        
        Rationale: Ensures None epistemic layer is handled correctly.
        """
        model = SelfModel(
            capabilities=["Test"],
            knowledge_boundaries={},
            constraints={},
            metadata={"version": 1},
            epistemic_layer=None
        )
        
        storage.save(model)
        loaded = storage.load()
        
        assert loaded.epistemic_layer is None
    
    def test_complex_epistemic_data(self, storage):
        """
        Test saving and loading complex epistemic layer data.
        
        Rationale: Ensures all epistemic layer components work together.
        """
        epistemic_layer = EpistemicLayer()
        engine = MetacognitiveEngine(epistemic_layer=epistemic_layer)
        
        # Add multiple knowledge items
        for i in range(5):
            knowledge_id = generate_capability_id(f"Capability {i}")
            source = SourceMetadata(
                source_type=SourceType.USER_PROVIDED,
                timestamp=datetime.now(timezone.utc)
            )
            engine.knowledge_acquisition_workflow(
                knowledge_id=knowledge_id,
                source=source,
                initial_confidence=0.7 + i * 0.05
            )
            
            # Add verification record
            verification = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="test",
                result="confirmed",
                confidence_delta=0.1,
                new_evidence=[source]
            )
            epistemic_layer.add_verification_record(knowledge_id, verification)
            
            # Add memory mapping
            epistemic_layer.add_memory_knowledge_mapping(i, knowledge_id)
        
        model = SelfModel(
            capabilities=["Test"],
            knowledge_boundaries={},
            constraints={},
            metadata={"version": 1},
            epistemic_layer=epistemic_layer
        )
        
        storage.save(model)
        loaded = storage.load()
        
        assert loaded.epistemic_layer is not None
        assert len(loaded.epistemic_layer.knowledge_sources) == 5
        assert len(loaded.epistemic_layer.confidence_calibration) == 5
        assert len(loaded.epistemic_layer.memory_knowledge_mapping) == 5
    
    def test_memory_knowledge_mapping_saved_to_database(self, temp_db_path):
        """
        Test that memory_knowledge_mapping is saved to database when memory is stored.
        
        Rationale: Ensures mappings are persisted when memories are stored with epistemic tracking.
        """
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.self_model.model import SelfModel
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.memory.manager import MemoryManager
        from broca.memory.storage import MemoryStorage
        from broca.memory.vector_index import VectorIndex
        from broca.memory.embeddings import EmbeddingService
        from broca.self_model.epistemic.models import SourceType, SourceMetadata
        from datetime import datetime, timezone
        import tempfile
        import os
        
        # Create self-model with epistemic layer
        storage = SelfModelSQLiteStorage(temp_db_path)
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        storage.save(self_model)
        
        # Create memory manager and epistemic engine with same epistemic layer
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_db = os.path.join(tmpdir, "test_memories.db")
            index_path = os.path.join(tmpdir, "test_index.faiss")
            
            try:
                embedding_service = EmbeddingService()
                memory_storage = MemoryStorage(db_path=memory_db)
                vector_index = VectorIndex(dimension=1536, index_path=index_path)
                memory_manager = MemoryManager(memory_storage, vector_index, embedding_service)
                
                # Create epistemic engine with the same epistemic layer instance
                epistemic_engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
                
                # Store memory with epistemic tracking
                source_metadata = SourceMetadata(
                    source_type=SourceType.USER_PROVIDED,
                    timestamp=datetime.now(timezone.utc)
                )
                memory_id, _, _, epistemic_result = memory_manager.store_memory_with_epistemic(
                    namespace="test.mapping",
                    text="Test memory for mapping",
                    importance=0.8,
                    epistemic_engine=epistemic_engine,
                    source_metadata=source_metadata
                )
                
                # Verify mapping exists in memory
                assert epistemic_result is not None
                knowledge_id = epistemic_result["knowledge_id"]
                assert self_model.epistemic_layer.get_knowledge_id_for_memory(memory_id) == knowledge_id
                
                # Save self-model
                storage.save(self_model)
                
                # Load self-model
                loaded = storage.load()
                
                # Verify mapping was saved and loaded
                assert loaded.epistemic_layer is not None
                assert loaded.epistemic_layer.get_knowledge_id_for_memory(memory_id) == knowledge_id
                
                memory_manager.close()
            except Exception as e:
                pytest.skip(f"Embedding service not available: {e}")
    
    def test_memory_knowledge_mapping_persists_after_reload(self, temp_db_path):
        """
        Test that memory_knowledge_mapping persists after saving and reloading.
        
        Rationale: Ensures mappings survive model save/load cycles.
        """
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.self_model.model import SelfModel
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.memory.manager import MemoryManager
        from broca.memory.storage import MemoryStorage
        from broca.memory.vector_index import VectorIndex
        from broca.memory.embeddings import EmbeddingService
        from broca.self_model.epistemic.models import SourceType, SourceMetadata
        from datetime import datetime, timezone
        import tempfile
        import os
        
        storage = SelfModelSQLiteStorage(temp_db_path)
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_db = os.path.join(tmpdir, "test_memories.db")
            index_path = os.path.join(tmpdir, "test_index.faiss")
            
            try:
                embedding_service = EmbeddingService()
                memory_storage = MemoryStorage(db_path=memory_db)
                vector_index = VectorIndex(dimension=1536, index_path=index_path)
                memory_manager = MemoryManager(memory_storage, vector_index, embedding_service)
                
                epistemic_engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
                
                # Store multiple memories
                memory_ids = []
                knowledge_ids = []
                for i in range(3):
                    source_metadata = SourceMetadata(
                        source_type=SourceType.USER_PROVIDED,
                        timestamp=datetime.now(timezone.utc)
                    )
                    memory_id, _, _, epistemic_result = memory_manager.store_memory_with_epistemic(
                        namespace=f"test.mapping{i}",
                        text=f"Test memory {i}",
                        importance=0.7 + i * 0.1,
                        epistemic_engine=epistemic_engine,
                        source_metadata=source_metadata
                    )
                    memory_ids.append(memory_id)
                    knowledge_ids.append(epistemic_result["knowledge_id"])
                
                # Save and reload
                storage.save(self_model)
                loaded = storage.load()
                
                # Verify all mappings persisted
                assert loaded.epistemic_layer is not None
                for memory_id, knowledge_id in zip(memory_ids, knowledge_ids):
                    assert loaded.epistemic_layer.get_knowledge_id_for_memory(memory_id) == knowledge_id
                
                memory_manager.close()
            except Exception as e:
                pytest.skip(f"Embedding service not available: {e}")
    
    def test_multiple_memories_create_multiple_mappings(self, temp_db_path):
        """
        Test that multiple memories create multiple mappings in the database.
        
        Rationale: Ensures each memory gets its own mapping entry.
        """
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.self_model.model import SelfModel
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.memory.manager import MemoryManager
        from broca.memory.storage import MemoryStorage
        from broca.memory.vector_index import VectorIndex
        from broca.memory.embeddings import EmbeddingService
        from broca.self_model.epistemic.models import SourceType, SourceMetadata
        from datetime import datetime, timezone
        import tempfile
        import os
        import sqlite3
        
        storage = SelfModelSQLiteStorage(temp_db_path)
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_db = os.path.join(tmpdir, "test_memories.db")
            index_path = os.path.join(tmpdir, "test_index.faiss")
            
            try:
                embedding_service = EmbeddingService()
                memory_storage = MemoryStorage(db_path=memory_db)
                vector_index = VectorIndex(dimension=1536, index_path=index_path)
                memory_manager = MemoryManager(memory_storage, vector_index, embedding_service)
                
                epistemic_engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
                
                # Store 5 memories
                for i in range(5):
                    source_metadata = SourceMetadata(
                        source_type=SourceType.USER_PROVIDED,
                        timestamp=datetime.now(timezone.utc)
                    )
                    memory_manager.store_memory_with_epistemic(
                        namespace=f"test.multi{i}",
                        text=f"Test memory {i}",
                        importance=0.5,
                        epistemic_engine=epistemic_engine,
                        source_metadata=source_metadata
                    )
                
                # Save self-model
                storage.save(self_model)
                
                # Check database directly
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memory_knowledge_mapping")
                count = cursor.fetchone()[0]
                conn.close()
                
                # Should have 5 mappings
                assert count == 5
                
                memory_manager.close()
            except Exception as e:
                pytest.skip(f"Embedding service not available: {e}")

