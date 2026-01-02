"""
Regression tests for PPO training health metrics.

Requirements from AGENTS.md:
- Property-based testing (via Hypothesis)
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

try:
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="PyTorch not available")


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(data=st.data())
def test_categorical_kl_from_logits_is_nonnegative(data):
    from broca.rl.ppo_policy import categorical_kl_from_logits

    batch = data.draw(st.integers(min_value=1, max_value=8))
    dim = data.draw(st.integers(min_value=2, max_value=12))
    f = st.floats(min_value=-8, max_value=8, allow_nan=False, allow_infinity=False, width=32)

    old = np.array(
        data.draw(
            st.lists(
                st.lists(f, min_size=dim, max_size=dim),
                min_size=batch,
                max_size=batch,
            )
        ),
        dtype=np.float32,
    )
    new = np.array(
        data.draw(
            st.lists(
                st.lists(f, min_size=dim, max_size=dim),
                min_size=batch,
                max_size=batch,
            )
        ),
        dtype=np.float32,
    )

    old_t = torch.tensor(old)
    new_t = torch.tensor(new)

    same = categorical_kl_from_logits(old_t, old_t)
    assert tuple(same.shape) == (batch,)
    assert torch.isfinite(same).all()
    assert float(torch.max(torch.abs(same)).item()) <= 1e-6

    kl = categorical_kl_from_logits(old_t, new_t)
    assert tuple(kl.shape) == (batch,)
    assert torch.isfinite(kl).all()
    assert float(torch.min(kl).item()) >= -1e-6

