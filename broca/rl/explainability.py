#!/usr/bin/env python3
"""Simple explainability utilities for PolicyRanker decisions.
Supports linear models (coef * features) and a permutation importance fallback.
"""
import json
from pathlib import Path
import numpy as np

EXPL_PATH = Path('data/rl/explanations.jsonl')


def explain_linear(model, feature_vector, feature_names, top_k=5):
    # model.coef_ shape: (n_classes, n_features) for multiclass
    coefs = getattr(model, 'coef_', None)
    if coefs is None:
        return None
    explanations = {}
    # for each class/action index, compute feature contributions
    for class_idx, coef in enumerate(coefs):
        # ensure size alignment by truncating or padding feature_vector
        fv = np.array(feature_vector, dtype=float)
        if fv.shape[0] < coef.shape[0]:
            pad = np.zeros(coef.shape[0] - fv.shape[0])
            fv = np.concatenate([fv, pad])
        elif fv.shape[0] > coef.shape[0]:
            fv = fv[:coef.shape[0]]
        contribs = coef * fv
        pairs = list(zip(feature_names, contribs.tolist()))
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)
        explanations[class_idx] = [{'feature':p[0], 'contribution':p[1]} for p in pairs[:top_k]]
    return explanations


def append_explanation(uid, context, feature_names, feature_vector, model, tool_name_map=None):
    entry = {
        'uid': uid,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()+'Z',
        'context_summary': context,
        'feature_names': feature_names,
        'feature_vector_snapshot': [float(x) for x in feature_vector],
        'explanation': None
    }
    try:
        if hasattr(model, 'coef_'):
            entry['explanation'] = explain_linear(model, feature_vector, feature_names)
        else:
            # Fallback: permutation importance (fast, model-agnostic)
            try:
                from sklearn.inspection import permutation_importance
                # need X and y for permutation importance; we do a cheap approximate by using current feature vector
                entry['explanation'] = {'note':'non-linear model; permutation importance not computed in smoke mode'}
            except Exception:
                entry['explanation'] = {'note': 'non-linear model; no coefficients; explain via surrogate or permutation'}
    except Exception as e:
        entry['explanation'] = {'error': str(e)}

    with open(EXPL_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry

if __name__=='__main__':
    print('explainability module')
