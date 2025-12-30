"""
LLM-based pattern matcher for production rules and working memory.

Replaces brittle dict subset/equality matching with semantic LLM-based matching
that supports variables, wildcards, negation, and complex patterns.
"""

from __future__ import annotations

import logging
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from collections import deque

if TYPE_CHECKING:
    from ..llm import LLMClient

logger = logging.getLogger(__name__)


class LLMPatternMatcher:
    """
    LLM-based pattern matcher for semantic pattern matching.
    
    Uses LLM to evaluate pattern matches, supporting:
    - Variables and wildcards
    - Negation
    - Complex existential patterns ("if there exists X such that...")
    - Semantic similarity (not just exact matches)
    """
    
    def __init__(
        self,
        llm_client: "LLMClient",
        model: str = "gpt-5-nano",
        cache_size: int = 100,
        batch_size: int = 10
    ):
        """
        Initialize LLM pattern matcher.
        
        Args:
            llm_client: LLM client for pattern matching
            model: Model name to use (default: gpt-5-nano)
            cache_size: Maximum number of cached pattern matches
            batch_size: Maximum number of patterns to match in one LLM call
        """
        self.llm = llm_client
        self.model = model
        self.cache_size = cache_size
        self.batch_size = batch_size
        
        # Cache for pattern matches: hash(pattern, content) -> (match, confidence)
        self._cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_order = deque()  # For LRU eviction
        
        # Pending batch for batching
        self._pending_batch: List[Tuple[Dict[str, Any], Dict[str, Any], str]] = []

        # Optional logger (PatternMatchLogger-style). Keep as attribute to avoid AttributeError.
        self.logger = None
        
    def match(
        self,
        pattern: Dict[str, Any],
        content: Dict[str, Any]
    ) -> bool:
        """
        Match a pattern against content using LLM.
        
        Args:
            pattern: Pattern to match (dict or string)
            content: Content to match against (dict or string)
            
        Returns:
            True if pattern matches content, False otherwise
        """
        start_time = time.time()
        cache_hit = False
        
        # Check cache first
        cache_key = self._get_cache_key(pattern, content)
        if cache_key in self._cache:
            match, confidence = self._cache[cache_key]
            cache_hit = True
            latency_ms = (time.time() - start_time) * 1000
            
            # Log cache hit
            if self.logger:
                self.logger.log(
                    component="LLMPatternMatcher",
                    operation="match",
                    model=self.model,
                    input_pattern=pattern,
                    input_content=content,
                    output_match=match,
                    output_confidence=confidence,
                    cache_hit=True,
                    latency_ms=latency_ms
                )
            
            return match
        
        # For single matches, we can batch them or process immediately
        # For now, process immediately (can be optimized later)
        results = self.match_batch([(pattern, content)])
        if results:
            match, confidence = results[0]
            # Cache result
            self._cache_result(cache_key, match, confidence)
            latency_ms = (time.time() - start_time) * 1000
            
            # Log cache miss (already logged in match_batch, but log here for single match context)
            if self.logger:
                self.logger.log(
                    component="LLMPatternMatcher",
                    operation="match",
                    model=self.model,
                    input_pattern=pattern,
                    input_content=content,
                    output_match=match,
                    output_confidence=confidence,
                    cache_hit=False,
                    latency_ms=latency_ms
                )
            
            return match
        
        return False
    
    def match_batch(
        self,
        pattern_content_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]
    ) -> List[Tuple[bool, float]]:
        """
        Batch match multiple patterns against contents.
        
        Args:
            pattern_content_pairs: List of (pattern, content) tuples to match
            
        Returns:
            List of (match, confidence) tuples, one per input pair
        """
        if not pattern_content_pairs:
            return []
        
        # Check cache for all pairs first
        results: List[Optional[Tuple[bool, float]]] = [None] * len(pattern_content_pairs)
        uncached_pairs: List[Tuple[int, Dict[str, Any], Dict[str, Any]]] = []
        
        for i, (pattern, content) in enumerate(pattern_content_pairs):
            cache_key = self._get_cache_key(pattern, content)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                uncached_pairs.append((i, pattern, content))
        
        # If all were cached, return results
        if not uncached_pairs:
            return [r for r in results if r is not None]  # type: ignore
        
        # Process uncached pairs in batches
        for batch_start in range(0, len(uncached_pairs), self.batch_size):
            batch = uncached_pairs[batch_start:batch_start + self.batch_size]
            batch_start_time = time.time()
            batch_results = self._match_batch_with_llm(batch)
            batch_latency_ms = (time.time() - batch_start_time) * 1000
            
            # Store results and cache them
            batch_inputs = []
            batch_outputs = []
            for (orig_idx, pattern, content), (match, confidence) in zip(batch, batch_results):
                results[orig_idx] = (match, confidence)
                cache_key = self._get_cache_key(pattern, content)
                self._cache_result(cache_key, match, confidence)
                
                # Prepare for logging
                batch_inputs.append({"pattern": pattern, "content": content})
                batch_outputs.append({
                    "match": match,
                    "confidence": confidence,
                    "cache_hit": False
                })
            
            # Log batch
            if self.logger and batch_inputs:
                self.logger.log_batch(
                    component="LLMPatternMatcher",
                    operation="match_batch",
                    model=self.model,
                    batch_inputs=batch_inputs,
                    batch_results=batch_outputs,
                    latency_ms=batch_latency_ms
                )
        
        # Log cache hits separately
        if self.logger:
            cache_hit_inputs = []
            cache_hit_outputs = []
            for i, (pattern, content) in enumerate(pattern_content_pairs):
                cache_key = self._get_cache_key(pattern, content)
                if cache_key in self._cache:
                    match, confidence = self._cache[cache_key]
                    cache_hit_inputs.append({"pattern": pattern, "content": content})
                    cache_hit_outputs.append({
                        "match": match,
                        "confidence": confidence,
                        "cache_hit": True
                    })
            
            if cache_hit_inputs:
                self.logger.log_batch(
                    component="LLMPatternMatcher",
                    operation="match_batch",
                    model=self.model,
                    batch_inputs=cache_hit_inputs,
                    batch_results=cache_hit_outputs,
                    latency_ms=0.0  # Cache hits are instant
                )
        
        return [r if r is not None else (False, 0.0) for r in results]
    
    def _match_batch_with_llm(
        self,
        batch: List[Tuple[int, Dict[str, Any], Dict[str, Any]]]
    ) -> List[Tuple[bool, float]]:
        """
        Use LLM to match a batch of patterns.
        
        Args:
            batch: List of (original_index, pattern, content) tuples
            
        Returns:
            List of (match, confidence) tuples
        """
        # Build prompt for LLM
        prompt = self._build_matching_prompt(batch)
        
        try:
            # Call LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a pattern matching assistant. Your task is to determine if patterns match content items. Return JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.llm.chat(messages, temperature=0.0)
            content = self.llm.extract_assistant_content(response)
            
            if not content:
                logger.warning("LLM returned empty content for pattern matching")
                return [(False, 0.0)] * len(batch)
            
            # Parse JSON response
            try:
                # Try to extract JSON from response (might have markdown code blocks)
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                result = json.loads(content)
                
                # Extract matches from result
                if isinstance(result, list):
                    matches = result
                elif isinstance(result, dict) and "matches" in result:
                    matches = result["matches"]
                else:
                    logger.warning(f"Unexpected LLM response format: {result}")
                    return [(False, 0.0)] * len(batch)
                
                # Convert to (match, confidence) tuples
                results = []
                for match_data in matches:
                    if isinstance(match_data, dict):
                        match = match_data.get("match", False)
                        confidence = match_data.get("confidence", 0.5)
                    elif isinstance(match_data, bool):
                        match = match_data
                        confidence = 1.0 if match else 0.0
                    else:
                        match = bool(match_data)
                        confidence = 1.0 if match else 0.0
                    
                    results.append((match, float(confidence)))
                
                # Ensure we have the right number of results
                if len(results) != len(batch):
                    logger.warning(
                        f"LLM returned {len(results)} results but expected {len(batch)}. "
                        f"Padding with False matches."
                    )
                    while len(results) < len(batch):
                        results.append((False, 0.0))
                    results = results[:len(batch)]
                
                return results
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}. Content: {content[:200]}")
                return [(False, 0.0)] * len(batch)
                
        except Exception as e:
            logger.error(f"Error calling LLM for pattern matching: {e}", exc_info=True)
            return [(False, 0.0)] * len(batch)
    
    def _build_matching_prompt(
        self,
        batch: List[Tuple[int, Dict[str, Any], Dict[str, Any]]]
    ) -> str:
        """
        Build prompt for LLM pattern matching.
        
        Args:
            batch: List of (original_index, pattern, content) tuples
            
        Returns:
            Prompt string
        """
        prompt_parts = [
            "You are a pattern matching assistant. Determine if each pattern matches its corresponding content.",
            "",
            "Patterns can contain:",
            "- Exact field matches (pattern.field == content.field)",
            "- Variables/wildcards (pattern.field can match any value in content)",
            "- Negation (pattern.field != value means content.field must not equal value)",
            "- Existential patterns (if pattern contains 'exists X such that...', check if such X exists in content)",
            "- Semantic similarity (similar meanings should match even if wording differs)",
            "- Contradiction detection (if pattern.type is 'contradiction_check', determine if the texts contradict each other)",
            "",
            "Special handling for contradiction_check:",
            "- If pattern.type is 'contradiction_check', check if pattern.text contradicts content.text",
            "- Consider semantic contradictions, not just exact word matches",
            "- Return match=true if texts contradict, false if they align or are unrelated",
            "- Confidence should reflect how strongly the texts contradict (higher = stronger contradiction)",
            "",
            "For each pattern-content pair, return:",
            "- 'match': boolean indicating if pattern matches",
            "- 'confidence': float 0.0-1.0 indicating confidence in the match",
            "",
            "Return a JSON array with one object per pattern-content pair:",
            "[",
            "  {",
            "    \"match\": true/false,",
            "    \"confidence\": 0.0-1.0",
            "  },",
            "  ...",
            "]",
            "",
            "Pattern-Content pairs to evaluate:",
            ""
        ]
        
        for idx, (orig_idx, pattern, content) in enumerate(batch):
            prompt_parts.append(f"Pair {idx + 1}:")
            prompt_parts.append(f"  Pattern: {json.dumps(pattern, indent=2)}")
            prompt_parts.append(f"  Content: {json.dumps(content, indent=2)}")
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    def _get_cache_key(self, pattern: Dict[str, Any], content: Dict[str, Any]) -> str:
        """Generate cache key for pattern-content pair."""
        # Create deterministic string representation
        pattern_str = json.dumps(pattern, sort_keys=True)
        content_str = json.dumps(content, sort_keys=True)
        combined = f"{pattern_str}|||{content_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, match: bool, confidence: float) -> None:
        """Cache a pattern matching result."""
        # Add to cache
        self._cache[cache_key] = (match, confidence)
        self._cache_order.append(cache_key)
        
        # Evict if cache is too large
        while len(self._cache) > self.cache_size:
            oldest_key = self._cache_order.popleft()
            if oldest_key in self._cache:
                del self._cache[oldest_key]
    
    def clear_cache(self) -> None:
        """Clear the pattern matching cache."""
        self._cache.clear()
        self._cache_order.clear()
        logger.debug("Cleared LLM pattern matching cache")

