"""
Property-based tests for running-variance normalization of reward components.
"""

from __future__ import annotations

import math

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from broca.reasoning.reward_normalizer import RewardVarianceNormalizer


@given(
    xs=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=200),
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reward_variance_normalizer_outputs_bounded_and_finite(tmp_path, xs):
    n = RewardVarianceNormalizer(
        storage_path=str(tmp_path / "norm.json"),
        enabled=True,
        min_samples=1,
        persist_interval_s=0.0,
    )

    for x in xs:
        z, varnorm = n.normalize("dissonance_reward", float(x))
        assert math.isfinite(z)
        assert math.isfinite(varnorm)
        assert 0.0 <= varnorm <= 1.0


def test_reward_variance_normalizer_persists_stats(tmp_path):
    path = tmp_path / "norm.json"
    n1 = RewardVarianceNormalizer(storage_path=str(path), enabled=True, min_samples=1, persist_interval_s=0.0)
    for x in [0.1, 0.2, 0.3]:
        _ = n1.normalize("surprise_reward", x)

    n2 = RewardVarianceNormalizer(storage_path=str(path), enabled=True, min_samples=1, persist_interval_s=0.0)
    snap = n2.snapshot()
    assert snap["stats"]["surprise_reward"]["n"] >= 3
