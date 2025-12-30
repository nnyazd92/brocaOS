#!/usr/bin/env python3
"""
Migration script to convert Behavior Cloning (BC) data to PPO format.
This script loads BC data, converts it to PPO-compatible format, and trains a PPO policy.
"""

import os
import sys
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional
import torch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broca.rl.ppo_policy import PPOPolicy, PPOConfig
from broca.rl.action_map import ActionMap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BCTOPPOMigrator:
    """Migrate BC data to PPO policy."""
    
    def __init__(self, data_dir: str = "data/rl"):
        self.data_dir = data_dir
        self.action_map = None
        self.bc_data = None
        self.ppo_training_data = []
        
    def load_action_map(self) -> bool:
        """Load action map."""
        try:
            action_map_path = os.path.join(self.data_dir, "action_map.json")
            if not os.path.exists(action_map_path):
                logger.error(f"Action map not found at {action_map_path}")
                return False
                
            with open(action_map_path, 'r') as f:
                action_map_data = json.load(f)
                
            self.action_map = ActionMap()
            self.action_map.load_from_dict(action_map_data)
            logger.info(f"Loaded action map with {len(self.action_map)} actions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load action map: {e}")
            return False
    
    def load_bc_data(self) -> bool:
        """Load BC data from expanded live data."""
        try:
            expanded_dir = os.path.join(self.data_dir, "expanded_live")
            if not os.path.exists(expanded_dir):
                logger.error(f"Expanded data directory not found: {expanded_dir}")
                return False
                
            # Load observations
            obs_path = os.path.join(expanded_dir, "observations.npy")
            if not os.path.exists(obs_path):
                logger.error(f"Observations file not found: {obs_path}")
                return False
                
            observations = np.load(obs_path, allow_pickle=True)
            
            # Load actions
            actions_path = os.path.join(expanded_dir, "actions.npy")
            if not os.path.exists(actions_path):
                logger.error(f"Actions file not found: {actions_path}")
                return False
                
            actions = np.load(actions_path, allow_pickle=True)
            
            # Load rewards
            rewards_path = os.path.join(expanded_dir, "rewards.npy")
            if not os.path.exists(rewards_path):
                logger.error(f"Rewards file not found: {rewards_path}")
                return False
                
            rewards = np.load(rewards_path, allow_pickle=True)
            
            self.bc_data = {
                'observations': observations,
                'actions': actions,
                'rewards': rewards
            }
            
            logger.info(f"Loaded {len(observations)} observations")
            logger.info(f"Loaded {len(actions)} actions")
            logger.info(f"Loaded {len(rewards)} rewards")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load BC data: {e}")
            return False
    
    def convert_to_ppo_format(self) -> bool:
        """Convert BC data to PPO training format."""
        if self.bc_data is None:
            logger.error("No BC data loaded")
            return False
            
        observations = self.bc_data['observations']
        actions = self.bc_data['actions']
        rewards = self.bc_data['rewards']
        
        # Check data consistency
        min_len = min(len(observations), len(actions), len(rewards))
        if min_len == 0:
            logger.error("No data to convert")
            return False
            
        logger.info(f"Converting {min_len} experiences to PPO format")
        
        # Convert to PPO format
        self.ppo_training_data = []
        
        for i in range(min_len):
            # Create experience tuple
            experience = {
                'state': observations[i],
                'action': int(actions[i]),
                'reward': float(rewards[i]),
                'next_state': observations[i + 1] if i + 1 < min_len else None,
                'done': i + 1 >= min_len  # Last experience marks episode end
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
            # Determine input/output dimensions
            sample_state = self.ppo_training_data[0]['state']
            input_dim = len(sample_state)
            
            # Determine output dimension from action map or data
            if self.action_map:
                output_dim = len(self.action_map)
            else:
                # Estimate from data
                all_actions = [exp['action'] for exp in self.ppo_training_data]
                output_dim = max(all_actions) + 1
            
            logger.info(f"Training PPO policy: input_dim={input_dim}, output_dim={output_dim}")
            
            # Create PPO config
            config = PPOConfig(
                buffer_size=len(self.ppo_training_data),
                batch_size=32,
                learning_rate=3e-4,
                gamma=0.99,
                gae_lambda=0.95,
                clip_epsilon=0.2,
                ppo_epochs=4,
                value_coef=0.5,
                entropy_coef=0.01
            )
            
            # Create PPO policy
            policy = PPOPolicy(config)
            logger.info("Initialized PPO policy")
            
            # Store all experiences in buffer
            logger.info(f"Storing {len(self.ppo_training_data)} experiences in buffer...")
            for exp in self.ppo_training_data:
                # For BC data, we don't have log_prob and value, so use defaults
                info = {
                    'log_prob': 0.0,  # Default value for BC data
                    'value': 0.0      # Default value for BC data
                }
                policy.store_experience(
                    state=exp['state'],
                    action=exp['action'],
                    reward=exp['reward'],
                    next_state=exp['next_state'],
                    info=info
                )
            
            # Train for multiple epochs
            logger.info(f"Training PPO policy for {num_epochs} epochs...")
            for epoch in range(num_epochs):
                # Train on current buffer
                policy._train()
                
                # Get training metrics
                metrics = policy.get_training_metrics()
                logger.info(f"Epoch {epoch + 1}/{num_epochs}: "
                          f"loss={metrics.get('loss', 0.0):.4f}, "
                          f"policy_loss={metrics.get('policy_loss', 0.0):.4f}, "
                          f"value_loss={metrics.get('value_loss', 0.0):.4f}")
            
            # Save the trained policy
            output_dir = os.path.join(self.data_dir, "ppo_policy")
            os.makedirs(output_dir, exist_ok=True)
            
            policy_path = os.path.join(output_dir, "bc_migrated_policy.pt")
            policy.save(policy_path)
            logger.info(f"Saved trained PPO policy to {policy_path}")
            
            # Save migration report
            self.save_migration_report(policy_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to train PPO policy: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_migration_report(self, policy_path: str):
        """Save migration report."""
        try:
            report = {
                'migration_summary': {
                    'bc_samples': len(self.bc_data['observations']) if self.bc_data else 0,
                    'ppo_experiences': len(self.ppo_training_data),
                    'action_space_size': len(self.action_map) if self.action_map else 0,
                    'input_dimension': len(self.bc_data['observations'][0]) if self.bc_data and len(self.bc_data['observations']) > 0 else 0,
                    'output_dimension': len(self.action_map) if self.action_map else 0
                },
                'data_quality': {
                    'observations_loaded': len(self.bc_data['observations']) if self.bc_data else 0,
                    'actions_loaded': len(self.bc_data['actions']) if self.bc_data else 0,
                    'rewards_loaded': len(self.bc_data['rewards']) if self.bc_data else 0,
                    'converted_experiences': len(self.ppo_training_data)
                },
                'policy_info': {
                    'path': policy_path,
                    'trained': True
                }
            }
            
            report_path = os.path.join(self.data_dir, "migration_report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Saved migration report to {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to save migration report: {e}")
    
    def run_migration(self, num_epochs: int = 10) -> bool:
        """Run complete migration pipeline."""
        logger.info("Starting BC to PPO migration...")
        
        steps = [
            ("Loading action map", self.load_action_map),
            ("Loading BC data", self.load_bc_data),
            ("Converting to PPO format", self.convert_to_ppo_format),
            (f"Training PPO policy ({num_epochs} epochs)", lambda: self.train_ppo_policy(num_epochs))
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Step failed: {step_name}")
                logger.error("❌ Migration failed")
                return False
        
        logger.info("✅ Migration completed successfully!")
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate BC data to PPO policy")
    parser.add_argument("--data-dir", default="data/rl", help="Data directory")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    
    args = parser.parse_args()
    
    migrator = BCTOPPOMigrator(args.data_dir)
    success = migrator.run_migration(args.epochs)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
