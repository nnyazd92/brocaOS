#!/usr/bin/env python3
"""
Build a canonical RL transitions dataset from live BrocaOS logs.

Inputs (best-effort):
- data/rl/experiences.jsonl (contains tool_call_id, tool_name, pre_context, post_context)
- data/rl_rewards.csv (contains composite_reward keyed by context string including tool_call_id)

Outputs:
- data/rl/transitions.jsonl
- data/rl/ppo_dataset.npz  (states, actions, rewards, next_states, dones)

Reward definition (authoritative):
1) post_context['rl_signals']['composite_reward'] if present
2) rl_rewards.csv row matched by tool_call_id embedded in its "context" column
3) fallback: 0.0
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


from .features import RL_SIGNAL_KEYS, extract_state_features


def _extract_tool_call_id_from_reward_context(ctx: str) -> Optional[str]:
    if not ctx:
        return None
    # Contexts are like: tool_call_{tool_name}_{tool_call_id}; tool_call_id starts with "call_"
    idx = str(ctx).rfind("call_")
    if idx == -1:
        return None
    return str(ctx)[idx:].strip()


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
    except Exception:
        return default
    if v != v:  # NaN
        return default
    if v == float("inf") or v == float("-inf"):
        return default
    return v


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def load_reward_rows_by_tool_call_id(rewards_csv: Path) -> Dict[str, Dict[str, str]]:
    if not rewards_csv.exists():
        return {}
    mapping: Dict[str, Dict[str, str]] = {}
    with open(rewards_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tool_call_id = _extract_tool_call_id_from_reward_context(row.get("context", "") or "")
            if tool_call_id:
                mapping[tool_call_id] = row
    return mapping


def iter_experiences(experiences_jsonl: Path) -> Iterable[Dict[str, Any]]:
    with open(experiences_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


@dataclass
class BuiltDataset:
    states: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    next_states: np.ndarray
    dones: np.ndarray
    action_map: Dict[int, str]


def build_dataset(
    workspace_root: Path,
    input_dim: int = 16,
) -> BuiltDataset:
    experiences_path = workspace_root / "data" / "rl" / "experiences.jsonl"
    rewards_csv = workspace_root / "data" / "rl_rewards.csv"

    if not experiences_path.exists():
        raise FileNotFoundError(f"Missing {experiences_path}")

    rewards_by_call = load_reward_rows_by_tool_call_id(rewards_csv)

    # Build action map from seen tool names (sorted for determinism)
    experiences = list(iter_experiences(experiences_path))
    tool_names = sorted({str(e.get("tool_name", "")) for e in experiences if e.get("tool_name")})
    tool_to_aid = {name: i for i, name in enumerate(tool_names)}
    action_map = {i: name for name, i in tool_to_aid.items()}

    states: List[np.ndarray] = []
    actions: List[int] = []
    rewards: List[float] = []
    next_states: List[np.ndarray] = []
    dones: List[float] = []

    for e in experiences:
        tool = e.get("tool_name")
        if not tool or tool not in tool_to_aid:
            continue

        pre_ctx = e.get("pre_context") if isinstance(e.get("pre_context"), dict) else {}
        post_ctx = e.get("post_context") if isinstance(e.get("post_context"), dict) else {}

        s = extract_state_features(pre_ctx, input_dim=input_dim)
        ns = extract_state_features(post_ctx, input_dim=input_dim) if post_ctx else s.copy()

        # Reward: combine intrinsic cognitive signals + extrinsic success/failure + latency penalty.
        from broca.config import config as _config
        from .reward import RewardWeights, compute_reward_from_outcome

        rl_s = post_ctx.get("rl_signals") if isinstance(post_ctx, dict) else None
        if not isinstance(rl_s, dict):
            # Fall back to rl_rewards.csv row matched by tool_call_id
            tool_call_id = e.get("tool_call_id")
            if tool_call_id and tool_call_id in rewards_by_call:
                rl_s = rewards_by_call[tool_call_id]

        success = bool(e.get("success", True))
        exec_ms = _safe_float(e.get("execution_time_ms", 0.0), 0.0)
        result_quality = _safe_float(e.get("result_quality", 0.5), 0.5)

        reward_val, _ = compute_reward_from_outcome(
            rl_signals=rl_s if isinstance(rl_s, dict) else None,
            intrinsic_keys=RL_SIGNAL_KEYS,
            success=success,
            execution_time_ms=exec_ms,
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

        # Non-episodic stream; treat last transition as terminal only at dataset end
        done = 0.0

        states.append(s)
        next_states.append(ns)
        actions.append(int(tool_to_aid[tool]))
        rewards.append(float(reward_val))
        dones.append(float(done))

    # Mark last transition terminal (helps advantage computation avoid bootstrapping forever)
    if dones:
        dones[-1] = 1.0

    if not states:
        raise RuntimeError("No transitions could be built from experiences.jsonl")

    return BuiltDataset(
        states=np.stack(states, axis=0),
        actions=np.array(actions, dtype=np.int64),
        rewards=np.array(rewards, dtype=np.float32),
        next_states=np.stack(next_states, axis=0),
        dones=np.array(dones, dtype=np.float32),
        action_map=action_map,
    )


def write_outputs(workspace_root: Path, dataset: BuiltDataset) -> Tuple[Path, Path]:
    out_dir = workspace_root / "data" / "rl"
    out_dir.mkdir(parents=True, exist_ok=True)

    transitions_path = out_dir / "transitions.jsonl"
    npz_path = out_dir / "ppo_dataset.npz"

    with open(transitions_path, "w", encoding="utf-8") as f:
        for i in range(len(dataset.actions)):
            rec = {
                "state": dataset.states[i].tolist(),
                "action": int(dataset.actions[i]),
                "reward": float(dataset.rewards[i]),
                "next_state": dataset.next_states[i].tolist(),
                "done": bool(dataset.dones[i] > 0.5),
            }
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")

    np.savez_compressed(
        npz_path,
        states=dataset.states,
        actions=dataset.actions,
        rewards=dataset.rewards,
        next_states=dataset.next_states,
        dones=dataset.dones,
    )

    # Write action map for analysis/debugging
    action_map_path = out_dir / "action_map.csv"
    with open(action_map_path, "w", encoding="utf-8", newline="") as f:
        f.write("tool_name,action_id\n")
        for aid, name in sorted(dataset.action_map.items(), key=lambda x: x[0]):
            f.write(f"{name},{aid}\n")

    return transitions_path, npz_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build PPO dataset from BrocaOS logs")
    parser.add_argument(
        "--workspace_root",
        type=str,
        default=str(Path(__file__).resolve().parents[2]),
        help="Workspace root (default: repo root)",
    )
    parser.add_argument("--input_dim", type=int, default=16, help="Feature dimension (default 16)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    root = Path(args.workspace_root).resolve()
    dataset = build_dataset(root, input_dim=args.input_dim)
    transitions_path, npz_path = write_outputs(root, dataset)
    logger.info(
        f"Built dataset: n={len(dataset.actions)} dim={dataset.states.shape[1]} "
        f"n_actions={len(dataset.action_map)} transitions={transitions_path} npz={npz_path}"
    )


if __name__ == "__main__":
    main()
