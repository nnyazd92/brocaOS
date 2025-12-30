#!/usr/bin/env python3
"""Train behavioral cloning model (sklearn) on expanded arrays and save classifier."""
import numpy as np
from pathlib import Path

base = Path('data/rl/expanded')
if not base.exists():
    print('no expanded data, run preprocess_expanded')
    raise SystemExit(1)

X = np.load(base/'observations.npy')
y = np.load(base/'actions.npy')
sample_weight = np.load(base/'rewards.npy')

# Use logistic regression multiclass
from sklearn.linear_model import LogisticRegression
import joblib
clf = LogisticRegression(max_iter=500)
clf.fit(X, y, sample_weight=sample_weight)

Path('models/rl').mkdir(parents=True, exist_ok=True)
joblib.dump(clf, 'models/rl/policy_bc.pkl')
print('saved BC model to models/rl/policy_bc.pkl')
