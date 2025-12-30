"""
Pattern matcher for working memory.

Now uses LLM-based semantic matching with batching support for efficient processing.
"""

from __future__ import annotations

import logging
import json
import hashlib
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from collections import deque

if TYPE_CHECKING:
    from ..llm import LLMClient

logger = logging.getLogger(__name__)


class PatternMatcher:
    """
    Matches patterns against working memory items using LLM-based semantic matching.
    
    Supports:
    - Semantic similarity (not just exact matches)
    - Variables with bindings
    - Negation
    - Wildcards
    - Complex patterns
    - Batching for efficient processing of multiple matches
    """
    
    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        model: Optional[str] = None,
        batch_size: int = 10,
        cache_size: int = 100,
        fallback_to_simple: bool = True
    ):
        """
        Initialize pattern matcher.
        
        Args:
            llm_client: Optional LLM client for pattern matching. If None, will try to create one.
            model: Model name to use (default: gpt-5-nano from config)
            batch_size: Maximum number of patterns to match in one LLM call
            cache_size: Maximum number of cached pattern matches
            fallback_to_simple: If True, fall back to simple equality matching if LLM fails
        """
        self.fallback_to_simple = fallback_to_simple
        self.batch_size = batch_size
        self.cache_size = cache_size
        
        # Initialize LLM client
        if llm_client is None:
            try:
                from ..llm import create_llm_client
                from ..config import config
                
                model_name = model or getattr(config.reasoning, 'llm_pattern_matching_model', 'gpt-5-nano')
                self.llm_client = create_llm_client(model=model_name)
                self.model = model_name
                logger.info(f"Initialized PatternMatcher with LLM (model: {model_name})")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client for PatternMatcher: {e}. Using simple matching.")
                self.llm_client = None
                self.model = None
        else:
            self.llm_client = llm_client
            self.model = model or "gpt-5-nano"
        
        # Cache for pattern matches: hash(pattern, item) -> (match, confidence)
        self._cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_order = deque()  # For LRU eviction
        
        # Simple matching fallback (for when LLM is not available)
        self._simple_match_enabled = True

        # Optional CSV logging for training data
        self._pm_logger = None
        self._pm_logging_enabled = False
        try:
            from .config import ReasoningConfig
            cfg = ReasoningConfig()
            self._pm_logging_enabled = bool(getattr(cfg, "llm_pattern_logging_enabled", False))
            if self._pm_logging_enabled:
                from .pattern_match_logger import PatternMatchLogger, PatternMatchLogConfig
                from pathlib import Path
                self._pm_logger = PatternMatchLogger(
                    PatternMatchLogConfig(
                        enabled=True,
                        base_path=Path(getattr(cfg, "llm_pattern_log_path", "data/llm_pattern_matching_log.csv")),
                        rotation=str(getattr(cfg, "llm_pattern_log_rotation", "daily")),
                        max_size_mb=int(getattr(cfg, "llm_pattern_log_max_size_mb", 100)),
                        max_content_chars=20_000,
                    )
                )
                logger.info(f"PatternMatcher CSV logging enabled at {cfg.llm_pattern_log_path}")
        except Exception as e:
            logger.debug(f"PatternMatcher CSV logging init failed (non-fatal): {e}")
    
    def match(self, pattern: Dict[str, Any], item: Dict[str, Any]) -> bool:
        """
        Check if pattern matches item using LLM-based semantic matching.
        
        Args:
            pattern: Pattern to match
            item: Item to check against
            
        Returns:
            True if pattern matches item
        """
        # If LLM is not available, use simple matching
        if self.llm_client is None:
            return self._simple_match(pattern, item)
        
        # Check cache first
        cache_key = self._get_cache_key(pattern, item)
        if cache_key in self._cache:
            match, _ = self._cache[cache_key]
            if self._pm_logger:
                try:
                    batch_id = f"cache_{uuid.uuid4()}"
                    self._pm_logger.log_pair(
                        batch_id=batch_id,
                        pair_index=0,
                        pattern=pattern,
                        item=item,
                        match_label=bool(match),
                        confidence=float(self._cache[cache_key][1]),
                        cache_hit=True,
                        fallback_used=False,
                        llm_used=False,
                        parse_ok=True,
                        error_type=None,
                        context="single_match_cache",
                    )
                except Exception:
                    pass
            return match
        
        # For single matches, batch them (process immediately with batch of 1)
        try:
            results = self._match_batch_with_llm([(0, pattern, item)], context="single_match_llm")
            if results:
                match, confidence = results[0]
                # Cache result
                self._cache_result(cache_key, match, confidence)
                return match
        except Exception as e:
            logger.warning(f"LLM pattern matching failed: {e}. Falling back to simple matching.")
            if self.fallback_to_simple:
                return self._simple_match(pattern, item)
            raise
        
        return False
    
    def find_matching(self, pattern: Dict[str, Any], 
                     items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find items matching pattern using batched LLM matching.
        
        Args:
            pattern: Pattern to match
            items: List of items to search
            
        Returns:
            List of matching items
        """
        if not items:
            return []
        
        # If LLM is not available, use simple matching
        if self.llm_client is None:
            return self._simple_find_matching(pattern, items)
        
        # Check cache for all items first
        results: List[Optional[bool]] = [None] * len(items)
        uncached_items: List[Tuple[int, Dict[str, Any]]] = []
        
        for i, item in enumerate(items):
            cache_key = self._get_cache_key(pattern, item)
            if cache_key in self._cache:
                match, _ = self._cache[cache_key]
                results[i] = match
                if self._pm_logger:
                    try:
                        batch_id = f"cache_{uuid.uuid4()}"
                        self._pm_logger.log_pair(
                            batch_id=batch_id,
                            pair_index=i,
                            pattern=pattern,
                            item=item,
                            match_label=bool(match),
                            confidence=float(self._cache[cache_key][1]),
                            cache_hit=True,
                            fallback_used=False,
                            llm_used=False,
                            parse_ok=True,
                            error_type=None,
                            context="find_matching_cache",
                        )
                    except Exception:
                        pass
            else:
                uncached_items.append((i, item))
        
        # If all were cached, return matching items
        if not uncached_items:
            matching = []
            for i, item in enumerate(items):
                if results[i]:
                    matching.append(item)
            return matching
        
        # Process uncached items in batches
        try:
            for batch_start in range(0, len(uncached_items), self.batch_size):
                batch = uncached_items[batch_start:batch_start + self.batch_size]
                # Create pattern-item pairs for batch
                batch_pairs = [(idx, pattern, item) for idx, item in batch]
                
                batch_results = self._match_batch_with_llm(batch_pairs, context="find_matching_llm")
                
                # Store results and cache them
                for (orig_idx, item), (match, confidence) in zip(batch, batch_results):
                    results[orig_idx] = match
                    cache_key = self._get_cache_key(pattern, item)
                    self._cache_result(cache_key, match, confidence)
            
            # Collect matching items
            matching = []
            for i, item in enumerate(items):
                if results[i]:
                    matching.append(item)
            return matching
            
        except Exception as e:
            logger.warning(f"LLM batch pattern matching failed: {e}. Falling back to simple matching.")
            if self.fallback_to_simple:
                return self._simple_find_matching(pattern, items)
            raise
    
    def extract_bindings(self, pattern: Dict[str, Any], 
                        item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract variable bindings from pattern match.
        
        This is a placeholder - can be enhanced to extract variables from LLM responses.
        For now, returns empty dict (variables would need to be identified in the pattern).
        """
        # TODO: Enhance to extract variables from LLM responses
        # For now, return empty dict
        return {}
    
    def _simple_match(self, pattern: Dict[str, Any], item: Dict[str, Any]) -> bool:
        """
        Simple equality-based matching (fallback when LLM is not available).
        
        Args:
            pattern: Pattern to match
            item: Item to check against
            
        Returns:
            True if pattern matches item
        """
        for key, value in pattern.items():
            if key not in item:
                return False
            if isinstance(value, dict) and isinstance(item[key], dict):
                # Recursive check for nested dicts
                if not self._simple_match(value, item[key]):
                    return False
            elif value != item[key]:
                return False
        return True
    
    def _simple_find_matching(self, pattern: Dict[str, Any], 
                             items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Simple equality-based matching for multiple items (fallback).
        
        Args:
            pattern: Pattern to match
            items: List of items to search
            
        Returns:
            List of matching items
        """
        matching = []
        for item in items:
            if self._simple_match(pattern, item):
                matching.append(item)
        return matching
    
    def _match_batch_with_llm(
        self,
        batch: List[Tuple[int, Dict[str, Any], Dict[str, Any]]],
        context: Optional[str] = None,
    ) -> List[Tuple[bool, float]]:
        """
        Use LLM to match a batch of patterns.
        
        Args:
            batch: List of (original_index, pattern, item) tuples
            
        Returns:
            List of (match, confidence) tuples
        """
        if not self.llm_client:
            raise RuntimeError("LLM client not available")
        
        # Build prompt for LLM
        prompt = self._build_matching_prompt(batch)
        batch_id = str(uuid.uuid4())
        t0 = time.time()
        cache_hits = 0  # caller logs cache hits; for LLM batch this is 0
        
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
            
            response = self.llm_client.chat(messages, temperature=0.0)
            content = self.llm_client.extract_assistant_content(response)
            latency_ms = (time.time() - t0) * 1000.0
            
            if not content:
                logger.warning("LLM returned empty content for pattern matching")
                if self._pm_logger:
                    try:
                        self._pm_logger.log_batch(
                            batch_id=batch_id,
                            model=str(self.model or ""),
                            num_pairs=len(batch),
                            prompt_text=prompt,
                            response_text="",
                            latency_ms=latency_ms,
                            cache_hits=cache_hits,
                            fallback_used=self.fallback_to_simple,
                            parse_ok=False,
                            error_type="empty_response",
                        )
                        for pair_index, (_, p, it) in enumerate(batch):
                            self._pm_logger.log_pair(
                                batch_id=batch_id,
                                pair_index=pair_index,
                                pattern=p,
                                item=it,
                                match_label=False,
                                confidence=0.0,
                                cache_hit=False,
                                fallback_used=self.fallback_to_simple,
                                llm_used=True,
                                parse_ok=False,
                                error_type="empty_response",
                                context=context,
                            )
                    except Exception:
                        pass
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

                if self._pm_logger:
                    try:
                        self._pm_logger.log_batch(
                            batch_id=batch_id,
                            model=str(self.model or ""),
                            num_pairs=len(batch),
                            prompt_text=prompt,
                            response_text=content,
                            latency_ms=latency_ms,
                            cache_hits=cache_hits,
                            fallback_used=False,
                            parse_ok=True,
                            error_type=None,
                        )
                        for pair_index, ((_, p, it), (m, conf)) in enumerate(zip(batch, results)):
                            self._pm_logger.log_pair(
                                batch_id=batch_id,
                                pair_index=pair_index,
                                pattern=p,
                                item=it,
                                match_label=bool(m),
                                confidence=float(conf),
                                cache_hit=False,
                                fallback_used=False,
                                llm_used=True,
                                parse_ok=True,
                                error_type=None,
                                context=context,
                            )
                    except Exception:
                        pass
                
                return results
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}. Content: {content[:200]}")
                if self._pm_logger:
                    try:
                        self._pm_logger.log_batch(
                            batch_id=batch_id,
                            model=str(self.model or ""),
                            num_pairs=len(batch),
                            prompt_text=prompt,
                            response_text=content,
                            latency_ms=latency_ms,
                            cache_hits=cache_hits,
                            fallback_used=self.fallback_to_simple,
                            parse_ok=False,
                            error_type="json_decode_error",
                        )
                        for pair_index, (_, p, it) in enumerate(batch):
                            self._pm_logger.log_pair(
                                batch_id=batch_id,
                                pair_index=pair_index,
                                pattern=p,
                                item=it,
                                match_label=False,
                                confidence=0.0,
                                cache_hit=False,
                                fallback_used=self.fallback_to_simple,
                                llm_used=True,
                                parse_ok=False,
                                error_type="json_decode_error",
                                context=context,
                            )
                    except Exception:
                        pass
                return [(False, 0.0)] * len(batch)
                
        except Exception as e:
            logger.error(f"Error calling LLM for pattern matching: {e}", exc_info=True)
            if self._pm_logger:
                try:
                    latency_ms = (time.time() - t0) * 1000.0
                    self._pm_logger.log_batch(
                        batch_id=batch_id,
                        model=str(self.model or ""),
                        num_pairs=len(batch),
                        prompt_text=prompt,
                        response_text="",
                        latency_ms=latency_ms,
                        cache_hits=cache_hits,
                        fallback_used=self.fallback_to_simple,
                        parse_ok=False,
                        error_type=type(e).__name__,
                    )
                    for pair_index, (_, p, it) in enumerate(batch):
                        self._pm_logger.log_pair(
                            batch_id=batch_id,
                            pair_index=pair_index,
                            pattern=p,
                            item=it,
                            match_label=False,
                            confidence=0.0,
                            cache_hit=False,
                            fallback_used=self.fallback_to_simple,
                            llm_used=True,
                            parse_ok=False,
                            error_type=type(e).__name__,
                            context=context,
                        )
                except Exception:
                    pass
            raise
    
    def _build_matching_prompt(
        self,
        batch: List[Tuple[int, Dict[str, Any], Dict[str, Any]]]
    ) -> str:
        """
        Build prompt for LLM pattern matching.
        
        Args:
            batch: List of (original_index, pattern, item) tuples
            
        Returns:
            Prompt string
        """
        prompt_parts = [
            "You are a pattern matching assistant for a cognitive AI system's working memory.",
            "",
            "## CRITICAL: What Pattern Matching Means",
            "",
            "A pattern MATCHES content if the content SATISFIES ALL constraints in the pattern.",
            "This is SUBSET matching, NOT exact matching:",
            "- Content may have MANY extra fields not in the pattern - this is OK, IGNORE them",
            "- Only check fields that ARE in the pattern",
            "- If pattern has {\"goal_type\": \"achieve\"}, match=true if content has goal_type=\"achieve\" (ignore all other fields)",
            "",
            "## The 'type' Field is a Semantic Hint",
            "",
            "When pattern has \"type\": \"goal\" or \"type\": \"task\", this indicates WHAT KIND of thing we expect:",
            "- \"type\": \"goal\" means content should represent a goal (has goal_type, priority, status, etc.)",
            "- \"type\": \"task\" means content should represent a task/action item",
            "- Content does NOT need a literal \"type\" field! Infer from context.",
            "",
            "## Matching Rules",
            "",
            "1. For each field in pattern, check if content satisfies it:",
            "   - Exact value: pattern.field == content.field",
            "   - Semantic similarity: \"high priority\" matches priority=0.9",
            "   - Type inference: pattern.type=\"goal\" matches content with goal_type, priority, etc.",
            "",
            "2. Special patterns:",
            "   - \"needs_information\": true - match if content seems to require more info",
            "   - \"complexity\": \"high\" - match if content description suggests complexity",
            "   - \"domain\": \"X\" - match if content is related to domain X",
            "",
            "3. Contradiction check (pattern.type == 'contradiction_check'):",
            "   - Check if pattern.text semantically contradicts content.text",
            "   - match=true means they CONTRADICT, match=false means they align or are unrelated",
            "",
            "## Examples",
            "",
            "Pattern: {\"type\": \"goal\", \"goal_type\": \"achieve\"}",
            "Content: {\"name\": \"implement_feature\", \"goal_type\": \"achieve\", \"priority\": 0.9, ...}",
            "Result: match=true (content has goal_type=\"achieve\", and looks like a goal)",
            "",
            "Pattern: {\"type\": \"task\", \"domain\": \"code_analysis\"}",
            "Content: {\"name\": \"be_helpful_assistant\", \"goal_type\": \"maintain\", ...}",
            "Result: match=false (not related to code_analysis domain)",
            "",
            "## Output Format",
            "",
            "Return a JSON array with one object per pair:",
            "[{\"match\": true/false, \"confidence\": 0.0-1.0}, ...]",
            "",
            "Pattern-Content pairs to evaluate:",
            ""
        ]
        
        for idx, (orig_idx, pattern, item) in enumerate(batch):
            prompt_parts.append(f"Pair {idx + 1}:")
            prompt_parts.append(f"  Pattern: {json.dumps(pattern, indent=2)}")
            prompt_parts.append(f"  Content: {json.dumps(item, indent=2)}")
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    def _get_cache_key(self, pattern: Dict[str, Any], item: Dict[str, Any]) -> str:
        """Generate cache key for pattern-item pair."""
        # Create deterministic string representation
        pattern_str = json.dumps(pattern, sort_keys=True)
        item_str = json.dumps(item, sort_keys=True)
        combined = f"{pattern_str}|||{item_str}"
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
        logger.debug("Cleared pattern matching cache")
