"""
K functor utilities (Exploration as stochastic convolution).

We implement K as a distribution-level operator:

  p' = (1 - alpha) * p + alpha * Uniform

and log a univariate time series K(t) = KL(p || p').
"""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np


def normalize_probs(x: np.ndarray, *, eps: float = 1e-12) -> np.ndarray:
    """
    Normalize a non-negative vector into a probability simplex.
    Falls back to uniform if sum is non-finite or <= 0.
    """
    a = np.asarray(x, dtype=np.float64).reshape(-1)
    n = int(a.size)
    if n <= 0:
        return np.zeros((0,), dtype=np.float64)
    a = np.where(np.isfinite(a), a, 0.0)
    a = np.maximum(a, 0.0)
    s = float(a.sum())
    if not np.isfinite(s) or s <= eps:
        return np.ones((n,), dtype=np.float64) / float(n)
    return a / s


def mix_with_uniform(p: np.ndarray, *, alpha: float) -> np.ndarray:
    """
    p' = (1-alpha)*p + alpha*U
    """
    p0 = normalize_probs(p)
    n = int(p0.size)
    if n <= 0:
        return p0
    a = float(alpha)
    if not np.isfinite(a):
        a = 0.0
    a = max(0.0, min(1.0, a))
    u = np.ones((n,), dtype=np.float64) / float(n)
    return normalize_probs((1.0 - a) * p0 + a * u)


def kl_divergence(p: np.ndarray, q: np.ndarray, *, eps: float = 1e-12) -> float:
    """
    KL(p || q) for categorical distributions, with clamping for numerical safety.
    Returns a finite float (>= 0).
    """
    p0 = normalize_probs(p)
    q0 = normalize_probs(q)
    if p0.size != q0.size:
        # Incompatible shapes: treat as maximal mismatch in this context.
        return float("inf")
    if p0.size == 0:
        return 0.0
    pe = np.clip(p0, eps, 1.0)
    qe = np.clip(q0, eps, 1.0)
    val = float(np.sum(pe * (np.log(pe) - np.log(qe))))
    # Guard against tiny negative due to floating error.
    if not np.isfinite(val):
        return float("inf")
    return max(0.0, val)


def compute_k_kl(p: np.ndarray, *, alpha: float) -> Tuple[np.ndarray, float]:
    """
    Compute post-K distribution p' and scalar K(t)=KL(p||p').
    """
    p0 = normalize_probs(p)
    p_prime = mix_with_uniform(p0, alpha=float(alpha))
    k = kl_divergence(p0, p_prime)
    return p_prime, float(k)


