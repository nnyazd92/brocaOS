#!/usr/bin/env python3
"""Preprocess transitions by joining with live rl_rewards.csv to include authoritative RL signals.
Matches transitions to nearest timestamp in rl_rewards.csv and includes rl_signals in features.
"""
import json
from pathlib import Path
import numpy as np
import csv
from datetime import datetime
from bisect import bisect_left

trans_p = Path('data/rl/transitions.jsonl')
rewards_csv = Path('data/rl_rewards.csv')
if not trans_p.exists() or not rewards_csv.exists():
    print('required files missing')
    raise SystemExit(1)

# load reward rows with timestamps
reward_rows = []
with open(rewards_csv,'r',encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        ts = r['timestamp']
        reward_rows.append((ts, r))

# helper to find nearest reward row by timestamp (simple linear search for now)
from dateutil import parser
reward_times = [parser.parse(ts) for ts,_ in reward_rows]

trans = [json.loads(l) for l in trans_p.read_text().splitlines()]
trans_sorted = sorted(trans, key=lambda x: x['timestamp'])

obs=[]
actions=[]
rews=[]

# read action map
am = {}
with open('data/rl/action_map.csv') as f:
    next(f)
    for l in f:
        k,v = l.strip().split(',',1)
        am[int(v)]=k

K=10
from collections import deque
window=deque(maxlen=K)
success_window=deque(maxlen=K)

for t in trans_sorted:
    aid = t['action_id']
    window.append(aid)
    success_window.append(t.get('reward',0.0))
    counts = [window.count(i) for i in sorted(am.keys())]
    succ_rate = sum(success_window)/len(success_window)
    # find nearest reward row by timestamp
    try:
        tt = parser.parse(t['timestamp'])
        idx = bisect_left(reward_times, tt)
        idx = max(0, min(idx, len(reward_rows)-1))
        rr = reward_rows[idx][1]
        composite = float(rr.get('composite_reward',0.0))
        dissonance = float(rr.get('dissonance_reward',0.0))
        surprise = float(rr.get('surprise_reward',0.0))
        curiosity = float(rr.get('curiosity_reward',0.0))
        info_gain = float(rr.get('information_gain_reward',0.0))
        coherence = float(rr.get('coherence_reward',0.0))
        exploration = float(rr.get('exploration_balance',0.0))
    except Exception:
        composite=dissonance=surprise=curiosity=info_gain=coherence=exploration=0.0

    hour = 0
    try:
        hour = int(t['timestamp'][11:13])
    except Exception:
        pass

    ch = t['state'].get('context_hash','')
    ch_bytes = [int(ch[i:i+2],16) if i+2<=len(ch) else 0 for i in range(0,8,2)]
    feat = counts + [succ_rate, hour] + ch_bytes + [composite, dissonance, surprise, curiosity, info_gain, coherence, exploration]
    obs.append(feat)
    actions.append(aid)
    rews.append(t.get('reward',0.0))

X = np.array(obs, dtype=float)
y = np.array(actions, dtype=int)
w = np.array(rews, dtype=float)

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
Xs = scaler.fit_transform(X)

out = Path('data/rl/expanded_live')
out.mkdir(parents=True, exist_ok=True)
np.save(out/'observations.npy', Xs)
np.save(out/'actions.npy', y)
np.save(out/'rewards.npy', w)
import joblib
joblib.dump(scaler, out/'scaler.joblib')

feature_map={'action_ids': {str(k):am[k] for k in am}, 'feature_description':'counts,success_rate,hour,context_bytes,composite,dissonance,surprise,curiosity,info_gain,coherence,exploration'}
out.joinpath('feature_map.json').write_text(json.dumps(feature_map))
print('wrote expanded_live dataset with shape', Xs.shape)
