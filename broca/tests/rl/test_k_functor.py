from __future__ import annotations

import numpy as np

from broca.rl.k_functor import compute_k_kl, kl_divergence, mix_with_uniform, normalize_probs


def test_normalize_probs_falls_back_to_uniform():
    p = normalize_probs(np.array([0.0, 0.0, 0.0]))
    assert p.shape == (3,)
    assert abs(float(p.sum()) - 1.0) < 1e-9


def test_k_alpha_zero_is_identity():
    p = np.array([0.1, 0.2, 0.7], dtype=np.float64)
    p2, k = compute_k_kl(p, alpha=0.0)
    assert np.allclose(normalize_probs(p), p2, atol=1e-12)
    assert abs(float(k) - 0.0) < 1e-12


def test_k_alpha_one_mixes_to_uniform():
    p = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    p2 = mix_with_uniform(p, alpha=1.0)
    assert np.allclose(p2, np.ones(3) / 3.0, atol=1e-12)


def test_kl_nonnegative():
    p = np.array([0.25, 0.75], dtype=np.float64)
    q = np.array([0.5, 0.5], dtype=np.float64)
    kl = kl_divergence(p, q)
    assert kl >= 0.0


