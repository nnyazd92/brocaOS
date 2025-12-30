"""
Expanded policy model for handling larger action spaces with fallback behavior.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression


class ExpandedPolicyModel:
    """Wrapper that handles expanded action space with fallback for unseen actions."""
    
    def __init__(self, base_model, n_actions=14):
        self.base_model = base_model
        self.n_actions = n_actions
        self.base_classes = set(base_model.classes_)
        
    def predict_proba(self, X):
        """Predict probabilities for all actions (including unseen ones)."""
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
        """Predict the most likely action."""
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)
    
    @property
    def classes_(self):
        """Return all possible classes (0 to n_actions-1)."""
        return np.arange(self.n_actions)


def create_expanded_policy(base_data_path='data/rl/expanded_live', n_actions=14):
    """Create an expanded policy model from training data."""
    import joblib
    from pathlib import Path
    
    # Load existing data
    base = Path(base_data_path)
    X = np.load(base/'observations.npy')
    y = np.load(base/'actions.npy')
    sample_weight = np.load(base/'rewards.npy')
    
    # Train base logistic regression
    clf = LogisticRegression(max_iter=1000, solver='lbfgs')
    clf.fit(X, y, sample_weight=sample_weight)
    
    # Create expanded wrapper
    return ExpandedPolicyModel(clf, n_actions=n_actions)


if __name__ == '__main__':
    # Test the module
    model = create_expanded_policy()
    print(f"Created expanded policy model with {model.n_actions} actions")
    print(f"Base classes: {sorted(model.base_classes)}")
