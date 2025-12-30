"""
Online PPO policy ranker for BrocaOS runtime tool selection.

This provides the same public surface area that ToolRegistry expects:
- select_tool(tools, context) -> ToolSelection
- record_outcome(tool_name, context, next_context, ..., reward=..., rl_signals=...)

Important: PPO is an on-policy algorithm. In this integration we only train on
transitions where the executed tool matches the PPO-selected tool in "forced"
mode (ToolRegistry enforces the tool choice in that mode).
"""

from __future__ import annotations

import atexit
import logging
import time
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .ppo_policy import PPOConfig, PPOPolicy
from .features import RL_SIGNAL_KEYS, extract_state_features
from .reward import RewardWeights, compute_reward_from_outcome
from .tool_selection_logging import get_tool_selection_logger

logger = logging.getLogger(__name__)

tool_selection_logger = get_tool_selection_logger()
tool_selection_logger.info("=" * 80)
tool_selection_logger.info("TOOL SELECTION LOGGING INITIALIZED (PPO)")
tool_selection_logger.info("=" * 80)

 # RL signal key order is shared across all policies/dataset builders.

# Registry of ranker instances for atexit cleanup
_ranker_instances: List[weakref.ref] = []


def _atexit_cleanup():
    for ref in _ranker_instances:
        ranker = ref()
        if ranker is not None:
            try:
                ranker.shutdown()
            except Exception:
                pass


atexit.register(_atexit_cleanup)


@dataclass
class ToolSelection:
    """Result of RL tool selection (mirrors broca.rl.online_policy.ToolSelection)."""

    tool_name: str
    score: float
    confidence: float
    mode: str  # "forced", "suggested", "fallback"
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    reason: str = ""
    all_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "score": self.score,
            "confidence": self.confidence,
            "mode": self.mode,
            "alternatives": self.alternatives,
            "reason": self.reason,
        }


class PPOOnlinePolicyRanker:
    """
    PPO-backed online policy ranker.

    Selection gating matches the behavior of OnlinePolicyRanker:
    - confidence >= force_threshold -> "forced"
    - confidence >= suggest_threshold -> "suggested"
    - else -> "fallback"
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        force_threshold: float = 0.85,
        suggest_threshold: float = 0.30,
        top_k_suggest: int = 3,
        hidden_dim: int = 128,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        batch_size: int = 64,
        buffer_size: int = 2048,
    ):
        self.model_path = Path(model_path or "models/rl/policy_ppo.pt")
        self.force_threshold = float(force_threshold)
        self.suggest_threshold = float(suggest_threshold)
        self.top_k_suggest = int(top_k_suggest)

        self._hidden_dim = int(hidden_dim)
        self._learning_rate = float(learning_rate)
        self._gamma = float(gamma)
        self._gae_lambda = float(gae_lambda)
        self._clip_epsilon = float(clip_epsilon)
        self._value_coef = float(value_coef)
        self._entropy_coef = float(entropy_coef)
        self._batch_size = int(batch_size)
        self._buffer_size = int(buffer_size)

        # Action mapping: tool_name <-> action_index
        self._tool_to_idx: Dict[str, int] = {}
        self._idx_to_tool: Dict[int, str] = {}
        self._n_actions = 0

        # Feature dimension (keep parity with OnlinePolicyRanker: 6 RL signals + 10 context features)
        self._input_dim = len(RL_SIGNAL_KEYS) + 10  # 16

        self._policy: Optional[PPOPolicy] = None
        self._lock = Lock()

        # Track last selection for on-policy training checks
        self._last_selection: Optional[ToolSelection] = None
        self._last_context: Optional[Dict[str, Any]] = None

        _ranker_instances.append(weakref.ref(self))

    def _ensure_policy(self, tools: List[Any]) -> None:
        tool_names = sorted([t.name for t in tools])
        new_mapping = {name: i for i, name in enumerate(tool_names)}

        if self._policy is None or new_mapping != self._tool_to_idx:
            self._tool_to_idx = new_mapping
            self._idx_to_tool = {v: k for k, v in new_mapping.items()}
            self._n_actions = len(new_mapping)

            config = PPOConfig(
                input_dim=self._input_dim,
                output_dim=self._n_actions,
                hidden_dim=self._hidden_dim,
                learning_rate=self._learning_rate,
                gamma=self._gamma,
                gae_lambda=self._gae_lambda,
                clip_epsilon=self._clip_epsilon,
                value_coef=self._value_coef,
                entropy_coef=self._entropy_coef,
                batch_size=self._batch_size,
                buffer_size=self._buffer_size,
            )
            self._policy = PPOPolicy(config)
            # Best-effort load; if mismatch (e.g., different tool set) start fresh.
            try:
                if self.model_path.exists():
                    self._policy.load(str(self.model_path))
                    logger.info(f"Loaded PPO model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load PPO model from {self.model_path}: {e}")

    def _extract_features(self, context: Dict[str, Any]) -> np.ndarray:
        """Match OnlinePolicyRanker feature extraction for parity."""
        return extract_state_features(context, input_dim=self._input_dim)

    def select_tool(self, tools: List[Any], context: Dict[str, Any]) -> ToolSelection:
        if not tools:
            return ToolSelection(
                tool_name="",
                score=0.0,
                confidence=0.0,
                mode="fallback",
                reason="No tools available",
            )

        self._ensure_policy(tools)
        assert self._policy is not None

        state = self._extract_features(context or {})
        probs = self._policy.predict_proba(state).astype(np.float32)
        if probs.ndim != 1 or len(probs) != self._n_actions:
            probs = np.ones(self._n_actions, dtype=np.float32) / max(1, self._n_actions)

        # Rank tools
        ranked_indices = np.argsort(probs)[::-1]
        ranked_tools: List[Tuple[str, float]] = []
        all_scores: Dict[str, float] = {}
        for idx in ranked_indices:
            name = self._idx_to_tool.get(int(idx))
            if name and any(t.name == name for t in tools):
                score = float(probs[int(idx)])
                ranked_tools.append((name, score))
                all_scores[name] = score

        if not ranked_tools:
            return ToolSelection(
                tool_name="",
                score=0.0,
                confidence=0.0,
                mode="fallback",
                reason="No valid tools in ranking",
            )

        top_tool, top_score = ranked_tools[0]
        confidence = float(max(0.0, min(1.0, top_score)))

        if confidence >= self.force_threshold:
            mode = "forced"
            reason = f"High confidence ({confidence:.1%}) - PPO forces selection"
        elif confidence >= self.suggest_threshold:
            mode = "suggested"
            reason = f"Medium confidence ({confidence:.1%}) - PPO suggests top-{self.top_k_suggest}"
        else:
            mode = "fallback"
            reason = f"Low confidence ({confidence:.1%}) - LLM has full choice (failsafe)"

        selection = ToolSelection(
            tool_name=top_tool,
            score=float(top_score),
            confidence=confidence,
            mode=mode,
            alternatives=ranked_tools[1 : self.top_k_suggest + 1],
            reason=reason,
            all_scores=all_scores,
        )

        try:
            tool_selection_logger.info(
                f"PPO_SELECTION | mode={mode} | confidence={confidence:.2%} | "
                f"tool={top_tool} | score={float(top_score):.4f} | "
                f"alternatives={[(t, f'{s:.4f}') for t, s in ranked_tools[1 : self.top_k_suggest + 1]]} | "
                f"thresholds=[force>={self.force_threshold:.0%}, suggest>={self.suggest_threshold:.0%}]"
            )
        except Exception:
            pass

        self._last_selection = selection
        self._last_context = (context or {}).copy()
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
        Record outcome and (optionally) update PPO.

        We only update PPO when:
        - last_selection exists
        - last_selection.mode == 'forced'
        - executed tool == last_selection.tool_name
        """
        if tool_name not in self._tool_to_idx:
            return

        # Require on-policy-ish transitions for PPO updates
        if (
            self._last_selection is None
            or self._last_selection.mode != "forced"
            or self._last_selection.tool_name != tool_name
        ):
            return

        ctx = context if isinstance(context, dict) else None
        if ctx is None:
            ctx = (self._last_context or {}) if isinstance(self._last_context, dict) else {}

        next_ctx = next_context if isinstance(next_context, dict) else None
        post_rl_signals = rl_signals if isinstance(rl_signals, dict) else None
        if next_ctx is not None and post_rl_signals is not None and "rl_signals" not in next_ctx:
            # Treat `rl_signals` as post-action signals when provided (matches ToolRegistry behavior).
            next_ctx = next_ctx.copy()
            next_ctx["rl_signals"] = post_rl_signals

        # Build authoritative reward from intrinsic signals + extrinsic outcome + latency penalty.
        # Latency is intentionally NOT included as a feature.
        from broca.config import config as _config

        if post_rl_signals is None and isinstance(next_ctx, dict):
            maybe = next_ctx.get("rl_signals")
            if isinstance(maybe, dict):
                post_rl_signals = maybe

        r, _parts = compute_reward_from_outcome(
            rl_signals=post_rl_signals if isinstance(post_rl_signals, dict) else None,
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

        if self._policy is None:
            return

        state = self._extract_features(ctx)
        next_state = self._extract_features(next_ctx) if next_ctx else None
        action = int(self._tool_to_idx[tool_name])

        # Store and train. We use done=False unless next_state missing.
        info = {"done": next_state is None}
        self._policy.store_experience(state, action, float(r), next_state, info)
        try:
            tool_selection_logger.info(
                f"PPO_OUTCOME | tool={tool_name} | action_idx={action} | "
                f"reward={float(r):.3f} | success={bool(success)} | "
                f"execution_time_ms={float(execution_time_ms or 0.0):.1f} | result_quality={float(result_quality):.3f}"
            )
        except Exception:
            pass

        # Persist periodically to survive restarts
        if self._policy.training_step % 5 == 0 and self._policy.training_step > 0:
            try:
                self._policy.save(str(self.model_path))
            except Exception:
                pass

    def shutdown(self) -> None:
        """Best-effort save on shutdown."""
        try:
            if self._policy is not None:
                self._policy.save(str(self.model_path))
        except Exception:
            pass


__all__ = ["PPOOnlinePolicyRanker", "ToolSelection"]
