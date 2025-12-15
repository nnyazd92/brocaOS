"""
SourceValidator for assessing reliability of knowledge sources.

Tracks tool reliability, memory quality, and validates logical inferences.
"""

from __future__ import annotations

from typing import Dict, List, DefaultDict
from collections import defaultdict
import logging

from .models import SourceMetadata, SourceType

logger = logging.getLogger(__name__)


class SourceValidator:
    """
    Validates and assesses reliability of knowledge sources.
    
    Tracks:
    - Tool reliability: Success rates by tool type
    - Memory quality: Consistency of memory retrievals
    - Logical validity: Validation of inference rules
    """
    
    def __init__(self) -> None:
        """Initialize source validator."""
        # Tool execution tracking: tool_type -> [success, failure, ...]
        self._tool_executions: DefaultDict[str, List[bool]] = defaultdict(list)
        
        # Memory retrieval tracking: memory_id -> [consistent, inconsistent, ...]
        self._memory_retrievals: DefaultDict[int, List[bool]] = defaultdict(list)
    
    def record_tool_execution(self, tool_type: str, success: bool) -> None:
        """
        Record a tool execution result.
        
        Args:
            tool_type: Type of tool (e.g., "terminal", "web_search")
            success: Whether execution was successful
        """
        self._tool_executions[tool_type].append(success)
        
        # Keep only last 1000 executions per tool
        if len(self._tool_executions[tool_type]) > 1000:
            self._tool_executions[tool_type] = self._tool_executions[tool_type][-1000:]
    
    def assess_tool_reliability(self, tool_type: str) -> float:
        """
        Assess reliability of a tool based on execution history.
        
        Args:
            tool_type: Type of tool to assess
            
        Returns:
            Reliability score (0-1)
        """
        executions = self._tool_executions.get(tool_type, [])
        
        if not executions:
            # No data - return neutral reliability
            return 0.5
        
        success_count = sum(1 for success in executions if success)
        total_count = len(executions)
        
        success_rate = success_count / total_count if total_count > 0 else 0.5
        
        # Adjust for sample size (more samples = more reliable estimate)
        # Use a simple confidence adjustment
        sample_size_factor = min(1.0, total_count / 20.0)  # Full confidence at 20+ samples
        reliability = 0.5 + (success_rate - 0.5) * sample_size_factor
        
        # For high success rates with sufficient samples, return higher reliability
        if success_rate >= 0.9 and total_count >= 10:
            reliability = success_rate * 0.95  # Slight discount for uncertainty
        
        return max(0.0, min(1.0, reliability))
    
    def record_memory_retrieval(self, memory_id: int, consistent: bool) -> None:
        """
        Record a memory retrieval result.
        
        Args:
            memory_id: ID of memory
            consistent: Whether retrieval was consistent with previous retrievals
        """
        self._memory_retrievals[memory_id].append(consistent)
        
        # Keep only last 100 retrievals per memory
        if len(self._memory_retrievals[memory_id]) > 100:
            self._memory_retrievals[memory_id] = self._memory_retrievals[memory_id][-100:]
    
    def assess_memory_quality(self, memory_id: int) -> float:
        """
        Assess quality of a memory based on retrieval consistency.
        
        Args:
            memory_id: ID of memory to assess
            
        Returns:
            Quality score (0-1)
        """
        retrievals = self._memory_retrievals.get(memory_id, [])
        
        if not retrievals:
            # No data - return neutral quality
            return 0.5
        
        consistent_count = sum(1 for consistent in retrievals if consistent)
        total_count = len(retrievals)
        
        consistency_rate = consistent_count / total_count if total_count > 0 else 0.5
        
        # Adjust for sample size
        sample_size_factor = min(1.0, total_count / 10.0)  # Full confidence at 10+ retrievals
        quality = 0.5 + (consistency_rate - 0.5) * sample_size_factor
        
        # For high consistency with sufficient samples, return higher quality
        if consistency_rate >= 0.8 and total_count >= 5:
            quality = consistency_rate * 0.95  # Slight discount for uncertainty
        
        return max(0.0, min(1.0, quality))
    
    def check_logical_validity(self, source: SourceMetadata) -> bool:
        """
        Check if a logical inference source is valid.
        
        Args:
            source: Source metadata to validate
            
        Returns:
            True if valid, False otherwise
        """
        if source.source_type != SourceType.LOGICAL_INFERENCE:
            # Non-inference sources don't need logical validation
            return True
        
        # Check inference type (normalize common variations)
        inference_type = source.inference_type
        if inference_type == "deduction":
            inference_type = "deductive"
        elif inference_type == "induction":
            inference_type = "inductive"
        elif inference_type == "abduction":
            inference_type = "abductive"
        elif inference_type == "consistency_check":
            # consistency_check is a special case - it's not really a logical inference
            # but rather a validation check, so we accept it as valid
            # It uses logical_strength to represent the validation result
            return True
        
        if inference_type not in ["deductive", "inductive", "abductive"]:
            logger.warning(f"Unknown inference type: {source.inference_type}")
            return False
        
        # Check logical strength
        if source.logical_strength is not None:
            if not 0.0 <= source.logical_strength <= 1.0:
                return False
            
            # Very weak inferences may be flagged
            if source.logical_strength < 0.1:
                logger.warning("Very weak logical inference detected")
                return False
        
        # Check that premises are provided for inference (warning but not invalid)
        if source.premise_ids is None or len(source.premise_ids) == 0:
            logger.warning("Logical inference without premises")
            # Don't invalidate, but log warning
        
        return True
    
    def assess_source_reliability(self, source: SourceMetadata) -> float:
        """
        Assess overall reliability of a source.
        
        Args:
            source: Source metadata to assess
            
        Returns:
            Reliability score (0-1)
        """
        if source.source_type == SourceType.TOOL_MEDIATED_VERIFICATION:
            if source.tool_type:
                base_reliability = self.assess_tool_reliability(source.tool_type)
                # If tool has high success rate, boost reliability
                if base_reliability > 0.6:
                    return min(1.0, base_reliability * 1.1)
                return base_reliability
            else:
                return 0.5  # Default if tool type unknown
        
        elif source.source_type == SourceType.MEMORY_RETRIEVAL:
            if source.memory_id is not None:
                return self.assess_memory_quality(source.memory_id)
            else:
                return 0.5  # Default if memory ID unknown
        
        elif source.source_type == SourceType.LOGICAL_INFERENCE:
            # Logical validity check
            is_valid = self.check_logical_validity(source)
            if not is_valid:
                return 0.2  # Low reliability for invalid inferences
            
            # Use logical strength as reliability indicator
            if source.logical_strength is not None:
                return source.logical_strength
            else:
                return 0.5  # Default
        
        elif source.source_type == SourceType.USER_PROVIDED:
            # User sources: verified > unverified > contradicted
            if source.verification_status == "verified":
                return 0.9
            elif source.verification_status == "unverified":
                return 0.6
            elif source.verification_status == "contradicted":
                return 0.1
            else:
                return 0.5  # Default
        
        elif source.source_type == SourceType.EMERGENT_PATTERN:
            # Use statistical significance and predictive accuracy
            if source.statistical_significance is not None and source.predictive_accuracy is not None:
                # Combine significance and accuracy
                reliability = (source.statistical_significance + source.predictive_accuracy) / 2.0
                return max(0.0, min(1.0, reliability))
            else:
                return 0.5  # Default
        
        else:
            # Unknown source type
            return 0.5  # Default neutral reliability

