"""
Conflict detection engine.

Detects contradictions and conflicts between memories using multiple methods:
- Semantic similarity (embedding-based)
- Rule-based pattern matching
- LLM-based analysis (optional)
"""

from __future__ import annotations

import re
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from .. import MemoryRecord
from .models import Conflict

logger = logging.getLogger(__name__)


# Rule-based contradiction patterns
CONTRADICTION_PATTERNS = [
    # Boolean contradictions
    (r'\b(prefers?|likes?|loves?|enjoys?)\b', r'\b(hates?|dislikes?|loathes?|despises?)\b'),
    (r'\b(always|all|every)\b', r'\b(never|none|no)\b'),
    (r'\b(yes|true|correct)\b', r'\b(no|false|incorrect|wrong)\b'),
    # Temporal contradictions
    (r'\b(yesterday|past|ago|was)\b', r'\b(tomorrow|future|will be|is)\b'),
    (r'\b(always|all the time)\b', r'\b(sometimes|occasionally|rarely)\b'),
    # Numerical contradictions (will be handled separately)
]


class ConflictDetector:
    """
    Detects conflicts between memories using multiple detection methods.
    
    Uses semantic similarity, rule-based patterns, and optional LLM analysis
    to identify contradictions and conflicts.
    """
    
    def __init__(
        self,
        memory_manager: Optional[Any] = None,
        similarity_threshold: float = 0.85,
        contradiction_threshold: float = 0.7,
        llm_client: Optional[Any] = None
    ) -> None:
        """
        Initialize conflict detector.
        
        Args:
            memory_manager: MemoryManager instance for semantic search (optional)
            similarity_threshold: Minimum similarity to consider for conflicts (0.0-1.0)
            contradiction_threshold: Minimum confidence for contradiction (0.0-1.0)
            llm_client: Optional LLM client for advanced analysis
        """
        self.memory_manager = memory_manager
        self.similarity_threshold = similarity_threshold
        self.contradiction_threshold = contradiction_threshold
        self.llm_client = llm_client
        
        logger.info(
            f"Initialized ConflictDetector "
            f"(similarity_threshold={similarity_threshold}, "
            f"contradiction_threshold={contradiction_threshold})"
        )
    
    def detect_conflicts(
        self,
        memory: MemoryRecord,
        existing_memories: List[MemoryRecord]
    ) -> List[Conflict]:
        """
        Detect conflicts between a new memory and existing memories.
        
        Args:
            memory: New memory to check
            existing_memories: List of existing memories to check against
            
        Returns:
            List of Conflict objects
        """
        conflicts: List[Conflict] = []
        
        # Filter out the memory itself from existing memories
        existing = [m for m in existing_memories if m.id != memory.id]
        
        if not existing:
            return conflicts
        
        # Try semantic detection first (if memory_manager available)
        if self.memory_manager:
            semantic_conflicts = self.detect_semantic_conflicts(memory, existing)
            # Enhance with temporal context
            for conflict in semantic_conflicts:
                self._enhance_conflict_with_temporal_context(conflict, memory)
            conflicts.extend(semantic_conflicts)
        
        # Also check rule-based for all pairs
        for existing_memory in existing:
            rule_conflict = self.detect_rule_based_conflicts(
                memory.text,
                existing_memory.text,
                memory1=memory,
                memory2=existing_memory
            )
            if rule_conflict:
                # Enhance with temporal context
                self._enhance_conflict_with_temporal_context(rule_conflict, memory)
                
                # Check if we already have this conflict from semantic detection
                if not any(
                    (c.memory1.id == memory.id and c.memory2.id == existing_memory.id) or
                    (c.memory1.id == existing_memory.id and c.memory2.id == memory.id)
                    for c in conflicts
                    if c.memory1.id and c.memory2.id
                ):
                    conflicts.append(rule_conflict)
        
        return conflicts
    
    def detect_semantic_conflicts(
        self,
        new_memory: MemoryRecord,
        existing_memories: List[MemoryRecord],
    ) -> List[Conflict]:
        """
        Detect conflicts using embedding similarity.
        
        Args:
            new_memory: New memory to check
            existing_memories: Existing memories to check against
            
        Returns:
            List of Conflict objects
        """
        if not self.memory_manager or not existing_memories:
            return []
        
        conflicts: List[Conflict] = []
        
        try:
            # Use memory manager to find similar memories
            # Search for similar memories using the new memory's text
            similar_memories = self.memory_manager.retrieve_memories(
                query=new_memory.text,
                limit=10  # Check top 10 similar
            )
            
            for similar_memory in similar_memories:
                # Skip if it's the same memory
                if similar_memory.id == new_memory.id:
                    continue
                
                # Skip exact duplicates (handled by deduplication)
                if (similar_memory.namespace == new_memory.namespace and
                    similar_memory.text == new_memory.text):
                    continue
                
                # Calculate similarity (using embedding if available)
                similarity = self._calculate_similarity(new_memory, similar_memory)
                
                if similarity >= self.similarity_threshold:
                    # High similarity - check for contradiction
                    contradiction_score = self._check_contradiction(
                        new_memory.text,
                        similar_memory.text
                    )
                    
                    if contradiction_score >= self.contradiction_threshold:
                        # Use LLM if available for better analysis
                        llm_result = None
                        if self.llm_client:
                            llm_result = self.analyze_with_llm(
                                new_memory.text,
                                similar_memory.text
                            )
                        
                        conflict_type = "contradiction"
                        confidence = contradiction_score
                        evidence = f"Semantic similarity: {similarity:.2f}, contradiction score: {contradiction_score:.2f}"
                        
                        if llm_result and llm_result.get("contradicts"):
                            conflict_type = llm_result.get("type", "contradiction")
                            confidence = max(confidence, llm_result.get("confidence", 0.0))
                            evidence = llm_result.get("explanation", evidence)
                        
                        conflicts.append(Conflict(
                            memory1=new_memory,
                            memory2=similar_memory,
                            conflict_type=conflict_type,
                            confidence=confidence,
                            evidence=evidence,
                            resolution_strategy="recency"
                        ))
        
        except Exception as e:
            logger.warning(f"Error in semantic conflict detection: {e}", exc_info=True)
        
        return conflicts
    
    def detect_rule_based_conflicts(
        self,
        text1: str,
        text2: str,
        memory1: Optional[MemoryRecord] = None,
        memory2: Optional[MemoryRecord] = None
    ) -> Optional[Conflict]:
        """
        Detect conflicts using rule-based pattern matching.
        
        Args:
            text1: First text to compare
            text2: Second text to compare
            memory1: Optional first memory record
            memory2: Optional second memory record
            
        Returns:
            Conflict object if detected, None otherwise
        """
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Check for numerical contradictions
        num_conflict = self._detect_numerical_contradiction(text1, text2, memory1, memory2)
        if num_conflict:
            return num_conflict
        
        # Check for pattern-based contradictions
        for pattern1, pattern2 in CONTRADICTION_PATTERNS:
            match1 = re.search(pattern1, text1_lower)
            match2 = re.search(pattern2, text2_lower)
            
            if match1 and match2:
                # Check if they're talking about the same thing (simple heuristic)
                # Extract context around matches
                context1 = self._extract_context(text1_lower, match1.start(), match1.end())
                context2 = self._extract_context(text2_lower, match2.start(), match2.end())
                
                # Simple overlap check
                if self._contexts_overlap(context1, context2):
                    # Use provided memories or create temporary ones
                    mem1 = memory1 or MemoryRecord(namespace="temp", text=text1, importance=0.5)
                    mem2 = memory2 or MemoryRecord(namespace="temp", text=text2, importance=0.5)
                    
                    return Conflict(
                        memory1=mem1,
                        memory2=mem2,
                        conflict_type="contradiction",
                        confidence=0.75,  # Medium confidence for rule-based
                        evidence=f"Rule-based: {pattern1} vs {pattern2}",
                        resolution_strategy="recency"
                    )
        
        return None
    
    def _detect_numerical_contradiction(
        self,
        text1: str,
        text2: str,
        memory1: Optional[MemoryRecord] = None,
        memory2: Optional[MemoryRecord] = None
    ) -> Optional[Conflict]:
        """Detect numerical contradictions (e.g., age, dates)."""
        # Pattern for numbers with units
        age_pattern = r'(\d+)\s*(?:year|month|day|hour)s?\s*old'
        
        match1 = re.search(age_pattern, text1.lower())
        match2 = re.search(age_pattern, text2.lower())
        
        if match1 and match2:
            num1 = int(match1.group(1))
            num2 = int(match2.group(1))
            
            # Extract context to see if they're talking about the same thing
            context1 = self._extract_context(text1.lower(), match1.start(), match1.end())
            context2 = self._extract_context(text2.lower(), match2.start(), match2.end())
            
            if self._contexts_overlap(context1, context2) and abs(num1 - num2) > 0:
                # Use provided memories or create temporary ones
                mem1 = memory1 or MemoryRecord(namespace="temp", text=text1, importance=0.5)
                mem2 = memory2 or MemoryRecord(namespace="temp", text=text2, importance=0.5)
                
                return Conflict(
                    memory1=mem1,
                    memory2=mem2,
                    conflict_type="contradiction",
                    confidence=0.8,  # High confidence for numerical contradictions
                    evidence=f"Numerical contradiction: {num1} vs {num2}",
                    resolution_strategy="recency"
                )
        
        return None
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 20) -> str:
        """Extract context around a match."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def _contexts_overlap(self, context1: str, context2: str) -> bool:
        """Check if two contexts are talking about the same thing."""
        # Simple heuristic: check for common words
        words1 = set(context1.split())
        words2 = set(context2.split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        # If they share at least 2 meaningful words, likely same topic
        common = words1 & words2
        return len(common) >= 2
    
    def _calculate_similarity(
        self,
        memory1: MemoryRecord,
        memory2: MemoryRecord
    ) -> float:
        """Calculate similarity between two memories."""
        # If embeddings are available, use cosine similarity
        if memory1.embedding and memory2.embedding:
            try:
                import numpy as np
                vec1 = np.array(memory1.embedding)
                vec2 = np.array(memory2.embedding)
                
                # Cosine similarity
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 > 0 and norm2 > 0:
                    return float(dot_product / (norm1 * norm2))
            except Exception as e:
                logger.debug(f"Error calculating embedding similarity: {e}")
        
        # Fallback: simple text similarity
        return self._text_similarity(memory1.text, memory2.text)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _check_contradiction(self, text1: str, text2: str) -> float:
        """Check for contradiction between two texts."""
        # Use rule-based detection as a proxy
        conflict = self.detect_rule_based_conflicts(text1, text2)
        if conflict:
            return conflict.confidence
        
        # If no rule-based conflict, check for negative words
        negative_words = {'not', 'no', 'never', 'none', 'hate', 'dislike', 'wrong', 'incorrect'}
        text1_has_negative = any(word in text1.lower() for word in negative_words)
        text2_has_negative = any(word in text2.lower() for word in negative_words)
        
        # If one has negative and other doesn't, might be contradiction
        if text1_has_negative != text2_has_negative:
            return 0.5  # Medium confidence
        
        return 0.0
    
    def analyze_with_llm(
        self,
        text1: str,
        text2: str,
        context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to analyze if two statements contradict.
        
        Args:
            text1: First statement
            text2: Second statement
            context: Optional context
            
        Returns:
            Dictionary with analysis results, or None on failure
        """
        if not self.llm_client:
            return None
        
        try:
            prompt = f"""Analyze if these two statements contradict each other:

Statement 1: {text1}
Statement 2: {text2}
{f'Context: {context}' if context else ''}

Respond with a JSON object containing:
- "contradicts": boolean
- "confidence": float (0.0-1.0)
- "type": string ("contradiction", "ambiguity", or "update")
- "explanation": string

JSON response:"""
            
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat(messages)
            
            # Extract content from response
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Try to parse JSON from response
            # LLM might wrap JSON in markdown code blocks
            content = content.strip()
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_start = None
                json_end = None
                for i, line in enumerate(lines):
                    if line.strip().startswith("```"):
                        if json_start is None:
                            json_start = i + 1
                        else:
                            json_end = i
                            break
                
                if json_start and json_end:
                    content = "\n".join(lines[json_start:json_end])
            
            # Try to find JSON object in response
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return result
            
            # Fallback: try parsing entire content
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                logger.warning(f"Could not parse LLM response as JSON: {content}")
                return None
        
        except Exception as e:
            logger.warning(f"Error in LLM contradiction analysis: {e}", exc_info=True)
            return None
    
    def _check_temporal_overlap(
        self,
        memory1: MemoryRecord,
        memory2: MemoryRecord
    ) -> bool:
        """
        Check if two memories have temporally overlapping validity periods.
        
        Args:
            memory1: First memory
            memory2: Second memory
            
        Returns:
            True if memories overlap temporally, False otherwise
        """
        # If neither has temporal metadata, assume they might overlap
        if not memory1.valid_from and not memory1.valid_until and \
           not memory2.valid_from and not memory2.valid_until:
            return True  # Unknown temporal scope, assume overlap
        
        # If one has temporal metadata and other doesn't, check if current time is in range
        now = datetime.now(timezone.utc)
        
        # Check memory1 validity
        mem1_valid = True
        if memory1.valid_from or memory1.valid_until:
            if memory1.valid_from and now < memory1.valid_from:
                mem1_valid = False
            if memory1.valid_until and now > memory1.valid_until:
                mem1_valid = False
        
        # Check memory2 validity
        mem2_valid = True
        if memory2.valid_from or memory2.valid_until:
            if memory2.valid_from and now < memory2.valid_from:
                mem2_valid = False
            if memory2.valid_until and now > memory2.valid_until:
                mem2_valid = False
        
        # If both have explicit validity periods, check overlap
        if memory1.valid_from and memory1.valid_until and \
           memory2.valid_from and memory2.valid_until:
            # Check if periods overlap
            return not (memory1.valid_until < memory2.valid_from or 
                       memory2.valid_until < memory1.valid_from)
        
        # If only one has explicit period, check if current time is in both
        return mem1_valid and mem2_valid
    
    def _is_update(
        self,
        memory1: MemoryRecord,
        memory2: MemoryRecord
    ) -> bool:
        """
        Check if one memory is an update of another (different time periods).
        
        Args:
            memory1: First memory
            memory2: Second memory
            
        Returns:
            True if memories appear to be updates (different periods), False otherwise
        """
        # If they don't overlap temporally and are similar, likely an update
        if not self._check_temporal_overlap(memory1, memory2):
            # Check if one is clearly after the other
            if memory1.valid_from and memory2.valid_from:
                return memory1.valid_from > memory2.valid_from or \
                       memory2.valid_from > memory1.valid_from
            # Check created_at as fallback
            return abs((memory1.created_at - memory2.created_at).total_seconds()) > 86400  # More than 1 day apart
        return False
    
    def _enhance_conflict_with_temporal_context(
        self,
        conflict: Conflict,
        new_memory: MemoryRecord
    ) -> None:
        """
        Enhance conflict with temporal context information.
        
        Args:
            conflict: Conflict to enhance
            new_memory: New memory that triggered the conflict
        """
        # Determine which memory is the new one and which is existing
        # Compare by id if available, otherwise by object identity
        if new_memory.id and conflict.memory1.id and new_memory.id == conflict.memory1.id:
            existing_memory = conflict.memory2
        elif new_memory.id and conflict.memory2.id and new_memory.id == conflict.memory2.id:
            existing_memory = conflict.memory1
        else:
            # Fallback: assume memory1 is new (common case)
            existing_memory = conflict.memory2
        
        # Calculate temporal gap
        conflict.temporal_gap = abs(new_memory.created_at - existing_memory.created_at)
        
        # Determine temporal context
        if self._check_temporal_overlap(new_memory, existing_memory):
            conflict.temporal_context = "same_period"
            # If same period, likely a true contradiction
            if conflict.conflict_type == "contradiction":
                # Keep as contradiction
                pass
        else:
            conflict.temporal_context = "different_periods"
            # If different periods, might be an update rather than contradiction
            if self._is_update(new_memory, existing_memory):
                conflict.conflict_type = "update"
                conflict.confidence = min(conflict.confidence, 0.8)  # Lower confidence for updates
                conflict.evidence += " (Different time periods suggest update rather than contradiction)"

