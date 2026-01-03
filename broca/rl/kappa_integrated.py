"""
Exponentially discounted integral of kappa(t):

  kappa_integrated(T) = ∫_0^T kappa(t) * exp(-lambda*(T-t)) dt

This satisfies the ODE:
  dI/dT = kappa(T) - lambda * I

Discrete-time exact update assuming kappa is piecewise-constant over (t_prev, t]:
  I_t = exp(-lambda*dt) * I_prev + kappa_t * (1 - exp(-lambda*dt)) / lambda

For lambda -> 0, it reduces to the plain integral:
  I_t = I_prev + kappa_t * dt
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import time
import math


@dataclass
class KappaIntegratedConfig:
    lam: float = 0.5  # lambda
    dt_max: float = 60.0  # clamp dt to avoid giant jumps on pauses/restarts


class KappaIntegratedTracker:
    def __init__(self, cfg: Optional[KappaIntegratedConfig] = None) -> None:
        self.cfg = cfg or KappaIntegratedConfig()
        self._last_t: Optional[float] = None
        self._I: float = 0.0

    @property
    def value(self) -> float:
        return float(self._I)

    def update(self, kappa_t: float, *, now: Optional[float] = None) -> float:
        t = float(now) if now is not None else time.time()
        if self._last_t is None:
            self._last_t = t
            # No dt yet; treat as instantaneous sample with dt=0.
            return float(self._I)

        dt = max(0.0, float(t) - float(self._last_t))
        if not math.isfinite(dt):
            dt = 0.0
        dt = min(dt, float(self.cfg.dt_max))

        lam = float(self.cfg.lam)
        if not math.isfinite(lam) or lam < 0.0:
            lam = 0.0

        try:
            k = float(kappa_t)
        except Exception:
            k = 0.0
        if not math.isfinite(k):
            k = 0.0
        # kappa is defined in [0,1]; clamp for safety.
        k = max(0.0, min(1.0, k))

        if lam <= 0.0:
            self._I = float(self._I) + float(k) * float(dt)
        else:
            decay = math.exp(-lam * dt)
            # exact discretization under piecewise-constant kappa on the interval
            gain = (1.0 - decay) / lam
            self._I = float(decay) * float(self._I) + float(k) * float(gain)

        self._last_t = t
        return float(self._I)


