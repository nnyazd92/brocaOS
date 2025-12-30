#!/usr/bin/env python3
"""PoC training script: try d3rlpy.CQL on transitions, else fallback to a simple Behavioral Cloning (logistic regression)"""
import json
from pathlib import Path

trans_p = Path('data/rl/transitions.jsonl')
if not trans_p.exists():
    print('no transitions.jsonl, run preprocess')
    raise SystemExit(1)

# Try import d3rlpy
try:
    import d3rlpy
    has_d3rlpy = True
except Exception:
    has_d3rlpy = False

if has_d3rlpy:
    print('d3rlpy available — would run CQL PoC here (skipping heavy training in this environment)')
    # Placeholder: in a real run, load dataset into d3rlpy format and train CQL
    Path('models/rl').mkdir(parents=True, exist_ok=True)
    Path('models/rl/policy_placeholder.txt').write_text('CQL model placeholder — train in full infra')
else:
    print('d3rlpy not available — running Behavioral Cloning (toy)')
    # Simple BC: predict action_id from context hash prefix using sklearn
    from sklearn.linear_model import LogisticRegression
    X = []
    y = []
    for line in trans_p.read_text(encoding='utf-8').splitlines():
        obj = json.loads(line)
        state = obj.get('state', {})
        ch = state.get('context_hash','')[:8]
        # simple featurization: hex -> int vector
        feat = [int(ch[i:i+2],16) for i in range(0, len(ch), 2)] if ch else [0]*4
        X.append(feat)
        y.append(obj.get('action_id',0))
    clf = LogisticRegression(max_iter=200)
    clf.fit(X,y)
    Path('models/rl').mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(clf, 'models/rl/policy_bc.pkl')
    print('saved BC policy to models/rl/policy_bc.pkl')
