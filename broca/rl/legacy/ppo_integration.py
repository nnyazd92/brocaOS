#!/usr/bin/env python3
"""
PPO Integration Script for BrocaOS RL System

This script migrates from behavioral cloning to PPO policy learning.
It provides:
1. PPO policy training from existing behavioral cloning data
2. Integration with the existing policy.py interface
3. Gradual migration with fallback support
"""

import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from broca.rl.ppo_policy import PPOPolicy, PPOConfig, PPOPolicyRanker
from broca.reasoning.rl_signals import RLSignalAggregator

logger = logging.getLogger(__name__)


class PPOIntegration:
    """Integration layer for migrating from behavioral cloning to PPO."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/rl/ppo_config.json"
        self.config = self._load_config()
        self.ppo_policy = None
        self.ppo_ranker = None
        self.rl_signals = RLSignalAggregator()
        self._setup_logging()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load PPO configuration."""
        default_config = {
            "input_dim": 17,  # RL signals (7) + context features (10)
            "output_dim": 14,  # Number of tools
            "hidden_dim": 128,
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "clip_epsilon": 0.2,
            "value_coef": 0.5,
            "entropy_coef": 0.01,
            "batch_size": 64,
            "epochs": 10,
            "buffer_size": 1000,
            "warmup_steps": 100,
            "migration_threshold": 0.7,  # Confidence threshold to switch to PPO
            "fallback_enabled": True,
            "data_path": "data/rl/behavioral_cloning_data.pkl"
        }
        
        try:
            with open(self.config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _setup_logging(self):
        """Setup logging for PPO integration."""
        log_dir = "logs/rl"
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{log_dir}/ppo_integration.log"),
                logging.StreamHandler()
            ]
        )
    
    def initialize_ppo(self):
        """Initialize PPO policy and ranker."""
        logger.info("Initializing PPO policy...")
        
        config = PPOConfig(
            input_dim=self.config["input_dim"],
            output_dim=self.config["output_dim"],
            hidden_dim=self.config["hidden_dim"],
            learning_rate=self.config["learning_rate"],
            gamma=self.config["gamma"],
            gae_lambda=self.config["gae_lambda"],
            clip_epsilon=self.config["clip_epsilon"],
            value_coef=self.config["value_coef"],
            entropy_coef=self.config["entropy_coef"]
        )
        
        self.ppo_policy = PPOPolicy(config)
        self.ppo_ranker = PPOPolicyRanker()
        
        logger.info(f"PPO policy initialized: input_dim={config.input_dim}, "
                   f"output_dim={config.output_dim}, hidden_dim={config.hidden_dim}")
        
        # Load behavioral cloning data for warm start
        self._warm_start_from_bc_data()
        
        return self.ppo_policy
    
    def _warm_start_from_bc_data(self):
        """Warm start PPO policy from behavioral cloning data."""
        data_path = self.config["data_path"]
        
        try:
            if os.path.exists(data_path):
                logger.info(f"Loading behavioral cloning data from {data_path}")
                with open(data_path, 'rb') as f:
                    bc_data = pickle.load(f)
                
                # Convert BC data to PPO experiences
                experiences = self._convert_bc_to_experiences(bc_data)
                
                # Store experiences in buffer
                for exp in experiences:
                    self.ppo_policy.store_experience(
                        exp["state"], exp["action"], exp["reward"], 
                        exp["next_state"], exp["info"]
                    )
                
                logger.info(f"Warm started with {len(experiences)} experiences from BC data")
                
                # Perform initial training
                if len(experiences) >= self.config["batch_size"]:
                    self.ppo_policy.train()
                    logger.info("Initial training completed from BC data")
            else:
                logger.warning(f"Behavioral cloning data not found at {data_path}")
                
        except Exception as e:
            logger.error(f"Failed to warm start from BC data: {e}")
    
    def _convert_bc_to_experiences(self, bc_data: Dict) -> List[Dict]:
        """Convert behavioral cloning data to PPO experiences."""
        experiences = []
        
        # BC data format: list of (state, action) pairs
        # We need to convert to (state, action, reward, next_state) format
        for i, (state, action) in enumerate(bc_data.get("samples", [])):
            # Create synthetic reward based on action success
            reward = 0.5  # Default moderate reward
            
            # Create next state (slightly modified current state)
            next_state = state.copy() if hasattr(state, 'copy') else np.array(state)
            if isinstance(next_state, np.ndarray):
                # Add small noise for next state
                next_state = next_state + np.random.normal(0, 0.01, size=next_state.shape)
            
            # Create action info
            info = {
                "probs": np.ones(self.config["output_dim"]) / self.config["output_dim"],
                "entropy": np.log(self.config["output_dim"])
            }
            
            experiences.append({
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "info": info
            })
        
        return experiences
    
    def prepare_state_vector(self, context: Dict[str, Any]) -> np.ndarray:
        """Prepare state vector from context for PPO policy."""
        # Extract RL signals
        rl_signals = context.get("rl_signals", {})
        
        # Get RL signal values
        signal_values = []
        for key in [
            'composite_reward',
            'dissonance_reward', 
            'surprise_reward',
            'curiosity_reward',
            'information_gain_reward',
            'coherence_reward',
            'exploration_balance'
        ]:
            signal_values.append(rl_signals.get(key, 0.5))
        
        # Add context features (simplified for now)
        context_features = [
            context.get("confidence", 0.5),
            context.get("complexity", 0.5),
            context.get("urgency", 0.5),
            len(context.get("available_tools", [])),
            context.get("success_rate", 0.5),
            context.get("error_rate", 0.5),
            context.get("recent_success", 0.5),
            context.get("tool_familiarity", 0.5),
            context.get("task_difficulty", 0.5),
            context.get("time_pressure", 0.5)
        ]
        
        # Combine into state vector
        state_vector = np.array(signal_values + context_features, dtype=np.float32)
        
        # Ensure correct dimension
        if len(state_vector) != self.config["input_dim"]:
            logger.warning(f"State vector dimension mismatch: {len(state_vector)} != {self.config['input_dim']}")
            # Pad or truncate
            if len(state_vector) < self.config["input_dim"]:
                padding = np.zeros(self.config["input_dim"] - len(state_vector), dtype=np.float32)
                state_vector = np.concatenate([state_vector, padding])
            else:
                state_vector = state_vector[:self.config["input_dim"]]
        
        return state_vector
    
    def select_tool_with_ppo(self, context: Dict[str, Any], tools: List[Any]) -> Dict[str, Any]:
        """Select tool using PPO policy."""
        if not self.ppo_policy:
            self.initialize_ppo()
        
        # Prepare state vector
        state = self.prepare_state_vector(context)
        
        # Select action using PPO policy
        action_idx, value, info = self.ppo_policy.select_action(state)
        
        # Map action index to tool
        if action_idx < len(tools):
            selected_tool = tools[action_idx]
            tool_name = getattr(selected_tool, 'name', str(selected_tool))
        else:
            # Fallback to first tool
            selected_tool = tools[0]
            tool_name = getattr(selected_tool, 'name', str(selected_tool))
            logger.warning(f"Action index {action_idx} out of bounds, using first tool")
        
        # Get rankings for all tools
        rankings = self.ppo_ranker.rank_tools(context, tools)
        
        # Find ranking for selected tool
        selected_ranking = next(
            (r for r in rankings if r["tool_name"] == tool_name),
            {"tool_name": tool_name, "score": 0.5, "expected_reward": 0.5}
        )
        
        # Add PPO-specific info
        selected_ranking.update({
            "ppo_action_idx": action_idx,
            "ppo_value_estimate": float(value),
            "ppo_entropy": float(info["entropy"]),
            "ppo_confidence": float(info["probs"][action_idx]),
            "policy_type": "ppo"
        })
        
        return selected_ranking
    
    def update_with_feedback(self, context: Dict[str, Any], tool_name: str, 
                           success: bool, execution_time: float = 1.0):
        """Update PPO policy with feedback from tool execution."""
        if not self.ppo_policy:
            logger.warning("PPO policy not initialized, skipping feedback update")
            return
        
        # Calculate reward
        reward = self._calculate_reward(success, execution_time, context)
        
        # Get current state (from context)
        state = self.prepare_state_vector(context)
        
        # Find action index for the tool
        # This would need tool-to-index mapping from context
        action_idx = context.get("tool_indices", {}).get(tool_name, 0)
        
        # Create next state (simplified - in practice would be next context)
        next_state = state.copy()
        # Add small noise to simulate state transition
        next_state = next_state + np.random.normal(0, 0.01, size=next_state.shape)
        
        # Create action info
        info = {
            "probs": np.ones(self.config["output_dim"]) / self.config["output_dim"],
            "entropy": np.log(self.config["output_dim"])
        }
        
        # Store experience
        self.ppo_policy.store_experience(state, action_idx, reward, next_state, info)
        
        # Train if buffer is sufficiently full
        if len(self.ppo_policy.buffer) >= self.config["batch_size"]:
            loss = self.ppo_policy.train()
            logger.info(f"PPO training completed: loss={loss:.4f}, buffer_size={len(self.ppo_policy.buffer)}")
    
    def _calculate_reward(self, success: bool, execution_time: float, 
                         context: Dict[str, Any]) -> float:
        """Calculate reward for tool execution."""
        base_reward = 1.0 if success else -1.0
        
        # Time efficiency bonus/penalty
        time_reward = 1.0 / max(execution_time, 0.1)
        
        # Contextual bonus
        context_bonus = 0.0
        if context.get("urgency", 0) > 0.7:
            # Bonus for quick decisions under time pressure
            context_bonus = 0.2
        
        # Combine rewards
        total_reward = base_reward * 0.6 + time_reward * 0.3 + context_bonus * 0.1
        
        # Normalize to [0, 1] range
        normalized_reward = (total_reward + 1) / 2
        
        return normalized_reward
    
    def save_policy(self, path: str = "models/rl/ppo_policy.pt"):
        """Save PPO policy to disk."""
        if not self.ppo_policy:
            logger.warning("No PPO policy to save")
            return
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.ppo_policy.save(path)
        logger.info(f"PPO policy saved to {path}")
    
    def load_policy(self, path: str = "models/rl/ppo_policy.pt"):
        """Load PPO policy from disk."""
        if not self.ppo_policy:
            self.initialize_ppo()
        
        if os.path.exists(path):
            self.ppo_policy.load(path)
            logger.info(f"PPO policy loaded from {path}")
        else:
            logger.warning(f"PPO policy file not found at {path}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status from behavioral cloning to PPO."""
        status = {
            "policy_type": "ppo" if self.ppo_policy else "behavioral_cloning",
            "ppo_initialized": bool(self.ppo_policy),
            "buffer_size": len(self.ppo_policy.buffer) if self.ppo_policy else 0,
            "total_reward": self.ppo_policy.total_reward if self.ppo_policy else 0.0,
            "training_steps": self.ppo_policy.training_steps if self.ppo_policy else 0,
            "migration_threshold": self.config["migration_threshold"],
            "fallback_enabled": self.config["fallback_enabled"]
        }
        
        # Calculate migration readiness
        if self.ppo_policy:
            readiness = min(1.0, len(self.ppo_policy.buffer) / self.config["warmup_steps"])
            status["migration_readiness"] = readiness
            status["ready_for_migration"] = readiness >= self.config["migration_threshold"]
        else:
            status["migration_readiness"] = 0.0
            status["ready_for_migration"] = False
        
        return status


def main():
    """Main function for testing PPO integration."""
    print("=== PPO Integration Test ===")
    
    # Initialize integration
    integration = PPOIntegration()
    
    # Initialize PPO
    integration.initialize_ppo()
    
    # Get migration status
    status = integration.get_migration_status()
    print("\nMigration Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test tool selection
    print("\nTesting tool selection...")
    
    # Create dummy context
    context = {
        "rl_signals": {
            'composite_reward': 0.8,
            'dissonance_reward': 0.7,
            'surprise_reward': 0.6,
            'curiosity_reward': 0.9,
            'information_gain_reward': 0.5,
            'coherence_reward': 0.8,
            'exploration_balance': 0.3
        },
        "confidence": 0.7,
        "complexity": 0.6,
        "urgency": 0.4,
        "available_tools": ["tool1", "tool2", "tool3"],
        "success_rate": 0.8,
        "error_rate": 0.1,
        "recent_success": 1.0,
        "tool_familiarity": 0.9,
        "task_difficulty": 0.5,
        "time_pressure": 0.3
    }
    
    # Create dummy tools
    class DummyTool:
        def __init__(self, name):
            self.name = name
    
    tools = [DummyTool(f"tool_{i}") for i in range(14)]
    
    # Select tool with PPO
    ranking = integration.select_tool_with_ppo(context, tools)
    
    print(f"\nSelected tool: {ranking['tool_name']}")
    print(f"Score: {ranking['score']:.4f}")
    print(f"PPO confidence: {ranking.get('ppo_confidence', 0):.4f}")
    print(f"Policy type: {ranking.get('policy_type', 'unknown')}")
    
    # Test feedback update
    print("\nTesting feedback update...")
    integration.update_with_feedback(context, ranking["tool_name"], success=True, execution_time=0.5)
    
    # Get updated status
    status = integration.get_migration_status()
    print(f"\nUpdated buffer size: {status['buffer_size']}")
    print(f"Total reward: {status['total_reward']:.4f}")
    
    # Save policy
    integration.save_policy()
    
    print("\n✅ PPO integration test completed successfully!")


if __name__ == "__main__":
    main()
