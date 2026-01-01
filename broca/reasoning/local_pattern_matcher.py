"""
Local (non-LLM) pattern matcher.

This is a thin adapter around `broca.matching.GeneralMatcher` so the rest of the
codebase can keep using the legacy `match()` / `match_batch()` interface.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LocalPatternMatcher:
    """
    Deterministic, local matcher implementing the minimal surface area of LLMPatternMatcher:
    - match(pattern: dict, content: dict) -> bool
    - match_batch([(pattern, content), ...]) -> [(bool, confidence), ...]
    """

    def __init__(
        self,
        *,
        cache_size: int = 20_000,
        text_match_threshold: float = 0.82,
        max_text_chars: int = 20_000,
    ) -> None:
        try:
            from broca.matching import GeneralMatcher, MatcherConfig

            cfg = MatcherConfig(
                cache_size=int(max(0, cache_size)),
                max_text_chars=int(max(256, max_text_chars)),
                text_threshold=float(text_match_threshold),
            )
            self._matcher = GeneralMatcher(cfg)
        except Exception as e:
            logger.warning(f"Failed to initialize GeneralMatcher; local matching disabled: {e}", exc_info=True)
            self._matcher = None

    def match(self, pattern: Dict[str, Any], content: Dict[str, Any]) -> bool:
        ok, _conf = self.match_with_confidence(pattern, content)
        return ok

    def match_with_confidence(
        self,
        pattern: Any,
        content: Any,
    ) -> Tuple[bool, float]:
        if self._matcher is None:
            return (False, 0.0)
        return self._matcher.match_with_confidence(pattern, content)

    def match_batch(
        self,
        pattern_content_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    ) -> List[Tuple[bool, float]]:
        if self._matcher is None:
            return [(False, 0.0) for _ in pattern_content_pairs]
        return self._matcher.match_batch(pattern_content_pairs)

    def rank_text_candidates(self, query: str, candidates: List[str], *, top_k: Optional[int] = None):
        if self._matcher is None:
            try:
                from broca.matching.ann_index import ANNQueryResult

                return ANNQueryResult(indices=[], scores=[], backend="disabled")
            except Exception:
                return {"indices": [], "scores": [], "backend": "disabled"}  # best-effort fallback
        return self._matcher.rank_text_candidates(query, candidates, top_k=top_k)
