from __future__ import annotations

import difflib
import hashlib
import json
import logging
import math
import re
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from .config import MatcherConfig
from .ann_index import ANNQueryResult, TextANNIndexCache, try_rank_with_faiss

logger = logging.getLogger(__name__)

Pattern = Union[Dict[str, Any], str]
Content = Union[Dict[str, Any], str]


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    confidence: float
    backend: str
    reason: str


@dataclass(frozen=True)
class MatcherCapabilities:
    rapidfuzz: bool
    regex_module: bool
    flashtext: bool
    ahocorasick: bool
    simhash: bool
    datasketch: bool
    hashing_tfidf: bool
    sentence_transformers: bool


_WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "it",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "we",
    "they",
    "he",
    "she",
    "as",
    "at",
    "by",
    "from",
}


def _clamp01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return float(x)


def _normalize_text(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokenize(s: str) -> List[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(s)]


def _topic_tokens(s: str) -> List[str]:
    toks = _tokenize(s)
    return [t for t in toks if t not in _STOPWORDS]


def _safe_json_dumps(obj: Any) -> str:
    def _default(o: Any) -> str:
        return str(o)

    try:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=_default)
    except Exception:
        return json.dumps(str(obj), sort_keys=True, ensure_ascii=False, default=_default)


def _hash_key(pattern: Any, content: Any) -> str:
    payload = _safe_json_dumps({"pattern": pattern, "content": content})
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()


class GeneralMatcher:
    """
    One matcher to rule them all:
    - structured dict matching with operators
    - text similarity (substring/token/fuzzy)
    - optional local-ML similarity (hashing TF-IDF, embeddings)
    - optional high-throughput keyword engines (flashtext/ahocorasick) for future prefiltering

    This is a deterministic, local module (no remote LLM calls).
    """

    def __init__(self, config: Optional[MatcherConfig] = None) -> None:
        self.config = config or MatcherConfig()

        self._cache: Dict[str, MatchResult] = {}
        self._cache_order: deque[str] = deque()

        self._rapidfuzz = None
        self._regex_mod = None
        self._flashtext = None
        self._ahocorasick = None
        self._simhash = None
        self._datasketch = None

        self._hashing_vectorizer = None
        self._sentence_transformer = None
        self._embed_cache: Dict[str, Any] = {}
        self._embed_cache_order: deque[str] = deque()
        self._ann_cache = TextANNIndexCache(max_size=int(self.config.ann_index_cache_size))

        self._init_optional_backends()
        self._hard_keys = {k.strip().lower() for k in (self.config.hard_keys_csv or "").split(",") if k.strip()}
        self._field_thresholds = self._parse_field_thresholds(self.config.field_thresholds_csv)

    def capabilities(self) -> MatcherCapabilities:
        return MatcherCapabilities(
            rapidfuzz=self._rapidfuzz is not None,
            regex_module=self._regex_mod is not None,
            flashtext=self._flashtext is not None,
            ahocorasick=self._ahocorasick is not None,
            simhash=self._simhash is not None,
            datasketch=self._datasketch is not None,
            hashing_tfidf=self._hashing_vectorizer is not None,
            sentence_transformers=self._sentence_transformer is not None,
        )

    def match(self, pattern: Pattern, content: Content) -> MatchResult:
        if not self.config.enabled:
            return MatchResult(False, 0.0, backend="disabled", reason="Matcher disabled by config")

        key = _hash_key(pattern, content)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            result = self._match_uncached(pattern, content)
        except Exception as e:
            logger.debug(f"GeneralMatcher failed (treated as no-match): {e}", exc_info=True)
            result = MatchResult(False, 0.0, backend="error", reason=type(e).__name__)

        self._cache_set(key, result)
        return result

    def match_with_confidence(self, pattern: Pattern, content: Content) -> Tuple[bool, float]:
        r = self.match(pattern, content)
        return (bool(r.matched), float(r.confidence))

    def match_batch(self, pattern_content_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[Tuple[bool, float]]:
        return [self.match_with_confidence(p, c) for p, c in pattern_content_pairs]

    def rank_text_candidates(self, query: str, candidates: List[str], *, top_k: Optional[int] = None) -> ANNQueryResult:
        """
        Return indices/scores for the top-K most similar candidates to `query`.

        Uses FAISS + sentence-transformers when enabled and available; otherwise falls back
        to per-candidate scoring with the current local similarity ensemble.
        """
        if not candidates or not query:
            return ANNQueryResult(indices=[], scores=[], backend="none")

        k = int(top_k if top_k is not None else self.config.ann_top_k)
        k = max(1, min(k, len(candidates)))

        # FAISS path (best for large candidate sets)
        if self.config.enable_sentence_transformers:
            self._ensure_sentence_transformer()
        if self._sentence_transformer is not None:
            res = try_rank_with_faiss(
                cfg=self.config,
                cache=self._ann_cache,
                model=self._sentence_transformer,
                model_name=str(self.config.sentence_transformer_model),
                query=query,
                candidates=candidates,
                top_k=k,
            )
            if res is not None:
                return res

        # Fallback: brute-force score with current ensemble (still deterministic).
        scored: List[Tuple[int, float]] = []
        qn = _normalize_text(query)
        for i, c in enumerate(candidates):
            cn = _normalize_text(c or "")
            scored.append((i, float(self._text_similarity(qn, cn))))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:k]
        return ANNQueryResult(indices=[i for i, _ in top], scores=[s for _, s in top], backend="bruteforce")

    def _cache_set(self, key: str, value: MatchResult) -> None:
        if self.config.cache_size <= 0:
            return
        if key in self._cache:
            self._cache[key] = value
            return
        self._cache[key] = value
        self._cache_order.append(key)
        while len(self._cache_order) > self.config.cache_size:
            old = self._cache_order.popleft()
            self._cache.pop(old, None)

    def _init_optional_backends(self) -> None:
        if self.config.enable_rapidfuzz:
            try:
                from rapidfuzz import fuzz  # type: ignore

                self._rapidfuzz = fuzz
            except Exception:
                self._rapidfuzz = None

        if self.config.enable_regex_module:
            try:
                import regex as regex_mod  # type: ignore

                self._regex_mod = regex_mod
            except Exception:
                self._regex_mod = None

        if self.config.enable_flashtext:
            try:
                from flashtext import KeywordProcessor  # type: ignore

                self._flashtext = KeywordProcessor
            except Exception:
                self._flashtext = None

        if self.config.enable_ahocorasick:
            try:
                import ahocorasick  # type: ignore

                self._ahocorasick = ahocorasick
            except Exception:
                self._ahocorasick = None

        if self.config.enable_simhash:
            try:
                from simhash import Simhash  # type: ignore

                self._simhash = Simhash
            except Exception:
                self._simhash = None

        if self.config.enable_datasketch_minhash:
            try:
                import datasketch  # type: ignore

                self._datasketch = datasketch
            except Exception:
                self._datasketch = None

        if self.config.enable_hashing_tfidf:
            try:
                from sklearn.feature_extraction.text import HashingVectorizer

                ngram_max = max(1, int(self.config.hashing_tfidf_ngram_max))
                self._hashing_vectorizer = HashingVectorizer(
                    n_features=int(self.config.hashing_tfidf_n_features),
                    alternate_sign=False,
                    norm="l2",
                    ngram_range=(1, ngram_max),
                    lowercase=True,
                )
            except Exception:
                self._hashing_vectorizer = None

        # SentenceTransformer is expensive; lazy-load only when enabled and needed.
        self._sentence_transformer = None

    def _ensure_sentence_transformer(self) -> None:
        if not self.config.enable_sentence_transformers:
            return
        if self._sentence_transformer is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            model = SentenceTransformer(self.config.sentence_transformer_model)

            # Optional: disk-backed cache to persist pattern embeddings across restarts.
            try:
                from .embedding_cache import CachedEmbeddingModel, SQLiteEmbeddingCache, load_embedding_cache_config_from_env

                cache_cfg = load_embedding_cache_config_from_env()
                cache = SQLiteEmbeddingCache(cache_cfg)
                model = CachedEmbeddingModel(model=model, model_name=str(self.config.sentence_transformer_model), cache=cache)
            except Exception as e:
                logger.debug(f"Embedding cache disabled/unavailable: {e}", exc_info=True)

            self._sentence_transformer = model
            logger.info(f"SentenceTransformer loaded: model={self.config.sentence_transformer_model}")
        except Exception as e:
            logger.warning(f"SentenceTransformer unavailable: {e}")
            self._sentence_transformer = None

    def _coerce_to_text(self, x: Any) -> str:
        if x is None:
            return ""
        if isinstance(x, str):
            return x[: self.config.max_text_chars]
        return _safe_json_dumps(x)[: self.config.max_text_chars]

    def _match_uncached(self, pattern: Pattern, content: Content) -> MatchResult:
        # 1. Handle string patterns
        if isinstance(pattern, str):
            if isinstance(content, str):
                score = self._score_text_similarity(pattern, content)
                return MatchResult(score >= self.config.text_threshold, score, "text", "string_similarity")
            else:
                # String pattern vs dict content: check if string is in any value
                content_str = _safe_json_dumps(content)
                score = self._score_text_similarity(pattern, content_str)
                return MatchResult(score >= self.config.text_threshold, score, "text", "string_in_dict")

        # 2. Handle dict patterns (structured matching)
        if isinstance(pattern, dict):
            if not isinstance(content, dict):
                return MatchResult(False, 0.0, "dict", "type_mismatch")
            
            return self._match_dict(pattern, content)

        return MatchResult(False, 0.0, "unknown", "unsupported_pattern_type")

    def _match_dict(self, pattern: Dict[str, Any], content: Dict[str, Any]) -> MatchResult:
        """Match a dictionary pattern against dictionary content with operator support."""
        for key, p_val in pattern.items():
            if key not in content:
                return MatchResult(False, 0.0, "dict", f"missing_key: {key}")
            
            c_val = content[key]
            
            # Handle operators
            if isinstance(p_val, dict) and any(k.startswith("$") for k in p_val):
                for op, val in p_val.items():
                    if op == "$gt":
                        if not (c_val > val): return MatchResult(False, 0.0, "operator", f"{key} not > {val}")
                    elif op == "$lt":
                        if not (c_val < val): return MatchResult(False, 0.0, "operator", f"{key} not < {val}")
                    elif op == "$gte":
                        if not (c_val >= val): return MatchResult(False, 0.0, "operator", f"{key} not >= {val}")
                    elif op == "$lte":
                        if not (c_val <= val): return MatchResult(False, 0.0, "operator", f"{key} not <= {val}")
                    elif op == "$eq":
                        if not (c_val == val): return MatchResult(False, 0.0, "operator", f"{key} not == {val}")
                    elif op == "$ne":
                        if not (c_val != val): return MatchResult(False, 0.0, "operator", f"{key} not != {val}")
                    elif op == "$in":
                        if c_val not in val: return MatchResult(False, 0.0, "operator", f"{key} not in {val}")
                    elif op == "$nin":
                        if c_val in val: return MatchResult(False, 0.0, "operator", f"{key} in {val}")
            elif isinstance(p_val, dict) and isinstance(c_val, dict):
                # Recursive match
                res = self._match_dict(p_val, c_val)
                if not res.matched:
                    return res
            elif p_val != c_val:
                # Fallback to text similarity if both are strings
                if isinstance(p_val, str) and isinstance(c_val, str):
                    score = self._score_text_similarity(p_val, c_val)
                    if score < self.config.text_threshold:
                        return MatchResult(False, score, "text", f"low_similarity: {key}")
                else:
                    return MatchResult(False, 0.0, "dict", f"value_mismatch: {key}")
        
        return MatchResult(True, 1.0, "dict", "all_keys_matched")
        if isinstance(pattern, str):
            pattern = {"text": pattern}
        if isinstance(content, str):
            content = {"text": content}

        if not isinstance(pattern, dict) or not isinstance(content, dict):
            return MatchResult(False, 0.0, backend="type", reason="pattern/content not dict")

        p_type = pattern.get("type")
        if p_type == "contradiction_check":
            a = self._coerce_to_text(pattern.get("text", ""))
            b = self._coerce_to_text(content.get("text", ""))
            score = self._contradiction_score(a, b)
            matched = bool(score >= self.config.contradiction_threshold)
            return MatchResult(matched, score, backend="contradiction", reason="contradiction_check")

        confidences: List[float] = []
        for key, p_val in pattern.items():
            if key == "description":
                continue
            if key not in content:
                return MatchResult(False, 0.0, backend="structured", reason=f"missing_key:{key}")
            ok, conf, reason = self._match_value(str(key), p_val, content.get(key))
            if not ok:
                return MatchResult(False, _clamp01(conf), backend="structured", reason=reason)
            confidences.append(conf)

        conf = _clamp01(min(confidences) if confidences else 1.0)
        return MatchResult(True, conf, backend="structured", reason="all_fields_matched")

    def _is_text_like_key(self, key: str) -> bool:
        key = (key or "").lower()
        if key == "text":
            return True
        return key.endswith("_text") or key.endswith("_message") or key.endswith("_description")

    def _is_operator_dict(self, d: Dict[str, Any]) -> bool:
        if len(d) != 1:
            return False
        return next(iter(d.keys())) in {
            "contains",
            "regex",
            "in",
            "any",
            "all",
            "eq",
            "ne",
            "gt",
            "gte",
            "lt",
            "lte",
            "exists",
        }

    def _match_value(self, key_path: str, p_val: Any, c_val: Any) -> Tuple[bool, float, str]:
        key_path = str(key_path or "")
        if isinstance(p_val, dict) and self._is_operator_dict(p_val):
            op, arg = next(iter(p_val.items()))
            ok, conf = self._match_operator(key_path, op, arg, c_val)
            return ok, conf, f"op:{op}"

        if isinstance(p_val, dict):
            if not isinstance(c_val, dict):
                return False, 0.0, "nested_type_mismatch"
            sub_confs: List[float] = []
            for k, v in p_val.items():
                if k == "description":
                    continue
                if k not in c_val:
                    return False, 0.0, f"missing_nested_key:{k}"
                child_path = f"{key_path}.{k}" if key_path else str(k)
                ok, conf, reason = self._match_value(child_path, v, c_val.get(k))
                if not ok:
                    return False, conf, reason
                sub_confs.append(conf)
            return True, _clamp01(min(sub_confs) if sub_confs else 1.0), "nested_ok"

        if isinstance(p_val, list):
            if isinstance(c_val, list):
                ok, conf = self._match_list_subset(p_val, c_val)
                return ok, conf, "list_subset"
            # list pattern against scalar: any element matches
            for v in p_val:
                ok, conf, _ = self._match_value(key_path, v, c_val)
                if ok:
                    return True, conf, "list_any"
            return False, 0.0, "list_any_failed"

        # Scalars
        ok, conf = self._match_scalar(p_val, c_val, key_path)
        return ok, conf, "scalar"

    def _match_operator(self, key_path: str, op: str, arg: Any, c_val: Any) -> Tuple[bool, float]:
        if op == "exists":
            return (bool(arg) is True, 1.0)

        if op == "contains":
            if c_val is None:
                return (False, 0.0)
            if isinstance(c_val, (list, tuple, set)):
                return (arg in c_val, 1.0 if arg in c_val else 0.0)
            c_text = _normalize_text(self._coerce_to_text(c_val))
            a_text = _normalize_text(self._coerce_to_text(arg))
            ok = bool(a_text) and a_text in c_text
            return (ok, 0.9 if ok else 0.0)

        if op == "regex":
            c_text = self._coerce_to_text(c_val)
            pat = str(arg)
            try:
                if self._regex_mod is not None:
                    ok = self._regex_mod.search(pat, c_text, flags=self._regex_mod.IGNORECASE) is not None
                else:
                    ok = re.search(pat, c_text, flags=re.IGNORECASE) is not None
                return (ok, 0.9 if ok else 0.0)
            except Exception:
                return (False, 0.0)

        if op == "in":
            try:
                seq = list(arg)
                return (c_val in seq, 1.0 if c_val in seq else 0.0)
            except Exception:
                return (False, 0.0)

        if op in {"gt", "gte", "lt", "lte"}:
            try:
                c_num = float(c_val)
                a_num = float(arg)
                if op == "gt":
                    ok = c_num > a_num
                elif op == "gte":
                    ok = c_num >= a_num
                elif op == "lt":
                    ok = c_num < a_num
                else:
                    ok = c_num <= a_num
                return (ok, 1.0 if ok else 0.0)
            except Exception:
                return (False, 0.0)

        if op == "eq":
            return self._match_scalar(arg, c_val, key_path)
        if op == "ne":
            ok, _ = self._match_scalar(arg, c_val, key_path)
            return (not ok, 1.0 if not ok else 0.0)

        if op == "any":
            if not isinstance(arg, list):
                return (False, 0.0)
            best = 0.0
            for v in arg:
                ok, conf = self._match_scalar(v, c_val, key_path)
                best = max(best, conf)
                if ok:
                    return (True, conf)
            return (False, best)

        if op == "all":
            if not isinstance(arg, list):
                return (False, 0.0)
            confs: List[float] = []
            for v in arg:
                ok, conf = self._match_scalar(v, c_val, key_path)
                if not ok:
                    return (False, conf)
                confs.append(conf)
            return (True, _clamp01(min(confs) if confs else 1.0))

        return (False, 0.0)

    def _match_list_subset(self, p_list: List[Any], c_list: List[Any]) -> Tuple[bool, float]:
        if not p_list:
            return (True, 1.0)
        if not c_list:
            return (False, 0.0)
        confs: List[float] = []
        for p in p_list:
            best = 0.0
            matched = False
            for c in c_list:
                ok, conf = self._match_scalar(p, c, key="list_item")
                best = max(best, conf)
                if ok:
                    matched = True
                    break
            if not matched:
                return (False, best)
            confs.append(best if best > 0 else 1.0)
        return (True, _clamp01(min(confs) if confs else 1.0))

    def _match_scalar(self, p_val: Any, c_val: Any, key_path: str) -> Tuple[bool, float]:
        if p_val == "*" or p_val == "__ANY__":
            return (True, 0.6)

        if not isinstance(p_val, str) or not isinstance(c_val, str):
            return (p_val == c_val, 1.0 if p_val == c_val else 0.0)

        p = _normalize_text(p_val)
        c = _normalize_text(c_val)
        if p == c:
            return (True, 1.0)
        if not p:
            return (False, 0.0)

        # Avoid fuzzy matching on hard/structured keys.
        key_path_l = (key_path or "").lower()
        leaf = key_path_l.rsplit(".", 1)[-1] if key_path_l else ""
        if key_path_l in self._hard_keys or leaf in self._hard_keys:
            return (False, 0.0)
        if not self._is_text_like_key(leaf or key_path_l):
            return (False, 0.0)

        conf = self._text_similarity(p, c)
        thresh = self._field_threshold(key_path_l)
        return (bool(conf >= thresh), conf)

    def _parse_field_thresholds(self, raw: str) -> Dict[str, float]:
        out: Dict[str, float] = {}
        if not raw:
            return out
        for part in raw.split(","):
            part = part.strip()
            if not part or ":" not in part:
                continue
            k, v = part.split(":", 1)
            k = k.strip().lower()
            try:
                out[k] = float(v.strip())
            except Exception:
                continue
        return out

    def _field_threshold(self, key_path: str) -> float:
        k = (key_path or "").lower()
        leaf = k.rsplit(".", 1)[-1] if k else ""
        if k in self._field_thresholds:
            return float(self._field_thresholds[k])
        if leaf in self._field_thresholds:
            return float(self._field_thresholds[leaf])
        # Common aliases
        if leaf.endswith("_description") and "description" in self._field_thresholds:
            return float(self._field_thresholds["description"])
        if leaf.endswith("_message") and "message" in self._field_thresholds:
            return float(self._field_thresholds["message"])
        return float(self.config.text_threshold)

    def _text_similarity(self, p: str, c: str) -> float:
        # fast paths
        if p == c:
            return 1.0
        if p in c:
            return 0.92

        scores: List[float] = []

        # token overlap / subset
        p_tokens = set(_topic_tokens(p))
        c_tokens = set(_topic_tokens(c))
        if p_tokens and c_tokens:
            if p_tokens.issubset(c_tokens):
                scores.append(0.88)
            inter = len(p_tokens & c_tokens)
            union = len(p_tokens | c_tokens)
            jacc = inter / max(1, union)
            scores.append(_clamp01(0.55 + 0.45 * jacc))

            # If all topic tokens match but phrase order differs, token overlap will capture it.
            if jacc >= self.config.text_threshold:
                return _clamp01(0.55 + 0.45 * jacc)

        # difflib (bounded)
        if len(p) <= 500 and len(c) <= 500:
            scores.append(_clamp01(difflib.SequenceMatcher(a=p, b=c).ratio()))

        # rapidfuzz
        if self._rapidfuzz is not None and len(p) <= 5000 and len(c) <= 5000:
            try:
                scores.append(_clamp01(float(self._rapidfuzz.token_set_ratio(p, c)) / 100.0))
                scores.append(_clamp01(float(self._rapidfuzz.partial_ratio(p, c)) / 100.0))
                if max(scores) >= self.config.text_threshold:
                    return _clamp01(max(scores))
            except Exception:
                pass

        # hashing TF-IDF cosine
        if self._hashing_vectorizer is not None and len(p) <= 20000 and len(c) <= 20000:
            try:
                X = self._hashing_vectorizer.transform([p, c])
                sim = float(X[0].multiply(X[1]).sum())
                scores.append(_clamp01(sim))
                if sim >= self.config.text_threshold:
                    return _clamp01(sim)
            except Exception:
                pass

        # simhash near-duplicate similarity (cheap; good for "same text with small edits")
        if self._simhash is not None and len(p) <= 20000 and len(c) <= 20000:
            try:
                fp = self._simhash(_topic_tokens(p))
                fc = self._simhash(_topic_tokens(c))
                dist = fp.distance(fc)
                sim = _clamp01(1.0 - (float(dist) / 64.0))
                scores.append(sim)
                if sim >= self.config.text_threshold:
                    return sim
            except Exception:
                pass

        # datasketch MinHash Jaccard estimate on topic tokens (cheap-ish, robust to ordering)
        if self._datasketch is not None and p_tokens and c_tokens:
            try:
                MinHash = self._datasketch.MinHash  # type: ignore[attr-defined]
                mh1 = MinHash(num_perm=64)
                mh2 = MinHash(num_perm=64)
                for t in p_tokens:
                    mh1.update(t.encode("utf-8", errors="replace"))
                for t in c_tokens:
                    mh2.update(t.encode("utf-8", errors="replace"))
                sim = _clamp01(float(mh1.jaccard(mh2)))
                scores.append(sim)
                if sim >= self.config.text_threshold:
                    return sim
            except Exception:
                pass

        # sentence-transformers embeddings cosine
        if self.config.enable_sentence_transformers:
            self._ensure_sentence_transformer()
        if self._sentence_transformer is not None:
            try:
                e1 = self._embed(p)
                e2 = self._embed(c)
                sim = self._cosine(e1, e2)
                scores.append(_clamp01(sim))
            except Exception:
                pass

        return _clamp01(max(scores) if scores else 0.0)

    def _embed(self, text: str) -> Any:
        key = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        cached = self._embed_cache.get(key)
        if cached is not None:
            return cached
        assert self._sentence_transformer is not None
        vec = self._sentence_transformer.encode([text], normalize_embeddings=True)[0]
        self._embed_cache_set(key, vec)
        return vec

    def _embed_cache_set(self, key: str, vec: Any) -> None:
        if self.config.embedding_cache_size <= 0:
            return
        if key in self._embed_cache:
            self._embed_cache[key] = vec
            return
        self._embed_cache[key] = vec
        self._embed_cache_order.append(key)
        while len(self._embed_cache_order) > self.config.embedding_cache_size:
            old = self._embed_cache_order.popleft()
            self._embed_cache.pop(old, None)

    def _cosine(self, a: Any, b: Any) -> float:
        # Inputs are expected normalized when coming from SentenceTransformer(normalize_embeddings=True),
        # but keep this safe.
        try:
            import numpy as np

            a = np.asarray(a, dtype=float)
            b = np.asarray(b, dtype=float)
            denom = float(np.linalg.norm(a) * np.linalg.norm(b))
            if denom <= 0:
                return 0.0
            return float(np.dot(a, b) / denom)
        except Exception:
            # Last-ditch pure python
            dot = 0.0
            na = 0.0
            nb = 0.0
            for x, y in zip(a, b):
                dot += float(x) * float(y)
                na += float(x) * float(x)
                nb += float(y) * float(y)
            denom = math.sqrt(na) * math.sqrt(nb)
            return dot / denom if denom > 0 else 0.0

    def _contradiction_score(self, a: str, b: str) -> float:
        a_n = _normalize_text(a)
        b_n = _normalize_text(b)
        if not a_n or not b_n:
            return 0.0
        if a_n == b_n:
            return 0.0

        a_toks = set(_topic_tokens(a_n))
        b_toks = set(_topic_tokens(b_n))
        overlap = 0.0
        if a_toks and b_toks:
            overlap = len(a_toks & b_toks) / max(1, min(len(a_toks), len(b_toks)))

        def has_any(text: str, terms: Iterable[str]) -> bool:
            return any(f" {t} " in f" {text} " for t in terms)

        neg_terms = {"not", "never", "no", "cannot", "can't", "dont", "don't", "wont", "won't"}
        a_neg = has_any(a_n, neg_terms)
        b_neg = has_any(b_n, neg_terms)

        antonyms = [
            ({"like", "likes", "love", "loves", "enjoy", "enjoys", "prefer", "prefers"}, {"hate", "hates", "dislike", "dislikes", "loathe", "loathes", "despise", "despises"}),
            ({"always", "all", "every"}, {"never", "none"}),
            ({"yes", "true", "correct"}, {"no", "false", "incorrect", "wrong"}),
            ({"enable", "enabled", "on", "allow", "allowed"}, {"disable", "disabled", "off", "deny", "denied"}),
        ]

        score = 0.0
        if a_neg != b_neg and overlap >= 0.25:
            score = max(score, 0.80 * overlap)
        for pos, neg in antonyms:
            if has_any(a_n, pos) and has_any(b_n, neg) and overlap >= 0.20:
                score = max(score, 0.90)
            if has_any(b_n, pos) and has_any(a_n, neg) and overlap >= 0.20:
                score = max(score, 0.90)

        if overlap < 0.15:
            score = min(score, 0.20)

        return _clamp01(score)
