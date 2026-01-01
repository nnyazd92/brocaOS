"""
Proximal Policy Optimization (PPO) implementation for BrocaOS RL.

PPO is a state-of-the-art policy gradient method that:
1. Uses clipped objective to prevent large policy updates
2. Supports both discrete and continuous action spaces
3. Includes value function estimation for advantage calculation
4. Compatible with the existing Experience replay buffer

Based on: "Proximal Policy Optimization Algorithms" by Schulman et al. (2017)
"""

from __future__ import annotations

import logging
import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import torch.nn.functional as F
from dataclasses import asdict

if TYPE_CHECKING:
    from ..tools import Tool

logger = logging.getLogger(__name__)
try:
    from .tool_selection_logging import get_tool_selection_logger as _get_ts_logger
except Exception:  # pragma: no cover - defensive
    _get_ts_logger = None  # type: ignore


class PPONetwork(nn.Module):
    """Neural network for PPO with shared feature extractor."""
    
    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        
        # Policy head
        self.policy = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, output_dim),
        )
        
        # Value head
        self.value = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.orthogonal_(module.weight, gain=math.sqrt(2))
            nn.init.constant_(module.bias, 0)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning policy logits and value estimate."""
        features = self.shared(x)
        policy_logits = self.policy(features)
        value = self.value(features)
        return policy_logits, value.squeeze(-1)


@dataclass
class PPOConfig:
    """Configuration for PPO training."""
    # Network architecture
    input_dim: int = 16  # 6 RL signals + 10 context features
    hidden_dim: int = 128
    output_dim: int = 14  # Number of tools
    
    # Training parameters
    learning_rate: float = 3e-4
    gamma: float = 0.99  # Discount factor
    gae_lambda: float = 0.95  # GAE parameter
    clip_epsilon: float = 0.2  # PPO clip parameter
    value_coef: float = 0.5  # Value loss coefficient
    entropy_coef: float = 0.01  # Entropy bonus coefficient
    max_grad_norm: float = 0.5  # Gradient clipping
    
    # Training steps
    ppo_epochs: int = 4  # Number of PPO epochs per update
    batch_size: int = 64  # Mini-batch size
    buffer_size: int = 2048  # Experience buffer size
    
    # Device
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class PPOPolicy:
    """PPO-based policy for tool selection."""
    
    def __init__(self, config: Optional[PPOConfig] = None):
        self.config = config or PPOConfig()
        self.device = torch.device(self.config.device)
        
        # Initialize network and optimizer
        self.network = PPONetwork(
            input_dim=self.config.input_dim,
            output_dim=self.config.output_dim,
            hidden_dim=self.config.hidden_dim
        ).to(self.device)
        
        self.optimizer = optim.Adam(
            self.network.parameters(),
            lr=self.config.learning_rate
        )
        
        # Experience buffer
        self.buffer: List[Dict[str, Any]] = []
        self.buffer_lock = Lock()
        
        # Training state
        self.training_step = 0
        self.total_reward = 0.0
        self.episode_count = 0
        self._last_loss: Optional[float] = None
        
        logger.info(f"Initialized PPO policy on {self.device}")
        logger.info(f"Network: {self.config.input_dim} → {self.config.hidden_dim} → {self.config.output_dim}")
    
    def select_action(self, state: np.ndarray, explore: bool = True) -> Tuple[int, float, Dict[str, Any]]:
        """Select action using current policy."""
        self.network.eval()
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            policy_logits, value = self.network(state_tensor)

            dist = Categorical(logits=policy_logits)
            if explore:
                action = int(dist.sample().item())
            else:
                action = int(torch.argmax(policy_logits, dim=1).item())

            # Log-prob under the current policy for the chosen action (even if deterministic)
            action_t = torch.tensor(action, device=self.device)
            log_prob = float(dist.log_prob(action_t).item())

            # Get action probabilities for explainability
            probs = torch.softmax(policy_logits, dim=1).squeeze().cpu().numpy()

            return action, float(value.item()), {
                "log_prob": log_prob,
                "value": float(value.item()),
                "probs": probs,
                "entropy": float(dist.entropy().mean().item()),
            }

    def evaluate_actions(
        self,
        states: np.ndarray,
        actions: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Evaluate log-probabilities, entropies, and values for given state/action batch.

        This is used to ensure log_prob corresponds to the actual executed action.
        """
        self.network.eval()
        with torch.no_grad():
            states_t = torch.FloatTensor(states).to(self.device)
            actions_t = torch.LongTensor(actions).to(self.device)
            logits, values = self.network(states_t)
            dist = Categorical(logits=logits)
            log_probs = dist.log_prob(actions_t)
            entropies = dist.entropy()
        return (
            log_probs.detach().cpu().numpy(),
            entropies.detach().cpu().numpy(),
            values.detach().cpu().numpy(),
        )
    
    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: Optional[np.ndarray],
        info: Dict[str, Any]
    ):
        """Store experience in buffer."""
        should_train = False
        with self.buffer_lock:
            done = bool(info.get("done", next_state is None))
            # Ensure log_prob/value correspond to the *actual* stored action.
            # We recompute to avoid mismatches from callers that sample a different action
            # just to get `log_prob`/`value` (a common integration mistake).
            log_prob = None
            value = None
            try:
                lp, _, vals = self.evaluate_actions(
                    np.array([state], dtype=np.float32),
                    np.array([int(action)], dtype=np.int64),
                )
                log_prob = float(lp[0])
                value = float(vals[0])
            except Exception:
                # Best-effort fallback to caller-provided info
                try:
                    log_prob = float(info.get("log_prob")) if info.get("log_prob") is not None else None
                except Exception:
                    log_prob = None
                try:
                    value = float(info.get("value")) if info.get("value") is not None else None
                except Exception:
                    value = None

            self.buffer.append({
                "state": state.copy(),
                "action": action,
                "reward": reward,
                "next_state": next_state.copy() if next_state is not None else None,
                # IMPORTANT: log_prob/value must correspond to *this* action and this state.
                # If absent, we will recompute at training time.
                "log_prob": log_prob,
                "value": value,
                "done": done,
            })
            
            self.total_reward += reward
            if done:
                self.episode_count += 1
            
            # Check if buffer is full
            should_train = len(self.buffer) >= self.config.buffer_size

        # IMPORTANT: do not call _train() while holding buffer_lock (would deadlock).
        if should_train:
            self._train()

    def behavior_clone(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        *,
        value_targets: Optional[np.ndarray] = None,
        sample_weights: Optional[np.ndarray] = None,
        epochs: int = 1,
        batch_size: Optional[int] = None,
        value_coef: float = 0.5,
        entropy_coef: float = 0.0,
        max_grad_norm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Supervised warm-start for the policy (and optionally value head).

        This is intended to bootstrap early training using logged (state, executed_action)
        pairs (behavior cloning). When value_targets are provided, we also regress the
        value head towards those targets for a faster critic warm-up.
        """
        if states is None or actions is None:
            return {"bc_steps": 0, "n": 0}

        states = np.asarray(states, dtype=np.float32)
        actions = np.asarray(actions, dtype=np.int64)
        if states.ndim != 2 or actions.ndim != 1 or len(states) != len(actions):
            return {"bc_steps": 0, "n": 0}

        n = int(len(actions))
        if n <= 0:
            return {"bc_steps": 0, "n": 0}

        if value_targets is not None:
            value_targets = np.asarray(value_targets, dtype=np.float32)
            if value_targets.shape != (n,):
                value_targets = None

        if sample_weights is not None:
            sample_weights = np.asarray(sample_weights, dtype=np.float32)
            if sample_weights.shape != (n,):
                sample_weights = None

        self.network.train()

        bs = int(batch_size or self.config.batch_size)
        bs = max(1, min(bs, n))
        epochs = max(1, int(epochs))

        max_gn = float(max_grad_norm) if max_grad_norm is not None else float(self.config.max_grad_norm)

        bc_steps = 0
        total_loss = 0.0
        total_ce = 0.0
        total_v = 0.0
        total_ent = 0.0
        n_batches = 0

        idx = np.arange(n)
        for _ in range(epochs):
            np.random.shuffle(idx)
            for start in range(0, n, bs):
                batch_idx = idx[start : start + bs]
                s_t = torch.FloatTensor(states[batch_idx]).to(self.device)
                a_t = torch.LongTensor(actions[batch_idx]).to(self.device)

                logits, v_pred = self.network(s_t)
                dist = Categorical(logits=logits)

                # Cross-entropy on executed actions (policy imitation).
                ce_per = F.cross_entropy(logits, a_t, reduction="none")
                if sample_weights is not None:
                    w_t = torch.FloatTensor(sample_weights[batch_idx]).to(self.device)
                    ce = (ce_per * w_t).sum() / (w_t.sum() + 1e-8)
                else:
                    ce = ce_per.mean()

                v_loss = torch.tensor(0.0, device=self.device)
                if value_targets is not None:
                    vt = torch.FloatTensor(value_targets[batch_idx]).to(self.device)
                    v_loss = F.mse_loss(v_pred, vt)

                ent = dist.entropy().mean()

                loss = ce + float(value_coef) * v_loss - float(entropy_coef) * ent

                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.network.parameters(), max_gn)
                self.optimizer.step()

                bc_steps += 1
                n_batches += 1
                total_loss += float(loss.detach().cpu().item())
                total_ce += float(ce.detach().cpu().item())
                total_v += float(v_loss.detach().cpu().item())
                total_ent += float(ent.detach().cpu().item())

        # Keep this separate from PPO's on-policy training_step.
        prev = getattr(self, "bc_step", 0)
        try:
            self.bc_step = int(prev) + int(bc_steps)
        except Exception:
            self.bc_step = int(bc_steps)

        return {
            "bc_steps": int(bc_steps),
            "n": int(n),
            "epochs": int(epochs),
            "batch_size": int(bs),
            "loss": total_loss / max(1, n_batches),
            "ce_loss": total_ce / max(1, n_batches),
            "value_loss": total_v / max(1, n_batches),
            "entropy": total_ent / max(1, n_batches),
        }
    
    def _compute_advantages(
        self,
        rewards: np.ndarray,
        values: np.ndarray,
        next_values: np.ndarray,
        dones: np.ndarray,
    ) -> np.ndarray:
        """Compute advantages using Generalized Advantage Estimation (GAE)."""
        T = int(len(rewards))
        advantages = np.zeros(T, dtype=np.float32)
        gae: float = 0.0
        for t in reversed(range(T)):
            nonterminal = 1.0 - float(dones[t])
            delta = float(rewards[t]) + self.config.gamma * float(next_values[t]) * nonterminal - float(values[t])
            gae = delta + self.config.gamma * self.config.gae_lambda * nonterminal * gae
            advantages[t] = gae
        return advantages

    def train(self) -> Dict[str, Any]:
        """Public training API. Returns metrics; no-op if not enough data."""
        return self._train() or self.get_training_metrics()
    
    def _train(self):
        """Train PPO on collected experiences."""
        # Snapshot buffer up-front to avoid training while holding the lock.
        with self.buffer_lock:
            local_buffer = list(self.buffer)
        if len(local_buffer) == 0:
            return

        # `batch_size` is a mini-batch size, not a minimum-data threshold.
        # Training is triggered by `buffer_size` in store_experience(), so if we get here with
        # fewer samples than the configured mini-batch size, still train using a smaller batch.
        # This avoids misconfiguration like: buffer_size=32, batch_size=64 (would never train).
        effective_batch_size = int(min(int(self.config.batch_size), len(local_buffer)))

        ts_logger = None
        try:
            if _get_ts_logger is not None:
                ts_logger = _get_ts_logger()
        except Exception:
            ts_logger = None

        try:
            if ts_logger is not None:
                ts_logger.info(
                    "PPO_TRAIN_START | "
                    f"n_experiences={len(local_buffer)} | "
                    f"minibatch_size={effective_batch_size} | "
                    f"configured_batch_size={int(self.config.batch_size)} | "
                    f"ppo_epochs={int(self.config.ppo_epochs)} | "
                    f"clip_epsilon={float(self.config.clip_epsilon):.3f} | "
                    f"value_coef={float(self.config.value_coef):.3f} | "
                    f"entropy_coef={float(self.config.entropy_coef):.3f} | "
                    f"learning_rate={float(self.config.learning_rate):.6f}"
                )
        except Exception:
            pass
        
        self.network.train()
        logger.info(f"Training PPO with {len(local_buffer)} experiences")
        
        # Convert buffer to arrays
        states = np.array([exp["state"] for exp in local_buffer])
        actions = np.array([exp["action"] for exp in local_buffer])
        rewards = np.array([exp["reward"] for exp in local_buffer])
        dones = np.array([exp["done"] for exp in local_buffer])
        next_states = [exp.get("next_state") for exp in local_buffer]

        # Compute current values and next_values for GAE bootstrapping
        with torch.no_grad():
            states_t = torch.FloatTensor(states).to(self.device)
            _, values_t = self.network(states_t)
            values = values_t.detach().cpu().numpy()

            next_values = np.zeros(len(states), dtype=np.float32)
            if any(ns is not None for ns in next_states):
                ns_idx = [i for i, ns in enumerate(next_states) if ns is not None and not bool(dones[i])]
                if ns_idx:
                    ns_batch = np.stack([next_states[i] for i in ns_idx], axis=0)
                    ns_t = torch.FloatTensor(ns_batch).to(self.device)
                    _, nv_t = self.network(ns_t)
                    nv = nv_t.detach().cpu().numpy()
                    for j, i in enumerate(ns_idx):
                        next_values[i] = float(nv[j])

        # Ensure we have old_log_probs aligned with executed actions.
        # If missing (e.g., offline dataset), use current policy's log_probs as a stable baseline.
        old_log_probs_list: List[float] = []
        missing_lp = False
        for exp in local_buffer:
            lp = exp.get("log_prob", None)
            if lp is None:
                missing_lp = True
                break
            try:
                old_log_probs_list.append(float(lp))
            except Exception:
                missing_lp = True
                break

        if missing_lp:
            try:
                lp, _, _ = self.evaluate_actions(states, actions)
                old_log_probs = lp.astype(np.float32)
            except Exception:
                old_log_probs = np.zeros(len(states), dtype=np.float32)
        else:
            old_log_probs = np.array(old_log_probs_list, dtype=np.float32)
        
        # Compute advantages and returns
        advantages = self._compute_advantages(
            rewards=rewards.astype(np.float32),
            values=values.astype(np.float32),
            next_values=next_values.astype(np.float32),
            dones=dones.astype(np.float32),
        )
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        returns = advantages + values.astype(np.float32)
        
        # Convert to tensors
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        old_log_probs_t = torch.FloatTensor(old_log_probs.astype(np.float32)).to(self.device)
        advantages_t = torch.FloatTensor(advantages).to(self.device)
        returns_t = torch.FloatTensor(returns).to(self.device)

        total_loss = 0.0
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        # Health monitoring aggregates (weighted by batch size)
        total_kl = 0.0
        total_clip_fraction = 0.0
        total_weight = 0.0
        n_batches = 0
        
        # PPO training epochs
        for epoch in range(self.config.ppo_epochs):
            # Shuffle indices for mini-batch training
            indices = np.arange(len(local_buffer))
            np.random.shuffle(indices)
            
            for start in range(0, len(indices), effective_batch_size):
                end = start + effective_batch_size
                batch_indices = indices[start:end]
                
                # Get batch
                batch_states = states_t[batch_indices]
                batch_actions = actions_t[batch_indices]
                batch_old_log_probs = old_log_probs_t[batch_indices]
                batch_advantages = advantages_t[batch_indices]
                batch_returns = returns_t[batch_indices]
                
                # Forward pass
                policy_logits, values_pred = self.network(batch_states)
                dist = Categorical(logits=policy_logits)
                
                # Compute losses
                new_log_probs = dist.log_prob(batch_actions)
                entropy = dist.entropy().mean()

                # Health metrics
                with torch.no_grad():
                    # approx_kl ~ E[log pi_old(a|s) - log pi_new(a|s)]
                    kl = (batch_old_log_probs - new_log_probs).mean()
                    ratio = torch.exp(new_log_probs - batch_old_log_probs)
                    clip_frac = (torch.abs(ratio - 1.0) > self.config.clip_epsilon).float().mean()
                    w = float(len(batch_indices))
                    total_kl += float(kl.item()) * w
                    total_clip_fraction += float(clip_frac.item()) * w
                    total_weight += w
                
                # PPO clipped objective
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # Value loss
                value_loss = nn.functional.mse_loss(values_pred, batch_returns)
                
                # Total loss
                loss = policy_loss + self.config.value_coef * value_loss - self.config.entropy_coef * entropy
                
                # Optimize
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.network.parameters(), self.config.max_grad_norm)
                self.optimizer.step()

                total_loss += float(loss.item())
                total_policy_loss += float(policy_loss.item())
                total_value_loss += float(value_loss.item())
                total_entropy += float(entropy.item())
                n_batches += 1

        # Episode return estimate for monitoring.
        episode_returns: List[float] = []
        running = 0.0
        for exp in local_buffer:
            if not isinstance(exp, dict):
                continue
            try:
                running += float(exp.get("reward", 0.0) or 0.0)
            except Exception:
                pass
            if bool(exp.get("done", False)):
                episode_returns.append(running)
                running = 0.0
        if not episode_returns:
            # If the rollout doesn't include terminal transitions, treat it as one partial episode.
            try:
                episode_returns.append(float(sum(float(e.get("reward", 0.0) or 0.0) for e in local_buffer if isinstance(e, dict))))
            except Exception:
                episode_returns.append(0.0)
        
        with self.buffer_lock:
            # Remove the trained prefix, preserving any concurrently appended samples.
            n = len(local_buffer)
            if n <= 0:
                pass
            elif len(self.buffer) <= n:
                self.buffer.clear()
            else:
                del self.buffer[:n]
        
        self.training_step += 1
        self._last_loss = (total_loss / max(1, n_batches))
        
        logger.info(f"PPO training step {self.training_step} complete")
        logger.info(f"Average reward: {self.total_reward / max(1, self.episode_count):.4f}")

        # Append per-update metrics to CSV for monitoring.
        try:
            from .ppo_training_logger import get_ppo_training_logger

            approx_kl = (total_kl / total_weight) if total_weight > 0 else 0.0
            clip_fraction = (total_clip_fraction / total_weight) if total_weight > 0 else 0.0

            lr = None
            try:
                lr = float(self.optimizer.param_groups[0].get("lr"))
            except Exception:
                lr = None

            get_ppo_training_logger().log_update(
                {
                    "training_step": int(self.training_step),
                    "n_experiences": int(len(local_buffer)),
                    "n_episodes": int(len(episode_returns)),
                    "mean_episode_return": float(sum(episode_returns) / max(1, len(episode_returns))),
                    "approx_kl": float(approx_kl),
                    "clip_fraction": float(clip_fraction),
                    "policy_entropy": float(total_entropy / max(1, n_batches)),
                    "policy_loss": float(total_policy_loss / max(1, n_batches)),
                    "value_loss": float(total_value_loss / max(1, n_batches)),
                    "total_loss": float(total_loss / max(1, n_batches)),
                    "learning_rate": lr,
                    "clip_epsilon": float(self.config.clip_epsilon),
                    "entropy_coef": float(self.config.entropy_coef),
                    "value_coef": float(self.config.value_coef),
                    "ppo_epochs": int(self.config.ppo_epochs),
                    "configured_batch_size": int(self.config.batch_size),
                    "configured_buffer_size": int(self.config.buffer_size),
                    "minibatch_size": int(effective_batch_size),
                }
            )
        except Exception:
            pass

        try:
            if ts_logger is not None:
                ts_logger.info(
                    "PPO_TRAIN_END | "
                    f"training_step={int(self.training_step)} | "
                    f"loss={float(self._last_loss):.4f} | "
                    f"policy_loss={float(total_policy_loss / max(1, n_batches)):.4f} | "
                    f"value_loss={float(total_value_loss / max(1, n_batches)):.4f} | "
                    f"entropy={float(total_entropy / max(1, n_batches)):.4f} | "
                    f"n_batches={int(n_batches)}"
                )
        except Exception:
            pass

        return {
            "training_step": self.training_step,
            "batches": n_batches,
            "loss": total_loss / max(1, n_batches),
            "policy_loss": total_policy_loss / max(1, n_batches),
            "value_loss": total_value_loss / max(1, n_batches),
            "entropy": total_entropy / max(1, n_batches),
        }
    
    def predict_proba(self, state: np.ndarray) -> np.ndarray:
        """Get action probabilities for given state."""
        self.network.eval()
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            policy_logits, _ = self.network(state_tensor)
            probs = torch.softmax(policy_logits, dim=1).squeeze().cpu().numpy()
            return probs
    
    def save(self, path: str):
        """Save model to disk."""
        # Store config as a plain dict to avoid torch.load "weights_only" pickling issues.
        try:
            config_payload: Any = asdict(self.config)
        except Exception:
            config_payload = dict(getattr(self.config, "__dict__", {}) or {})
        torch.save({
            'network_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': config_payload,
            'training_step': self.training_step,
            'total_reward': self.total_reward,
            'episode_count': self.episode_count,
        }, path)
        logger.info(f"Saved PPO model to {path}")
    
    def load(self, path: str):
        """Load model from disk."""
        checkpoint = None
        # PyTorch 2.6+ defaults to weights_only=True; our payload is safe (dict + tensors),
        # but older checkpoints may contain a PPOConfig object. We support both.
        try:
            checkpoint = torch.load(path, map_location=self.device, weights_only=True)
        except TypeError:
            checkpoint = torch.load(path, map_location=self.device)
        except Exception:
            # Retry with safe globals for older checkpoints that stored PPOConfig instances.
            try:
                import torch.serialization
                torch.serialization.add_safe_globals([PPOConfig])
                checkpoint = torch.load(path, map_location=self.device, weights_only=True)
            except Exception:
                checkpoint = torch.load(path, map_location=self.device)

        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_step = checkpoint.get('training_step', 0)
        self.total_reward = checkpoint.get('total_reward', 0.0)
        self.episode_count = checkpoint.get('episode_count', 0)
        # IMPORTANT: Do NOT overwrite self.config from checkpoint.
        # Runtime configuration (e.g., env vars) must control batch_size/buffer_size and other
        # training hyperparameters across restarts. Loading the checkpoint's config can cause
        # silent no-training behavior (e.g., checkpoint batch_size=64, runtime buffer_size=32).
        logger.info(f"Loaded PPO model from {path}")
    
    def get_training_metrics(self) -> Dict[str, Any]:
        """Get current training metrics."""
        return {
            "training_step": self.training_step,
            "episode_count": self.episode_count,
            "average_reward": self.total_reward / max(1, self.episode_count),
            "buffer_size": len(self.buffer),
            "device": str(self.device),
            "last_loss": self._last_loss,
        }


# Integration with existing PolicyRanker
class PPOPolicyRanker:
    """Wrapper to integrate PPO with existing PolicyRanker interface."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.ppo_policy = PPOPolicy()
        
        if model_path and Path(model_path).exists():
            self.ppo_policy.load(model_path)
    
    def load_model(self, model_path: Optional[str] = None):
        """Load PPO model."""
        path = model_path or self.model_path
        if path and Path(path).exists():
            self.ppo_policy.load(path)
    
    def rank_tools(self, context: Dict[str, Any], tools: List[Any]) -> List[Dict[str, Any]]:
        """Rank tools using PPO policy."""
        # Extract features from context
        state = self._context_to_state(context)
        
        # Get action probabilities
        probs = self.ppo_policy.predict_proba(state)
        
        # Create rankings
        rankings = []
        for i, tool in enumerate(tools):
            tool_name = getattr(tool, 'name', str(tool))
            if i < len(probs):
                score = float(probs[i])
            else:
                score = 0.0  # Default for tools beyond action space
            
            rankings.append({
                "tool_name": tool_name,
                "score": score,
                "expected_reward": score,  # Use probability as expected reward proxy
            })
        
        rankings.sort(key=lambda r: r['score'], reverse=True)
        return rankings
    
    def predict_distribution(self, context: Dict[str, Any], tools: List[Any]) -> Dict[str, float]:
        """Get probability distribution over tools."""
        state = self._context_to_state(context)
        probs = self.ppo_policy.predict_proba(state)
        
        distribution = {}
        for i, tool in enumerate(tools):
            tool_name = getattr(tool, 'name', str(tool))
            if i < len(probs):
                distribution[tool_name] = float(probs[i])
            else:
                distribution[tool_name] = 0.0
        
        # Normalize
        total = sum(distribution.values())
        if total > 0:
            distribution = {k: v / total for k, v in distribution.items()}
        
        return distribution
    
    def _context_to_state(self, context: Dict[str, Any]) -> np.ndarray:
        """Convert context dictionary to feature vector."""
        from .features import extract_state_features

        return extract_state_features(context, input_dim=16)


if __name__ == "__main__":
    # Test the PPO implementation
    print("Testing PPO implementation...")
    
    # Create dummy config
    config = PPOConfig(input_dim=16, output_dim=14)
    policy = PPOPolicy(config)
    
    # Test action selection
    test_state = np.random.randn(16).astype(np.float32)
    action, value, info = policy.select_action(test_state)
    print(f"Selected action: {action}, Value: {value:.4f}")
    print(f"Action probabilities: {info['probs']}")
    
    # Test training
    for i in range(10):
        next_state = np.random.randn(17).astype(np.float32)
        reward = random.random()
        policy.store_experience(test_state, action, reward, next_state, info)
        test_state = next_state
    
    print("PPO implementation test complete!")
