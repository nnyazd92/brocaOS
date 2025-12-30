#!/usr/bin/env python3
"""Migrate data/rl/experiences.jsonl to redact raw token jti and store hashed jti.
Creates a backup experiences.jsonl.bak timestamped.
"""
import json
from pathlib import Path
import hashlib
from datetime import datetime

p = Path('data/rl/experiences.jsonl')
if not p.exists():
    print('no experiences.jsonl found')
    raise SystemExit(1)

bak = p.with_name(f"experiences.jsonl.bak.{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
print('backing up', p, '->', bak)
bak.write_bytes(p.read_bytes())

out = []
for line in p.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    obj = json.loads(line)
    prov = obj.get('provenance') or {}
    jti = prov.get('token_jti')
    if jti:
        h = hashlib.sha256(jti.encode()).hexdigest()
        obj['provenance'] = {'token_jti_hash': h, 'scopes': prov.get('scopes')}
    else:
        obj['provenance'] = None
    out.append(obj)

p.write_text('\n'.join(json.dumps(o, ensure_ascii=False) for o in out) + '\n')
print('migration complete, wrote', len(out), 'records')
