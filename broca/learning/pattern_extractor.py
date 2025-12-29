"""
Pattern extraction from tool call sequences.

Extracts patterns from successful tool executions for
learning and generalization.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class PatternExtractor:
    """
    Extracts patterns from tool call sequences.
    
    Identifies common patterns in successful tool executions,
    generalizes them, and creates reusable templates.
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.patterns: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized PatternExtractor with similarity threshold {similarity_threshold}")
    
    def extract_patterns_from_sequence(
        self,
        sequence: List[Dict[str, Any]],
        dissonance_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract patterns from a tool call sequence with optional dissonance context.
        
        Args:
            sequence: List of tool call observations
            dissonance_context: Optional dissonance context with metrics for filtering
            
        Returns:
            List of extracted patterns
        """
        if len(sequence) < 2:
            return []
        
        patterns = []
        
        # Extract tool call patterns
        tool_patterns = self._extract_tool_patterns(sequence)
        patterns.extend(tool_patterns)
        
        # Extract parameter patterns
        param_patterns = self._extract_parameter_patterns(sequence)
        patterns.extend(param_patterns)
        
        # Extract timing patterns
        timing_patterns = self._extract_timing_patterns(sequence)
        patterns.extend(timing_patterns)
        
        # Generalize patterns
        generalized = self._generalize_patterns(patterns)
        
        # Add dissonance metadata if available
        if dissonance_context:
            for pattern in generalized:
                pattern["dissonance_metadata"] = {
                    "average_dissonance": dissonance_context.get("average_dissonance", 0.0),
                    "dissonance_reduction": dissonance_context.get("dissonance_reduction", 0.0),
                    "is_low_dissonance": dissonance_context.get("average_dissonance", 1.0) < 0.3
                }
        
        logger.info(f"Extracted {len(generalized)} patterns from {len(sequence)} tool calls")
        return generalized
    
    def extract_dissonance_reduction_patterns(
        self,
        sequences: List[List[Dict[str, Any]]],
        dissonance_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract patterns from sequences that successfully reduce dissonance.
        
        Args:
            sequences: List of tool call sequences
            dissonance_data: List of dissonance metrics for each sequence
            
        Returns:
            List of patterns that correlate with dissonance reduction
        """
        if len(sequences) != len(dissonance_data):
            logger.warning("Mismatch between sequences and dissonance data")
            return []
        
        reduction_patterns = []
        
        # Find sequences that reduced dissonance
        for i, (sequence, dissonance) in enumerate(zip(sequences, dissonance_data)):
            dissonance_before = dissonance.get("dissonance_before", 1.0)
            dissonance_after = dissonance.get("dissonance_after", 1.0)
            
            if dissonance_before > dissonance_after:  # Reduction occurred
                dissonance_reduction = dissonance_before - dissonance_after
                
                # Extract patterns from this sequence
                context = {
                    "average_dissonance": (dissonance_before + dissonance_after) / 2.0,
                    "dissonance_reduction": dissonance_reduction,
                    "is_low_dissonance": dissonance_after < 0.3
                }
                
                patterns = self.extract_patterns_from_sequence(sequence, context)
                
                # Mark patterns as dissonance-reducing
                for pattern in patterns:
                    pattern["dissonance_reduction_pattern"] = True
                    pattern["reduction_magnitude"] = dissonance_reduction
                
                reduction_patterns.extend(patterns)
        
        logger.info(f"Extracted {len(reduction_patterns)} dissonance-reduction patterns")
        return reduction_patterns
    
    def _extract_tool_patterns(self, sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns in tool call ordering."""
        tool_names = []
        for obs in sequence:
            tool_call = obs.get("tool_call", {})
            tool_names.append(tool_call.get("name", "unknown"))
        
        patterns = []
        
        # Look for repeating sequences
        for seq_len in range(2, min(5, len(tool_names) // 2 + 1)):
            for i in range(len(tool_names) - seq_len):
                subseq = tool_names[i:i + seq_len]
                
                # Check if this subsequence appears again
                for j in range(i + seq_len, len(tool_names) - seq_len + 1):
                    if tool_names[j:j + seq_len] == subseq:
                        pattern = {
                            "type": "tool_sequence",
                            "sequence": subseq,
                            "occurrences": 2,
                            "positions": [i, j],
                        }
                        patterns.append(pattern)
                        break
        
        return patterns
    
    def _extract_parameter_patterns(self, sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns in tool parameters."""
        patterns = []
        
        for obs in sequence:
            tool_call = obs.get("tool_call", {})
            tool_name = tool_call.get("name", "unknown")
            parameters = tool_call.get("parameters", {})
            
            # Extract common parameter structures
            param_pattern = {
                "type": "parameter_structure",
                "tool_name": tool_name,
                "parameter_keys": list(parameters.keys()),
                "parameter_types": self._extract_parameter_types(parameters),
            }
            patterns.append(param_pattern)
        
        return patterns
    
    def _extract_parameter_types(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Extract types of parameter values."""
        types = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # Check if it's a template (contains {{ }})
                if "{{" in value and "}}" in value:
                    types[key] = "template"
                else:
                    types[key] = "string"
            elif isinstance(value, (int, float)):
                types[key] = "number"
            elif isinstance(value, bool):
                types[key] = "boolean"
            elif isinstance(value, list):
                types[key] = "list"
            elif isinstance(value, dict):
                types[key] = "object"
            else:
                types[key] = "unknown"
        
        return types
    
    def _extract_timing_patterns(self, sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns in timing between tool calls."""
        if len(sequence) < 2:
            return []
        
        patterns = []
        timestamps = []
        
        for obs in sequence:
            timestamp_str = obs.get("timestamp", "")
            if timestamp_str:
                # Parse timestamp
                from datetime import datetime
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    timestamps.append(timestamp)
                except (ValueError, TypeError):
                    pass
        
        if len(timestamps) < 2:
            return patterns
        
        # Calculate time differences
        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            time_diffs.append(diff)
        
        # Look for patterns in time differences
        if len(time_diffs) >= 2:
            avg_diff = sum(time_diffs) / len(time_diffs)
            pattern = {
                "type": "timing",
                "average_interval_seconds": avg_diff,
                "min_interval": min(time_diffs),
                "max_interval": max(time_diffs),
            }
            patterns.append(pattern)
        
        return patterns
    
    def _generalize_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generalize patterns by merging similar ones."""
        if not patterns:
            return []
        
        # Group patterns by type
        by_type = defaultdict(list)
        for pattern in patterns:
            by_type[pattern["type"]].append(pattern)
        
        generalized = []
        
        for pattern_type, type_patterns in by_type.items():
            if pattern_type == "tool_sequence":
                generalized.extend(self._generalize_tool_sequences(type_patterns))
            elif pattern_type == "parameter_structure":
                generalized.extend(self._generalize_parameter_structures(type_patterns))
            else:
                # Keep other patterns as-is
                generalized.extend(type_patterns)
        
        return generalized
    
    def _generalize_tool_sequences(self, sequences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generalize tool sequence patterns."""
        if not sequences:
            return []
        
        # Find common subsequences
        all_sequences = [seq["sequence"] for seq in sequences]
        
        # Simple generalization: find common prefixes
        common_patterns = []
        
        if len(all_sequences) >= 2:
            # Compare first two sequences
            seq1 = all_sequences[0]
            seq2 = all_sequences[1]
            
            # Find common prefix
            common_prefix = []
            for i in range(min(len(seq1), len(seq2))):
                if seq1[i] == seq2[i]:
                    common_prefix.append(seq1[i])
                else:
                    break
            
            if common_prefix:
                pattern = {
                    "type": "tool_sequence",
                    "sequence": common_prefix,
                    "is_generalized": True,
                    "original_count": len(sequences),
                    "pattern_type": "common_prefix",
                }
                common_patterns.append(pattern)
        
        return common_patterns
    
    def _generalize_parameter_structures(self, structures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generalize parameter structure patterns."""
        if not structures:
            return []
        
        # Group by tool name
        by_tool = defaultdict(list)
        for struct in structures:
            tool_name = struct.get("tool_name", "unknown")
            by_tool[tool_name].append(struct)
        
        generalized = []
        
        for tool_name, tool_structures in by_tool.items():
            if len(tool_structures) == 1:
                # Single structure, keep as-is
                generalized.extend(tool_structures)
                continue
            
            # Find common parameter keys
            all_keys = [set(struct.get("parameter_keys", [])) for struct in tool_structures]
            common_keys = set.intersection(*all_keys) if all_keys else set()
            
            if common_keys:
                pattern = {
                    "type": "parameter_structure",
                    "tool_name": tool_name,
                    "parameter_keys": list(common_keys),
                    "is_generalized": True,
                    "common_keys_count": len(common_keys),
                    "original_count": len(tool_structures),
                }
                generalized.append(pattern)
        
        return generalized
    
    def find_similar_patterns(self, pattern: Dict[str, Any], 
                             patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find patterns similar to the given pattern."""
        similar = []
        
        for other_pattern in patterns:
            if self._patterns_similar(pattern, other_pattern):
                similar.append(other_pattern)
        
        return similar
    
    def _patterns_similar(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> bool:
        """Check if two patterns are similar."""
        if pattern1.get("type") != pattern2.get("type"):
            return False
        
        pattern_type = pattern1.get("type")
        
        if pattern_type == "tool_sequence":
            return self._tool_sequences_similar(pattern1, pattern2)
        elif pattern_type == "parameter_structure":
            return self._parameter_structures_similar(pattern1, pattern2)
        else:
            # For other types, use exact match for now
            return pattern1 == pattern2
    
    def _tool_sequences_similar(self, seq1: Dict[str, Any], seq2: Dict[str, Any]) -> bool:
        """Check if tool sequences are similar."""
        s1 = seq1.get("sequence", [])
        s2 = seq2.get("sequence", [])
        
        if len(s1) != len(s2):
            return False
        
        # Compare element by element
        for tool1, tool2 in zip(s1, s2):
            if tool1 != tool2:
                return False
        
        return True
    
    def _parameter_structures_similar(self, struct1: Dict[str, Any], 
                                    struct2: Dict[str, Any]) -> bool:
        """Check if parameter structures are similar."""
        if struct1.get("tool_name") != struct2.get("tool_name"):
            return False
        
        keys1 = set(struct1.get("parameter_keys", []))
        keys2 = set(struct2.get("parameter_keys", []))
        
        # Calculate Jaccard similarity
        intersection = len(keys1.intersection(keys2))
        union = len(keys1.union(keys2))
        
        if union == 0:
            return True
        
        similarity = intersection / union
        return similarity >= self.similarity_threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert extractor to dictionary representation."""
        return {
            "patterns": self.patterns,
            "similarity_threshold": self.similarity_threshold,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternExtractor:
        """Create extractor from dictionary representation."""
        extractor = cls(similarity_threshold=data.get("similarity_threshold", 0.8))
        extractor.patterns = data.get("patterns", [])
        return extractor
