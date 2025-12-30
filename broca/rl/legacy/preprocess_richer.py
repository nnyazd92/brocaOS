#!/usr/bin/env python3
"""Richer preprocessing for BC: produce scaled numeric features and feature metadata.
Features:
 - recent tool counts (last K=10) per action_id
 - running success rate (last K)
 - tool reliability (from experiences epistemic if available)
 - time of day bucket
 - goal count (if available in experiences' ephemeral context)
 - hashed context embedding (first N bytes as ints)

Outputs:
 - data/rl/expanded_rich/observations.npy
 - data/rl/expanded_rich/actions.npy
 - data/rl/expanded_rich/rewards.npy
 - data/rl/expanded_rich/scaler.joblib
 - data/rl/expanded_rich/feature_map.json
"""
import json
from pathlib import Path
import numpy as np
from collections import deque, Counter

p = Path('data/rl/transitions.jsonl')
if not p.exists():
    print('no transitions, run preprocess')
    raise SystemExit(1)

lines = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
lines_sorted = sorted(lines, key=lambda x: x['timestamp'])

# read action map
am = {}
with open('data/rl/action_map.csv') as f:
    next(f)
    for l in f:
        k,v = l.strip().split(',',1)
        am[int(v)]=k

K=10
window = deque(maxlen=K)
success_window = deque(maxlen=K)

obs=[]
actions=[]
rews=[]

for t in lines_sorted:
    aid = t['action_id']
    window.append(aid)
    success_window.append(t.get('reward',0.0))
    # counts per action id (sorted by action id)
    action_ids_sorted = sorted(am.keys())
    counts = [window.count(i) for i in action_ids_sorted]
    # success rate
    succ_rate = sum(success_window)/len(success_window)
    # tool reliability from experiences epistemic if present
    try:
        tr = json.loads(Path('data/rl/tool_reliability.json').read_text())
        reliability = tr.get(am.get(aid), {}).get('success_rate', 0.5)
    except Exception:
        reliability = 0.5
    # time bucket
    try:
        hour = int(t['timestamp'][11:13])
    except Exception:
        hour = 0
    # simple context hash bytes
    ch = t['state'].get('context_hash','')
    ch_bytes = [int(ch[i:i+2],16) if i+2<=len(ch) else 0 for i in range(0,8,2)]
    feat = counts + [succ_rate, reliability, hour] + ch_bytes
    obs.append(feat)
    actions.append(aid)
    rews.append(t.get('reward',0.0))

X = np.array(obs, dtype=float)
y = np.array(actions, dtype=int)
w = np.array(rews, dtype=float)

# scale
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
Xs = scaler.fit_transform(X)

out = Path('data/rl/expanded_rich')
out.mkdir(parents=True, exist_ok=True)
np.save(out/'observations.npy', Xs)
np.save(out/'actions.npy', y)
np.save(out/'rewards.npy', w)

import joblib
joblib.dump(scaler, out/'scaler.joblib')

feature_map={'action_ids': {str(k):am[k] for k in am}, 'feature_description': ['counts_per_action_sorted_by_action_id','success_rate_last_K','tool_reliability_est','hour_bucket']}
out.joinpath('feature_map.json').write_text(json.dumps(feature_map))
print('wrote expanded_rich dataset with shape', Xs.shape)
