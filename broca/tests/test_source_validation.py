"""
Tests for SourceValidator.

Tests tool reliability, memory quality, and logical validity assessment.
"""

from __future__ import annotations

import pytest

from broca.self_model.epistemic.validation import SourceValidator
from broca.self_model.epistemic.models import SourceMetadata, SourceType


class TestSourceValidatorToolReliability:
    """Test tool reliability assessment."""
    
    def test_assess_tool_reliability_high_success(self):
        """Test assessing tool with high success rate."""
        validator = SourceValidator()
        
        # Record successful tool executions
        for i in range(10):
            validator.record_tool_execution("terminal", success=True)
        
        reliability = validator.assess_tool_reliability("terminal")
        
        assert reliability > 0.8
        assert 0.0 <= reliability <= 1.0
    
    def test_assess_tool_reliability_mixed_success(self):
        """Test assessing tool with mixed success."""
        validator = SourceValidator()
        
        # Record mixed executions
        for i in range(5):
            validator.record_tool_execution("terminal", success=True)
        for i in range(5):
            validator.record_tool_execution("terminal", success=False)
        
        reliability = validator.assess_tool_reliability("terminal")
        
        assert 0.4 <= reliability <= 0.6
        assert 0.0 <= reliability <= 1.0
    
    def test_assess_tool_reliability_unknown_tool(self):
        """Test assessing unknown tool."""
        validator = SourceValidator()
        
        reliability = validator.assess_tool_reliability("unknown_tool")
        
        # Should return default/neutral reliability
        assert 0.0 <= reliability <= 1.0


class TestSourceValidatorMemoryQuality:
    """Test memory quality assessment."""
    
    def test_assess_memory_quality_consistent(self):
        """Test assessing memory with consistent retrievals."""
        validator = SourceValidator()
        
        # Record consistent retrievals
        for i in range(5):
            validator.record_memory_retrieval(123, consistent=True)
        
        quality = validator.assess_memory_quality(123)
        
        assert quality > 0.7
        assert 0.0 <= quality <= 1.0
    
    def test_assess_memory_quality_inconsistent(self):
        """Test assessing memory with inconsistent retrievals."""
        validator = SourceValidator()
        
        # Record inconsistent retrievals
        for i in range(3):
            validator.record_memory_retrieval(123, consistent=True)
        for i in range(3):
            validator.record_memory_retrieval(123, consistent=False)
        
        quality = validator.assess_memory_quality(123)
        
        assert quality < 0.7
        assert 0.0 <= quality <= 1.0
    
    def test_assess_memory_quality_unknown(self):
        """Test assessing unknown memory."""
        validator = SourceValidator()
        
        quality = validator.assess_memory_quality(999)
        
        # Should return default quality
        assert 0.0 <= quality <= 1.0


class TestSourceValidatorLogicalValidity:
    """Test logical validity checking."""
    
    def test_check_logical_validity_valid(self):
        """Test checking valid logical inference."""
        validator = SourceValidator()
        
        source = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            inference_type="deductive",
            logical_strength=0.9
        )
        
        is_valid = validator.check_logical_validity(source)
        
        assert is_valid is True
    
    def test_check_logical_validity_weak(self):
        """Test checking weak logical inference."""
        validator = SourceValidator()
        
        source = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            inference_type="inductive",
            logical_strength=0.3
        )
        
        is_valid = validator.check_logical_validity(source)
        
        # Weak inferences may still be valid but flagged
        assert isinstance(is_valid, bool)
    
    def test_check_logical_validity_non_inference(self):
        """Test checking non-inference source."""
        validator = SourceValidator()
        
        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            user_identity="developer"
        )
        
        is_valid = validator.check_logical_validity(source)
        
        # Non-inference sources don't need logical validation
        assert is_valid is True
    
    def test_check_logical_validity_consistency_check(self):
        """
        Test that consistency_check is accepted as a valid inference type.
        
        Rationale: consistency_check is used for consistency violations and should not cause warnings.
        """
        validator = SourceValidator()
        
        source = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            inference_type="consistency_check",
            logical_strength=0.7
        )
        
        is_valid = validator.check_logical_validity(source)
        
        # consistency_check should be accepted as valid
        assert is_valid is True


class TestSourceValidatorSourceReliability:
    """Test overall source reliability assessment."""
    
    def test_assess_source_reliability_tool(self):
        """Test assessing tool-mediated source."""
        validator = SourceValidator()
        
        # Record tool successes
        for i in range(10):
            validator.record_tool_execution("terminal", success=True)
        
        source = SourceMetadata(
            source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
            tool_type="terminal"
        )
        
        reliability = validator.assess_source_reliability(source)
        
        assert reliability > 0.7
        assert 0.0 <= reliability <= 1.0
    
    def test_assess_source_reliability_memory(self):
        """Test assessing memory source."""
        validator = SourceValidator()
        
        # Record memory consistency
        for i in range(5):
            validator.record_memory_retrieval(123, consistent=True)
        
        source = SourceMetadata(
            source_type=SourceType.MEMORY_RETRIEVAL,
            memory_id=123
        )
        
        reliability = validator.assess_source_reliability(source)
        
        assert reliability > 0.6
        assert 0.0 <= reliability <= 1.0
    
    def test_assess_source_reliability_user(self):
        """Test assessing user-provided source."""
        validator = SourceValidator()
        
        source = SourceMetadata(
            source_type=SourceType.USER_PROVIDED,
            user_identity="developer",
            verification_status="verified"
        )
        
        reliability = validator.assess_source_reliability(source)
        
        # Verified user sources should have high reliability
        assert reliability > 0.7
        assert 0.0 <= reliability <= 1.0

