"""
Regression: affective valence must be routed into RL signals as:
- a reward component (valence_reward in [0,1])
- a state feature (available via rl_signals dict / feature extraction)
"""

from __future__ import annotations

from broca.reasoning.reward_normalizer import RewardVarianceNormalizer
from broca.reasoning.rl_signals import RLSignalAggregator


def test_valence_reward_mapping_and_bounds(tmp_path):
    rn = RewardVarianceNormalizer(
        storage_path=str(tmp_path / "norm.json"),
        enabled=True,
        min_samples=1,
        persist_interval_s=0.0,
    )
    agg = RLSignalAggregator(weight_valence=0.25, reward_normalizer=rn)

    metrics = agg.compute_signals(
        affective_state={"valence": -1.0, "data_quality": {"valence": "high"}},
        allow_estimation=False,
    )
    assert metrics.valence_raw == -1.0
    assert metrics.valence_reward == 0.0
    assert 0.0 <= metrics.valence_reward_varnorm <= 1.0
    assert 0.0 <= metrics.composite_reward <= 1.0

    metrics2 = agg.compute_signals(
        affective_state={"valence": 1.0, "data_quality": {"valence": "high"}},
        allow_estimation=False,
    )
    assert metrics2.valence_raw == 1.0
    assert metrics2.valence_reward == 1.0
    assert 0.0 <= metrics2.valence_reward_varnorm <= 1.0
    assert 0.0 <= metrics2.composite_reward <= 1.0

