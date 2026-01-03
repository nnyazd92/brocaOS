from __future__ import annotations

from hypothesis import given, strategies as st
import numpy as np

from broca.rl.k_functor import compute_k_kl, normalize_probs


@given(
    n=st.integers(min_value=1, max_value=50),
    alpha=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    vals=st.lists(st.floats(allow_nan=True, allow_infinity=True, width=32), min_size=1, max_size=50),
)
def test_k_kl_is_finite_and_nonnegative(n, alpha, vals):
    # Force vector length n
    x = np.array((vals + [0.0] * n)[:n], dtype=np.float64)
    p = normalize_probs(x)
    p2, k = compute_k_kl(p, alpha=float(alpha))
    assert p2.shape == p.shape
    assert 0.999999 <= float(p2.sum()) <= 1.000001
    assert k == k  # not NaN
    assert k >= 0.0


