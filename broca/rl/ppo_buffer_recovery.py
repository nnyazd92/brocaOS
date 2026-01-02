from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class MergeStats:
    sources: int
    total_seen: int
    added: int
    deduped: int
    dropped_unknown_tool: int
    dropped_bad_action: int
    dropped_bad_state: int
    capped: int


def _mapping_list(payload: Dict[str, Any]) -> List[str]:
    m = payload.get("mapping")
    if not isinstance(m, str) or not m.strip():
        return []
    return [x for x in m.split("|") if x]


def _action_to_tool(old_mapping: List[str], action: Any) -> Optional[str]:
    try:
        a = int(action)
    except Exception:
        return None
    if a < 0 or a >= len(old_mapping):
        return None
    tool = old_mapping[a]
    return tool if isinstance(tool, str) and tool else None


def _state_ok(state: Any, *, input_dim: int) -> bool:
    if state is None:
        return False
    if not isinstance(state, list):
        return False
    return len(state) == int(input_dim)


def _exp_fingerprint(exp: Dict[str, Any]) -> str:
    """
    Dedup key: stable hash of the semantic fields we care about.
    We intentionally ignore log_prob/value because those can vary across runs.
    """
    payload = {
        "s": exp.get("state"),
        "a": exp.get("action"),
        "r": exp.get("reward"),
        "ns": exp.get("next_state"),
        "d": exp.get("done"),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()


def merge_ppo_buffers(
    *,
    current_path: Path,
    extra_paths: Iterable[Path],
    max_buffer_size: Optional[int] = None,
) -> Tuple[Dict[str, Any], MergeStats]:
    """
    Merge experiences from 'extra_paths' into 'current_path' buffer payload by remapping
    action indices via tool-name mapping strings.
    """
    cur_payload = json.loads(current_path.read_text(encoding="utf-8"))
    if not isinstance(cur_payload, dict):
        raise ValueError("current buffer payload is not a dict")

    new_mapping = _mapping_list(cur_payload)
    if not new_mapping:
        raise ValueError("current buffer has no valid mapping")
    new_tool_to_idx = {name: i for i, name in enumerate(new_mapping)}

    input_dim = int(cur_payload.get("input_dim", 0) or 0)
    if input_dim <= 0:
        raise ValueError("current buffer has invalid input_dim")

    existing_exps = cur_payload.get("experiences")
    if not isinstance(existing_exps, list):
        existing_exps = []

    seen: set[str] = set()
    for exp in existing_exps:
        if isinstance(exp, dict):
            seen.add(_exp_fingerprint(exp))

    added = 0
    deduped = 0
    dropped_unknown_tool = 0
    dropped_bad_action = 0
    dropped_bad_state = 0
    total_seen = 0

    merged: List[Dict[str, Any]] = [e for e in existing_exps if isinstance(e, dict)]

    for p in extra_paths:
        payload = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        old_mapping = _mapping_list(payload)
        if not old_mapping:
            continue
        exps = payload.get("experiences")
        if not isinstance(exps, list):
            continue

        for exp in exps:
            if not isinstance(exp, dict):
                continue
            total_seen += 1

            st = exp.get("state")
            ns = exp.get("next_state")
            if not _state_ok(st, input_dim=input_dim):
                dropped_bad_state += 1
                continue
            if ns is not None and not _state_ok(ns, input_dim=input_dim):
                # Keep experience but drop invalid next_state.
                ns = None

            tool = _action_to_tool(old_mapping, exp.get("action"))
            if tool is None:
                dropped_bad_action += 1
                continue
            if tool not in new_tool_to_idx:
                dropped_unknown_tool += 1
                continue

            new_action = int(new_tool_to_idx[tool])
            recovered = dict(exp)
            recovered["action"] = new_action
            recovered["next_state"] = ns
            # Optional: embed tool name for future-proofing.
            recovered["tool"] = tool

            fp = _exp_fingerprint(recovered)
            if fp in seen:
                deduped += 1
                continue
            seen.add(fp)
            merged.append(recovered)
            added += 1

    cap = int(max_buffer_size or cur_payload.get("buffer_size", 0) or 0)
    if cap <= 0:
        cap = len(merged)
    capped = max(0, len(merged) - cap)
    merged = merged[-cap:]

    cur_payload["experiences"] = merged
    # Keep mapping consistent with the current policy mapping.
    cur_payload["mapping"] = "|".join(new_mapping)
    # Update output_dim to match mapping length (best effort).
    cur_payload["output_dim"] = int(len(new_mapping))

    stats = MergeStats(
        sources=1 + len(list(extra_paths)),
        total_seen=total_seen,
        added=added,
        deduped=deduped,
        dropped_unknown_tool=dropped_unknown_tool,
        dropped_bad_action=dropped_bad_action,
        dropped_bad_state=dropped_bad_state,
        capped=capped,
    )
    return cur_payload, stats


def recover_into_current_buffer(
    *,
    current_path: Path,
    incompatible_glob: str = "ppo_buffer.incompatible.*.json",
    max_buffer_size: Optional[int] = None,
    backup: bool = True,
) -> MergeStats:
    """
    Backup current buffer and merge preserved incompatible buffers into it.
    """
    cur = Path(current_path)
    extras = sorted(cur.parent.glob(incompatible_glob))

    merged_payload, stats = merge_ppo_buffers(
        current_path=cur,
        extra_paths=extras,
        max_buffer_size=max_buffer_size,
    )

    if backup and cur.exists():
        ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        bak = cur.with_suffix(cur.suffix + f".premerge.{ts}.bak")
        bak.write_text(cur.read_text(encoding="utf-8"), encoding="utf-8")

    cur.write_text(json.dumps(merged_payload, ensure_ascii=False), encoding="utf-8")
    return stats


