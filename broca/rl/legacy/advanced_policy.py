"""
Advanced PolicyRanker with support for multiple RL algorithms:
1. Behavioral Cloning (BC) - Existing sklearn models
2. Proximal Policy Optimization (PPO) - New PyTorch implementation
3. Hybrid mode - Can switch between or ensemble both

Provides backward compatibility with existing interface.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Literal

import numpy as np

logger = logging.getLogger(__name__)


class AdvancedPolicyRanker:
    """Advanced policy ranker supporting multiple RL algorithms."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        algorithm: Literal["bc", "ppo", "auto"] = "auto",
        config: Optional[Dict[str, Any]] = None
    ):
        self.model_path = model_path
        self.algorithm = algorithm
        self.config = config or {}
        
        # Models
        self.bc_model = None
        self.ppo_model = None
        self.action_map = None
        
        # State
        self.current_algorithm = None
        self.performance_metrics = {
            "bc_accuracy": 0.0,
            "ppo_accuracy": 0.0,
            "total_predictions": 0,
            "algorithm_switches": 0,
        }
    
    def load_model(self, model_path: Optional[str] = None):
        """Load appropriate model based on algorithm selection."""
        path = model_path or self.model_path
        
        try:
            # Load action map
            self._load_action_map()
            
            # Determine algorithm if auto
            if self.algorithm == "auto":
                self._auto_select_algorithm(path)
            
            # Load specific model
            if self.current_algorithm == "bc":
                self._load_bc_model(path)
            elif self.current_algorithm == "ppo":
                self._load_ppo_model(path)
            
            logger.info(f"Loaded {self.current_algorithm.upper()} model from {path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Fallback to simple heuristic
            self.current_algorithm = "heuristic"
    
    def _load_action_map(self):
        """Load action map from CSV."""
        try:
            action_map_path = Path("data/rl/action_map.csv")
            if action_map_path.exists():
                action_map = {}
                with open(action_map_path) as f:
                    next(f)  # Skip header
                    for line in f:
                        tool_name, action_id = line.strip().split(',')
                        action_map[int(action_id)] = tool_name
                self.action_map = action_map
                logger.info(f"Loaded action map with {len(action_map)} actions")
        except Exception as e:
            logger.warning(f"Failed to load action map: {e}")
            self.action_map = None
    
    def _auto_select_algorithm(self, path: str):
        """Automatically select best algorithm based on available models."""
        path_obj = Path(path) if path else Path("models/rl/")
        
        # Check for PPO model
        ppo_path = path_obj if path and path.endswith(".pt") else Path("models/rl/policy_ppo.pt")
        if ppo_path.exists():
            self.current_algorithm = "ppo"
            return
        
        # Check for BC model
        bc_path = path_obj if path and (path.endswith(".pkl") or path.endswith(".joblib")) else Path("models/rl/policy_bc.pkl")
        if bc_path.exists():
            self.current_algorithm = "bc"
            return
        
        # Default to BC if training data exists
        expanded_path = Path("data/rl/expanded_live/observations.npy")
        if expanded_path.exists():
            self.current_algorithm = "bc"
        else:
            self.current_algorithm = "heuristic"
    
    def _load_bc_model(self, path: str):
        """Load behavioral cloning model."""
        try:
            import joblib
            model_path = path or "models/rl/policy_bc.pkl"
            self.bc_model = joblib.load(model_path)
            
            # Check if it's our expanded policy wrapper
            if hasattr(self.bc_model, 'predict_proba'):
                logger.info("Loaded BC model with predict_proba method")
            else:
                logger.warning("BC model doesn't have predict_proba, may need conversion")
                
        except Exception as e:
            logger.error(f"Failed to load BC model: {e}")
            raise
    
    def _load_ppo_model(self, path: str):
        """Load PPO model."""
        try:
            from .ppo_policy import PPOPolicyRanker
            model_path = path or "models/rl/policy_ppo.pt"
            self.ppo_model = PPOPolicyRanker(model_path)
            logger.info("Loaded PPO model")
        except Exception as e:
            logger.error(f"Failed to load PPO model: {e}")
            raise
    
    def rank_tools(self, context: Dict[str, Any], tools: List[Any]) -> List[Dict[str, Any]]:
        """Rank tools using selected algorithm."""
        if self.current_algorithm == "bc":
            return self._rank_with_bc(context, tools)
        elif self.current_algorithm == "ppo":
            return self._rank_with_ppo(context, tools)
        else:
            return self._rank_heuristic(context, tools)
    
    def _rank_with_bc(self, context: Dict[str, Any], tools: List[Any]) -> List[Dict[str, Any]]:
        """Rank tools using behavioral cloning."""
        try:
            # Extract features
            state = self._context_to_state(context)
            
            # Get predictions
            if hasattr(self.bc_model, 'predict_proba'):
                probs = self.bc_model.predict_proba(state.reshape(1, -1))[0]
            else:
                # Fallback for models without predict_proba
                probs = np.ones(len(tools)) / len(tools)
            
            # Create rankings
            rankings = []
            for i, tool in enumerate(tools):
                tool_name = getattr(tool, 'name', str(tool))
                if i < len(probs):
                    score = float(probs[i])
                else:
                    score = 0.0
                
                rankings.append({
                    "tool_name": tool_name,
                    "score": score,
                    "expected_reward": score,
                    "algorithm": "bc"
                })
            
            rankings.sort(key=lambda r: r['score'], reverse=True)
            return rankings
            
        except Exception as e:
            logger.error(f"BC ranking failed: {e}, falling back to heuristic")
            return self._rank_heuristic(context, tools)
    
    def _rank_with_ppo(self, context: Dict[str, Any], tools: List[Any]) -> List[Dict[str, Any]]:
        """Rank tools using PPO."""
        try:
            if self.ppo_model is None:
                raise ValueError("PPO model not loaded")
            
            rankings = self.ppo_model.rank_tools(context, tools)
            
            # Add algorithm info
            for r in rankings:
                r["algorithm"] = "ppo"
            
            return rankings
            
        except Exception as e:
            logger.error(f"PPO ranking failed: {e}, falling back to BC")
            return self._rank_with_bc(context, tools)
    
    def _rank_heuristic(self, context: Dict[str, Any], tools: List[Any]) -> List[Dict[str, Any]]:
        """Fallback heuristic ranking."""
        n = max(1, len(tools))
        rankings = []
        
        for tool in tools:
            tool_name = getattr(tool, 'name', str(tool))
            rankings.append({
                "tool_name": tool_name,
                "score": 1.0 / n,
                "expected_reward": 0.5,
                "algorithm": "heuristic"
            })
        
        rankings.sort(key=lambda r: r['score'], reverse=True)
        return rankings
    
    def predict_distribution(self, context: Dict[str, Any], tools: List[Any]) -> Dict[str, float]:
        """Get probability distribution over tools."""
        rankings = self.rank_tools(context, tools)
        
        distribution = {}
        for ranking in rankings:
            distribution[ranking["tool_name"]] = ranking["score"]
        
        # Normalize
        total = sum(distribution.values())
        if total > 0:
            distribution = {k: v / total for k, v in distribution.items()}
        
        return distribution
    
    def _context_to_state(self, context: Dict[str, Any]) -> np.ndarray:
        """Convert context to feature vector."""
        from .features import extract_state_features

        return extract_state_features(context, input_dim=16)
    
    def switch_algorithm(self, algorithm: Literal["bc", "ppo", "heuristic"]):
        """Switch to different algorithm."""
        if algorithm != self.current_algorithm:
            self.current_algorithm = algorithm
            self.performance_metrics["algorithm_switches"] += 1
            logger.info(f"Switched to {algorithm.upper()} algorithm")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self.performance_metrics,
            "current_algorithm": self.current_algorithm,
            "action_map_size": len(self.action_map) if self.action_map else 0,
        }
    
    def save_ppo_model(self, path: str = "models/rl/policy_ppo.pt"):
        """Save PPO model to disk."""
        if self.ppo_model and hasattr(self.ppo_model, 'ppo_policy'):
            self.ppo_model.ppo_policy.save(path)
            logger.info(f"Saved PPO model to {path}")
        else:
            logger.warning("No PPO model to save")


# Backward compatibility wrapper
class PolicyRanker(AdvancedPolicyRanker):
    """Backward compatible PolicyRanker that defaults to BC."""
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_path, algorithm="bc")


if __name__ == "__main__":
    # Test the advanced policy ranker
    print("Testing AdvancedPolicyRanker...")
    
    ranker = AdvancedPolicyRanker(algorithm="auto")
    ranker.load_model()
    
    print(f"Loaded algorithm: {ranker.current_algorithm}")
    print(f"Action map: {ranker.action_map}")
    
    # Test ranking
    class DummyTool:
        def __init__(self, name):
            self.name = name
    
    tools = [DummyTool(f"tool_{i}") for i in range(14)]
    context = {"rl_signals": {"composite_reward": 0.8}}
    
    rankings = ranker.rank_tools(context, tools)
    print(f"\nGenerated {len(rankings)} rankings")
    print("Top 5:")
    for i, r in enumerate(rankings[:5]):
        print(f"  {i+1}. {r['tool_name']}: {r['score']:.4f} ({r['algorithm']})")
    
    print("\n✅ AdvancedPolicyRanker test complete!")
