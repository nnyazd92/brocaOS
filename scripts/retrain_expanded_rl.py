#!/usr/bin/env python3
"""Retrain RL model with expanded action space (14 tools)."""
import numpy as np
from pathlib import Path
import joblib
from sklearn.linear_model import LogisticRegression

# Create models directory
Path('models/rl').mkdir(parents=True, exist_ok=True)

# Load existing data
base = Path('data/rl/expanded_live')
X = np.load(base/'observations.npy')
y = np.load(base/'actions.npy')
sample_weight = np.load(base/'rewards.npy')

print(f"Original data shape: X={X.shape}, y={y.shape}")
print(f"Unique actions in training data: {np.unique(y)}")

# Train logistic regression for multiclass
# In sklearn 1.8.0, multi_class is handled automatically
clf = LogisticRegression(max_iter=1000, solver='lbfgs')
clf.fit(X, y, sample_weight=sample_weight)

# Save the model
model_path = 'models/rl/policy_bc_expanded.pkl'
joblib.dump(clf, model_path)
print(f"Saved expanded model to {model_path}")

# Test predictions
print(f"\nModel classes: {clf.classes_}")
print(f"Number of classes learned: {len(clf.classes_)}")
print(f"Model coefficients shape: {clf.coef_.shape}")

# Create a simple test to show predictions
test_features = X[0:1]  # First observation
probs = clf.predict_proba(test_features)[0]
print(f"\nTest prediction probabilities for first observation:")
for class_idx, prob in zip(clf.classes_, probs):
    print(f"  Action {class_idx}: {prob:.4f}")
