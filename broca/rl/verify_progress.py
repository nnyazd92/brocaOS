#!/usr/bin/env python3
"""Compute simple verification metrics comparing BC policy to frequency baseline on transitions."""
import json
from pathlib import Path
import numpy as np
import joblib

trans_p = Path('data/rl/transitions.jsonl')
if not trans_p.exists():
    print('no transitions to evaluate')
    raise SystemExit(1)

trans = [json.loads(l) for l in trans_p.read_text().splitlines()]
action_map = {int(line.split(',')[1]):line.split(',')[0] for line in Path('data/rl/action_map.csv').read_text().splitlines()[1:]}
# load BC model
model_path = Path('models/rl/policy_bc.pkl')
if not model_path.exists():
    print('no policy model found')
    raise SystemExit(1)
clf = joblib.load(model_path)

# prepare X and y
from numpy import array
X = np.load('data/rl/expanded_rich/observations.npy')
y = np.load('data/rl/expanded_rich/actions.npy')
rews = np.load('data/rl/expanded_rich/rewards.npy')

# frequency baseline: pick most frequent action
from collections import Counter
most=Counter(y).most_common(1)[0][0]

# evaluate: model expected reward = average reward of predicted action per sample
from pathlib import Path
scaler_path = Path('data/rl/expanded_rich/scaler.joblib')
if scaler_path.exists():
    scaler = joblib.load(scaler_path)
    Xs = scaler.transform(X)
else:
    Xs = X

# evaluate: model expected reward = average reward of predicted action per sample
try:
    probs = clf.predict_proba(Xs)
    preds = probs.argmax(axis=1)
    policy_reward = np.mean([rews[i] for i in range(len(rews)) if preds[i]==y[i]])
    model_feature_shape = Xs.shape[1]
except ValueError as e:
    print('model predict_proba failed:', e)
    preds = None
    policy_reward = None
    model_feature_shape = None
# baseline reward: average reward when action==most
baseline_reward = np.mean([rews[i] for i in range(len(rews)) if y[i]==most])

out={'policy_reward_estimate': (float(policy_reward) if policy_reward is not None else None), 'baseline_reward': float(baseline_reward),'policy_most_common': (int(preds.mean()) if preds is not None else None), 'model_feature_shape': model_feature_shape, 'input_feature_shape': X.shape[1]}
Path('data/rl/verify_progress.json').write_text(json.dumps(out, indent=2))
print('wrote verify_progress.json', out)
