"""
Online Neural Policy Ranker for BrocaOS.

Features:
- PyTorch neural network for tool selection with online learning
- Confidence estimation via MC Dropout ensemble
- Experience replay buffer with prioritized sampling
- RL-primary selection with LLM as failsafe (<30% confidence)

Confidence Thresholds:
- ≥85%: RL forces tool selection (LLM bypassed)
- 30-85%: RL suggests top-K tools (LLM picks from subset)
- <30%: LLM has full choice (failsafe mode)
"""

from __future__ import annotations

import atexit
import json
import logging
import math
import random
import time
import weakref
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np

from .features import RL_SIGNAL_KEYS, extract_state_features
from .reward import RewardWeights, compute_reward_from_outcome

# Registry of ranker instances for atexit cleanup
_ranker_instances: List[weakref.ref] = []


def _atexit_cleanup():
    """Cleanup handler called on interpreter shutdown."""
    for ref in _ranker_instances:
        ranker = ref()
        if ranker is not None:
            try:
                ranker.shutdown()
            except Exception:
                pass  # Ignore errors during shutdown


atexit.register(_atexit_cleanup)

if TYPE_CHECKING:
    from ..tools import Tool

logger = logging.getLogger(__name__)

# Dedicated logger for tool selection debug output (separate file)
tool_selection_logger = logging.getLogger("broca.rl.tool_selection")
_tool_selection_logging_initialized = False


def _setup_tool_selection_logging() -> None:
    """Configure dedicated file handler for tool selection logging."""
    global _tool_selection_logging_initialized
    if _tool_selection_logging_initialized:
        return
    
    try:
        log_path = Path("data/rl/tool_selection.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler for detailed debug output
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-5s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Prevent duplicate handlers
        if not tool_selection_logger.handlers:
            tool_selection_logger.addHandler(file_handler)
        tool_selection_logger.setLevel(logging.DEBUG)
        # Don't propagate to root logger (avoid duplicate console output)
        tool_selection_logger.propagate = False
        
        _tool_selection_logging_initialized = True
        tool_selection_logger.info("=" * 80)
        tool_selection_logger.info("TOOL SELECTION LOGGING INITIALIZED")
        tool_selection_logger.info("=" * 80)
    except Exception as e:
        logger.warning(f"Failed to setup tool selection logging: {e}")


# Initialize logging on module load
_setup_tool_selection_logging()


@dataclass
class Experience:
    """Single experience for replay buffer."""
    state: np.ndarray  # Feature vector from RL signals + context
    action: int  # Tool index
    reward: float  # 0.0-1.0 reward (success, execution time, etc.)
    next_state: Optional[np.ndarray] = None
    timestamp: float = field(default_factory=time.time)
    priority: float = 1.0  # For prioritized replay
    tool_name: str = ""  # Original tool name for debugging


class PrioritizedReplayBuffer:
    """Experience replay buffer with prioritized sampling."""

    def __init__(self, capacity: int = 10000, alpha: float = 0.6):
        """
        Args:
            capacity: Maximum buffer size
            alpha: Prioritization exponent (0 = uniform, 1 = full priority)
        """
        self.capacity = capacity
        self.alpha = alpha
        self.buffer: deque[Experience] = deque(maxlen=capacity)
        self._lock = Lock()

    def add(self, experience: Experience) -> None:
        """Add experience to buffer."""
        with self._lock:
            self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Experience]:
        """Sample batch with prioritized sampling."""
        with self._lock:
            if len(self.buffer) == 0:
                return []

            batch_size = min(batch_size, len(self.buffer))

            # Compute sampling probabilities
            priorities = np.array([e.priority ** self.alpha for e in self.buffer])
            probs = priorities / (priorities.sum() + 1e-10)

            indices = np.random.choice(
                len(self.buffer), size=batch_size, replace=False, p=probs
            )
            return [self.buffer[i] for i in indices]

    def update_priorities(self, indices: List[int], priorities: List[float]) -> None:
        """Update priorities for experiences."""
        with self._lock:
            for idx, priority in zip(indices, priorities):
                if 0 <= idx < len(self.buffer):
                    self.buffer[idx].priority = priority + 1e-6  # Avoid zero priority

    def __len__(self) -> int:
        return len(self.buffer)

    def save(self, path: Path) -> None:
        """Save buffer to disk."""
        with self._lock:
            data = [
                {
                    'state': e.state.tolist(),
                    'action': e.action,
                    'reward': e.reward,
                    'next_state': e.next_state.tolist() if e.next_state is not None else None,
                    'timestamp': e.timestamp,
                    'priority': e.priority,
                    'tool_name': e.tool_name,
                }
                for e in self.buffer
            ]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f)
        logger.debug(f"Saved replay buffer ({len(data)} experiences) to {path}")

    def load(self, path: Path) -> None:
        """Load buffer from disk."""
        if not path.exists():
            return
        try:
            with open(path) as f:
                data = json.load(f)
            with self._lock:
                self.buffer.clear()
                for item in data[-self.capacity:]:
                    self.buffer.append(Experience(
                        state=np.array(item['state'], dtype=np.float32),
                        action=item['action'],
                        reward=item['reward'],
                        next_state=np.array(item['next_state'], dtype=np.float32) if item.get('next_state') else None,
                        timestamp=item.get('timestamp', time.time()),
                        priority=item.get('priority', 1.0),
                        tool_name=item.get('tool_name', ''),
                    ))
            logger.info(f"Loaded replay buffer ({len(self.buffer)} experiences) from {path}")
        except Exception as e:
            logger.warning(f"Failed to load replay buffer from {path}: {e}")


class PyTorchPolicyNetwork:
    """
    PyTorch MLP policy network with MC Dropout for uncertainty estimation.
    
    Architecture:
    - Input: RL signals + context features
    - Hidden: 2 layers with ReLU + Dropout
    - Output: Action logits (softmax for probabilities)
    """

    def __init__(
        self,
        input_dim: int,
        n_actions: int,
        hidden_dims: Tuple[int, ...] = (128, 64),
        learning_rate: float = 0.001,
        dropout_rate: float = 0.3,
        weight_decay: float = 1e-4,
    ):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.dropout_rate = dropout_rate
        self.weight_decay = weight_decay

        self._model = None
        self._optimizer = None
        self._criterion = None
        self._is_fitted = False
        self._n_samples_seen = 0
        self._device = None
        self._training_lock = Lock()

        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize PyTorch model."""
        try:
            import torch
            import torch.nn as nn

            # Determine device
            self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"PyTorch using device: {self._device}")

            # Build network
            layers = []
            prev_dim = self.input_dim

            for hidden_dim in self.hidden_dims:
                layers.extend([
                    nn.Linear(prev_dim, hidden_dim),
                    nn.BatchNorm1d(hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(self.dropout_rate),
                ])
                prev_dim = hidden_dim

            layers.append(nn.Linear(prev_dim, self.n_actions))

            self._model = nn.Sequential(*layers).to(self._device)
            self._optimizer = torch.optim.AdamW(
                self._model.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay,
            )
            self._criterion = nn.CrossEntropyLoss(reduction='none')

            logger.debug(
                f"Initialized PyTorch policy network: "
                f"input_dim={self.input_dim}, n_actions={self.n_actions}, "
                f"hidden_dims={self.hidden_dims}"
            )

        except ImportError as e:
            logger.error(f"PyTorch not available: {e}")
            raise RuntimeError("PyTorch is required for OnlinePolicyRanker") from e

    def predict_proba(
        self, X: np.ndarray, n_mc_samples: int = 20
    ) -> Tuple[np.ndarray, float]:
        """
        Predict action probabilities with MC Dropout uncertainty estimation.

        Args:
            X: Input feature matrix (batch_size, input_dim) or (input_dim,)
            n_mc_samples: Number of MC dropout forward passes

        Returns:
            Tuple of (probabilities, confidence)
            - probabilities: (batch_size, n_actions) or (n_actions,)
            - confidence: scalar confidence score (0.0-1.0)
        """
        import torch
        import torch.nn.functional as F

        # Handle 1D input
        squeeze_output = False
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
            squeeze_output = True

        if not self._is_fitted or self._n_samples_seen < 10:
            # Return uniform distribution if not fitted
            uniform = np.ones((X.shape[0], self.n_actions)) / self.n_actions
            tool_selection_logger.debug(
                f"NN_PREDICT | UNTRAINED | n_samples_seen={self._n_samples_seen} | "
                f"is_fitted={self._is_fitted} | returning_uniform=True | n_actions={self.n_actions}"
            )
            if squeeze_output:
                uniform = uniform.squeeze(0)
            return uniform, 0.0  # Zero confidence when untrained

        X_tensor = torch.FloatTensor(X).to(self._device)
        
        # Log input tensor stats
        input_mean = float(X_tensor.mean())
        input_std = float(X_tensor.std())
        input_min = float(X_tensor.min())
        input_max = float(X_tensor.max())

        # Thread safety: acquire lock to prevent race conditions with training
        with self._training_lock:
            # MC Dropout: multiple forward passes with dropout enabled
            # Set model to eval mode first (BatchNorm uses running stats)
            self._model.eval()
            
            # Enable dropout layers specifically for MC Dropout
            for module in self._model.modules():
                if isinstance(module, torch.nn.Dropout):
                    module.train()
            
            predictions = []

            with torch.no_grad():
                for _ in range(n_mc_samples):
                    logits = self._model(X_tensor)
                    proba = F.softmax(logits, dim=-1)
                    predictions.append(proba.cpu().numpy())

        predictions = np.array(predictions)  # (n_mc_samples, batch, n_actions)

        # Mean prediction
        mean_proba = predictions.mean(axis=0)
        
        # Log MC dropout sample statistics
        predictions_std = predictions.std(axis=0)
        tool_selection_logger.debug(
            f"NN_PREDICT | input_shape={X_tensor.shape} | "
            f"input_stats=[mean={input_mean:.4f}, std={input_std:.4f}, min={input_min:.4f}, max={input_max:.4f}] | "
            f"mc_samples={n_mc_samples} | n_actions={self.n_actions} | "
            f"mean_proba={[f'{p:.4f}' for p in mean_proba.flatten()[:10]]}{'...' if len(mean_proba.flatten()) > 10 else ''} | "
            f"std_across_samples={[f'{s:.4f}' for s in predictions_std.flatten()[:10]]}{'...' if len(predictions_std.flatten()) > 10 else ''}"
        )

        # Confidence from prediction variance (lower variance = higher confidence)
        # Use predictive entropy as uncertainty measure
        entropy = -np.sum(mean_proba * np.log(mean_proba + 1e-10), axis=-1)
        max_entropy = np.log(self.n_actions) if self.n_actions > 1 else 1.0
        entropy_confidence = 1.0 - (entropy.mean() / max_entropy) if max_entropy > 0 else 0.0

        # Also consider variance across MC samples
        variance = predictions.var(axis=0).mean()
        max_variance = 0.25  # Theoretical max for uniform distribution
        variance_confidence = 1.0 - min(1.0, variance / max_variance)

        # Combined confidence (entropy + variance)
        raw_confidence = 0.6 * entropy_confidence + 0.4 * variance_confidence

        # Scale by number of samples seen (warm-up period)
        sample_factor = min(1.0, self._n_samples_seen / 50)
        confidence = raw_confidence * sample_factor
        
        # Log confidence computation details
        tool_selection_logger.debug(
            f"CONFIDENCE | entropy={float(entropy.mean()):.4f} | max_entropy={max_entropy:.4f} | "
            f"entropy_confidence={entropy_confidence:.4f} | "
            f"variance={variance:.6f} | max_variance={max_variance:.4f} | "
            f"variance_confidence={variance_confidence:.4f} | "
            f"raw_confidence={raw_confidence:.4f} | sample_factor={sample_factor:.4f} | "
            f"n_samples_seen={self._n_samples_seen} | final_confidence={confidence:.4f}"
        )

        if squeeze_output:
            mean_proba = mean_proba.squeeze(0)

        return mean_proba, float(max(0.0, min(1.0, confidence)))

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> float:
        """
        Incrementally train on new data.

        Args:
            X: Feature matrix (batch_size, input_dim)
            y: Action indices (batch_size,)
            sample_weight: Optional weights (batch_size,)

        Returns:
            Training loss
        """
        import torch

        # Thread safety: acquire lock before modifying model state
        with self._training_lock:
            self._model.train()

            X_tensor = torch.FloatTensor(X).to(self._device)
            y_tensor = torch.LongTensor(y).to(self._device)

            # Handle batch normalization for single samples
            if X_tensor.shape[0] == 1:
                # Skip batch norm for single samples - just forward pass without updating
                self._model.eval()
                with torch.no_grad():
                    logits = self._model(X_tensor)
                self._model.train()
                self._n_samples_seen += 1
                self._is_fitted = True
                return 0.0

            self._optimizer.zero_grad()

            logits = self._model(X_tensor)
            loss = self._criterion(logits, y_tensor)

            if sample_weight is not None:
                weight_tensor = torch.FloatTensor(sample_weight).to(self._device)
                loss = (loss * weight_tensor).mean()
            else:
                loss = loss.mean()

            loss.backward()

            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(self._model.parameters(), max_norm=1.0)

            self._optimizer.step()

            self._n_samples_seen += len(y)
            self._is_fitted = True

            return float(loss.item())

    def save(self, path: Path) -> None:
        """Save model to disk."""
        import torch

        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state': self._model.state_dict(),
            'optimizer_state': self._optimizer.state_dict(),
            'n_samples_seen': self._n_samples_seen,
            'is_fitted': self._is_fitted,
            'input_dim': self.input_dim,
            'n_actions': self.n_actions,
            'hidden_dims': self.hidden_dims,
        }, path)
        logger.debug(f"Saved PyTorch policy model to {path}")

    def load(self, path: Path) -> bool:
        """Load model from disk. Returns True if successful."""
        if not path.exists():
            return False

        try:
            import torch

            checkpoint = torch.load(path, map_location=self._device, weights_only=False)

            # Verify architecture matches
            if (checkpoint.get('input_dim') != self.input_dim or
                checkpoint.get('n_actions') != self.n_actions):
                logger.warning(
                    f"Model architecture mismatch: "
                    f"saved (in={checkpoint.get('input_dim')}, out={checkpoint.get('n_actions')}) "
                    f"vs current (in={self.input_dim}, out={self.n_actions})"
                )
                return False

            self._model.load_state_dict(checkpoint['model_state'])
            self._optimizer.load_state_dict(checkpoint['optimizer_state'])
            self._n_samples_seen = checkpoint.get('n_samples_seen', 0)
            self._is_fitted = checkpoint.get('is_fitted', False)

            logger.info(
                f"Loaded PyTorch policy model from {path} "
                f"(samples_seen={self._n_samples_seen}, is_fitted={self._is_fitted})"
            )
            return True

        except Exception as e:
            logger.warning(f"Failed to load model from {path}: {e}")
            return False


@dataclass
class ToolSelection:
    """Result of RL tool selection."""
    tool_name: str
    score: float
    confidence: float
    mode: str  # "forced", "suggested", "fallback"
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    reason: str = ""
    all_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'tool_name': self.tool_name,
            'score': self.score,
            'confidence': self.confidence,
            'mode': self.mode,
            'alternatives': self.alternatives,
            'reason': self.reason,
        }


class OnlinePolicyRanker:
    """
    Online RL policy ranker with PyTorch neural network backbone.

    Features:
    - PyTorch MLP for tool selection with MC Dropout uncertainty
    - Online learning with prioritized experience replay
    - Confidence-gated tool forcing:
        - ≥85% confidence: RL forces tool (LLM bypassed)
        - 30-85% confidence: LLM picks from RL's top-K
        - <30% confidence: LLM has full choice (failsafe)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        buffer_path: Optional[str] = None,
        force_threshold: float = 0.85,
        suggest_threshold: float = 0.30,  # Below this = LLM full choice
        top_k_suggest: int = 3,
        replay_buffer_size: int = 10000,
        batch_size: int = 32,
        update_frequency: int = 1,  # Update every N experiences
        learning_rate: float = 0.001,
        hidden_dims: Tuple[int, ...] = (128, 64),
        dropout_rate: float = 0.3,
        mc_samples: int = 20,
    ):
        """
        Args:
            model_path: Path to save/load model
            buffer_path: Path to save/load replay buffer
            force_threshold: Confidence threshold for forcing RL choice (≥85%)
            suggest_threshold: Confidence threshold below which LLM has full choice (<30%)
            top_k_suggest: Number of tools to suggest when in suggest mode
            replay_buffer_size: Size of experience replay buffer
            batch_size: Batch size for training updates
            update_frequency: How often to update model (every N experiences)
            learning_rate: Learning rate for online updates
            hidden_dims: Hidden layer dimensions for MLP
            dropout_rate: Dropout rate for MC Dropout
            mc_samples: Number of MC samples for uncertainty estimation
        """
        self.model_path = Path(model_path or "models/rl/online_policy.pt")
        self.buffer_path = Path(buffer_path or "data/rl/replay_buffer.json")
        self.force_threshold = force_threshold
        self.suggest_threshold = suggest_threshold
        self.top_k_suggest = top_k_suggest
        self.batch_size = batch_size
        self.update_frequency = update_frequency
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate
        self.mc_samples = mc_samples
        self.learning_rate = learning_rate

        # Action mapping: tool_name <-> action_index
        self._tool_to_idx: Dict[str, int] = {}
        self._idx_to_tool: Dict[int, str] = {}
        self._n_actions = 0

        # Neural network (initialized lazily when tools are known)
        self._network: Optional[PyTorchPolicyNetwork] = None
        self._input_dim = len(RL_SIGNAL_KEYS) + 10  # RL signals + context features

        # Experience replay
        self.replay_buffer = PrioritizedReplayBuffer(capacity=replay_buffer_size)

        # Counters
        self._experiences_since_update = 0
        self._total_experiences = 0
        self._lock = Lock()

        # Track last selection for outcome recording
        self._last_selection: Optional[ToolSelection] = None
        self._last_context: Optional[Dict[str, Any]] = None

        # Load existing buffer
        self.replay_buffer.load(self.buffer_path)

        # Register for atexit cleanup
        _ranker_instances.append(weakref.ref(self))

        logger.info(
            f"Initialized OnlinePolicyRanker: "
            f"force_threshold={force_threshold:.0%}, "
            f"suggest_threshold={suggest_threshold:.0%}, "
            f"top_k={top_k_suggest}, "
            f"hidden_dims={hidden_dims}"
        )

    def _ensure_network(self, tools: List[Any]) -> None:
        """Initialize or update network when tool set changes."""
        # Build tool mapping (sorted for consistency)
        tool_names = sorted([t.name for t in tools])
        new_mapping = {name: i for i, name in enumerate(tool_names)}

        if new_mapping != self._tool_to_idx or self._network is None:
            old_n_actions = self._n_actions
            self._tool_to_idx = new_mapping
            self._idx_to_tool = {v: k for k, v in new_mapping.items()}
            self._n_actions = len(new_mapping)

            # Reinitialize network if action space changed
            if self._network is None or self._n_actions != old_n_actions:
                self._network = PyTorchPolicyNetwork(
                    input_dim=self._input_dim,
                    n_actions=self._n_actions,
                    hidden_dims=self.hidden_dims,
                    learning_rate=self.learning_rate,
                    dropout_rate=self.dropout_rate,
                )

                # Try to load existing model
                if not self._network.load(self.model_path):
                    logger.info(
                        f"No existing model found at {self.model_path}, "
                        f"starting fresh with {self._n_actions} actions"
                    )

    def _extract_features(self, context: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector from context."""
        feature_array = extract_state_features(context, input_dim=self._input_dim)
        
        # Log feature extraction details
        rl_signals = (context.get("rl_signals", {}) or {}) if isinstance(context, dict) else {}
        active_goals = context.get("active_goals", []) if isinstance(context, dict) else []
        goal_types = []
        try:
            goal_types = [g.get("goal_type", "") for g in (active_goals or []) if isinstance(g, dict)]
        except Exception:
            goal_types = []
        skills = context.get("applicable_skills", []) if isinstance(context, dict) else []
        wm_items = context.get("working_memory_items", []) if isinstance(context, dict) else []
        recent_tools = context.get("recent_tools", []) if isinstance(context, dict) else []
        rules = context.get("production_rules", []) if isinstance(context, dict) else []
        try:
            active_rules = sum(1 for r in (rules or []) if isinstance(r, dict) and r.get("active", False))
        except Exception:
            active_rules = 0

        tool_selection_logger.debug(
            f"FEATURES | rl_signals={rl_signals} | "
            f"active_goals={len(active_goals)} | goal_types={goal_types[:3]} | "
            f"applicable_skills={len(skills)} | "
            f"working_memory_items={len(wm_items)} | "
            f"recent_tools={recent_tools[:5] if recent_tools else []} | "
            f"production_rules={len(rules)} (active={active_rules}) | "
            f"feature_vector={[f'{v:.3f}' for v in feature_array[:17]]}"
        )
        
        return feature_array

    def select_tool(
        self,
        tools: List[Any],
        context: Dict[str, Any],
    ) -> ToolSelection:
        """
        Select tool with confidence-gated forcing.

        Args:
            tools: List of available Tool objects
            context: Context dict with rl_signals, active_goals, etc.

        Returns:
            ToolSelection with mode indicating how to proceed:
            - "forced": RL forces this tool (LLM should not choose)
            - "suggested": RL suggests top-K (LLM picks from subset)
            - "fallback": RL uncertain (LLM has full choice)
        """
        tool_names_available = [t.name for t in tools]
        tool_selection_logger.debug(
            f"SELECT_START | tools_available={tool_names_available} | "
            f"n_tools={len(tools)} | context_keys={list(context.keys())}"
        )
        
        if not tools:
            tool_selection_logger.info(
                "SELECT_RESULT | mode=fallback | reason=no_tools_available"
            )
            return ToolSelection(
                tool_name="",
                score=0.0,
                confidence=0.0,
                mode="fallback",
                reason="No tools available"
            )

        self._ensure_network(tools)

        # Extract features
        features = self._extract_features(context)

        # Get predictions with confidence
        proba, confidence = self._network.predict_proba(features, n_mc_samples=self.mc_samples)
        proba = proba.flatten()

        # Rank tools by probability
        ranked_indices = np.argsort(proba)[::-1]  # Descending
        ranked_tools: List[Tuple[str, float]] = []
        all_scores: Dict[str, float] = {}

        for idx in ranked_indices:
            if idx in self._idx_to_tool:
                tool_name = self._idx_to_tool[idx]
                # Verify tool exists in current tools list
                if any(t.name == tool_name for t in tools):
                    score = float(proba[idx])
                    ranked_tools.append((tool_name, score))
                    all_scores[tool_name] = score

        # Log full ranking
        tool_selection_logger.debug(
            f"RANKING | n_tools={len(ranked_tools)} | "
            f"all_scores={[(t, f'{s:.4f}') for t, s in ranked_tools]} | "
            f"idx_to_tool_mapping={self._idx_to_tool}"
        )

        if not ranked_tools:
            tool_selection_logger.info(
                "SELECT_RESULT | mode=fallback | reason=no_valid_tools_in_ranking"
            )
            return ToolSelection(
                tool_name="",
                score=0.0,
                confidence=0.0,
                mode="fallback",
                reason="No valid tools in ranking"
            )

        top_tool, top_score = ranked_tools[0]
        alternatives = ranked_tools[1:self.top_k_suggest + 1]

        # Determine mode based on confidence
        if confidence >= self.force_threshold:
            mode = "forced"
            reason = f"High confidence ({confidence:.1%}) - RL forces selection"
        elif confidence >= self.suggest_threshold:
            mode = "suggested"
            reason = f"Medium confidence ({confidence:.1%}) - RL suggests top-{self.top_k_suggest}"
        else:
            mode = "fallback"
            reason = f"Low confidence ({confidence:.1%}) - LLM has full choice (failsafe)"

        selection = ToolSelection(
            tool_name=top_tool,
            score=top_score,
            confidence=confidence,
            mode=mode,
            alternatives=alternatives,
            reason=reason,
            all_scores=all_scores,
        )

        # Store for outcome recording
        self._last_selection = selection
        self._last_context = context.copy()

        # Log the selection decision
        tool_selection_logger.info(
            f"SELECTION | mode={mode} | confidence={confidence:.2%} | "
            f"tool={top_tool} | score={top_score:.4f} | "
            f"alternatives={[(t, f'{s:.4f}') for t, s in alternatives]} | "
            f"thresholds=[force>={self.force_threshold:.0%}, suggest>={self.suggest_threshold:.0%}] | "
            f"reason={reason}"
        )

        logger.info(
            f"RL selection: tool={top_tool}, score={top_score:.3f}, "
            f"confidence={confidence:.1%}, mode={mode}",
            extra={
                "event": "rl_tool_selection",
                "tool": top_tool,
                "score": top_score,
                "confidence": confidence,
                "mode": mode,
                "alternatives": [t for t, _ in alternatives],
                "top_5_scores": {t: s for t, s in ranked_tools[:5]},
            }
        )

        return selection

    def record_outcome(
        self,
        tool_name: str,
        context: Optional[Dict[str, Any]] = None,
        next_context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        execution_time_ms: float = 0.0,
        result_quality: float = 0.5,
        reward: Optional[float] = None,
        rl_signals: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record tool execution outcome for online learning.

        Args:
            tool_name: Tool that was executed
            context: Context when tool was selected (uses last_context if None)
            next_context: Optional context after the tool completed (for building transitions)
            success: Whether execution succeeded
            execution_time_ms: Execution time in milliseconds
            result_quality: Quality score of result (0.0-1.0)
            reward: Optional authoritative reward override (0.0-1.0). If not provided,
                    falls back to internal heuristic reward computation.
            rl_signals: Optional RL signals dict for debug logging / provenance
        """
        tool_selection_logger.debug(
            f"OUTCOME_START | tool={tool_name} | success={success} | "
            f"execution_time_ms={execution_time_ms:.1f} | result_quality={result_quality:.3f}"
        )
        
        if tool_name not in self._tool_to_idx:
            tool_selection_logger.debug(
                f"OUTCOME_SKIP | tool={tool_name} | reason=unknown_tool | "
                f"known_tools={list(self._tool_to_idx.keys())}"
            )
            logger.debug(f"Unknown tool '{tool_name}' in outcome recording, skipping")
            return

        # Use provided context or fall back to last selection context
        ctx = context if context is not None else self._last_context
        if ctx is None:
            ctx = {}

        # Compute reward:
        # - intrinsic: selected cognitive RL signals (reward-space) if present
        # - extrinsic: tool success/failure (+quality bonus)
        # - latency penalty: subtract (NOT a feature)
        if reward is not None:
            # Explicit override still wins (escape hatch).
            try:
                reward_value = float(reward)
            except Exception:
                reward_value = 0.0
            reward_value = max(0.0, min(1.0, reward_value))
            reward_source = "explicit_override"
        else:
            from broca.config import config as _config

            # Prefer provided rl_signals; else use post-action next_context.rl_signals if available.
            post_rl_signals = rl_signals if isinstance(rl_signals, dict) else None
            if post_rl_signals is None and isinstance(next_context, dict):
                maybe = next_context.get("rl_signals")
                if isinstance(maybe, dict):
                    post_rl_signals = maybe

            shaped, parts = compute_reward_from_outcome(
                rl_signals=post_rl_signals,
                intrinsic_keys=RL_SIGNAL_KEYS,
                success=bool(success),
                execution_time_ms=float(execution_time_ms or 0.0),
                result_quality=float(result_quality if result_quality is not None else 0.5),
                reward_success=_config.rl.reward_success,
                reward_failure=_config.rl.reward_failure,
                time_penalty_factor=_config.rl.time_penalty_factor,
                max_latency_penalty=_config.rl.max_latency_penalty,
                quality_bonus_factor=_config.rl.quality_bonus_factor,
                weights=RewardWeights(
                    extrinsic_weight=_config.rl.extrinsic_reward_weight,
                    intrinsic_weight=_config.rl.intrinsic_reward_weight,
                ),
            )
            reward_value = float(shaped)
            reward_source = f"shaped:{parts}"

        # Create experience
        state = self._extract_features(ctx)
        action = self._tool_to_idx[tool_name]
        next_state = None
        if next_context is not None:
            try:
                next_state = self._extract_features(next_context)
            except Exception:
                next_state = None

        # Priority: higher for unexpected outcomes (for prioritized replay)
        expected_reward = 0.5 if self._last_selection is None else self._last_selection.score
        td_error = abs(reward_value - expected_reward)
        priority = td_error + 0.1  # Base priority

        experience = Experience(
            state=state,
            action=action,
            reward=reward_value,
            next_state=next_state,
            priority=priority,
            tool_name=tool_name,
        )

        # Add to replay buffer
        self.replay_buffer.add(experience)
        self._experiences_since_update += 1
        self._total_experiences += 1
        
        # Log outcome recording
        tool_selection_logger.info(
            f"OUTCOME | tool={tool_name} | action_idx={action} | "
            f"reward={reward_value:.3f} | reward_source={reward_source} | expected_reward={expected_reward:.3f} | "
            f"td_error={td_error:.3f} | priority={priority:.3f} | "
            f"buffer_size={len(self.replay_buffer)} | "
            f"total_experiences={self._total_experiences} | "
            f"experiences_since_update={self._experiences_since_update}"
        )
        if rl_signals:
            try:
                tool_selection_logger.debug(f"OUTCOME_RL_SIGNALS | tool={tool_name} | rl_signals={rl_signals}")
            except Exception:
                pass

        # Online update
        if self._experiences_since_update >= self.update_frequency:
            self._online_update()
            self._experiences_since_update = 0

        logger.debug(
            f"Recorded outcome: tool={tool_name}, success={success}, "
            f"reward={reward_value:.3f}, priority={priority:.3f}",
            extra={
                "event": "rl_outcome_recorded",
                "tool": tool_name,
                "success": success,
                "reward": reward_value,
                "execution_time_ms": execution_time_ms,
                "result_quality": result_quality,
                "total_experiences": self._total_experiences,
            }
        )

        # Save buffer after each outcome to ensure persistence across session restarts
        # Only save buffer (not model) for efficiency - model saved during updates
        try:
            self.replay_buffer.save(self.buffer_path)
        except Exception as e:
            logger.debug(f"Failed to save replay buffer after outcome: {e}")

    def _compute_reward(
        self,
        success: bool,
        execution_time_ms: float,
        result_quality: float,
    ) -> float:
        """Compute reward from outcome metrics."""
        # Base reward from success (0.2 for failure, 0.8 for success)
        base_reward = 0.8 if success else 0.2

        # Time penalty (slower = lower reward, max 0.2 penalty for >10s)
        time_penalty = min(execution_time_ms / 50000, 0.2)

        # Quality bonus (0.0-0.2 based on result quality)
        quality_bonus = result_quality * 0.2

        reward = base_reward - time_penalty + quality_bonus
        final_reward = max(0.0, min(1.0, reward))
        
        # Log reward computation details
        tool_selection_logger.debug(
            f"REWARD | success={success} | execution_time_ms={execution_time_ms:.1f} | "
            f"result_quality={result_quality:.3f} | "
            f"base_reward={base_reward:.3f} | time_penalty={time_penalty:.4f} | "
            f"quality_bonus={quality_bonus:.3f} | raw_reward={reward:.3f} | "
            f"final_reward={final_reward:.3f}"
        )
        
        return final_reward

    def _online_update(self) -> None:
        """Perform online model update from replay buffer."""
        if self._network is None:
            tool_selection_logger.debug("UPDATE_SKIP | reason=no_network")
            return

        buffer_size = len(self.replay_buffer)
        
        if buffer_size < self.batch_size:
            # Not enough samples for batch update
            # Do single-sample update if we have any experiences
            if buffer_size >= 1:
                mini_batch_size = min(buffer_size, 8)
                batch = self.replay_buffer.sample(mini_batch_size)
                if batch:
                    X = np.array([e.state for e in batch])
                    y = np.array([e.action for e in batch])
                    weights = np.array([e.reward for e in batch])
                    
                    tool_selection_logger.debug(
                        f"UPDATE_MINI | buffer_size={buffer_size} < batch_size={self.batch_size} | "
                        f"mini_batch_size={mini_batch_size} | "
                        f"actions={y.tolist()} | rewards={[f'{w:.3f}' for w in weights]}"
                    )
                    
                    self._network.partial_fit(X, y, sample_weight=weights)
                    
                    # Save during mini-batch updates too (was missing - caused model to never persist!)
                    if self._total_experiences % 10 == 0:
                        self._save_state()
                        tool_selection_logger.info(
                            f"UPDATE_SAVE | total_experiences={self._total_experiences} | "
                            f"buffer_size={buffer_size}"
                        )
            else:
                tool_selection_logger.debug(
                    f"UPDATE_SKIP | reason=buffer_empty | buffer_size={buffer_size}"
                )
            return

        with self._lock:
            # Sample batch with prioritized replay
            batch = self.replay_buffer.sample(self.batch_size)

            if not batch:
                tool_selection_logger.debug("UPDATE_SKIP | reason=empty_batch_sample")
                return

            # Prepare training data
            X = np.array([e.state for e in batch])
            y = np.array([e.action for e in batch])
            weights = np.array([e.reward for e in batch])
            
            # Log batch statistics
            batch_tools = [e.tool_name for e in batch]
            batch_priorities = [e.priority for e in batch]

            # Incremental training
            loss = self._network.partial_fit(X, y, sample_weight=weights)

            # Periodic save - save every 10 experiences to ensure persistence across session restarts
            if self._total_experiences % 10 == 0:
                self._save_state()
                tool_selection_logger.info(
                    f"UPDATE_SAVE | total_experiences={self._total_experiences} | "
                    f"buffer_size={buffer_size}"
                )

            # Log update details
            tool_selection_logger.info(
                f"UPDATE | batch_size={len(batch)} | loss={loss:.4f} | "
                f"total_experiences={self._total_experiences} | "
                f"buffer_size={buffer_size} | "
                f"n_samples_seen={self._network._n_samples_seen} | "
                f"batch_tools={batch_tools} | "
                f"reward_stats=[min={weights.min():.3f}, max={weights.max():.3f}, mean={weights.mean():.3f}] | "
                f"priority_stats=[min={min(batch_priorities):.3f}, max={max(batch_priorities):.3f}]"
            )

            logger.debug(
                f"Online update: batch_size={len(batch)}, loss={loss:.4f}, "
                f"total_experiences={self._total_experiences}",
                extra={
                    "event": "rl_online_update",
                    "batch_size": len(batch),
                    "loss": loss,
                    "total_experiences": self._total_experiences,
                }
            )

    def _save_state(self) -> None:
        """Save model and buffer to disk."""
        try:
            if self._network:
                self._network.save(self.model_path)
            self.replay_buffer.save(self.buffer_path)
        except Exception as e:
            logger.warning(f"Failed to save RL state: {e}")

    def export_action_map(self, path: Optional[str] = None) -> Dict[str, int]:
        """
        Export the current action map (tool_name -> action_index).
        
        This is useful for debugging and analysis. The action map is dynamically
        built from registered tools, so it always reflects the current tool set.
        
        Args:
            path: Optional file path to save the action map as CSV.
                  If None, only returns the dict without saving.
        
        Returns:
            Dictionary mapping tool names to action indices.
        """
        action_map = dict(self._tool_to_idx)
        
        if path:
            try:
                from pathlib import Path
                output_path = Path(path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    f.write("tool_name,action_id\n")
                    for tool_name, action_id in sorted(action_map.items(), key=lambda x: x[1]):
                        f.write(f"{tool_name},{action_id}\n")
                
                logger.info(f"Exported action map ({len(action_map)} tools) to {path}")
            except Exception as e:
                logger.warning(f"Failed to export action map: {e}")
        
        return action_map
    
    def get_registered_tools(self) -> List[str]:
        """
        Get list of tool names currently registered in the action map.
        
        Returns:
            List of tool names sorted by action index.
        """
        return [self._idx_to_tool[i] for i in range(self._n_actions)]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the policy ranker."""
        return {
            "total_experiences": self._total_experiences,
            "buffer_size": len(self.replay_buffer),
            "n_actions": self._n_actions,
            "registered_tools": self.get_registered_tools(),
            "is_fitted": self._network._is_fitted if self._network else False,
            "samples_seen": self._network._n_samples_seen if self._network else 0,
            "force_threshold": self.force_threshold,
            "suggest_threshold": self.suggest_threshold,
            "top_k_suggest": self.top_k_suggest,
            "model_path": str(self.model_path),
            "buffer_path": str(self.buffer_path),
        }

    def shutdown(self) -> None:
        """Graceful shutdown - save state."""
        logger.info("OnlinePolicyRanker shutting down, saving state...")
        self._save_state()


__all__ = [
    "OnlinePolicyRanker",
    "ToolSelection",
    "PrioritizedReplayBuffer",
    "Experience",
]
