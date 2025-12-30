#!/usr/bin/env python3
"""Preprocess experiences.jsonl into transitions.jsonl for RL training.
Simple encoding: action_id per tool_name, args hashed, timestamp, success->reward (1/0)
"""
import json
from pathlib import Path
import hashlib

p = Path('data/rl/experiences.jsonl')
if not p.exists():
    print('no experiences.jsonl found')
    raise SystemExit(1)

out_p = Path('data/rl/transitions.jsonl')
map_p = Path('data/rl/action_map.csv')

action_map = {}
next_id = 0
transitions = []

for line in p.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    obj = json.loads(line)
    tool = obj.get('tool_name')
    if tool not in action_map:
        action_map[tool] = next_id
        next_id += 1
    action_id = action_map[tool]
    args = obj.get('arguments') or {}
    args_hash = hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()
    ts = obj.get('timestamp')
    success = obj.get('success', False)
    reward = 1.0 if success else 0.0
    transitions.append({
        'uid': obj.get('uid'),
        'timestamp': ts,
        'state': {
            'context_hash': hashlib.sha256((str(obj.get('epistemic')) + str(ts)).encode()).hexdigest()[:16]
        },
        'action_id': action_id,
        'action_args_hash': args_hash,
        'reward': reward
    })

out_p.write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in transitions) + '\n')
map_p.write_text('tool_name,action_id\n' + '\n'.join(f'{k},{v}' for k,v in action_map.items()) + '\n')
print('wrote', len(transitions), 'transitions to', out_p)
