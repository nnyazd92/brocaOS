from __future__ import annotations

import logging
import re
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger(__name__)


_TEXT_KEYS = {"text", "query", "prompt", "message", "content"}
_MAX_NESTED_DEPTH = 3


def _is_text_like_key(key: str) -> bool:
    k = (key or "").lower()
    return k in _TEXT_KEYS or k.endswith("_text") or k.endswith("_message") or k.endswith("_description")


@dataclass(frozen=True)
class CompiledRegexConstraint:
    field: str
    pattern: str
    compiled: Any


@dataclass
class CompiledPattern:
    pattern: Dict[str, Any]
    required: List[Tuple[str, Any]]
    required_count: int
    regex_constraints: List[CompiledRegexConstraint]
    text_contains: List[str]
    text_projection: str


class CompiledPatternSet:
    """
    Precompiled, indexed representation of many patterns.

    Goal: cheaply prefilter candidate pattern indices per content item before calling the full matcher.
    This must be conservative (never drop a true match).
    """

    def __init__(self, patterns: Sequence[Dict[str, Any]], *, enable_flashtext: bool = True, enable_ahocorasick: bool = True) -> None:
        self.patterns: List[Dict[str, Any]] = list(patterns)
        self.compiled: List[CompiledPattern] = []
        self.pattern_texts: List[str] = []

        # Inverted index: (field, value) -> pattern indices requiring it
        self._inv: Dict[Tuple[str, Any], List[int]] = {}

        # Special inverted indices
        self._tags_inv: Dict[str, List[int]] = {}  # tag -> patterns requiring tag in tags
        self._text_contains_inv: Dict[str, List[int]] = {}  # keyword(lower) -> patterns requiring keyword in text-like field

        self._unconstrained: List[int] = []

        # Keyword engines (optional)
        self._flash = None
        self._aho = None
        self._use_flash = bool(enable_flashtext)
        self._use_aho = bool(enable_ahocorasick)

        self._build()

    def _join(self, prefix: str, key: str) -> str:
        k = str(key)
        return k if not prefix else f"{prefix}.{k}"

    def _is_operator_dict(self, d: Dict[str, Any]) -> bool:
        if len(d) != 1:
            return False
        return next(iter(d.keys())) in {"contains", "regex", "in", "any", "all", "eq", "ne", "gt", "gte", "lt", "lte", "exists"}

    def _collect_from_pattern(
        self,
        obj: Any,
        *,
        prefix: str,
        depth: int,
        req: List[Tuple[str, Any]],
        regex_constraints: List[CompiledRegexConstraint],
        text_contains: List[str],
        text_parts: List[str],
        regex_mod: Any,
    ) -> None:
        if depth > _MAX_NESTED_DEPTH:
            return
        if not isinstance(obj, dict):
            return
        for k, v in obj.items():
            if str(k) == "description":
                continue
            path = self._join(prefix, str(k))

            # Operator dict at this level (pattern value is an operator dict)
            if isinstance(v, dict) and self._is_operator_dict(v):
                op, arg = next(iter(v.items()))
                if op == "regex":
                    pat = str(arg)
                    # Regex prefilter is only safe when the content value is a string and fails the regex,
                    # so we keep it conservative and ignore compilation errors.
                    try:
                        compiled = (
                            regex_mod.compile(pat, flags=regex_mod.IGNORECASE)
                            if regex_mod is not None
                            else re.compile(pat, flags=re.IGNORECASE)
                        )
                        regex_constraints.append(CompiledRegexConstraint(field=path, pattern=pat, compiled=compiled))
                    except Exception:
                        pass
                    if _is_text_like_key(str(k)):
                        text_parts.append(pat)
                    continue

                if op == "contains":
                    # Conservative indexing: only tags membership or text keyword containment.
                    if str(k).lower() == "tags":
                        try:
                            tag = str(arg)
                            self._tags_inv.setdefault(tag, []).append(self._current_pattern_index)
                            req.append(("tags_contains", tag))
                        except Exception:
                            pass
                        continue
                    if _is_text_like_key(str(k)):
                        kw = str(arg).strip().lower()
                        if kw:
                            text_contains.append(kw)
                            self._text_contains_inv.setdefault(kw, []).append(self._current_pattern_index)
                            req.append(("text_contains", kw))
                            text_parts.append(kw)
                        continue
                    # For non-text fields, "contains" may mean substring; indexing it would be unsafe.
                    continue

                # Other operators are not safely indexable without understanding semantics; skip.
                continue

            # Nested dict: recurse and (if key is text-like) collect text-ish values too.
            if isinstance(v, dict):
                self._collect_from_pattern(
                    v,
                    prefix=path,
                    depth=depth + 1,
                    req=req,
                    regex_constraints=regex_constraints,
                    text_contains=text_contains,
                    text_parts=text_parts,
                    regex_mod=regex_mod,
                )
                continue

            # Scalar equality constraints are only safe to index for non-text-like keys,
            # because text-like scalars can match fuzzily in the full matcher.
            if isinstance(v, (str, int, float, bool)) or v is None:
                if not _is_text_like_key(str(k)):
                    req.append((path, v))
                if _is_text_like_key(str(k)) and isinstance(v, str) and v.strip():
                    text_parts.append(v.strip())
                continue

    def _collect_content_features(self, obj: Any, *, prefix: str, depth: int, features: List[Tuple[str, Any]], text_parts: List[str]) -> None:
        if depth > _MAX_NESTED_DEPTH:
            return
        if not isinstance(obj, dict):
            return
        for k, v in obj.items():
            path = self._join(prefix, str(k))
            if isinstance(v, dict):
                self._collect_content_features(v, prefix=path, depth=depth + 1, features=features, text_parts=text_parts)
                continue
            if str(k).lower() == "tags" and isinstance(v, list):
                for t in v:
                    try:
                        features.append(("tags_contains", str(t)))
                    except Exception:
                        continue
                continue
            if isinstance(v, (str, int, float, bool)) or v is None:
                if not _is_text_like_key(str(k)):
                    features.append((path, v))
                if _is_text_like_key(str(k)) and isinstance(v, str) and v:
                    text_parts.append(v)
                continue

    def _build(self) -> None:
        regex_mod = None
        try:
            import regex as regex_mod  # type: ignore
        except Exception:
            regex_mod = None

        # Try to set up keyword engines; safe to ignore if not installed.
        if self._use_flash:
            try:
                from flashtext import KeywordProcessor  # type: ignore

                self._flash = KeywordProcessor(case_sensitive=False)
            except Exception:
                self._flash = None
        if self._use_aho:
            try:
                import ahocorasick  # type: ignore

                self._aho = ahocorasick.Automaton()
            except Exception:
                self._aho = None

        for i, p in enumerate(self.patterns):
            self._current_pattern_index = i  # used for inverted indices during collection
            req: List[Tuple[str, Any]] = []
            regex_constraints: List[CompiledRegexConstraint] = []
            text_contains: List[str] = []
            text_parts: List[str] = []

            self._collect_from_pattern(
                p or {},
                prefix="",
                depth=0,
                req=req,
                regex_constraints=regex_constraints,
                text_contains=text_contains,
                text_parts=text_parts,
                regex_mod=regex_mod,
            )

            required_count = len(req)
            text_projection = " ".join([t.strip() for t in text_parts if str(t).strip()]).strip()
            cp = CompiledPattern(
                pattern=p,
                required=req,
                required_count=required_count,
                regex_constraints=regex_constraints,
                text_contains=text_contains,
                text_projection=text_projection,
            )
            self.compiled.append(cp)
            self.pattern_texts.append(text_projection)

            # Patterns with no indexed hard constraints are always candidates; any regex constraints
            # will be applied later during filtering.
            if required_count == 0:
                self._unconstrained.append(i)

            for field, value in req:
                self._inv.setdefault((field, value), []).append(i)

        # Populate keyword engines with all text-contains keywords (single pass search).
        if self._flash is not None:
            try:
                for kw in self._text_contains_inv.keys():
                    self._flash.add_keyword(kw)
            except Exception:
                self._flash = None
        if self._aho is not None:
            try:
                for idx, kw in enumerate(self._text_contains_inv.keys()):
                    self._aho.add_word(kw, (idx, kw))
                self._aho.make_automaton()
            except Exception:
                self._aho = None

    def candidate_indices_for_content(self, content: Dict[str, Any]) -> List[int]:
        """
        Return pattern indices that satisfy all indexed hard constraints.
        Regex constraints are applied here too (safe, cheap).
        """
        if not self.compiled:
            return []

        # Collect available features from content (including nested scalar fields).
        features: List[Tuple[str, Any]] = []
        text_parts: List[str] = []
        self._collect_content_features(content or {}, prefix="", depth=0, features=features, text_parts=text_parts)

        # Text-contains keywords: only if there are any such patterns.
        if self._text_contains_inv:
            text = " ".join([t for t in text_parts if isinstance(t, str) and t]).strip()
            if text:
                hits = self._extract_keyword_hits(text)
                for kw in hits:
                    features.append(("text_contains", kw))

        # Count satisfied constraints per pattern index.
        counts: Dict[int, int] = {}
        for feat in features:
            for idx in self._inv.get(feat, []):
                counts[idx] = counts.get(idx, 0) + 1

        # Patterns with no required constraints are always candidates.
        candidates: List[int] = list(self._unconstrained)

        for idx, cp in enumerate(self.compiled):
            if cp.required_count <= 0:
                continue
            if counts.get(idx, 0) >= cp.required_count:
                candidates.append(idx)

        # Apply regex constraints for candidates (safe: failing regex means cannot match).
        filtered: List[int] = []
        for idx in candidates:
            cp = self.compiled[idx]
            ok = True
            for rc in cp.regex_constraints:
                val = self._get_by_path(content, rc.field)
                # Must stay conservative: GeneralMatcher coerces non-strings to text for regex matches,
                # so do the same here instead of dropping candidates.
                val_text = self._coerce_to_text(val)
                if rc.compiled.search(val_text) is None:
                    ok = False
                    break
            if ok:
                filtered.append(idx)

        return filtered

    def _extract_keyword_hits(self, text: str) -> Set[str]:
        t = text.lower()
        if self._flash is not None:
            try:
                found = set(self._flash.extract_keywords(t))
                return {str(x).lower() for x in found if str(x).strip()}
            except Exception:
                return set()
        if self._aho is not None:
            try:
                found: Set[str] = set()
                for _end, (_i, kw) in self._aho.iter(t):
                    found.add(str(kw).lower())
                return found
            except Exception:
                return set()
        # Fallback: naive scan (only safe for small keyword sets).
        found = set()
        for kw in self._text_contains_inv.keys():
            if kw and kw in t:
                found.add(kw)
        return found

    def _get_by_path(self, obj: Dict[str, Any], path: str) -> Any:
        cur: Any = obj
        for part in (path or "").split("."):
            if not part:
                continue
            if not isinstance(cur, dict):
                return None
            if part not in cur:
                return None
            cur = cur.get(part)
        return cur

    def _coerce_to_text(self, x: Any) -> str:
        # Keep in sync (conservatively) with GeneralMatcher._coerce_to_text so prefiltering never
        # drops a candidate that the full matcher could accept.
        if x is None:
            return ""
        if isinstance(x, str):
            return x[:20000]
        try:
            return json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)[:20000]
        except Exception:
            return str(x)[:20000]
