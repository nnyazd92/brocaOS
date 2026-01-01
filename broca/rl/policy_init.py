"""
Initialize RL tool-selection policy ranker.

Shared entrypoint used by REPL and runtime surfaces to avoid drift.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import config

logger = logging.getLogger(__name__)


def initialize_online_policy_ranker() -> Optional[Any]:
    """
    Initialize OnlinePolicyRanker/PPOOnlinePolicyRanker for RL-primary tool selection.

    Returns:
        Ranker instance if successfully initialized, otherwise None.
    """
    if not config.rl.enabled:
        logger.debug("RL-primary tool selection is disabled (BROCA_RL_ENABLED=false)")
        return None

    # Apply active version (if any) before constructing the ranker so it loads the correct artifacts.
    try:
        from .policy_active import apply_active_policy_version

        applied, info = apply_active_policy_version(runtime_algorithm=config.rl.algorithm)
        if applied:
            logger.info(f"✓ Applied active policy version v{info.get('version_id')} ({len(info.get('changed', {}))} change(s))")
    except Exception as e:
        logger.debug(f"Failed to apply active policy version: {e}")

    try:
        if config.rl.algorithm == "ppo":
            from .ppo_online_policy import PPOOnlinePolicyRanker

            ranker = PPOOnlinePolicyRanker(
                model_path=config.rl.ppo_model_path,
                force_threshold=config.rl.force_threshold,
                suggest_threshold=config.rl.suggest_threshold,
                top_k_suggest=config.rl.top_k_suggest,
                hidden_dim=config.rl.ppo_hidden_dim,
                learning_rate=config.rl.ppo_learning_rate,
                buffer_size=config.rl.ppo_buffer_size,
                batch_size=config.rl.ppo_batch_size,
            )
            logger.info(
                f"✓ PPOOnlinePolicyRanker initialized: "
                f"force>={config.rl.force_threshold:.0%}, "
                f"suggest>={config.rl.suggest_threshold:.0%}, "
                f"<{config.rl.suggest_threshold:.0%}=LLM full choice"
            )
            return ranker

        from .online_policy import OnlinePolicyRanker

        ranker = OnlinePolicyRanker(
            model_path=config.rl.model_path,
            buffer_path=config.rl.buffer_path,
            force_threshold=config.rl.force_threshold,
            suggest_threshold=config.rl.suggest_threshold,
            top_k_suggest=config.rl.top_k_suggest,
            replay_buffer_size=config.rl.replay_buffer_size,
            batch_size=config.rl.batch_size,
            update_frequency=config.rl.update_frequency,
            learning_rate=config.rl.learning_rate,
            hidden_dims=tuple(config.rl.hidden_dims),
            dropout_rate=config.rl.dropout_rate,
            mc_samples=config.rl.mc_samples,
        )
        logger.info(
            f"✓ OnlinePolicyRanker initialized: "
            f"force>={config.rl.force_threshold:.0%}, "
            f"suggest>={config.rl.suggest_threshold:.0%}, "
            f"<{config.rl.suggest_threshold:.0%}=LLM full choice"
        )
        return ranker
    except ImportError as e:
        logger.warning(f"PyTorch not available, RL-primary tool selection disabled: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to initialize OnlinePolicyRanker: {e}", exc_info=True)
        return None
