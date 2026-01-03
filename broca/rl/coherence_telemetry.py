"""
Coherence telemetry (κ proxy + κ_integrated) with a safe fallback path.

Why this exists:
- `PredictiveInteroception` may be absent/disabled in some runtimes.
- We still want κ and κ_integrated series CSVs to exist by default for debugging/analysis.

Design:
- Maintain singleton trackers (process-local state):
  - `KappaProxyTracker` for κ proxy (0..1)
  - `KappaIntegratedTracker` for exponentially discounted integral I(t)
- Provide a single entrypoint that:
  - updates trackers from a context dict (feature extraction)
  - optionally prefers an externally-computed κ_integrated (e.g., PredictiveInteroception) for logging
  - logs to existing CSV loggers
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CoherenceTelemetrySample:
    kappa: float
    kappa_integrated: float


class CoherenceTelemetry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kappa_tracker = None
        self._kappa_integrated_tracker = None
        self._last: Optional[CoherenceTelemetrySample] = None

    def _ensure_trackers(self) -> None:
        if self._kappa_tracker is None or self._kappa_integrated_tracker is None:
            from .kappa_proxy import KappaProxyTracker
            from .kappa_integrated import KappaIntegratedTracker

            if self._kappa_tracker is None:
                self._kappa_tracker = KappaProxyTracker()
            if self._kappa_integrated_tracker is None:
                self._kappa_integrated_tracker = KappaIntegratedTracker()

    def last(self) -> Optional[CoherenceTelemetrySample]:
        return self._last

    def observe(
        self,
        *,
        kappa: float,
        kappa_integrated: Optional[float] = None,
        now: Optional[float] = None,
    ) -> CoherenceTelemetrySample:
        """
        Update trackers with a raw κ observation and log.

        If `kappa_integrated` is provided, it is preferred for logging (source-of-truth),
        but the fallback integrator still advances on κ so it can take over when needed.
        """
        with self._lock:
            self._ensure_trackers()
            try:
                k = float(kappa)
            except Exception:
                k = 0.0
            if not (k == k) or k in (float("inf"), float("-inf")):
                k = 0.0
            k = max(0.0, min(1.0, k))

            # Advance fallback integrator.
            i_fallback = float(self._kappa_integrated_tracker.update(k, now=now))

            i_log = i_fallback
            if kappa_integrated is not None:
                try:
                    i_override = float(kappa_integrated)
                except Exception:
                    i_override = None
                else:
                    if (i_override == i_override) and i_override not in (float("inf"), float("-inf")):
                        i_log = float(i_override)

            # Log series.
            from .kappa_logger import get_kappa_series_logger
            from .kappa_integrated_logger import get_kappa_integrated_logger

            get_kappa_series_logger().log_kappa(k)
            get_kappa_integrated_logger().log_value(i_log)

            s = CoherenceTelemetrySample(kappa=float(k), kappa_integrated=float(i_log))
            self._last = s
            return s

    def update_from_context(
        self,
        context: Optional[Dict[str, Any]],
        *,
        tool_name: str = "",
        success: Optional[bool] = None,
        now: Optional[float] = None,
        kappa_integrated_override: Optional[float] = None,
    ) -> CoherenceTelemetrySample:
        """
        Update from a context dict (feature extraction) and log.
        """
        ctx = context or {}
        with self._lock:
            self._ensure_trackers()
            from .features import extract_state_features, BASE_STATE_DIM

            z = extract_state_features(ctx, input_dim=int(BASE_STATE_DIM))
            rl_s = ctx.get("rl_signals") if isinstance(ctx, dict) else None
            parts = self._kappa_tracker.update(
                z_t=z,
                rl_signals=rl_s if isinstance(rl_s, dict) else None,
                success=success,
                tool_name=str(tool_name or ""),
            )
            kappa_val = float(parts.get("kappa", 0.0))
        # Defer to observe() for locking + logging + integrator advance.
        return self.observe(kappa=kappa_val, kappa_integrated=kappa_integrated_override, now=now)


_GLOBAL: Optional[CoherenceTelemetry] = None
_GLOBAL_LOCK = threading.Lock()


def get_coherence_telemetry() -> CoherenceTelemetry:
    global _GLOBAL
    with _GLOBAL_LOCK:
        if _GLOBAL is None:
            _GLOBAL = CoherenceTelemetry()
        return _GLOBAL


def log_from_context(
    context: Optional[Dict[str, Any]],
    *,
    tool_name: str = "",
    success: Optional[bool] = None,
    now: Optional[float] = None,
    kappa_integrated_override: Optional[float] = None,
) -> CoherenceTelemetrySample:
    """
    Convenience wrapper for callers that just want "do the thing".
    """
    if now is None:
        now = time.time()
    return get_coherence_telemetry().update_from_context(
        context,
        tool_name=tool_name,
        success=success,
        now=now,
        kappa_integrated_override=kappa_integrated_override,
    )


