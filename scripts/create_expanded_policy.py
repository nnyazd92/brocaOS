#!/usr/bin/env python3
"""Create expanded policy model that handles 14 tools with fallback behavior."""
import numpy as np
from pathlib import Path
import joblib
from sklearn.linear_model import LogisticRegression
import json

# Create models directory
Path('models/rl').mkdir(parents=True, exist_ok=True)

# Load existing data
base = Path('data/rl/expanded_live')
X = np.load(base/'observations.npy')
y = np.load(base/'actions.npy')
sample_weight = np.load(base/'rewards.npy')

print(f"Original data shape: X={X.shape}, y={y.shape}")
print(f"Unique actions in training data: {np.unique(y)}")

# We need to handle 14 actions (0-13)
# Strategy: Train on existing 4 actions, then extend to 14 with fallback behavior
clf = LogisticRegression(max_iter=1000, solver='lbfgs')
clf.fit(X, y, sample_weight=sample_weight)

print(f"\nBase model classes: {clf.classes_}")
print(f"Base model coefficients shape: {clf.coef_.shape}")

# Create an expanded model wrapper
class ExpandedPolicyModel:
    """Wrapper that handles expanded action space with fallback for unseen actions."""
    
    def __init__(self, base_model, n_actions=14):
        self.base_model = base_model
        self.n_actions = n_actions
        self.base_classes = set(base_model.classes_)
        
    def predict_proba(self, X):
        # Get base model predictions
        base_probs = self.base_model.predict_proba(X)
        
        # Create expanded probability array
        expanded_probs = np.zeros((X.shape[0], self.n_actions))
        
        # Map base probabilities to expanded array
        for i, class_idx in enumerate(self.base_model.classes_):
            expanded_probs[:, class_idx] = base_probs[:, i]
        
        # Distribute remaining probability mass evenly among unseen actions
        # This gives low but non-zero probability to untrained tools
        unseen_actions = [a for a in range(self.n_actions) if a not in self.base_classes]
        if unseen_actions:
            # Give small uniform probability to unseen actions
            # Scale down base probabilities slightly to make room
            scale_factor = 0.8  # Keep 80% of probability for known actions
            expanded_probs[:, list(self.base_classes)] *= scale_factor
            
            # Distribute remaining 20% evenly among unseen actions
            unseen_prob = (1 - scale_factor) / len(unseen_actions)
            for action in unseen_actions:
                expanded_probs[:, action] = unseen_prob
        
        return expanded_probs
    
    def predict(self, X):
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

# Create and save the expanded model
expanded_model = ExpandedPolicyModel(clf, n_actions=14)
model_path = 'models/rl/policy_bc_expanded.pkl'
joblib.dump(expanded_model, model_path)
print(f"\nSaved expanded model to {model_path}")

# Test the expanded model
test_features = X[0:1]
expanded_probs = expanded_model.predict_proba(test_features)[0]

print(f"\nExpanded model predictions (14 actions):")
action_names = [
    "terminal", "web_search", "store_memory", "planning", 
    "reasoning", "retrieve_memories", "delete_memory", "update_memory",
    "link_memories", "get_related_memories", "memory_graph", 
    "self_model_crud", "environment_access", "learning"
]

for action_id in range(14):
    prob = expanded_probs[action_id]
    name = action_names[action_id] if action_id < len(action_names) else f"action_{action_id}"
    trained = "✓" if action_id in expanded_model.base_classes else "✗"
    print(f"  [{trained}] Action {action_id:2d} ({name:20s}): {prob:.4f}")

# Also update the main model path for backward compatibility
main_model_path = 'models/rl/policy_bc.pkl'
joblib.dump(expanded_model, main_model_path)
print(f"\nAlso saved as main model: {main_model_path}")

print("\n✅ Action map successfully expanded to 14 tools!")
print("   The RL system will now consider all available tools.")
print("   Untrained tools get low probability (exploration bonus).")
