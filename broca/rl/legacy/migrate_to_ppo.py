"""
Migration script to convert behavioral cloning data to PPO training format.

This script:
1. Loads existing BC training data
2. Converts it to PPO-compatible format
3. Trains an initial PPO policy
4. Saves the PPO model
5. Creates comparison metrics
"""

import logging
from pathlib import Path
import numpy as np
import pickle
import json
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BCToPPOMigrator:
    """Migrate from Behavioral Cloning to Proximal Policy Optimization."""
    
    def __init__(self, data_dir: str = "data/rl", models_dir: str = "models/rl"):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Data containers
        self.bc_data = None
        self.ppo_training_data = []
        self.action_map = None
        
    def load_bc_data(self) -> bool:
        """Load behavioral cloning training data."""
        try:
            # Check for expanded live data
            expanded_dir = self.data_dir / "expanded_live"
            if expanded_dir.exists():
                logger.info(f"Loading expanded live data from {expanded_dir}")
                
                # Load observations
                obs_path = expanded_dir / "observations.npy"
                if obs_path.exists():
                    observations = np.load(obs_path)
                    logger.info(f"Loaded {len(observations)} observations")
                else:
                    logger.warning(f"No observations.npy found in {expanded_dir}")
                    observations = np.array([])
                
                # Load actions
                actions_path = expanded_dir / "actions.npy"
                if actions_path.exists():
                    actions = np.load(actions_path)
                    logger.info(f"Loaded {len(actions)} actions")
                else:
                    logger.warning(f"No actions.npy found in {expanded_dir}")
                    actions = np.array([])
                
                # Load rewards
                rewards_path = expanded_dir / "rewards.npy"
                if rewards_path.exists():
                    rewards = np.load(rewards_path)
                    logger.info(f"Loaded {len(rewards)} rewards")
                else:
                    logger.warning(f"No rewards.npy found in {expanded_dir}")
                    rewards = np.array([])
                
                self.bc_data = {
                    'observations': observations,
                    'actions': actions,
                    'rewards': rewards
                }
                return True
                
            else:
                logger.warning(f"Expanded live directory not found: {expanded_dir}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load BC data: {e}")
            return False
    
    def load_action_map(self) -> bool:
        """Load action map from CSV."""
        try:
            action_map_path = self.data_dir / "action_map.csv"
            if action_map_path.exists():
                action_map = {}
                with open(action_map_path) as f:
                    next(f)  # Skip header
                    for line in f:
                        tool_name, action_id = line.strip().split(',')
                        action_map[int(action_id)] = tool_name
                self.action_map = action_map
                logger.info(f"Loaded action map with {len(action_map)} actions")
                return True
            else:
                logger.warning(f"Action map not found: {action_map_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to load action map: {e}")
            return False
    
    def convert_to_ppo_format(self) -> bool:
        """Convert BC data to PPO training format."""
        if self.bc_data is None:
            logger.error("No BC data loaded")
            return False
        
        observations = self.bc_data['observations']
        actions = self.bc_data['actions']
        rewards = self.bc_data['rewards']
        
        if len(observations) == 0:
            logger.error("No observations to convert")
            return False
        
        # Ensure arrays have same length
        min_len = min(len(observations), len(actions), len(rewards))
        if min_len == 0:
            logger.error("No valid data to convert")
            return False
        
        observations = observations[:min_len]
        actions = actions[:min_len]
        rewards = rewards[:min_len]
        
        # Convert to PPO format
        self.ppo_training_data = []
        
        for i in range(min_len):
            # Create experience tuple for PPO
            state = observations[i]
            action = int(actions[i])
            reward = float(rewards[i])
            
            # For BC data, next_state is None (terminal state)
            experience = {
                'state': state,
                'action': action,
                'reward': reward,
                'next_state': None,
                'tool_name': self.action_map.get(action, f'action_{action}') if self.action_map else f'action_{action}'
            }
            
            self.ppo_training_data.append(experience)
        
        logger.info(f"Converted {len(self.ppo_training_data)} experiences to PPO format")
        return True
    
    def train_ppo_policy(self, num_epochs: int = 10) -> bool:
        """Train a PPO policy from BC data."""
        if len(self.ppo_training_data) == 0:
            logger.error("No PPO training data available")
            return False
        
        try:
            from broca.rl.ppo_policy import PPOPolicy, PPOConfig
            
            # Determine input/output dimensions
            sample_state = self.ppo_training_data[0]['state']
            input_dim = len(sample_state)
            
            # Determine output dimension from action map
            if self.action_map:
                output_dim = max(self.action_map.keys()) + 1
            else:
                # Estimate from data
                all_actions = [exp['action'] for exp in self.ppo_training_data]
                output_dim = max(all_actions) + 1
            
            logger.info(f"Training PPO policy: input_dim={input_dim}, output_dim={output_dim}")
            
            # Create PPO config and policy
            config = PPOConfig(
                input_dim=input_dim,
                output_dim=output_dim,
                learning_rate=3e-4,
                gamma=0.99,
                gae_lambda=0.95,
                clip_epsilon=0.2,
                entropy_coef=0.01,
                value_coef=0.5,
                max_grad_norm=0.5,
                batch_size=64,
                ppo_epochs=num_epochs
            )
            
            policy = PPOPolicy(config)
            
            # Train on BC data
            logger.info(f"Training PPO policy for {num_epochs} epochs...")
            
            for epoch in range(num_epochs):
                epoch_losses = []
                
                # Shuffle data
                np.random.shuffle(self.ppo_training_data)
                
                # Mini-batch training
                for i in range(0, len(self.ppo_training_data), config.batch_size):
                    batch = self.ppo_training_data[i:i + config.batch_size]
                    
                    # Extract batch data
                    states = np.array([exp['state'] for exp in batch])
                    actions = np.array([exp['action'] for exp in batch])
                    rewards = np.array([exp['reward'] for exp in batch])
                    
                    # Train step
                    loss = policy.train_step(states, actions, rewards)
                    epoch_losses.append(loss)
                
                avg_loss = np.mean(epoch_losses) if epoch_losses else 0.0
                logger.info(f"Epoch {epoch + 1}/{num_epochs}: avg_loss={avg_loss:.4f}")
            
            # Save the trained policy
            model_path = self.models_dir / "policy_ppo.pt"
            policy.save(str(model_path))
            logger.info(f"Saved PPO policy to {model_path}")
            
            # Also save a copy for immediate use
            immediate_path = self.models_dir / "policy_ppo_immediate.pt"
            policy.save(str(immediate_path))
            
            self.trained_policy = policy
            return True
            
        except Exception as e:
            logger.error(f"Failed to train PPO policy: {e}")
            return False
    
    def create_comparison_metrics(self) -> Dict[str, Any]:
        """Create comparison metrics between BC and PPO."""
        if self.bc_data is None or not hasattr(self, 'trained_policy'):
            return {}
        
        metrics = {
            'data_summary': {
                'bc_samples': len(self.bc_data['observations']),
                'ppo_experiences': len(self.ppo_training_data),
                'action_space_size': len(self.action_map) if self.action_map else 0,
                'input_dimension': len(self.bc_data['observations'][0]) if len(self.bc_data['observations']) > 0 else 0
            },
            'performance_metrics': {
                'bc_reward_mean': float(np.mean(self.bc_data['rewards'])) if len(self.bc_data['rewards']) > 0 else 0.0,
                'bc_reward_std': float(np.std(self.bc_data['rewards'])) if len(self.bc_data['rewards']) > 0 else 0.0,
                'ppo_initial_reward': 0.0,  # Will be updated after evaluation
            },
            'migration_status': 'completed'
        }
        
        # Save metrics
        metrics_path = self.models_dir / "migration_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Saved migration metrics to {metrics_path}")
        return metrics
    
    def run_migration(self, num_epochs: int = 10) -> bool:
        """Run complete migration pipeline."""
        logger.info("Starting BC to PPO migration...")
        
        steps = [
            ("Loading action map", self.load_action_map),
            ("Loading BC data", self.load_bc_data),
            ("Converting to PPO format", self.convert_to_ppo_format),
            (f"Training PPO policy ({num_epochs} epochs)", lambda: self.train_ppo_policy(num_epochs)),
            ("Creating comparison metrics", self.create_comparison_metrics)
        ]
        
        success = True
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            try:
                if not step_func():
                    logger.error(f"Step failed: {step_name}")
                    success = False
                    break
            except Exception as e:
                logger.error(f"Error in step '{step_name}': {e}")
                success = False
                break
        
        if success:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.error("❌ Migration failed")
        
        return success


def main():
    """Main migration function."""
    migrator = BCToPPOMigrator()
    
    # Run migration
    success = migrator.run_migration(num_epochs=5)
    
    if success:
        print("\n" + "="*60)
        print("MIGRATION SUCCESSFUL!")
        print("="*60)
        print("\nNext steps:")
        print("1. Update your code to use AdvancedPolicyRanker")
        print("2. Set algorithm='ppo' or algorithm='auto'")
        print("3. The system will automatically use the PPO model")
        print("\nFiles created:")
        print(f"  - {migrator.models_dir}/policy_ppo.pt (main PPO model)")
        print(f"  - {migrator.models_dir}/policy_ppo_immediate.pt (backup)")
        print(f"  - {migrator.models_dir}/migration_metrics.json")
        print("\nTo test the new PPO policy:")
        print("  from broca.rl.advanced_policy import AdvancedPolicyRanker")
        print("  ranker = AdvancedPolicyRanker(algorithm='ppo')")
        print("  ranker.load_model()")
        print("="*60)
    else:
        print("\n❌ Migration failed. Check logs for details.")
    
    return success


if __name__ == "__main__":
    main()
