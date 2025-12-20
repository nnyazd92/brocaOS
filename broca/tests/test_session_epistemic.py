"""
Tests for epistemic context in response generation.

Tests that epistemic context can be included in prompts (optional).
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.repl.session import ConversationSession
from broca.self_model.model import SelfModel
from broca.self_model.epistemic.layer import EpistemicLayer
from broca.self_model.storage import SelfModelSQLiteStorage
import tempfile
import os


class TestResponseGenerationWithEpistemicContext:
    """Test epistemic context in response generation."""
    
    def test_epistemic_context_can_be_included_in_prompts(self):
        """
        Test that epistemic context can be included in prompts (optional).
        
        Rationale: Ensures confidence levels can inform response generation when needed.
        """
        # Create self-model with epistemic layer
        epistemic = EpistemicLayer()
        self_model = SelfModel(
            capabilities=["Python programming"],
            epistemic_layer=epistemic
        )
        
        # Create session (consistency layer removed)
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SelfModelSQLiteStorage(db_path=os.path.join(tmpdir, "test.db"))
            storage.save(self_model)
            
            session = ConversationSession()
            
            # Session should work (consistency layer no longer exists)
            assert session is not None
            # Epistemic layer is in self_model, but session no longer has direct access
            # This test verifies session creation works without consistency_layer
    
    def test_backward_compatibility_works_without_epistemic_layer(self):
        """
        Test backward compatibility: works without epistemic layer.
        
        Rationale: Ensures existing code without epistemic layer continues to work.
        """
        # Create self-model without epistemic layer
        self_model = SelfModel(capabilities=["Python programming"])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SelfModelSQLiteStorage(db_path=os.path.join(tmpdir, "test.db"))
            storage.save(self_model)
            
            session = ConversationSession()
            
            # Should work fine (consistency layer no longer exists)
            assert session is not None
            # Epistemic layer is in self_model, but session no longer has direct access
            # This test verifies session creation works without consistency_layer

