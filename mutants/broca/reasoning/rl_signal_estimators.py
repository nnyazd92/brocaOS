"""
LLM-based estimators for RL signals when upstream sensors are missing/low-quality.

Design goals:
- Avoid silent placeholder defaults (0.0 / 0.5) masquerading as real measurements
- Provide bounded [0,1] estimates + an uncertainty score
- Batch multiple missing-signal estimates into a single LLM call
- Cache by (needed_signals + compact_context_hash) for determinism and cost control
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..llm import LLMClient, create_llm_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SignalEstimate:
    value: float
    uncertainty: float
    estimator: str = "estimated_llm"


class LLMRLSignalEstimator:
    """
    Estimate RL signal components using an LLM (default: gpt-5-nano).

    Public surface is intentionally small:
    - estimate_dissonance(context) -> (overall_dissonance, uncertainty)
    - estimate_surprise(context)   -> (raw_surprise, uncertainty)
    - estimate_curiosity(context)  -> (curiosity_drive, uncertainty)
    - estimate_information_gain(context) -> (info_gain, uncertainty)
    - estimate_coherence(context)  -> (coherence_pleasure, uncertainty)
    """

    def __init__(
        self,
        model: str = "gpt-5-nano",
        llm_client: Optional["LLMClient"] = None,
        batch_size: int = 8,
        cache_size: int = 128,
        timeout_s: Optional[float] = None,
    ) -> None:
        self.model = model
        self.batch_size = max(1, int(batch_size))
        self.cache_size = max(0, int(cache_size))
        self.timeout_s = timeout_s
        self.llm_client: Optional["LLMClient"] = llm_client or create_llm_client(model=model)
        self._cache: "OrderedDict[str, Dict[str, SignalEstimate]]" = OrderedDict()

    # ---- single-signal convenience wrappers ----
    def estimate_dissonance(self, *, context: Dict[str, Any]) -> Tuple[float, float]:
        est = self._estimate_many(["dissonance"], context).get("dissonance")
        if est is None:
            return 0.5, 1.0
        return est.value, est.uncertainty

    def estimate_surprise(self, *, context: Dict[str, Any]) -> Tuple[float, float]:
        est = self._estimate_many(["surprise"], context).get("surprise")
        if est is None:
            return 0.5, 1.0
        return est.value, est.uncertainty

    def estimate_curiosity(self, *, context: Dict[str, Any]) -> Tuple[float, float]:
        est = self._estimate_many(["curiosity"], context).get("curiosity")
        if est is None:
            return 0.5, 1.0
        return est.value, est.uncertainty

    def estimate_information_gain(self, *, context: Dict[str, Any]) -> Tuple[float, float]:
        est = self._estimate_many(["information_gain"], context).get("information_gain")
        if est is None:
            return 0.0, 1.0
        return est.value, est.uncertainty

    def estimate_coherence(self, *, context: Dict[str, Any]) -> Tuple[float, float]:
        est = self._estimate_many(["coherence"], context).get("coherence")
        if est is None:
            return 0.5, 1.0
        return est.value, est.uncertainty

    # ---- internal ----
    def _estimate_many(self, needed: List[str], context: Dict[str, Any]) -> Dict[str, SignalEstimate]:
        if not self.llm_client:
            return {}

        needed_norm = [str(x).strip().lower() for x in needed if str(x).strip()]
        needed_norm = sorted(set(needed_norm))
        if not needed_norm:
            return {}

        cache_key = self._cache_key(needed_norm, context)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        prompt = self._build_prompt(needed_norm, context)
        t0 = time.time()
        try:
            response = self.llm_client.chat(
                [
                    {"role": "system", "content": "You output strict JSON only. No prose."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = self.llm_client.extract_assistant_content(response)
            parsed = self._parse_response(content, needed_norm)
            self._cache_put(cache_key, parsed)
            dt_ms = (time.time() - t0) * 1000.0
            logger.debug(f"LLMRLSignalEstimator: estimated {needed_norm} in {dt_ms:.1f}ms")
            return parsed
        except Exception as e:
            logger.debug(f"LLMRLSignalEstimator failed: {e}", exc_info=True)
            return {}

    def _build_prompt(self, needed: List[str], context: Dict[str, Any]) -> str:
        # Keep context compact: we hash large blobs and include only small summaries.
        compact_context = self._compact_context(context)
        wanted = ", ".join(needed)
        return (
            "Estimate missing RL signal components for a cognitive architecture.\n"
            "Each signal is a scalar in [0,1]. Provide uncertainty in [0,1] (1 = very uncertain).\n\n"
            "Signal definitions:\n"
            "- dissonance: overall cognitive dissonance (0 none, 1 extreme)\n"
            "- surprise: surprise / prediction error magnitude (0 none, 1 extreme)\n"
            "- curiosity: intrinsic exploration drive (0 none, 1 extreme)\n"
            "- information_gain: epistemic value / expected info gain (0 none, 1 high)\n"
            "- coherence: coherence pleasure / internal consistency (0 low, 1 high)\n\n"
            f"Needed: {wanted}\n\n"
            "Context (JSON):\n"
            f"{json.dumps(compact_context, sort_keys=True)}\n\n"
            "Return strict JSON with this shape:\n"
            "{\n"
            '  \"estimates\": {\n'
            '    \"dissonance\": {\"value\": 0.0, \"uncertainty\": 0.0},\n'
            '    \"surprise\": {\"value\": 0.0, \"uncertainty\": 0.0},\n'
            '    \"curiosity\": {\"value\": 0.0, \"uncertainty\": 0.0},\n'
            '    \"information_gain\": {\"value\": 0.0, \"uncertainty\": 0.0},\n'
            '    \"coherence\": {\"value\": 0.0, \"uncertainty\": 0.0}\n'
            "  }\n"
            "}\n"
            "Only include keys for signals in Needed."
        )

    def _compact_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        def _hash_if_large(obj: Any, limit: int = 2000) -> Any:
            try:
                s = json.dumps(obj, sort_keys=True, default=str)
            except Exception:
                s = str(obj)
            if len(s) <= limit:
                return obj
            h = hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
            return {"_hash": h, "_len": len(s)}

        compact: Dict[str, Any] = {}
        for k, v in (context or {}).items():
            if k in ("messages", "conversation", "raw_text", "tool_result"):
                compact[k] = _hash_if_large(v)
            else:
                compact[k] = _hash_if_large(v)
        return compact

    def _parse_response(self, content: str, needed: List[str]) -> Dict[str, SignalEstimate]:
        if not content:
            return {}
        try:
            data = json.loads(content)
        except Exception:
            # Attempt to extract JSON substring
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    data = json.loads(content[start : end + 1])
                except Exception:
                    return {}
            else:
                return {}

        estimates = data.get("estimates") if isinstance(data, dict) else None
        if not isinstance(estimates, dict):
            return {}

        out: Dict[str, SignalEstimate] = {}
        for key in needed:
            item = estimates.get(key)
            if not isinstance(item, dict):
                continue
            try:
                val = float(item.get("value"))
                unc = float(item.get("uncertainty"))
                val = max(0.0, min(1.0, val))
                unc = max(0.0, min(1.0, unc))
                out[key] = SignalEstimate(value=val, uncertainty=unc)
            except Exception:
                continue
        return out

    def _cache_key(self, needed: List[str], context: Dict[str, Any]) -> str:
        try:
            ctx = self._compact_context(context)
            payload = json.dumps({"needed": needed, "context": ctx}, sort_keys=True, default=str)
        except Exception:
            payload = str({"needed": needed})
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> Optional[Dict[str, SignalEstimate]]:
        if self.cache_size <= 0:
            return None
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _cache_put(self, key: str, value: Dict[str, SignalEstimate]) -> None:
        if self.cache_size <= 0:
            return
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)


