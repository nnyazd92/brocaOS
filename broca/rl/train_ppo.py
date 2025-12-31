"""
Training script for PPO policy using logged transitions with RL-signal rewards.

This script:
1. Builds/loads a canonical transitions dataset (states, actions, rewards, next_states)
2. Trains a PPO model offline from that dataset
3. Saves the trained PPO model
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from broca.rl.ppo_policy import PPOPolicy, PPOConfig
from broca.rl.dataset_builder import build_dataset, write_outputs

logger = logging.getLogger(__name__)


def load_npz_dataset(path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    data = np.load(path)
    return (
        data["states"],
        data["actions"],
        data["rewards"],
        data["next_states"],
        data["dones"],
    )


def train_ppo_from_dataset(
    states: np.ndarray,
    actions: np.ndarray,
    rewards: np.ndarray,
    next_states: np.ndarray,
    dones: np.ndarray,
    epochs: int = 100,
    batch_size: int = 64,
    save_path: str = "models/rl/policy_ppo.pt",
):
    """Train PPO model from a transitions dataset."""
    if states.ndim != 2:
        raise ValueError(f"states must be 2D [N, D]; got shape {states.shape}")
    if len(states) == 0:
        raise ValueError("Empty dataset")

    output_dim = int(actions.max()) + 1 if len(actions) else 1

    # Create PPO config
    config = PPOConfig(
        input_dim=int(states.shape[1]),
        output_dim=output_dim,
        batch_size=batch_size,
        buffer_size=min(2048, int(len(states))),  # Train in chunks
    )
    
    # Initialize PPO policy
    policy = PPOPolicy(config)

    logger.info(
        f"Loaded dataset: N={len(states)} D={states.shape[1]} "
        f"n_actions={output_dim} reward_stats=[min={rewards.min():.3f}, max={rewards.max():.3f}, mean={rewards.mean():.3f}]"
    )

    # Training loop (offline replay)
    logger.info(f"Starting PPO training for {epochs} epochs (offline)")
    for epoch in range(epochs):
        indices = np.random.permutation(len(states))
        for idx in indices:
            s = states[idx]
            a = int(actions[idx])
            r = float(rewards[idx])
            done = bool(dones[idx] > 0.5)
            ns = None if done else next_states[idx]
            policy.store_experience(
                state=s,
                action=a,
                reward=r,
                next_state=ns,
                info={"done": done},
            )

        # Force a train step at end of epoch if enough data accumulated
        if len(policy.buffer) >= batch_size:
            policy.train()

        if (epoch + 1) % 10 == 0:
            metrics = policy.get_training_metrics()
            logger.info(
                f"Epoch {epoch + 1}/{epochs}: "
                f"training_step={metrics.get('training_step')} last_loss={metrics.get('last_loss')} "
                f"buffer_size={metrics.get('buffer_size')}"
            )
    
    # Save model
    save_dir = Path(save_path).parent
    save_dir.mkdir(parents=True, exist_ok=True)
    policy.save(save_path)
    
    logger.info(f"Saved PPO model to {save_path}")
    return policy


def main():
    parser = argparse.ArgumentParser(description="Train PPO model from BC data")
    parser.add_argument("--dataset_npz", type=str, default="data/rl/ppo_dataset.npz",
                       help="Path to PPO dataset .npz (built from experiences + rl_rewards)")
    parser.add_argument("--build_dataset", action="store_true",
                       help="Build dataset from logs before training (recommended)")
    parser.add_argument("--epochs", type=int, default=100,
                       help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=64,
                       help="Batch size for training")
    parser.add_argument("--save_path", type=str, default="models/rl/policy_ppo.pt",
                       help="Path to save trained PPO model")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        dataset_path = Path(args.dataset_npz)
        if args.build_dataset or not dataset_path.exists():
            root = Path(__file__).resolve().parents[2]
            ds = build_dataset(root)
            _, dataset_path = write_outputs(root, ds)

        states, actions, rewards, next_states, dones = load_npz_dataset(dataset_path)

        logger.info("Training PPO model...")
        train_ppo_from_dataset(
            states=states,
            actions=actions,
            rewards=rewards,
            next_states=next_states,
            dones=dones,
            epochs=args.epochs,
            batch_size=args.batch_size,
            save_path=args.save_path,
        )

        logger.info("Training complete!")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
