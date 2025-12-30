#!/usr/bin/env python3
"""Compute permutation importance for current BC model using expanded_live data.
Saves JSONL lines with feature importances.
"""
import json
from pathlib import Path
import joblib
import numpy as np
from sklearn.inspection import permutation_importance

base = Path('data/rl/expanded_live')
if not base.exists():
    raise SystemExit('expanded_live dataset missing')

X = np.load(base/'observations.npy')
y = np.load(base/'actions.npy')
model_path = Path('models/rl/policy_bc.pkl')
if not model_path.exists():
    raise SystemExit('model missing')
model = joblib.load(model_path)

# compute permutation importance per class by using scoring='accuracy'
res = permutation_importance(model, X, y, scoring='accuracy', n_repeats=10, random_state=0, n_jobs=1)

feature_names = json.loads((base/'feature_map.json').read_text()).get('feature_description')
if isinstance(feature_names, str):
    # simple comma-separated description -> synthesize names
    feature_names = ['f'+str(i) for i in range(X.shape[1])]

outp = Path('data/rl/explanations_permutation.jsonl')
with open(outp,'w',encoding='utf-8') as f:
    # res.importances_mean shape: (n_features,) for single-output; for multiclass scikit-learn returns same shape
    for i, mean_imp in enumerate(res.importances_mean):
        entry = {
            'feature_index': i,
            'feature_name': feature_names[i] if i < len(feature_names) else f'f{i}',
            'importance_mean': float(mean_imp),
            'importance_std': float(res.importances_std[i]),
        }
        f.write(json.dumps(entry) + '\n')

print('wrote', outp)
