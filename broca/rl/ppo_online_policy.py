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
import json
import logging
import random
import time
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .ppo_policy import PPOConfig, PPOPolicy
from .features import RL_SIGNAL_KEYS, extract_state_features, BASE_STATE_DIM
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

        # Feature dimension (parity across policies; optional text embedding dims are appended)
        try:
            from broca.config import config as _config

            self._text_embed_dim = int(getattr(_config.rl, "text_embedding_dim", 0) or 0)
            self._text_embed_max_chars = int(getattr(_config.rl, "text_embedding_max_chars", 2000) or 2000)
            fields = str(getattr(_config.rl, "text_embedding_fields", "") or "")
            self._text_embed_fields = [x.strip() for x in fields.split(",") if x.strip()] or None
        except Exception:
            self._text_embed_dim = 0
            self._text_embed_max_chars = 2000
            self._text_embed_fields = None

        self._input_dim = int(BASE_STATE_DIM + max(0, self._text_embed_dim))

        self._policy: Optional[PPOPolicy] = None
        self._lock = Lock()

        # Track last selection for on-policy training checks
        self._last_selection: Optional[ToolSelection] = None
        self._last_context: Optional[Dict[str, Any]] = None
        self._bc_warm_started_for_mapping: Optional[str] = None

        # Persist PPO rollout buffer across restarts so forced-exploration on-policy data survives.
        try:
            from broca.config import config as _config

            self._buffer_path = Path(str(getattr(_config.rl, "ppo_buffer_path", "data/rl/ppo_buffer.json")))
        except Exception:
            self._buffer_path = Path("data/rl/ppo_buffer.json")

        _ranker_instances.append(weakref.ref(self))

    def _mapping_fingerprint(self) -> str:
        try:
            return "|".join(sorted(self._tool_to_idx.keys()))
        except Exception:
            return ""

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
            loaded_ok = False
            try:
                if self.model_path.exists():
                    self._policy.load(str(self.model_path))
                    loaded_ok = True
                    logger.info(f"Loaded PPO model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load PPO model from {self.model_path}: {e}")

            # Load persisted rollout buffer after model/tool mapping is established.
            try:
                self._load_buffer()
            except Exception:
                pass

            # Always log bootstrap status for visibility.
            try:
                ts = int(getattr(self._policy, "training_step", 0))
            except Exception:
                ts = 0
            try:
                bc = int(getattr(self._policy, "bc_step", 0))
            except Exception:
                bc = 0
            try:
                tool_selection_logger.info(
                    f"PPO_POLICY_READY | mapping_tools={list(self._tool_to_idx.keys())} | "
                    f"input_dim={self._input_dim} | text_embed_dim={self._text_embed_dim} | "
                    f"model_path={str(self.model_path)} | model_exists={self.model_path.exists()} | "
                    f"model_loaded={bool(loaded_ok)} | training_step={ts} | bc_step={bc}"
                )
            except Exception:
                pass

            # Bootstrap: behavior cloning warm-start from logged experiences.
            try:
                from broca.config import config as _config

                if _config.rl.ppo_bc_warm_start_enabled:
                    self._maybe_bc_warm_start(
                        epochs=_config.rl.ppo_bc_epochs,
                        batch_size=_config.rl.ppo_bc_batch_size,
                        max_samples=_config.rl.ppo_bc_max_samples,
                        value_coef=_config.rl.ppo_bc_value_coef,
                        entropy_coef=_config.rl.ppo_bc_entropy_coef,
                    )
            except Exception:
                pass

    def _iter_experiences_jsonl(self, path: Path, max_samples: int) -> List[Dict[str, Any]]:
        """
        Read up to max_samples experience records from a JSONL file.

        We keep the tail so warm-start uses the most recent tool distribution.
        """
        if max_samples <= 0:
            return []
        records: List[Dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if isinstance(obj, dict):
                        records.append(obj)
        except Exception:
            return []
        if len(records) > max_samples:
            records = records[-max_samples:]
        return records

    def _iter_learning_experiences_json(self, path: Path, max_samples: int) -> List[Dict[str, Any]]:
        """
        Read up to max_samples tool execution experiences from data/experiences.json.

        This file may not contain rich contexts; if so, warm-start degenerates to learning
        a state-independent prior, which is still a useful cold-start bias.
        """
        if max_samples <= 0:
            return []
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        xs = obj.get("experiences") if isinstance(obj, dict) else None
        if not isinstance(xs, list):
            return []
        # Tail bias: prefer recent experiences
        xs = xs[-max_samples:]
        out: List[Dict[str, Any]] = []
        for item in xs:
            if not isinstance(item, dict):
                continue
            data = item.get("data")
            if not isinstance(data, dict):
                continue
            tool_name = data.get("tool_name")
            if not isinstance(tool_name, str):
                continue
            out.append(item)
        return out

    def _maybe_bc_warm_start(
        self,
        *,
        epochs: int,
        batch_size: int,
        max_samples: int,
        value_coef: float,
        entropy_coef: float,
    ) -> None:
        if self._policy is None:
            return

        fp = self._mapping_fingerprint()
        if self._bc_warm_started_for_mapping == fp:
            try:
                tool_selection_logger.info(f"PPO_BC_SKIP | reason=already_warm_started | mapping={fp}")
            except Exception:
                pass
            return

        # Only warm-start a "fresh" policy (avoid expensive BC on every restart).
        # If you want to re-run BC, delete the model file or change mapping.
        from broca.config import config as _config
        try:
            training_step = int(getattr(self._policy, "training_step", 0))
        except Exception:
            training_step = 0
        force = bool(getattr(_config.rl, "ppo_bc_force", False))
        if training_step > 0 and not force:
            try:
                tool_selection_logger.info(
                    f"PPO_BC_SKIP | reason=training_step_gt_zero | training_step={training_step} | mapping={fp}"
                )
            except Exception:
                pass
            self._bc_warm_started_for_mapping = fp
            return

        # Build a supervised dataset.
        states: List[np.ndarray] = []
        actions: List[int] = []
        value_targets: List[float] = []

        n_used_contextful = 0
        n_used_prior = 0

        # Prefer context-rich RL experiences (JSONL) when available.
        jsonl_path = Path("data/rl/experiences.jsonl")
        if jsonl_path.exists():
            try:
                records = []
                with jsonl_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        if isinstance(obj, dict):
                            records.append(obj)
                if len(records) > max_samples:
                    records = records[-max_samples:]

                for rec in records:
                    tool_name = rec.get("tool_name")
                    if tool_name not in self._tool_to_idx:
                        continue

                    pre_ctx = rec.get("pre_context")
                    post_ctx = rec.get("post_context")
                    if not isinstance(pre_ctx, dict):
                        # Best-effort fallback: try post_ctx for feature extraction.
                        pre_ctx = post_ctx if isinstance(post_ctx, dict) else {}
                    if not isinstance(pre_ctx, dict):
                        continue

                    # Extract state features.
                    s = self._extract_features(pre_ctx)
                    if s is None:
                        continue

                    # Build reward target from post-action signals and outcome.
                    success = bool(rec.get("success", True))
                    execution_time_ms = float(rec.get("execution_time_ms", 0.0) or 0.0)
                    result_quality = 0.5
                    if isinstance(rec.get("epistemic"), dict):
                        try:
                            result_quality = float(rec["epistemic"].get("evidence_strength", 0.5))
                        except Exception:
                            result_quality = 0.5

                    post_rl_signals = None
                    if isinstance(post_ctx, dict):
                        maybe = post_ctx.get("rl_signals")
                        if isinstance(maybe, dict):
                            post_rl_signals = maybe

                    r, _ = compute_reward_from_outcome(
                        rl_signals=post_rl_signals,
                        intrinsic_keys=RL_SIGNAL_KEYS,
                        success=success,
                        execution_time_ms=execution_time_ms,
                        result_quality=result_quality,
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

                    states.append(s)
                    actions.append(int(self._tool_to_idx[tool_name]))
                    value_targets.append(float(r))
                    n_used_contextful += 1
            except Exception:
                pass

        # Also consume the generic learning experience store as a weak prior (no contexts).
        exp_path = Path("data/experiences.json")
        if exp_path.exists() and len(states) < max_samples:
            try:
                obj = json.loads(exp_path.read_text(encoding="utf-8"))
                xs = obj.get("experiences") if isinstance(obj, dict) else None
                if isinstance(xs, list):
                    for item in xs[-max_samples:]:
                        if not isinstance(item, dict):
                            continue
                        data = item.get("data")
                        if not isinstance(data, dict):
                            continue
                        tool_name = data.get("tool_name")
                        if tool_name not in self._tool_to_idx:
                            continue
                        # No context available: learn a global prior over actions.
                        s = np.zeros(self._input_dim, dtype=np.float32)
                        states.append(s)
                        actions.append(int(self._tool_to_idx[tool_name]))
                        value_targets.append(0.5)
                        n_used_prior += 1
                        if len(states) >= max_samples:
                            break
            except Exception:
                pass

        if not states:
            try:
                tool_selection_logger.info(
                    f"PPO_BC_SKIP | reason=no_bc_samples | mapping={fp} | "
                    f"contextful={n_used_contextful} | prior={n_used_prior} | "
                    f"experiences_jsonl_exists={jsonl_path.exists()} | experiences_json_exists={Path('data/experiences.json').exists()}"
                )
            except Exception:
                pass
            self._bc_warm_started_for_mapping = fp
            return

        # Train policy with BC and a small value warm-up.
        st = np.stack(states, axis=0).astype(np.float32)
        act = np.asarray(actions, dtype=np.int64)
        vt = np.asarray(value_targets, dtype=np.float32)

        metrics = self._policy.behavior_clone(
            st,
            act,
            value_targets=vt,
            epochs=int(epochs),
            batch_size=int(batch_size),
            value_coef=float(value_coef),
            entropy_coef=float(entropy_coef),
        )
        try:
            tool_selection_logger.info(
                f"PPO_BC_WARM_START | n={metrics.get('n')} | bc_steps={metrics.get('bc_steps')} | "
                f"contextful={n_used_contextful} | prior={n_used_prior} | "
                f"loss={metrics.get('loss'):.4f} | ce={metrics.get('ce_loss'):.4f} | v={metrics.get('value_loss'):.4f}"
            )
        except Exception:
            pass

        # Persist immediately to survive restarts
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            self._policy.save(str(self.model_path))
        except Exception:
            pass

        self._bc_warm_started_for_mapping = fp

    def _extract_features(self, context: Dict[str, Any]) -> np.ndarray:
        """Match OnlinePolicyRanker feature extraction for parity."""
        return extract_state_features(
            context,
            input_dim=self._input_dim,
            text_embedding_dim=self._text_embed_dim,
            text_fields=self._text_embed_fields,
            text_max_chars=self._text_embed_max_chars,
        )

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

        # Forced exploration: occasionally force a PPO-sampled action even at low confidence.
        # This guarantees early on-policy data collection for PPO.
        try:
            from broca.config import config as _config

            p = float(_config.rl.ppo_forced_exploration_prob)
            roll = random.random()
            try:
                tool_selection_logger.info(
                    f"PPO_EXPLORE_CHECK | p={p:.3f} | roll={roll:.3f} | triggered={bool(p > 0 and roll < p)}"
                )
            except Exception:
                pass

            if p > 0 and roll < p:
                # Sample from current policy distribution.
                a, _, _info = self._policy.select_action(state, explore=True)
                forced_tool = self._idx_to_tool.get(int(a), "")
                if forced_tool:
                    selection = ToolSelection(
                        tool_name=forced_tool,
                        score=float(probs[int(a)]) if int(a) < len(probs) else 0.0,
                        confidence=float(probs[int(a)]) if int(a) < len(probs) else 0.0,
                        mode="forced",
                        alternatives=[],
                        reason=f"Forced exploration (p={p:.3f}) - collect on-policy data",
                        all_scores={self._idx_to_tool[i]: float(probs[i]) for i in range(min(len(probs), self._n_actions)) if self._idx_to_tool.get(i)},
                    )
                    try:
                        tool_selection_logger.info(
                            f"PPO_FORCED_EXPLORATION | tool={forced_tool} | action_idx={int(a)} | p={p:.3f}"
                        )
                    except Exception:
                        pass
                    self._last_selection = selection
                    self._last_context = (context or {}).copy()
                    return selection
        except Exception:
            pass

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

        # Optional: force PPO mode regardless of confidence gating (bootstrapping).
        try:
            from broca.config import config as _config

            if bool(getattr(_config.rl, "ppo_always_forced", False)) and mode != "forced":
                tool_selection_logger.info(
                    f"PPO_FORCE_OVERRIDE | prev_mode={mode} | forced_tool={top_tool} | confidence={confidence:.2%}"
                )
                mode = "forced"
                reason = "PPO always-forced enabled - collect on-policy rollouts"
        except Exception:
            pass

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

        # Visibility: surface PPO internals even when we aren't training yet.
        try:
            buf_len = None
            if self._policy is not None:
                try:
                    with self._policy.buffer_lock:
                        buf_len = len(self._policy.buffer)
                except Exception:
                    buf_len = None
            ts = getattr(self._policy, "training_step", None) if self._policy is not None else None
            last_loss = getattr(self._policy, "_last_loss", None) if self._policy is not None else None
            epochs = getattr(getattr(self._policy, "config", None), "ppo_epochs", None) if self._policy is not None else None

            tool_selection_logger.info(
                "PPO_STATUS | "
                f"mode={mode} | "
                f"training_step={ts} | buffer_len={buf_len} | "
                f"buffer_size={int(getattr(self, '_buffer_size', 0) or 0)} | "
                f"batch_size={int(getattr(self, '_batch_size', 0) or 0)} | "
                f"ppo_epochs={epochs} | "
                f"last_loss={None if last_loss is None else float(last_loss):.4f}"
            )
        except Exception:
            pass

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
            try:
                if self._last_selection is None:
                    reason = "no_last_selection"
                    sel_tool = None
                    sel_mode = None
                    sel_conf = None
                else:
                    sel_tool = getattr(self._last_selection, "tool_name", None)
                    sel_mode = getattr(self._last_selection, "mode", None)
                    sel_conf = getattr(self._last_selection, "confidence", None)
                    if sel_mode != "forced":
                        # This is the common source of confusion:
                        # the model can execute the PPO-top tool in fallback/suggested mode,
                        # but PPO policy-gradient updates remain disabled to avoid off-policy bias.
                        if sel_tool == tool_name:
                            reason = "matched_but_not_forced"
                        else:
                            reason = "not_forced_mode"
                    elif sel_tool != tool_name:
                        reason = "executed_mismatch"
                    else:
                        reason = "unknown_skip"

                tool_selection_logger.info(
                    f"PPO_SKIP | reason={reason} | executed_tool={tool_name} | "
                    f"last_tool={sel_tool} | last_mode={sel_mode} | last_confidence={sel_conf}"
                )
            except Exception:
                pass
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
        prev_step = int(getattr(self._policy, "training_step", 0))
        prev_buf_len = None
        try:
            with getattr(self._policy, "buffer_lock"):
                prev_buf_len = len(getattr(self._policy, "buffer", []))
        except Exception:
            prev_buf_len = None

        self._policy.store_experience(state, action, float(r), next_state, info)

        # Persist buffer frequently so on-policy rollouts survive restarts.
        try:
            self._save_buffer()
        except Exception:
            pass

        new_step = int(getattr(self._policy, "training_step", 0))
        new_buf_len = None
        try:
            with getattr(self._policy, "buffer_lock"):
                new_buf_len = len(getattr(self._policy, "buffer", []))
        except Exception:
            new_buf_len = None

        try:
            tool_selection_logger.info(
                f"PPO_OUTCOME | tool={tool_name} | action_idx={action} | "
                f"reward={float(r):.3f} | success={bool(success)} | "
                f"execution_time_ms={float(execution_time_ms or 0.0):.1f} | result_quality={float(result_quality):.3f}"
            )
        except Exception:
            pass

        # Visibility: show when PPO is merely collecting vs actually training.
        try:
            tool_selection_logger.info(
                "PPO_BUFFER | "
                f"buffer_len={new_buf_len} | buffer_size={int(getattr(self, '_buffer_size', 0) or 0)} | "
                f"trained={bool(new_step != prev_step)} | training_step={new_step} | "
                f"prev_buffer_len={prev_buf_len}"
            )
        except Exception:
            pass

        if new_step != prev_step:
            try:
                loss = getattr(self._policy, "_last_loss", None)
                loss_str = f"{float(loss):.4f}" if isinstance(loss, (int, float)) else "None"
                tool_selection_logger.info(
                    f"PPO_UPDATE | training_step={new_step} | loss={loss_str} | "
                    f"rollout_size={int(getattr(self, '_buffer_size', 0) or 0)}"
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
        try:
            self._save_buffer()
        except Exception:
            pass

    def _save_buffer(self) -> None:
        if self._policy is None:
            return
        path = Path(self._buffer_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with self._policy.buffer_lock:
            exps = list(self._policy.buffer)

        payload: Dict[str, Any] = {
            "version": 1,
            "mapping": self._mapping_fingerprint(),
            "input_dim": int(getattr(self._policy.config, "input_dim", self._input_dim)),
            "output_dim": int(getattr(self._policy.config, "output_dim", self._n_actions)),
            "buffer_size": int(getattr(self._policy.config, "buffer_size", self._buffer_size)),
            "batch_size": int(getattr(self._policy.config, "batch_size", self._batch_size)),
            "training_step": int(getattr(self._policy, "training_step", 0)),
            "experiences": [
                {
                    "state": exp.get("state").tolist() if hasattr(exp.get("state"), "tolist") else exp.get("state"),
                    "action": int(exp.get("action", 0)),
                    "reward": float(exp.get("reward", 0.0)),
                    "next_state": (
                        exp.get("next_state").tolist()
                        if exp.get("next_state") is not None and hasattr(exp.get("next_state"), "tolist")
                        else exp.get("next_state")
                    ),
                    "log_prob": exp.get("log_prob", None),
                    "value": exp.get("value", None),
                    "done": bool(exp.get("done", False)),
                }
                for exp in exps
                if isinstance(exp, dict)
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tool_selection_logger.info(
            f"PPO_BUFFER_SAVE | path={str(path)} | n={len(exps)} | training_step={payload['training_step']}"
        )

    def _load_buffer(self) -> None:
        if self._policy is None:
            return
        path = Path(self._buffer_path)
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(payload, dict):
            return

        if payload.get("mapping") != self._mapping_fingerprint():
            tool_selection_logger.info("PPO_BUFFER_LOAD_SKIP | reason=mapping_mismatch")
            return
        if int(payload.get("input_dim", -1)) != int(getattr(self._policy.config, "input_dim", self._input_dim)):
            tool_selection_logger.info("PPO_BUFFER_LOAD_SKIP | reason=input_dim_mismatch")
            return
        if int(payload.get("output_dim", -1)) != int(getattr(self._policy.config, "output_dim", self._n_actions)):
            tool_selection_logger.info("PPO_BUFFER_LOAD_SKIP | reason=output_dim_mismatch")
            return

        exps = payload.get("experiences")
        if not isinstance(exps, list):
            return

        restored: List[Dict[str, Any]] = []
        for exp in exps:
            if not isinstance(exp, dict):
                continue
            st = exp.get("state")
            ns = exp.get("next_state")
            try:
                state = np.asarray(st, dtype=np.float32) if st is not None else None
                next_state = np.asarray(ns, dtype=np.float32) if ns is not None else None
                if state is None or state.shape != (int(self._policy.config.input_dim),):
                    continue
                if next_state is not None and next_state.shape != (int(self._policy.config.input_dim),):
                    next_state = None
                restored.append(
                    {
                        "state": state,
                        "action": int(exp.get("action", 0)),
                        "reward": float(exp.get("reward", 0.0)),
                        "next_state": next_state,
                        "log_prob": exp.get("log_prob", None),
                        "value": exp.get("value", None),
                        "done": bool(exp.get("done", False)),
                    }
                )
            except Exception:
                continue

        max_n = int(getattr(self._policy.config, "buffer_size", self._buffer_size))
        restored = restored[-max_n:]

        with self._policy.buffer_lock:
            self._policy.buffer.clear()
            self._policy.buffer.extend(restored)

        tool_selection_logger.info(f"PPO_BUFFER_LOAD | path={str(path)} | n={len(restored)}")


__all__ = ["PPOOnlinePolicyRanker", "ToolSelection"]
