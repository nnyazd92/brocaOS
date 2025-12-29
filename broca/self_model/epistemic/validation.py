"""
SourceValidator for assessing reliability of knowledge sources.

Tracks tool reliability, memory quality, and validates logical inferences.
"""

from __future__ import annotations

from typing import Dict, List, DefaultDict, Any, Tuple
from collections import defaultdict
import logging

from .models import SourceMetadata, SourceType

logger = logging.getLogger(__name__)

# Import data quality utilities for Bayesian priors
try:
    from ...internal_sensing.data_quality import (
        bayesian_reliability_estimate,
        DataQuality,
        assess_data_quality,
    )
    HAS_DATA_QUALITY = True
except ImportError:
    HAS_DATA_QUALITY = False
    logger.warning("Data quality module not available, using fallback methods")


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
    
    def assess_tool_reliability(self, tool_type: str, return_metadata: bool = False) -> float | Dict[str, Any]:
        """
        Assess reliability of a tool based on execution history using Bayesian estimation.
        
        Args:
            tool_type: Type of tool to assess
            return_metadata: If True, return full metadata including confidence intervals
            
        Returns:
            Reliability score (0-1) if return_metadata=False, or dict with metadata if True
        """
        executions = self._tool_executions.get(tool_type, [])
        
        if not executions:
            # No data - use Bayesian prior (Jeffreys prior: Beta(0.5, 0.5))
            if HAS_DATA_QUALITY and return_metadata:
                result = bayesian_reliability_estimate(0, 0, prior_alpha=0.5, prior_beta=0.5)
                return result
            elif HAS_DATA_QUALITY:
                result = bayesian_reliability_estimate(0, 0, prior_alpha=0.5, prior_beta=0.5)
                return result["reliability"]  # Return mean from prior
            else:
                # Fallback: return 0.5 with high uncertainty indicator
                if return_metadata:
                    return {
                        "reliability": 0.5,
                        "confidence_interval": (0.1, 0.9),
                        "sample_size": 0,
                        "data_quality": "missing",
                        "uncertainty": 0.9,
                    }
                return 0.5
        
        success_count = sum(1 for success in executions if success)
        failure_count = len(executions) - success_count
        
        if HAS_DATA_QUALITY:
            # Use Bayesian estimation with Jeffreys prior
            result = bayesian_reliability_estimate(success_count, failure_count, prior_alpha=0.5, prior_beta=0.5)
            if return_metadata:
                return result
            return result["reliability"]
        else:
            # Fallback: simple calculation
            success_rate = success_count / len(executions) if len(executions) > 0 else 0.5
            sample_size_factor = min(1.0, len(executions) / 20.0)
            reliability = 0.5 + (success_rate - 0.5) * sample_size_factor
            
            if return_metadata:
                # Approximate confidence interval
                std_dev = (success_rate * (1 - success_rate) / len(executions)) ** 0.5 if len(executions) > 1 else 0.4
                margin = 1.96 * std_dev  # 95% confidence
                return {
                    "reliability": max(0.0, min(1.0, reliability)),
                    "confidence_interval": (max(0.0, success_rate - margin), min(1.0, success_rate + margin)),
                    "sample_size": len(executions),
                    "data_quality": assess_data_quality(len(executions)).value if HAS_DATA_QUALITY else "unknown",
                    "uncertainty": min(1.0, margin * 2),
                }
            
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
    
    def assess_memory_quality(self, memory_id: int, return_metadata: bool = False) -> float | Dict[str, Any]:
        """
        Assess quality of a memory based on retrieval consistency using Bayesian estimation.
        
        Args:
            memory_id: ID of memory to assess
            return_metadata: If True, return full metadata including confidence intervals
            
        Returns:
            Quality score (0-1) if return_metadata=False, or dict with metadata if True
        """
        retrievals = self._memory_retrievals.get(memory_id, [])
        
        if not retrievals:
            # No data - use Bayesian prior (Beta(1, 1) = uniform prior)
            if HAS_DATA_QUALITY and return_metadata:
                result = bayesian_reliability_estimate(0, 0, prior_alpha=1.0, prior_beta=1.0)
                return result
            elif HAS_DATA_QUALITY:
                result = bayesian_reliability_estimate(0, 0, prior_alpha=1.0, prior_beta=1.0)
                return result["reliability"]
            else:
                if return_metadata:
                    return {
                        "reliability": 0.5,
                        "confidence_interval": (0.1, 0.9),
                        "sample_size": 0,
                        "data_quality": "missing",
                        "uncertainty": 0.9,
                    }
                return 0.5
        
        consistent_count = sum(1 for consistent in retrievals if consistent)
        inconsistent_count = len(retrievals) - consistent_count
        
        if HAS_DATA_QUALITY:
            # Use Bayesian estimation with uniform prior (Beta(1, 1))
            result = bayesian_reliability_estimate(consistent_count, inconsistent_count, prior_alpha=1.0, prior_beta=1.0)
            if return_metadata:
                return result
            return result["reliability"]
        else:
            # Fallback: simple calculation
            consistency_rate = consistent_count / len(retrievals) if len(retrievals) > 0 else 0.5
            sample_size_factor = min(1.0, len(retrievals) / 10.0)
            quality = 0.5 + (consistency_rate - 0.5) * sample_size_factor
            
            if return_metadata:
                std_dev = (consistency_rate * (1 - consistency_rate) / len(retrievals)) ** 0.5 if len(retrievals) > 1 else 0.4
                margin = 1.96 * std_dev
                return {
                    "reliability": max(0.0, min(1.0, quality)),
                    "confidence_interval": (max(0.0, consistency_rate - margin), min(1.0, consistency_rate + margin)),
                    "sample_size": len(retrievals),
                    "data_quality": assess_data_quality(len(retrievals)).value if HAS_DATA_QUALITY else "unknown",
                    "uncertainty": min(1.0, margin * 2),
                }
            
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
    
    def assess_source_reliability(self, source: SourceMetadata, return_metadata: bool = False) -> float | Dict[str, Any]:
        """
        Assess overall reliability of a source using Bayesian methods.
        
        Args:
            source: Source metadata to assess
            return_metadata: If True, return full metadata including confidence intervals
            
        Returns:
            Reliability score (0-1) if return_metadata=False, or dict with metadata if True
        """
        if source.source_type == SourceType.TOOL_MEDIATED_VERIFICATION:
            if source.tool_type:
                base_result = self.assess_tool_reliability(source.tool_type, return_metadata=True)
                if isinstance(base_result, dict):
                    base_reliability = base_result["reliability"]
                    # If tool has high success rate, boost reliability slightly
                    if base_reliability > 0.6:
                        adjusted_reliability = min(1.0, base_reliability * 1.05)  # Smaller boost
                        if return_metadata:
                            result = base_result.copy()
                            result["reliability"] = adjusted_reliability
                            return result
                        return adjusted_reliability
                    if return_metadata:
                        return base_result
                    return base_reliability
                else:
                    # Fallback for old return format
                    base_reliability = base_result
                    if base_reliability > 0.6:
                        return min(1.0, base_reliability * 1.05)
                    return base_reliability
            else:
                # Tool type unknown - use high uncertainty
                if return_metadata:
                    return {
                        "reliability": 0.5,
                        "confidence_interval": (0.1, 0.9),
                        "sample_size": 0,
                        "data_quality": "missing",
                        "uncertainty": 0.9,
                    }
                return 0.5
        
        elif source.source_type == SourceType.MEMORY_RETRIEVAL:
            if source.memory_id is not None:
                return self.assess_memory_quality(source.memory_id, return_metadata=return_metadata)
            else:
                # Memory ID unknown - use high uncertainty
                if return_metadata:
                    return {
                        "reliability": 0.5,
                        "confidence_interval": (0.1, 0.9),
                        "sample_size": 0,
                        "data_quality": "missing",
                        "uncertainty": 0.9,
                    }
                return 0.5
        
        elif source.source_type == SourceType.LOGICAL_INFERENCE:
            # Logical validity check
            is_valid = self.check_logical_validity(source)
            if not is_valid:
                if return_metadata:
                    return {
                        "reliability": 0.2,
                        "confidence_interval": (0.1, 0.3),
                        "sample_size": 1,
                        "data_quality": "low",
                        "uncertainty": 0.2,
                    }
                return 0.2
            
            # Use logical strength as reliability indicator
            if source.logical_strength is not None:
                reliability = source.logical_strength
                # Add uncertainty based on logical strength
                uncertainty = 1.0 - reliability  # Lower strength = higher uncertainty
                if return_metadata:
                    margin = uncertainty * 0.3
                    return {
                        "reliability": reliability,
                        "confidence_interval": (max(0.0, reliability - margin), min(1.0, reliability + margin)),
                        "sample_size": 1,
                        "data_quality": "medium" if reliability > 0.7 else "low",
                        "uncertainty": uncertainty,
                    }
                return reliability
            else:
                # No logical strength - use high uncertainty
                if return_metadata:
                    return {
                        "reliability": 0.5,
                        "confidence_interval": (0.1, 0.9),
                        "sample_size": 0,
                        "data_quality": "missing",
                        "uncertainty": 0.9,
                    }
                return 0.5
        
        elif source.source_type == SourceType.USER_PROVIDED:
            # User sources: verified > unverified > contradicted
            if source.verification_status == "verified":
                reliability = 0.9
                uncertainty = 0.1
            elif source.verification_status == "unverified":
                reliability = 0.6
                uncertainty = 0.4
            elif source.verification_status == "contradicted":
                reliability = 0.1
                uncertainty = 0.2
            else:
                # Unknown status - use high uncertainty
                reliability = 0.5
                uncertainty = 0.9
            
            if return_metadata:
                margin = uncertainty * 0.3
                return {
                    "reliability": reliability,
                    "confidence_interval": (max(0.0, reliability - margin), min(1.0, reliability + margin)),
                    "sample_size": 1,
                    "data_quality": "high" if reliability > 0.8 else "medium" if reliability > 0.5 else "low",
                    "uncertainty": uncertainty,
                }
            return reliability
        
        elif source.source_type == SourceType.EMERGENT_PATTERN:
            # Use statistical significance and predictive accuracy
            if source.statistical_significance is not None and source.predictive_accuracy is not None:
                # Combine significance and accuracy
                reliability = (source.statistical_significance + source.predictive_accuracy) / 2.0
                reliability = max(0.0, min(1.0, reliability))
                uncertainty = 1.0 - reliability
                
                if return_metadata:
                    margin = uncertainty * 0.3
                    return {
                        "reliability": reliability,
                        "confidence_interval": (max(0.0, reliability - margin), min(1.0, reliability + margin)),
                        "sample_size": source.observation_count or 1,
                        "data_quality": assess_data_quality(source.observation_count or 1).value if HAS_DATA_QUALITY else "unknown",
                        "uncertainty": uncertainty,
                    }
                return reliability
            else:
                # Missing data - use high uncertainty
                if return_metadata:
                    return {
                        "reliability": 0.5,
                        "confidence_interval": (0.1, 0.9),
                        "sample_size": 0,
                        "data_quality": "missing",
                        "uncertainty": 0.9,
                    }
                return 0.5
        
        else:
            # Unknown source type - use high uncertainty
            if return_metadata:
                return {
                    "reliability": 0.5,
                    "confidence_interval": (0.1, 0.9),
                    "sample_size": 0,
                    "data_quality": "missing",
                    "uncertainty": 0.9,
                }
            return 0.5

