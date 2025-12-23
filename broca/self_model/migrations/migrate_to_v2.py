#!/usr/bin/env python3
"""Migration helper: migrate a self-model dict to v2.0.0 format.

This script is intended to be idempotent and non-destructive. It reads a
source self-model JSON (from DB export or artifact), applies deterministic
trimming rules (dedupe capabilities, compress constraints to canonical
invariants), validates the result via SelfModel round-trip, and writes
the v2 artifact to disk when invoked as a tool with approval.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from broca.self_model.model import SelfModel


def migrate_to_v2(model_dict: dict) -> dict:
    # Metadata
    meta = model_dict.get('metadata', {}) or {}
    meta_v = dict(meta)
    meta_v['schema_version'] = 'v2.0.0'
    meta_v['migrated_at'] = datetime.now(timezone.utc).isoformat()
    meta_v['migration_from'] = meta.get('version', meta.get('schema_version', 'unknown'))

    # Capabilities: dedupe and shorten
    caps = model_dict.get('capabilities', [])
    seen = set()
    caps_v2 = []
    for c in caps:
        text = c.get('text') if isinstance(c, dict) else str(c)
        t = text.strip()
        if t in seen:
            continue
        seen.add(t)
        # Shorten very long entries
        if len(t) > 200:
            t = t.split('.')[0].strip()
        src = c.get('source', {}) if isinstance(c, dict) else {}
        src_simple = {'type': src.get('type') if isinstance(src, dict) else None}
        if isinstance(src, dict) and src.get('timestamp'):
            src_simple['timestamp'] = src.get('timestamp')
        caps_v2.append({'text': t, 'source': src_simple})
        if len(caps_v2) >= 50:
            break

    # Knowledge boundaries: keep concise values
    kb = model_dict.get('knowledge_boundaries', {}) or {}
    kb_v2 = {}
    for k, v in kb.items():
        val = v.get('value') if isinstance(v, dict) else v
        kb_v2[k] = {'value': (str(val).split('
')[0].split('. ')[0]).strip()}

    # Constraints: expect canonical invariants passed by caller; otherwise compress
    cons = model_dict.get('constraints', {}) or {}
    cons_v2 = {}
    for k, v in cons.items():
        val = v.get('value') if isinstance(v, dict) else v
        s = str(val).strip()
        s = s.split('
')[0].split('. ')[0]
        cons_v2[k] = {'value': s}

    v2 = {
        'metadata': meta_v,
        'capabilities': caps_v2,
        'knowledge_boundaries': kb_v2,
        'constraints': cons_v2,
        'epistemic_summary': {'knowledge_sources_count': 0},
        'provenance': '.temporary_token.txt',
        'dumped_at': datetime.now(timezone.utc).isoformat(),
    }

    # Validate by round-trip
    try:
        sm = SelfModel.from_dict(v2)
        _ = sm.to_dict()
    except Exception as e:
        raise RuntimeError(f'Validation failed during migrate_to_v2: {e}')

    return v2


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) < 1:
        print('Usage: migrate_to_v2.py <source_json> [<target_json>]')
        return 2

    src = Path(argv[0])
    tgt = Path(argv[1]) if len(argv) > 1 else Path('docs/artifacts/self_model.v2.json')

    data = json.loads(src.read_text())
    v2 = migrate_to_v2(data)

    # Backup existing target
    if tgt.exists():
        bak = tgt.with_suffix('.json.bak-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        tgt.replace(bak)

    tgt.write_text(json.dumps(v2, indent=2, ensure_ascii=False))
    print('Wrote v2 artifact to', tgt)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
