#!/usr/bin/env python3
"""Expanded preprocessing to produce arrays for d3rlpy MDPDataset.
- Observations: vector containing recent tool counts (last K=5), context_hash bytes, time bucket
- Actions: action_id
- Rewards: reward
- Next observation: same features (shifted)
"""
import json
from pathlib import Path
import numpy as np
import hashlib

p = Path('data/rl/transitions.jsonl')
if not p.exists():
    print('run preprocess first')
    raise SystemExit(1)

lines = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
# Build time-ordered by timestamp
lines_sorted = sorted(lines, key=lambda x: x['timestamp'])

# Map action ids
action_ids = [t['action_id'] for t in lines_sorted]
K=5
# build recent K counts per sample
obs = []
actions = []
rewards = []
next_obs = []

from collections import deque, Counter
window = deque(maxlen=K)
for t in lines_sorted:
    window.append(t['action_id'])
    counts = [window.count(i) for i in sorted(set(action_ids))]
    # context hash bytes
    ch = t['state'].get('context_hash','')
    ch_bytes = [int(ch[i:i+2],16) if i+2<=len(ch) else 0 for i in range(0,8,2)]
    # time bucket (hour of timestamp naive)
    try:
        hour = int(t['timestamp'][11:13])
    except Exception:
        hour = 0
    obs_vec = counts + ch_bytes + [hour]
    obs.append(obs_vec)
    actions.append(t['action_id'])
    rewards.append(t['reward'])

# next_obs is shifted by one (last sample next_obs is zeros)
for i in range(len(obs)-1):
    next_obs.append(obs[i+1])
# pad last
if obs:
    next_obs.append([0]*len(obs[0]))

obs_a = np.array(obs, dtype=float)
acts_a = np.array(actions, dtype=int)
rews_a = np.array(rewards, dtype=float)
next_a = np.array(next_obs, dtype=float)

out_dir = Path('data/rl/expanded')
out_dir.mkdir(parents=True, exist_ok=True)
np.save(out_dir/'observations.npy', obs_a)
np.save(out_dir/'actions.npy', acts_a)
np.save(out_dir/'rewards.npy', rews_a)
np.save(out_dir/'next_observations.npy', next_a)
print('wrote arrays to', out_dir)
