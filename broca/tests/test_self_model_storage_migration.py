"""
Tests for self-model storage migration from JSON to SQLite.

Tests migration functionality, data preservation, and rollback capabilities.
"""

from __future__ import annotations

import pytest
import tempfile
import os
import json
import sqlite3
from pathlib import Path

from broca.self_model.model import SelfModel
from broca.self_model.storage import SelfModelStorage
from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.epistemic.models import SourceType, SourceMetadata, ConfidenceMetrics
from datetime import datetime, timezone


class TestSelfModelStorageMigration:
    """Test self-model storage migration from JSON to SQLite."""
    
    @pytest.fixture
    def sample_self_model(self):
        """Create a sample self-model with epistemic layer for testing."""
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.ids import generate_capability_id
        
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
            capabilities=["Test capability"],
            knowledge_boundaries={"test": "boundary"},
            constraints={"test": "constraint"},
            metadata={"version": 1, "test": "metadata"},
            epistemic_layer=epistemic_layer
        )
        
        return model
    
    @pytest.fixture
    def temp_json_file(self, sample_self_model):
        """Create a temporary JSON file with self-model data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name
            storage = SelfModelStorage(storage_path=json_path)
            storage.save(sample_self_model)
            yield json_path
            # Cleanup
            if os.path.exists(json_path):
                os.unlink(json_path)
    
    def test_migrate_json_to_sqlite(self, temp_json_file, sample_self_model):
        """
        Test basic migration from JSON to SQLite.
        
        Rationale: Ensures migration script can convert JSON to SQLite format.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name
        
        try:
            # Import migration function (will be created)
            from broca.self_model.migrate_to_sqlite import migrate_json_to_sqlite
            
            # Run migration
            migrate_json_to_sqlite(
                json_path=temp_json_file,
                sqlite_path=sqlite_path,
                backup_json=False
            )
            
            # Verify SQLite file exists
            assert os.path.exists(sqlite_path)
            
            # Verify we can load from SQLite
            from broca.self_model.storage import SelfModelSQLiteStorage
            sqlite_storage = SelfModelSQLiteStorage(db_path=sqlite_path)
            loaded_model = sqlite_storage.load()
            
            assert loaded_model is not None
            assert loaded_model.capabilities == sample_self_model.capabilities
            
        finally:
            if os.path.exists(sqlite_path):
                os.unlink(sqlite_path)
    
    def test_migrate_preserves_all_data(self, temp_json_file, sample_self_model):
        """
        Test that migration preserves all self-model data.
        
        Rationale: Ensures no data loss during migration.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name
        
        try:
            from broca.self_model.migrate_to_sqlite import migrate_json_to_sqlite
            from broca.self_model.storage import SelfModelSQLiteStorage
            
            migrate_json_to_sqlite(
                json_path=temp_json_file,
                sqlite_path=sqlite_path,
                backup_json=False
            )
            
            sqlite_storage = SelfModelSQLiteStorage(db_path=sqlite_path)
            loaded_model = sqlite_storage.load()
            
            # Verify all fields preserved
            assert loaded_model.capabilities == sample_self_model.capabilities
            assert loaded_model.knowledge_boundaries == sample_self_model.knowledge_boundaries
            assert loaded_model.constraints == sample_self_model.constraints
            assert loaded_model.metadata["version"] == sample_self_model.metadata["version"]
            
        finally:
            if os.path.exists(sqlite_path):
                os.unlink(sqlite_path)
    
    def test_migrate_epistemic_layer(self, temp_json_file, sample_self_model):
        """
        Test that migration preserves epistemic layer data.
        
        Rationale: Ensures epistemic layer is fully migrated to SQLite.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name
        
        try:
            from broca.self_model.migrate_to_sqlite import migrate_json_to_sqlite
            from broca.self_model.storage import SelfModelSQLiteStorage
            
            migrate_json_to_sqlite(
                json_path=temp_json_file,
                sqlite_path=sqlite_path,
                backup_json=False
            )
            
            sqlite_storage = SelfModelSQLiteStorage(db_path=sqlite_path)
            loaded_model = sqlite_storage.load()
            
            # Verify epistemic layer exists
            assert loaded_model.epistemic_layer is not None
            
            # Verify knowledge sources
            original_sources = sample_self_model.epistemic_layer.knowledge_sources
            loaded_sources = loaded_model.epistemic_layer.knowledge_sources
            assert len(loaded_sources) == len(original_sources)
            
            # Verify confidence calibration
            original_metrics = sample_self_model.epistemic_layer.confidence_calibration
            loaded_metrics = loaded_model.epistemic_layer.confidence_calibration
            assert len(loaded_metrics) == len(original_metrics)
            
            # Verify memory mapping
            original_mapping = sample_self_model.epistemic_layer.memory_knowledge_mapping
            loaded_mapping = loaded_model.epistemic_layer.memory_knowledge_mapping
            assert loaded_mapping == original_mapping
            
        finally:
            if os.path.exists(sqlite_path):
                os.unlink(sqlite_path)
    
    def test_migrate_version_history(self, temp_json_file):
        """
        Test that migration preserves version history.
        
        Rationale: Ensures version history is migrated correctly.
        """
        # Create JSON with version history
        with open(temp_json_file, 'r') as f:
            json_data = json.load(f)
        
        # Add version history
        json_data["version_history"] = [
            {
                "version": 1,
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "model": json_data["current"]
            }
        ]
        
        with open(temp_json_file, 'w') as f:
            json.dump(json_data, f)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name
        
        try:
            from broca.self_model.migrate_to_sqlite import migrate_json_to_sqlite
            from broca.self_model.storage import SelfModelSQLiteStorage
            
            migrate_json_to_sqlite(
                json_path=temp_json_file,
                sqlite_path=sqlite_path,
                backup_json=False
            )
            
            sqlite_storage = SelfModelSQLiteStorage(db_path=sqlite_path)
            history = sqlite_storage.get_version_history()
            
            assert len(history) >= 1
            
        finally:
            if os.path.exists(sqlite_path):
                os.unlink(sqlite_path)
    
    def test_rollback_on_migration_failure(self, temp_json_file):
        """
        Test that migration handles failures gracefully.
        
        Rationale: Ensures migration doesn't corrupt data on failure.
        """
        # Create invalid JSON file
        with open(temp_json_file, 'w') as f:
            f.write("invalid json content {")
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name
        
        try:
            from broca.self_model.migrate_to_sqlite import migrate_json_to_sqlite
            
            # Should raise an exception
            with pytest.raises(Exception):
                migrate_json_to_sqlite(
                    json_path=temp_json_file,
                    sqlite_path=sqlite_path,
                    backup_json=False
                )
            
            # SQLite file should not exist or be empty
            if os.path.exists(sqlite_path):
                assert os.path.getsize(sqlite_path) == 0 or not os.path.exists(sqlite_path)
            
        finally:
            if os.path.exists(sqlite_path):
                os.unlink(sqlite_path)
    
    def test_load_from_sqlite_after_migration(self, temp_json_file, sample_self_model):
        """
        Test that we can load self-model from SQLite after migration.
        
        Rationale: Ensures SQLite storage works correctly after migration.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name
        
        try:
            from broca.self_model.migrate_to_sqlite import migrate_json_to_sqlite
            from broca.self_model.storage import SelfModelSQLiteStorage
            
            # Migrate
            migrate_json_to_sqlite(
                json_path=temp_json_file,
                sqlite_path=sqlite_path,
                backup_json=False
            )
            
            # Load from SQLite
            sqlite_storage = SelfModelSQLiteStorage(db_path=sqlite_path)
            loaded_model = sqlite_storage.load()
            
            # Verify we can save and reload
            loaded_model.metadata["version"] = 2
            sqlite_storage.save(loaded_model)
            
            reloaded = sqlite_storage.load()
            assert reloaded.metadata["version"] == 2
            
        finally:
            if os.path.exists(sqlite_path):
                os.unlink(sqlite_path)

