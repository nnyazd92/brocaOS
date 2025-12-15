"""
Tests for SelfModel epistemic layer integration.

Tests backward compatibility and epistemic layer functionality.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from broca.self_model.model import SelfModel
from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.epistemic.models import (
    SourceType,
    SourceMetadata,
    ConfidenceMetrics,
)
from broca.self_model.epistemic.ids import generate_capability_id


class TestSelfModelEpistemicBackwardCompatibility:
    """Test backward compatibility of SelfModel with epistemic layer."""
    
    def test_self_model_without_epistemic_layer(self):
        """Test that SelfModel works without epistemic layer (backward compatibility)."""
        model = SelfModel(
            capabilities=["Python programming"]
        )
        
        assert len(model.capabilities) == 1
        assert model.capabilities[0]["text"] == "Python programming"
        assert model.epistemic_layer is None
    
    def test_self_model_with_epistemic_layer(self):
        """Test that SelfModel can have epistemic layer."""
        epistemic = EpistemicLayer()
        model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic
        )
        
        assert model.epistemic_layer is not None
        assert isinstance(model.epistemic_layer, EpistemicLayer)
    
    def test_self_model_to_dict_without_epistemic(self):
        """Test that to_dict works without epistemic layer."""
        model = SelfModel(capabilities=["Python programming"])
        data = model.to_dict()
        
        assert "capabilities" in data
        assert "epistemic_layer" in data
        assert data["epistemic_layer"] is None
    
    def test_self_model_to_dict_with_epistemic(self):
        """Test that to_dict includes epistemic layer."""
        epistemic = EpistemicLayer()
        model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic
        )
        
        data = model.to_dict()
        
        assert "epistemic_layer" in data
        assert data["epistemic_layer"] is not None
    
    def test_self_model_from_dict_without_epistemic(self):
        """Test that from_dict works without epistemic layer (backward compatibility)."""
        data = {
            "capabilities": ["Python programming"],
            "preferences": {},
            "knowledge_boundaries": {},
            "constraints": {},
            "behavioral_patterns": [],
            "metadata": {"version": 1}
        }
        
        model = SelfModel.from_dict(data)
        
        # Capabilities are stored as dicts with "text" and "source" keys
        assert len(model.capabilities) == 1
        assert model.capabilities[0]["text"] == "Python programming"
        assert model.epistemic_layer is None
    
    def test_self_model_from_dict_with_epistemic(self):
        """Test that from_dict loads epistemic layer."""
        epistemic = EpistemicLayer()
        knowledge_id = generate_capability_id("Python programming")
        
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        epistemic.add_knowledge_source(knowledge_id, source)
        
        model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic
        )
        
        data = model.to_dict()
        loaded_model = SelfModel.from_dict(data)
        
        assert loaded_model.epistemic_layer is not None
        assert loaded_model.epistemic_layer.has_knowledge(knowledge_id)


class TestSelfModelEpistemicFunctionality:
    """Test epistemic layer functionality in SelfModel."""
    
    def test_add_epistemic_metadata_to_capability(self):
        """Test adding epistemic metadata for a capability."""
        epistemic = EpistemicLayer()
        model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic
        )
        
        knowledge_id = generate_capability_id("Python programming")
        source = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="terminal"
        )
        model.epistemic_layer.add_knowledge_source(knowledge_id, source)
        
        metrics = ConfidenceMetrics(overall_confidence=0.9)
        model.epistemic_layer.add_confidence_metrics(knowledge_id, metrics)
        
        assert model.epistemic_layer.get_knowledge_source(knowledge_id) == source
        assert model.epistemic_layer.get_confidence_metrics(knowledge_id).overall_confidence == 0.9
    
    def test_merge_self_models_with_epistemic(self):
        """Test merging self-models with epistemic layers."""
        epistemic1 = EpistemicLayer()
        model1 = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic1
        )
        
        epistemic2 = EpistemicLayer()
        model2 = SelfModel(
            capabilities=["JavaScript programming"],
            epistemic_layer=epistemic2
        )
        
        merged = model1.merge(model2, strategy="append")
        
        # Capabilities are stored as dicts with "text" and "source" keys
        capability_texts = [cap.get("text", str(cap)) for cap in merged.capabilities]
        assert "Python programming" in capability_texts
        assert "JavaScript programming" in capability_texts
        # Epistemic layers should be merged or one should be kept
        assert merged.epistemic_layer is not None
    
    def test_validate_self_model_with_epistemic(self):
        """Test that validation works with epistemic layer."""
        epistemic = EpistemicLayer()
        model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic
        )
        
        is_valid, errors = model.validate()
        
        assert is_valid
        assert len(errors) == 0


class TestSelfModelDefaultInitialization:
    """Test default self-model initialization with epistemic layer."""
    
    def test_create_default_initializes_epistemic_layer(self):
        """
        Test that SelfModel.create_default() initializes with EpistemicLayer() by default.
        
        Rationale: Ensures new self-models have epistemic tracking enabled by default.
        """
        model = SelfModel.create_default()
        
        assert model.epistemic_layer is not None
        assert isinstance(model.epistemic_layer, EpistemicLayer)
    
    def test_create_default_backward_compatibility_explicit_none(self):
        """
        Test that existing code can still create models without epistemic layer explicitly.
        
        Rationale: Ensures backward compatibility - code that explicitly sets epistemic_layer=None still works.
        """
        # This should still work - explicit None should be respected
        model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=None
        )
        
        assert model.epistemic_layer is None
    
    def test_loading_old_self_models_without_epistemic(self):
        """
        Test that loading old self-models (without epistemic layer) still works.
        
        Rationale: Ensures backward compatibility when loading existing self-model JSON files.
        """
        # Simulate old self-model data without epistemic_layer field
        data = {
            "capabilities": ["Python programming"],
            "preferences": {"response_style": "helpful"},
            "knowledge_boundaries": {},
            "constraints": {},
            "behavioral_patterns": [],
            "metadata": {"version": 1, "created_at": "2024-01-01T00:00:00+00:00"}
        }
        
        model = SelfModel.from_dict(data)
        
        # Capabilities are stored as dicts with "text" and "source" keys
        assert len(model.capabilities) == 1
        assert model.capabilities[0]["text"] == "Python programming"
        # Old models without epistemic_layer should load with None
        assert model.epistemic_layer is None
    
    def test_loading_old_self_models_with_explicit_none(self):
        """
        Test that loading self-models with explicit epistemic_layer: null works.
        
        Rationale: Ensures backward compatibility when epistemic_layer is explicitly null in JSON.
        """
        data = {
            "capabilities": ["Python programming"],
            "preferences": {},
            "knowledge_boundaries": {},
            "constraints": {},
            "behavioral_patterns": [],
            "metadata": {"version": 1},
            "epistemic_layer": None
        }
        
        model = SelfModel.from_dict(data)
        
        # Capabilities are stored as dicts with "text" and "source" keys
        assert len(model.capabilities) == 1
        assert model.capabilities[0]["text"] == "Python programming"
        assert model.epistemic_layer is None


class TestEpistemicLayerAutoInitialization:
    """Test automatic initialization of epistemic layer for existing models."""
    
    def test_auto_initialize_epistemic_layer_for_existing_model(self, tmp_path):
        """
        Test that _initialize_self_model() auto-initializes epistemic layer for existing models.
        
        Rationale: Ensures existing self-models without epistemic layer get one initialized
        when enable_epistemic is True.
        """
        import tempfile
        import os
        from broca.self_model.model import SelfModel
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.main_repl import _initialize_self_model
        from broca.config import config
        
        # Create a model without epistemic layer
        model_without_epistemic = SelfModel(
            capabilities=["Python programming", "Code analysis"],
            knowledge_boundaries={"training_cutoff": "unknown"},
            constraints={"cannot_execute_arbitrary_code": "limited to whitelisted commands"},
            epistemic_layer=None
        )
        
        # Save it to a temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_self_model.db")
            storage = SelfModelSQLiteStorage(db_path=db_path)
            storage.save(model_without_epistemic)
            
            # Temporarily override config
            original_enabled = config.self_model.enabled
            original_enable_epistemic = config.self_model.enable_epistemic
            
            try:
                config.self_model.enabled = True
                config.self_model.enable_epistemic = True
                
                # Initialize self-model (should auto-initialize epistemic layer)
                # Pass db_path directly to avoid config issues
                consistency_layer, loaded_model, epistemic_engine = _initialize_self_model(storage_path_override=db_path)
                
                # Verify epistemic layer was initialized
                assert loaded_model is not None
                assert loaded_model.epistemic_layer is not None
                assert epistemic_engine is not None
                
                # Verify epistemic layer has knowledge items for existing data
                from broca.self_model.epistemic.ids import (
                    generate_capability_id,
                    generate_constraint_id,
                    generate_knowledge_boundary_id,
                )
                
                # Check capabilities
                for cap_dict in model_without_epistemic.capabilities:
                    capability = cap_dict.get("text", str(cap_dict))
                    knowledge_id = generate_capability_id(capability)
                    assert loaded_model.epistemic_layer.has_knowledge(knowledge_id)
                
                # Check knowledge boundaries
                for key, value_dict in model_without_epistemic.knowledge_boundaries.items():
                    value = value_dict.get("value", str(value_dict))
                    knowledge_id = generate_knowledge_boundary_id(key, value)
                    assert loaded_model.epistemic_layer.has_knowledge(knowledge_id)
                
                # Check constraints
                for key, value_dict in model_without_epistemic.constraints.items():
                    value = value_dict.get("value", str(value_dict))
                    knowledge_id = generate_constraint_id(key, value)
                    assert loaded_model.epistemic_layer.has_knowledge(knowledge_id)
                
            finally:
                # Restore config
                config.self_model.enabled = original_enabled
                config.self_model.enable_epistemic = original_enable_epistemic
    
    def test_auto_initialization_respects_enable_epistemic_flag(self, tmp_path):
        """
        Test that auto-initialization respects enable_epistemic config flag.
        
        Rationale: Ensures epistemic layer is not initialized if enable_epistemic is False.
        """
        import tempfile
        import os
        from broca.self_model.model import SelfModel
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.main_repl import _initialize_self_model
        from broca.config import config
        
        # Create a model without epistemic layer
        model_without_epistemic = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=None
        )
        
        # Save it to a temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_self_model.db")
            storage = SelfModelSQLiteStorage(db_path=db_path)
            storage.save(model_without_epistemic)
            
            # Temporarily override config
            original_enabled = config.self_model.enabled
            original_enable_epistemic = config.self_model.enable_epistemic
            
            try:
                config.self_model.enabled = True
                
                # Initialize self-model (should NOT auto-initialize epistemic layer)
                # Pass db_path and enable_epistemic directly to avoid config issues
                consistency_layer, loaded_model, epistemic_engine = _initialize_self_model(
                    storage_path_override=db_path,
                    enable_epistemic_override=False
                )
                
                # Verify epistemic layer was NOT initialized
                assert loaded_model is not None
                assert loaded_model.epistemic_layer is None
                assert epistemic_engine is None
                
            finally:
                # Restore config
                config.self_model.enabled = original_enabled
                config.self_model.enable_epistemic = original_enable_epistemic
    
    def test_auto_initialization_preserves_existing_epistemic_layer(self, tmp_path):
        """
        Test that auto-initialization doesn't modify existing epistemic layer.
        
        Rationale: Ensures models with existing epistemic layer are not modified.
        """
        import tempfile
        import os
        from broca.self_model.model import SelfModel
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.main_repl import _initialize_self_model
        from broca.config import config
        
        # Create a model WITH epistemic layer
        existing_epistemic = EpistemicLayer()
        model_with_epistemic = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=existing_epistemic
        )
        
        # Add some existing knowledge
        from broca.self_model.epistemic.ids import generate_capability_id
        from broca.self_model.epistemic.models import SourceMetadata, SourceType, ConfidenceMetrics
        from datetime import datetime, timezone
        
        knowledge_id = generate_capability_id("Python programming")
        source = SourceMetadata(source_type=SourceType.USER_PROVIDED)
        metrics = ConfidenceMetrics(overall_confidence=0.9)
        existing_epistemic.add_knowledge_source(knowledge_id, source)
        existing_epistemic.add_confidence_metrics(knowledge_id, metrics)
        
        # Save it to a temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_self_model.db")
            storage = SelfModelSQLiteStorage(db_path=db_path)
            storage.save(model_with_epistemic)
            
            # Temporarily override config
            original_enabled = config.self_model.enabled
            original_enable_epistemic = config.self_model.enable_epistemic
            
            try:
                config.self_model.enabled = True
                config.self_model.enable_epistemic = True
                
                # Initialize self-model (should preserve existing epistemic layer)
                # Pass db_path directly to avoid config issues
                consistency_layer, loaded_model, epistemic_engine = _initialize_self_model(storage_path_override=db_path)
                
                # Verify epistemic layer was preserved
                assert loaded_model is not None
                assert loaded_model.epistemic_layer is not None
                assert epistemic_engine is not None
                
                # Verify existing knowledge is still there
                assert loaded_model.epistemic_layer.has_knowledge(knowledge_id)
                loaded_metrics = loaded_model.epistemic_layer.get_confidence_metrics(knowledge_id)
                assert loaded_metrics is not None
                assert loaded_metrics.overall_confidence == 0.9
                
            finally:
                # Restore config
                config.self_model.enabled = original_enabled
                config.self_model.enable_epistemic = original_enable_epistemic
    
    def test_backfill_is_idempotent(self, tmp_path):
        """
        Test that backfilling is idempotent (can be called multiple times safely).
        
        Rationale: Ensures backfilling doesn't create duplicate knowledge items.
        """
        import tempfile
        import os
        from broca.self_model.model import SelfModel
        from broca.self_model.storage import SelfModelSQLiteStorage
        from broca.main_repl import _initialize_self_model, _backfill_epistemic_layer
        from broca.config import config
        
        # Create a model without epistemic layer
        model_without_epistemic = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=None
        )
        
        # Save it to a temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_self_model.db")
            storage = SelfModelSQLiteStorage(db_path=db_path)
            storage.save(model_without_epistemic)
            
            # Temporarily override config
            original_enabled = config.self_model.enabled
            original_enable_epistemic = config.self_model.enable_epistemic
            
            try:
                config.self_model.enabled = True
                config.self_model.enable_epistemic = True
                
                # Initialize self-model (first backfill)
                # Pass db_path directly to avoid config issues
                consistency_layer, loaded_model, epistemic_engine = _initialize_self_model(storage_path_override=db_path)
                
                # Count knowledge items after first backfill
                from broca.self_model.epistemic.ids import generate_capability_id
                capability_id = generate_capability_id("Python programming")
                
                initial_capability_count = len(loaded_model.epistemic_layer.knowledge_sources)
                
                # Call backfill again (should be idempotent)
                _backfill_epistemic_layer(loaded_model, epistemic_engine)
                
                # Count knowledge items after second backfill
                final_capability_count = len(loaded_model.epistemic_layer.knowledge_sources)
                
                # Should have same count (no duplicates)
                assert final_capability_count == initial_capability_count
                
                # Knowledge items should still exist
                assert loaded_model.epistemic_layer.has_knowledge(capability_id)
                # Note: preferences attribute was removed from SelfModel - no preference_id to check
                
            finally:
                # Restore config
                config.self_model.enabled = original_enabled
                config.self_model.enable_epistemic = original_enable_epistemic


class TestQuerySelfModelEpistemicLoading:
    """Test that query_self_model tool loads epistemic_layer from database."""
    
    def test_query_self_model_loads_epistemic_layer(self, tmp_path):
        """
        Test that query_self_model loads epistemic_layer if data exists in database.
        
        Rationale: Ensures query tool can access epistemic data even if it wasn't loaded initially.
        """
        from broca.self_model.storage import create_storage
        from broca.self_model.layer import ConsistencyLayer
        from broca.self_model.consistency import ConsistencyChecker
        from broca.self_model.updater import SelfModelUpdater
        from broca.tools.self_model_tool import QuerySelfModelTool
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceType, SourceMetadata
        from broca.self_model.epistemic.ids import generate_capability_id
        import os
        
        # Create storage
        db_path = os.path.join(tmp_path, "test_model.db")
        storage = create_storage(storage_type="sqlite", storage_path=db_path)
        
        # Create and save self-model with epistemic layer containing knowledge
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
        knowledge_id = generate_capability_id("Python programming")
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        engine.knowledge_acquisition_workflow(knowledge_id, source, 0.5)
        
        # Save model
        storage.save(self_model)
        
        # Create a NEW self-model instance without epistemic_layer (simulating stale instance)
        loaded_model = storage.load()
        # Manually set epistemic_layer to None to simulate the problem
        loaded_model.epistemic_layer = None
        
        # Create consistency layer with the model that has None epistemic_layer
        checker = ConsistencyChecker()
        updater = SelfModelUpdater()
        consistency_layer = ConsistencyLayer(
            self_model=loaded_model,
            storage=storage,
            checker=checker,
            updater=updater
        )
        
        # Create query tool
        query_tool = QuerySelfModelTool(consistency_layer)
        
        # Query epistemic aspect - should load epistemic_layer on demand
        result = query_tool.execute(aspect="epistemic")
        
        # Verify epistemic_layer was loaded
        assert result["success"] is True
        assert result.get("epistemic_layer") is not None
        assert result.get("total_knowledge_items", 0) > 0
        
        # Verify the self-model in consistency layer now has epistemic_layer
        updated_model = consistency_layer.get_self_model()
        assert updated_model.epistemic_layer is not None
        assert updated_model.epistemic_layer.has_knowledge(knowledge_id)
    
    def test_consistency_layer_refreshes_epistemic_layer(self, tmp_path):
        """
        Test that consistency layer refreshes epistemic layer when self-model is accessed.
        
        Rationale: Ensures get_self_model() loads epistemic_layer if missing but data exists.
        """
        from broca.self_model.storage import create_storage
        from broca.self_model.layer import ConsistencyLayer
        from broca.self_model.consistency import ConsistencyChecker
        from broca.self_model.updater import SelfModelUpdater
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceType, SourceMetadata
        from broca.self_model.epistemic.ids import generate_capability_id
        import os
        
        # Create storage
        db_path = os.path.join(tmp_path, "test_model.db")
        storage = create_storage(storage_type="sqlite", storage_path=db_path)
        
        # Create and save self-model with epistemic layer
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
        knowledge_id = generate_capability_id("Test capability")
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        engine.knowledge_acquisition_workflow(knowledge_id, source, 0.6)
        
        storage.save(self_model)
        
        # Load model and set epistemic_layer to None
        loaded_model = storage.load()
        loaded_model.epistemic_layer = None
        
        # Create consistency layer
        checker = ConsistencyChecker()
        updater = SelfModelUpdater()
        consistency_layer = ConsistencyLayer(
            self_model=loaded_model,
            storage=storage,
            checker=checker,
            updater=updater
        )
        
        # Initially, epistemic_layer is None in the loaded_model
        assert loaded_model.epistemic_layer is None
        
        # After accessing via get_self_model(), epistemic_layer should be loaded (lazy load)
        refreshed_model = consistency_layer.get_self_model()
        # After fix: should have epistemic_layer loaded from database
        assert refreshed_model.epistemic_layer is not None
        assert refreshed_model.epistemic_layer.has_knowledge(knowledge_id)
        
        # Verify it's the same instance (lazy loading updated the model)
        assert refreshed_model is consistency_layer.self_model
    
    def test_epistemic_layer_loaded_on_demand(self, tmp_path):
        """
        Test that epistemic layer is loaded on-demand if missing but data exists.
        
        Rationale: Ensures lazy loading works correctly when epistemic data exists in database.
        """
        from broca.self_model.storage import create_storage
        from broca.self_model.layer import ConsistencyLayer
        from broca.self_model.consistency import ConsistencyChecker
        from broca.self_model.updater import SelfModelUpdater
        from broca.self_model.epistemic.layer import EpistemicLayer
        from broca.self_model.epistemic.engine import MetacognitiveEngine
        from broca.self_model.epistemic.models import SourceType, SourceMetadata
        from broca.self_model.epistemic.ids import generate_capability_id, generate_constraint_id
        import os
        
        # Create storage
        db_path = os.path.join(tmp_path, "test_model.db")
        storage = create_storage(storage_type="sqlite", storage_path=db_path)
        
        # Create and save self-model with epistemic layer
        self_model = SelfModel.create_default()
        self_model.epistemic_layer = EpistemicLayer()
        
        engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
        
        # Add multiple knowledge items
        knowledge_id1 = generate_capability_id("Capability 1")
        knowledge_id2 = generate_constraint_id("constraint_key", "value")
        
        source1 = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        source2 = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        
        engine.knowledge_acquisition_workflow(knowledge_id1, source1, 0.5)
        engine.knowledge_acquisition_workflow(knowledge_id2, source2, 0.7)
        
        storage.save(self_model)
        
        # Load model and remove epistemic_layer
        loaded_model = storage.load()
        loaded_model.epistemic_layer = None
        
        # Create consistency layer
        checker = ConsistencyChecker()
        updater = SelfModelUpdater()
        consistency_layer = ConsistencyLayer(
            self_model=loaded_model,
            storage=storage,
            checker=checker,
            updater=updater
        )
        
        # Access self-model - should trigger lazy load
        model = consistency_layer.get_self_model()
        
        # After fix: epistemic_layer should be loaded with all knowledge items
        assert model.epistemic_layer is not None
        assert len(model.epistemic_layer.knowledge_sources) == 2
        assert model.epistemic_layer.has_knowledge(knowledge_id1)
        assert model.epistemic_layer.has_knowledge(knowledge_id2)

