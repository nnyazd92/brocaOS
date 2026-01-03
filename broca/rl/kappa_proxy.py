"""
Computable proxy for the coherence functional kappa.

We approximate "closed-loop idempotence / contractivity" from observed trajectories
in a stable feature embedding z_t (we use extract_state_features outputs).

Proxy definition (online):
  rho_t = ||z_t - z_{t-1}|| / (||z_{t-1} - z_{t-2}|| + eps)
  lambda_hat_t = EMA(rho_t)
  kappa_contr = exp(-beta * max(0, lambda_hat_t - 1))

Loop-error proxy (conflict / prediction error / instability):
  e_t = w_d * D + w_c*(1-C) + w_s*S + w_f*(1-success) + w_x*churn
  e_hat_t = EMA(e_t)
  kappa_err = exp(-gamma * e_hat_t)

Final:
  kappa = clamp01(kappa_contr * kappa_err)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


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


def _ema(prev: float, x: float, alpha: float) -> float:
    a = float(alpha)
    a = max(0.0, min(1.0, a))
    return (1.0 - a) * float(prev) + a * float(x)


@dataclass
class KappaProxyConfig:
    eps: float = 1e-6
    ema_alpha_lambda: float = 0.2
    ema_alpha_err: float = 0.2
    beta: float = 2.0
    gamma: float = 2.0
    # Loop-error weights (all inputs expected in [0,1])
    w_dissonance: float = 0.35
    w_incoherence: float = 0.25
    w_surprise: float = 0.15
    w_failure: float = 0.20
    w_churn: float = 0.05


class KappaProxyTracker:
    """
    Online tracker producing kappa_proxy(t) from:
    - z_t: feature vector (np.ndarray)
    - rl_signals: dict (optional)
    - success: bool (optional)
    - tool_name: str (optional, for churn)
    """

    def __init__(self, cfg: Optional[KappaProxyConfig] = None) -> None:
        self.cfg = cfg or KappaProxyConfig()
        self._z_prev2: Optional[np.ndarray] = None
        self._z_prev1: Optional[np.ndarray] = None
        self._lambda_hat: float = 1.0
        self._e_hat: float = 0.0
        self._last_tool: str = ""

    def update(
        self,
        *,
        z_t: np.ndarray,
        rl_signals: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        tool_name: Optional[str] = None,
    ) -> Dict[str, float]:
        z = np.asarray(z_t, dtype=np.float64).reshape(-1)
        if z.size == 0:
            return {"kappa": 0.0, "kappa_contr": 0.0, "kappa_err": 0.0, "lambda_hat": float(self._lambda_hat), "e_hat": float(self._e_hat)}

        # Contractivity ratio
        rho = 1.0
        if self._z_prev1 is not None and self._z_prev2 is not None:
            d1 = float(np.linalg.norm(z - self._z_prev1))
            d0 = float(np.linalg.norm(self._z_prev1 - self._z_prev2))
            rho = d1 / (d0 + float(self.cfg.eps))
            if not np.isfinite(rho) or rho <= 0:
                rho = 1.0

        self._lambda_hat = _ema(self._lambda_hat, rho, self.cfg.ema_alpha_lambda)
        kappa_contr = float(np.exp(-float(self.cfg.beta) * max(0.0, float(self._lambda_hat) - 1.0)))

        # Loop-error term
        rl = rl_signals if isinstance(rl_signals, dict) else {}
        # Prefer varnorm keys when present
        d = _clamp01(_safe_float(rl.get("dissonance_reward_varnorm", rl.get("dissonance_reward", 0.5)), 0.5))
        c = _clamp01(_safe_float(rl.get("coherence_reward_varnorm", rl.get("coherence_reward", 0.5)), 0.5))
        s = _clamp01(_safe_float(rl.get("surprise_reward_varnorm", rl.get("surprise_reward", 0.5)), 0.5))
        fail = 0.0
        if success is not None:
            fail = 0.0 if bool(success) else 1.0
        churn = 0.0
        tn = str(tool_name or "")
        if tn and self._last_tool:
            churn = 0.0 if tn == self._last_tool else 1.0

        e = (
            float(self.cfg.w_dissonance) * float(d)
            + float(self.cfg.w_incoherence) * (1.0 - float(c))
            + float(self.cfg.w_surprise) * float(s)
            + float(self.cfg.w_failure) * float(fail)
            + float(self.cfg.w_churn) * float(churn)
        )
        e = _clamp01(e)
        self._e_hat = _ema(self._e_hat, e, self.cfg.ema_alpha_err)
        kappa_err = float(np.exp(-float(self.cfg.gamma) * float(self._e_hat)))

        kappa = _clamp01(float(kappa_contr) * float(kappa_err))

        # roll state
        self._z_prev2 = self._z_prev1
        self._z_prev1 = z.copy()
        if tn:
            self._last_tool = tn

        return {
            "kappa": float(kappa),
            "kappa_contr": float(kappa_contr),
            "kappa_err": float(kappa_err),
            "lambda_hat": float(self._lambda_hat),
            "e_hat": float(self._e_hat),
        }


