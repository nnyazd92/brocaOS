"""
Prompt priming utilities.

These helpers implement a lightweight, psychology-inspired priming mechanism:
- Retrieve a small candidate set from semantic memory (top-k)
- Select a diverse subset using MMR (maximal marginal relevance)
- Render a structured "priming card" for injection into the system prompt
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple
import math
import re
import hashlib
from datetime import datetime, timezone


_PATH_RE = re.compile(
    r"(?:(?:[A-Za-z]:)?[\\/][\\w .\\/\\\\-]+\\.[A-Za-z0-9]{1,6})|(?:[\\w./-]+\\.[A-Za-z0-9]{1,6})"
)
_TOOL_RE = re.compile(r"\\b[A-Z_]{3,}\\b")
_IDENT_RE = re.compile(r"\\b[A-Za-z_][A-Za-z0-9_]{2,}\\b")
_TOKEN_RE = re.compile(r"[a-z0-9_]+")

_STOPWORDS = {
    "the",
    "and",
    "that",
    "with",
    "this",
    "from",
    "into",
    "when",
    "then",
    "than",
    "just",
    "like",
    "also",
    "very",
    "have",
    "has",
    "had",
    "will",
    "would",
    "should",
    "could",
    "can",
    "you",
    "your",
    "we",
    "our",
    "i",
    "me",
    "my",
    "a",
    "an",
    "to",
    "of",
    "in",
    "on",
    "for",
    "it",
    "is",
    "are",
    "be",
    "as",
}


def _unique_limited(items: Iterable[str], limit: int) -> List[str]:
    out: List[str] = []
    seen = set()
    for it in items:
        s = str(it or "").strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= limit:
            break
    return out


def infer_task_type(user_text: str, recent_messages: Optional[List[dict]] = None) -> str:
    t = (user_text or "").lower()
    if any(k in t for k in ("pytest", "unittest", "flake8", "ruff", "mypy", "pip ", "poetry", "uv ", "venv")):
        return "coding"
    if any(k in t for k in ("implement", "refactor", "fix", "bug", "error", "traceback", ".py", ".ts", ".rs", ".go")):
        return "coding"
    if any(k in t for k in ("plan", "roadmap", "architecture", "design", "spec", "tdd", "tests first")):
        return "planning"
    if any(k in t for k in ("use tool", "web_search", "terminal", "patch_file", "apply_patch", "api endpoint")):
        return "tools"
    # Look at recent messages if provided.
    if recent_messages:
        joined = " ".join(str(m.get("content") or "").lower() for m in recent_messages[-4:] if isinstance(m, dict))
        if any(k in joined for k in ("pytest", "implement", "refactor", "code", ".py")):
            return "coding"
    return "chat"


def extract_entities(user_text: str) -> List[str]:
    text = str(user_text or "")
    paths = _PATH_RE.findall(text)
    tools = [t for t in _TOOL_RE.findall(text) if t not in ("USER", "ASSISTANT", "SYSTEM")]
    idents = [w for w in _IDENT_RE.findall(text) if w.lower() not in ("the", "and", "that", "with", "this", "from")]
    # Prefer concrete entities (paths/tools) first.
    return _unique_limited(list(paths) + list(tools) + list(idents), limit=12)


def extract_constraints(user_text: str) -> List[str]:
    text = str(user_text or "")
    # Split into rough clauses.
    clauses = re.split(r"[\\n\\.!?;]+", text)
    hits: List[str] = []
    for c in clauses:
        cc = c.strip()
        if not cc:
            continue
        low = cc.lower()
        if any(k in low for k in ("must", "should", "don't", "do not", "never", "avoid", "ensure", "no regressions", "tdd")):
            hits.append(cc)
    return _unique_limited(hits, limit=8)


def extract_intent(user_text: str) -> str:
    text = str(user_text or "").strip()
    if not text:
        return ""
    # Heuristic: first sentence/line as intent.
    first = re.split(r"[\\n\\.!?]+", text, maxsplit=1)[0].strip()
    # Normalize common leading phrases.
    first = re.sub(r"^(please\\s+)?(can\\s+you\\s+|could\\s+you\\s+|i\\s+want\\s+to\\s+|we\\s+need\\s+to\\s+|let'?s\\s+)", "", first, flags=re.IGNORECASE).strip()
    return first[:200]

def tokenize(text: str) -> List[str]:
    s = str(text or "").lower()
    toks = _TOKEN_RE.findall(s)
    toks = [t for t in toks if t and t not in _STOPWORDS and len(t) > 1]
    return toks


def _normalize_text_for_hash(text: str) -> str:
    s = str(text or "").strip().lower()
    # Collapse whitespace to improve match stability.
    s = re.sub(r"\s+", " ", s)
    return s


def _sha256_text(text: str) -> str:
    s = _normalize_text_for_hash(text)
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


def token_jaccard(a: str, b: str) -> float:
    """
    Deterministic token-set Jaccard similarity in [0, 1].
    """
    ta = set(tokenize(a))
    tb = set(tokenize(b))
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return float(inter / union) if union else 0.0


def build_topic_signature(cue_meta: dict[str, Any]) -> str:
    """
    Build a compact, deterministic topic signature from cue metadata.

    This is intentionally heuristic: it is used only for repeat-suppression gating
    (topic continuity vs topic shift), not as a user-facing artifact.
    """
    meta = cue_meta or {}
    task_type = str(meta.get("task_type") or "").strip()
    intent = str(meta.get("intent") or "").strip()
    entities = meta.get("entities") or []
    constraints = meta.get("constraints") or []

    ent = ", ".join(str(e) for e in list(entities)[:8] if str(e or "").strip())
    con = " | ".join(str(c) for c in list(constraints)[:6] if str(c or "").strip())

    # Keep format stable for tests/golden traces.
    return "\n".join(
        [
            f"task_type:{task_type}",
            f"intent:{intent}",
            f"entities:{ent}",
            f"constraints:{con}",
        ]
    ).strip()


def _extract_bullets_from_section(text: str, *, header: str, limit: int = 5) -> List[str]:
    """
    Extract bullet lines ("- ...") under a section header.
    """
    lines = [ln.rstrip("\n") for ln in str(text or "").splitlines()]
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().lower() == header.strip().lower():
            start = i + 1
            break
    if start is None:
        return []
    out: List[str] = []
    for ln in lines[start:]:
        s = ln.strip()
        if not s:
            if out:
                break
            continue
        # Stop if we reached the next section-like header.
        if s.endswith(":") and not s.startswith("-"):
            break
        if s.startswith("-"):
            item = s.lstrip("-").strip()
            if item:
                out.append(item)
        if len(out) >= limit:
            break
    return out


def priming_used_score(*, assistant_text: str, primed_card_text: str) -> float:
    """
    Heuristic score in [0, 1] for whether the primed memory was used.

    This is deterministic and intentionally lightweight:
    - Prefer overlap with Key facts / Action implications sections
    - Fall back to 0.0 when we can't extract useful anchors
    """
    a = str(assistant_text or "")
    p = str(primed_card_text or "")
    if not a.strip() or not p.strip():
        return 0.0

    anchors: List[str] = []
    anchors.extend(_extract_bullets_from_section(p, header="Key facts:", limit=5))
    anchors.extend(_extract_bullets_from_section(p, header="Action implications:", limit=4))

    anchor_text = " ".join(anchors).strip()
    if not anchor_text:
        return 0.0

    a_toks = set(tokenize(a))
    k_toks = set(tokenize(anchor_text))
    if not a_toks or not k_toks:
        return 0.0

    inter = len(a_toks & k_toks)
    denom = max(1, len(k_toks))
    score = float(inter / denom)
    return max(0.0, min(1.0, score))


def is_self_hit(
    *,
    user_text: str,
    cue_query: str,
    memory_text: str,
    token_overlap_threshold: float = 0.85,
) -> bool:
    """
    Detect when a retrieved memory is effectively the prompt itself (or a trivial echo).

    This is an interference control: it prevents the memory system from repeatedly surfacing
    the prompt content back into the system prompt.
    """
    u = str(user_text or "").strip()
    q = str(cue_query or "").strip()
    m = str(memory_text or "").strip()
    if not u or not m:
        return False

    # Exact/normalized hash match against user prompt or cue query.
    try:
        m_hash = _sha256_text(m)
        if m_hash == _sha256_text(u):
            return True
        if q and m_hash == _sha256_text(q):
            return True
    except Exception:
        # Fall through to overlap heuristics.
        pass

    # Containment heuristics (bounded to avoid worst-case quadratic behavior).
    try:
        uu = _normalize_text_for_hash(u)
        mm = _normalize_text_for_hash(m)
        # Only do contains checks for moderately sized, non-trivial strings.
        # Avoid pathological cases like 1-3 character memories ("a") matching everything.
        min_len = 32
        if min_len <= len(mm) <= 2000 and min_len <= len(uu) <= 2000:
            if mm in uu or uu in mm:
                return True
    except Exception:
        pass

    # High token overlap (Jaccard) indicates the memory is mostly an echo.
    try:
        thr = float(token_overlap_threshold)
    except Exception:
        thr = 0.85
    thr = max(0.0, min(1.0, thr))
    try:
        if token_jaccard(u, m) >= thr:
            return True
        # Also compare to cue query when present (cue query often includes the user prompt).
        if q and token_jaccard(q, m) >= thr:
            return True
    except Exception:
        return False

    return False


def bm25_scores(
    *,
    query: str,
    documents: List[str],
    k1: float = 1.2,
    b: float = 0.75,
) -> List[float]:
    """
    Compute BM25 scores for a query against a small list of documents.

    This is intended as a cheap reranker inside a candidate set (not a full index).
    """
    q_terms = tokenize(query)
    if not q_terms or not documents:
        return [0.0 for _ in documents]

    docs_terms: List[List[str]] = [tokenize(d) for d in documents]
    doc_lens = [len(dt) for dt in docs_terms]
    avgdl = (sum(doc_lens) / len(doc_lens)) if doc_lens else 0.0
    if avgdl <= 0:
        return [0.0 for _ in documents]

    # Document frequencies.
    df: dict[str, int] = {}
    for dt in docs_terms:
        for term in set(dt):
            df[term] = df.get(term, 0) + 1

    N = float(len(documents))
    # Precompute idf.
    idf: dict[str, float] = {}
    for term in set(q_terms):
        n_q = float(df.get(term, 0))
        # Standard BM25 idf.
        idf[term] = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1.0)

    scores: List[float] = []
    for dt, dl in zip(docs_terms, doc_lens):
        tf: dict[str, int] = {}
        for term in dt:
            tf[term] = tf.get(term, 0) + 1
        denom_norm = k1 * (1.0 - b + b * (float(dl) / avgdl))
        score = 0.0
        for term in q_terms:
            if term not in idf:
                continue
            f = float(tf.get(term, 0))
            if f <= 0:
                continue
            score += idf[term] * ((f * (k1 + 1.0)) / (f + denom_norm))
        scores.append(float(score))

    return scores


def parse_affect_from_tags(tags: Iterable[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for raw in tags or []:
        t = str(raw or "").strip().lower()
        if not t:
            continue
        if t.startswith("valence:"):
            v = t.split(":", 1)[1].strip()
            if v in ("positive", "+", "pos"):
                parsed["valence"] = 1.0
            elif v in ("negative", "-", "neg"):
                parsed["valence"] = -1.0
            else:
                try:
                    parsed["valence"] = float(v)
                except Exception:
                    pass
        if t.startswith("arousal:"):
            v = t.split(":", 1)[1].strip()
            if v in ("high", "h"):
                parsed["arousal"] = 1.0
            elif v in ("low", "l"):
                parsed["arousal"] = 0.0
            else:
                try:
                    parsed["arousal"] = float(v)
                except Exception:
                    pass
    return parsed


def parse_affect_from_metadata(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    out: dict[str, Any] = {}
    for k in ("valence", "arousal", "dissonance"):
        v = metadata.get(k)
        if isinstance(v, (int, float)):
            out[k] = float(v)
    return out


def affect_congruency_score(
    current_affect: Optional[dict[str, Any]],
    memory_tags: Iterable[str],
    *,
    memory_metadata: Any = None,
) -> float:
    """
    Score 0..1 for how congruent a memory is with current affect.

    Primarily uses explicit tags like `valence:negative` / `arousal:high`.
    """
    if not isinstance(current_affect, dict) or not current_affect:
        return 0.0
    mem_aff = parse_affect_from_tags(memory_tags)
    if memory_metadata is not None:
        mem_aff.update(parse_affect_from_metadata(memory_metadata))
    if not mem_aff:
        return 0.0

    score = 0.0
    count = 0
    for key in ("valence", "arousal"):
        cv = current_affect.get(key)
        mv = mem_aff.get(key)
        if isinstance(cv, (int, float)) and isinstance(mv, (int, float)):
            count += 1
            # Clamp to [-1, 1] for valence; [0, 1] for arousal-ish.
            if key == "valence":
                cvf = max(-1.0, min(1.0, float(cv)))
                mvf = max(-1.0, min(1.0, float(mv)))
                score += 1.0 - (abs(cvf - mvf) / 2.0)
            else:
                cvf = max(0.0, min(1.0, float(cv)))
                mvf = max(0.0, min(1.0, float(mv)))
                score += 1.0 - abs(cvf - mvf)
    return float(score / count) if count else 0.0


def goal_congruency_score(goals: Iterable[str], *, memory_text: str, memory_tags: Iterable[str], memory_namespace: str) -> float:
    """
    Score 0..1 for how much a memory matches the current goal set.
    """
    goal_terms = tokenize(" ".join(str(g or "") for g in (goals or [])))
    if not goal_terms:
        return 0.0
    doc = " ".join([str(memory_text or ""), str(memory_namespace or ""), " ".join(memory_tags or [])])
    doc_terms = set(tokenize(doc))
    if not doc_terms:
        return 0.0
    hit = sum(1 for t in set(goal_terms) if t in doc_terms)
    return float(hit / max(1, len(set(goal_terms))))


def half_life_decay(age_seconds: float, half_life_seconds: float) -> float:
    if half_life_seconds <= 0:
        return 0.0
    if age_seconds <= 0:
        return 1.0
    return float(math.exp(-math.log(2.0) * (float(age_seconds) / float(half_life_seconds))))


def _parse_iso8601(s: Any) -> Optional[datetime]:
    if not isinstance(s, str) or not s.strip():
        return None
    v = s.strip()
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def extract_key_facts(text: str, *, limit: int = 3) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    # Prefer non-empty lines; otherwise fall back to sentences.
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    facts: List[str] = []
    for ln in lines:
        if len(ln) < 8:
            continue
        facts.append(ln)
        if len(facts) >= limit:
            return facts
    # Sentence fallback.
    parts = re.split(r"(?<=[.!?])\\s+", raw)
    for p in parts:
        pp = p.strip()
        if len(pp) < 12:
            continue
        if pp not in facts:
            facts.append(pp)
        if len(facts) >= limit:
            break
    return facts[:limit]


def extract_action_implications(
    text: str,
    *,
    task_type: str,
    entities: List[str],
    limit: int = 2,
) -> List[str]:
    raw = str(text or "")
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    actions: List[str] = []
    verbs = ("run ", "use ", "set ", "avoid ", "ensure ", "add ", "remove ", "update ", "check ", "verify ")
    for ln in lines:
        low = ln.lower()
        if low.startswith(verbs) or " should " in low or low.startswith("should "):
            actions.append(ln)
        if len(actions) >= limit:
            return actions
    if entities:
        # Heuristic: point at concrete file entities first.
        paths = [e for e in entities if "/" in e or "\\" in e]
        if paths:
            actions.append(f"Review {paths[0]}")
    if task_type == "coding":
        actions.append("Run targeted tests to confirm no regressions")
    if len(actions) < limit:
        actions.append("Validate against current goal/constraints")
    return actions[:limit]


def build_structured_priming_card(
    *,
    query_preview: str,
    cue_meta: dict[str, Any],
    selection: dict[str, Any],
    items: List[dict[str, Any]],
    conflicts: Optional[List[dict[str, Any]]] = None,
    unknowns: Optional[List[str]] = None,
) -> str:
    """
    Render a structured priming card that is suggestive but non-hijacking.
    """
    q = str(query_preview or "").strip()
    task_type = str((cue_meta or {}).get("task_type") or "")
    intent = str((cue_meta or {}).get("intent") or "")
    entities = list((cue_meta or {}).get("entities") or [])
    constraints = list((cue_meta or {}).get("constraints") or [])
    goals = list((cue_meta or {}).get("goals") or [])
    affect = (cue_meta or {}).get("affect") or {}

    header = "PRIMED MEMORY (why it matches, provenance, confidence, last_used):\n"
    lines: List[str] = [header]
    lines.append("Why it matches:")
    if task_type:
        lines.append(f"- task_type: {task_type}")
    if intent:
        lines.append(f"- intent: {intent}")
    if entities:
        lines.append(f"- entities: {', '.join(str(e) for e in entities[:8])}")
    if constraints:
        lines.append(f"- constraints: {' | '.join(str(c) for c in constraints[:6])}")
    if goals:
        lines.append(f"- goals: {', '.join(str(g) for g in goals[:4])}")
    if isinstance(affect, dict) and affect:
        lines.append(f"- affect: {affect}")
    if selection:
        strategy = selection.get("strategy")
        lines.append(f"- selection: {strategy}")
    lines.append("")

    # Use first item as primary, but include provenance for all.
    lines.append("Provenance:")
    for idx, it in enumerate(items[:3], start=1):
        mid = it.get("id")
        ns = it.get("namespace") or ""
        src = it.get("source_type") or ""
        created = it.get("created_at") or ""
        last_used = it.get("last_used_at") or ""
        imp = it.get("importance")
        why = it.get("why") if isinstance(it.get("why"), dict) else {}
        why_bits: List[str] = []
        for k in ("sim", "bm25", "goal", "affect", "recency", "usage", "penalty"):
            v = why.get(k)
            if isinstance(v, (int, float)):
                why_bits.append(f"{k}={float(v):.3f}")
        why_str = f" ({', '.join(why_bits)})" if why_bits else ""
        conf = float(imp) if isinstance(imp, (int, float)) else None
        conf_str = f"{conf:.2f}" if conf is not None else "?"
        lines.append(f"- [{idx}] id={mid} ns={ns} source={src}{why_str}")
        lines.append(f"  Confidence: {conf_str}")
        lines.append(f"  Last used: {last_used}")
        if created:
            lines.append(f"  Created: {created}")
    lines.append("")

    primary = items[0] if items else {}
    primary_text = str(primary.get("text") or "")
    key_facts = extract_key_facts(primary_text, limit=3)
    lines.append("Key facts:")
    if key_facts:
        for f in key_facts:
            lines.append(f"- {f[:240]}")
    else:
        lines.append("- (none)")
    lines.append("")

    action_imp = extract_action_implications(primary_text, task_type=task_type, entities=[str(e) for e in entities], limit=2)
    lines.append("Action implications:")
    for a in action_imp:
        lines.append(f"- {a[:240]}")
    lines.append("")

    lines.append("Known conflicts/unknowns:")
    if conflicts:
        for c in conflicts[:4]:
            ctype = c.get("type") or "related"
            cid = c.get("id")
            preview = str(c.get("preview") or "").strip()
            lines.append(f"- {ctype}: id={cid} {preview[:200]}")
    else:
        lines.append("- conflicts: none detected")
    if unknowns:
        for u in unknowns[:3]:
            lines.append(f"- unknown: {str(u)[:200]}")
    else:
        lines.append("- unknowns: none")

    return "\n".join(lines).rstrip() + "\n"


def build_thought_priming_card(
    *,
    query_preview: str,
    cue_meta: dict[str, Any],
    selection: dict[str, Any],
    items: List[dict[str, Any]],
) -> str:
    """
    Render a compact priming card for internal recursive-thought prompts.

    This format is intentionally shorter and more reflective than chat priming:
    it should suggest, not hijack.
    """
    q = str(query_preview or "").strip()
    task_type = str((cue_meta or {}).get("task_type") or "")
    intent = str((cue_meta or {}).get("intent") or "")

    header = "PRIMED MEMORY (thought):\n"
    lines: List[str] = [header]
    if q:
        lines.append(f"Query: {q}")
    if task_type:
        lines.append(f"Task: {task_type}")
    if intent:
        lines.append(f"Intent: {intent}")
    if selection and selection.get("strategy"):
        lines.append(f"Selection: {selection.get('strategy')}")
    lines.append("")

    primary = items[0] if items else {}
    mid = primary.get("id")
    ns = primary.get("namespace") or ""
    last_used = primary.get("last_used_at") or ""
    imp = primary.get("importance")
    conf = float(imp) if isinstance(imp, (int, float)) else None
    conf_str = f"{conf:.2f}" if conf is not None else "?"
    lines.append("Provenance:")
    lines.append(f"- id={mid} ns={ns} confidence={conf_str} last_used={last_used}")
    lines.append("")

    primary_text = str(primary.get("text") or "")
    facts = extract_key_facts(primary_text, limit=3)
    lines.append("Key facts:")
    if facts:
        for f in facts:
            lines.append(f"- {f[:240]}")
    else:
        lines.append("- (none)")
    lines.append("")

    # Reflection prompts are intentionally generic to avoid over-directing.
    lines.append("Reflection prompts:")
    lines.append("- How does this change the next concrete step?")
    lines.append("- What would falsify or contradict this memory?")

    return "\n".join(lines).rstrip() + "\n"


def build_cue_query(
    *,
    user_text: str,
    recent_messages: Optional[List[dict]] = None,
    affect: Optional[dict[str, Any]] = None,
    goals: Optional[List[str]] = None,
) -> Tuple[str, dict[str, Any]]:
    """
    Build a cue-rich query for memory retrieval/embedding.

    This mimics cue-dependent recall: the same prompt can retrieve different
    memories depending on task type, entities, constraints, and affect.
    """
    prompt = str(user_text or "").strip()
    task_type = infer_task_type(prompt, recent_messages=recent_messages)
    intent = extract_intent(prompt)
    entities = extract_entities(prompt)
    constraints = extract_constraints(prompt)

    affect_snapshot: dict[str, Any] = {}
    if isinstance(affect, dict):
        for k in ("valence", "arousal", "dissonance"):
            v = affect.get(k)
            if isinstance(v, (int, float)):
                affect_snapshot[k] = float(v)

    context_snippet = ""
    if recent_messages:
        # Keep this short; it's a cue, not a transcript.
        parts: List[str] = []
        for m in list(recent_messages)[-4:]:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "").strip()
            content = str(m.get("content") or "").strip()
            if not role or not content:
                continue
            parts.append(f"{role.upper()}: {content[:300]}")
        context_snippet = "\n".join(parts).strip()

    cue_lines = [
        f"USER_PROMPT: {prompt}",
        f"TASK_TYPE: {task_type}",
        f"GOALS: {', '.join(_unique_limited(goals or [], limit=5)) if goals else ''}",
        f"INTENT: {intent}",
        f"ENTITIES: {', '.join(entities) if entities else ''}",
        f"CONSTRAINTS: {' | '.join(constraints) if constraints else ''}",
        f"AFFECT: {affect_snapshot}",
    ]
    if context_snippet:
        cue_lines.append("RECENT_CONTEXT:\n" + context_snippet)

    cue_text = "\n".join(cue_lines).strip() + "\n"
    cue_meta: dict[str, Any] = {
        "task_type": task_type,
        "goals": _unique_limited(goals or [], limit=5) if goals else [],
        "intent": intent,
        "entities": entities[:12],
        "constraints": constraints[:8],
        "affect": affect_snapshot,
    }
    return cue_text, cue_meta


def _normalize(vec: Sequence[float]) -> List[float]:
    v = [float(x) for x in (vec or [])]
    if not v:
        return []
    norm = math.sqrt(sum(x * x for x in v))
    if norm <= 0:
        return [0.0 for _ in v]
    return [x / norm for x in v]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    aa = _normalize(a)
    bb = _normalize(b)
    if not aa or not bb or len(aa) != len(bb):
        return 0.0
    return float(sum(x * y for x, y in zip(aa, bb)))


def mmr_select(
    *,
    query_vector: Sequence[float],
    candidates: Sequence[Any],
    candidate_vectors: Sequence[Sequence[float]],
    k: int,
    lambda_mult: float = 0.7,
) -> List[Any]:
    """
    Select up to k diverse candidates using maximal marginal relevance.

    Args:
        query_vector: Query embedding vector
        candidates: Candidate items (parallel to candidate_vectors)
        candidate_vectors: Candidate embedding vectors
        k: Maximum number of items to select
        lambda_mult: Relevance/diversity tradeoff (0..1); higher = more relevance
    """
    if k <= 0:
        return []
    if not candidates or not candidate_vectors:
        return []
    if len(candidates) != len(candidate_vectors):
        raise ValueError("candidates and candidate_vectors must have same length")

    lam = float(lambda_mult)
    if lam < 0.0:
        lam = 0.0
    if lam > 1.0:
        lam = 1.0

    q = _normalize(query_vector)
    vectors = [_normalize(v) for v in candidate_vectors]

    # Precompute relevance.
    rel = [cosine_similarity(q, v) for v in vectors]

    # Always start from the most relevant.
    selected_idx: List[int] = []
    remaining = set(range(len(candidates)))
    first = max(remaining, key=lambda i: rel[i])
    selected_idx.append(first)
    remaining.remove(first)

    while remaining and len(selected_idx) < k:
        def _mmr(i: int) -> float:
            # Diversity penalty is maximum similarity to any already selected item.
            div = max(cosine_similarity(vectors[i], vectors[j]) for j in selected_idx)
            return lam * rel[i] - (1.0 - lam) * div

        best = max(remaining, key=_mmr)
        selected_idx.append(best)
        remaining.remove(best)

    return [candidates[i] for i in selected_idx]


def build_priming_card(*, query_preview: str, items: Iterable[dict[str, Any]], selection: dict[str, Any]) -> str:
    """
    Render a structured priming card suitable for system prompt injection.

    The output should be deterministic and stable for golden-trace tests.
    """
    q = str(query_preview or "").strip()
    sel = selection or {}
    strategy = str(sel.get("strategy") or "topk")
    top_k = sel.get("top_k")
    max_items = sel.get("max_items")
    lam = sel.get("lambda")

    header = "PRIMED MEMORY:\n"
    meta = f"Query: {q}\n"
    meta += f"Selection: {strategy}"
    if top_k is not None:
        meta += f" top_k={top_k}"
    if max_items is not None:
        meta += f" max_items={max_items}"
    if lam is not None:
        try:
            meta += f" lambda={float(lam):.2f}"
        except Exception:
            meta += f" lambda={lam}"
    meta += "\n\n"

    lines: List[str] = [header + meta]

    for idx, item in enumerate(items, start=1):
        memory_id = item.get("id")
        namespace = item.get("namespace") or ""
        score = item.get("score")
        text = str(item.get("text") or "").strip()

        score_str = ""
        if isinstance(score, (int, float)):
            score_str = f", sim={float(score):.3f}"
        elif score is not None:
            score_str = f", sim={score}"

        prefix = f"[{idx}]"
        if memory_id is not None:
            prefix += f" id={memory_id}"
        if namespace:
            prefix += f" ns={namespace}"
        prefix += score_str

        lines.append(prefix)
        if text:
            lines.append(text)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
