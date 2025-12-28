"""
Damping pipeline implementation.

Applies ordered transforms (validation, clamping, outlier rejection, EMA,
deadband, rate limiting, hysteresis) to signal updates.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Optional

from .profiles import DampingProfile
from ..signals.schema import SignalSpec

logger = logging.getLogger(__name__)


class DampingPipeline:
    """Pipeline for damping signal updates."""
    
    def __init__(self, profile: DampingProfile, signal_spec: SignalSpec):
        """
        Initialize damping pipeline.
        
        Args:
            profile: Damping profile to use
            signal_spec: Signal specification for validation
        """
        self._profile = profile
        self._signal_spec = signal_spec
        self._last_value: Optional[float] = None
        self._last_timestamp: Optional[datetime] = None
        self._hysteresis_state: Optional[bool] = None  # None = unknown, True/False = ON/OFF
        
    def apply(
        self,
        raw_value: float | int | bool | str,
        current_value: Optional[float | int | bool | str],
        timestamp: datetime
    ) -> float | int | bool | str:
        """
        Apply damping pipeline to raw value.
        
        Pipeline order:
        1. Validate (type/range check)
        2. Clamp hard bounds
        3. Outlier reject (optional)
        4. EMA/low-pass (tau-based or alpha-based)
        5. Deadband
        6. Rate limiting (slew rate)
        7. Hysteresis (for boolean triggers)
        8. Return damped value
        
        Args:
            raw_value: Raw input value
            current_value: Current damped value (if any)
            timestamp: Current timestamp
            
        Returns:
            Damped value
        """
        # Use current_value as starting point if provided, else use last_value
        if current_value is not None:
            x_old = current_value
        else:
            x_old = self._last_value if self._last_value is not None else self._signal_spec.default
        
        # Step 1: Validate (type/range check)
        if not self._signal_spec.validate_value(raw_value):
            logger.warning(f"Invalid value {raw_value} for signal {self._signal_spec.name}, clamping")
            raw_value = self._signal_spec.clamp_value(raw_value)
        
        # Convert to numeric for processing (preserve type for categorical/bool)
        x_raw = raw_value
        if isinstance(raw_value, bool):
            x_raw_num = 1.0 if raw_value else 0.0
            x_old_num = 1.0 if x_old else 0.0
        elif isinstance(raw_value, str):
            # Categorical - no numeric processing
            self._last_value = raw_value
            self._last_timestamp = timestamp
            return raw_value
        else:
            x_raw_num = float(raw_value)
            x_old_num = float(x_old)
        
        # Step 2: Clamp hard bounds
        if self._profile.clamp_min is not None:
            x_raw_num = max(self._profile.clamp_min, x_raw_num)
        if self._profile.clamp_max is not None:
            x_raw_num = min(self._profile.clamp_max, x_raw_num)
        
        # Step 3: Outlier reject (optional)
        if self._last_value is not None and isinstance(self._last_value, (int, float)):
            x_damped = self._reject_outliers(x_raw_num, x_old_num)
        else:
            x_damped = x_raw_num
        
        # Step 4: EMA/low-pass
        if self._last_timestamp is not None:
            dt = (timestamp - self._last_timestamp).total_seconds()
            dt = max(0.0, dt)  # Ensure non-negative
        else:
            dt = 0.0
        
        if dt > 0 and self._last_value is not None:
            x_damped = self._apply_ema(x_damped, x_old_num, dt)
        
        # Step 5: Deadband
        if abs(x_damped - x_old_num) < self._profile.deadband:
            x_damped = x_old_num
        
        # Step 6: Rate limiting (slew rate)
        if self._profile.rate_limit is not None and dt > 0:
            max_step = self._profile.rate_limit * dt
            delta = x_damped - x_old_num
            delta_clamped = max(-max_step, min(max_step, delta))
            x_damped = x_old_num + delta_clamped
        
        # Step 7: Hysteresis (for boolean-like triggers)
        if self._profile.hysteresis_on is not None and self._profile.hysteresis_off is not None:
            x_damped = self._apply_hysteresis(x_damped)
        
        # Convert back to original type
        if isinstance(raw_value, bool):
            result = x_damped > 0.5
        elif isinstance(raw_value, int):
            result = int(round(x_damped))
        else:
            result = x_damped
        
        # Update state
        self._last_value = result
        self._last_timestamp = timestamp
        
        return result
    
    def _reject_outliers(self, x_raw: float, x_old: float) -> float:
        """Reject outliers using z-score or percentile clipping."""
        # Simple outlier rejection: if z-score threshold specified, use it
        # For now, just pass through (can be enhanced with history-based stats)
        if self._profile.outlier_reject_zscore is not None:
            # Would need history to compute z-score properly
            # For now, skip if change is too large relative to current value
            if x_old != 0:
                z_score_approx = abs((x_raw - x_old) / x_old)
                if z_score_approx > self._profile.outlier_reject_zscore:
                    logger.debug(f"Outlier rejected: z_score_approx={z_score_approx:.3f}")
                    return x_old
        return x_raw
    
    def _apply_ema(self, x_raw: float, x_old: float, dt: float) -> float:
        """Apply exponential moving average (tau-based or alpha-based)."""
        if self._profile.smoothing_tau is not None:
            # Tau-based EMA: alpha_dt = 1 - exp(-dt/tau)
            if dt > 0 and self._profile.smoothing_tau > 0:
                alpha_dt = 1.0 - math.exp(-dt / self._profile.smoothing_tau)
            else:
                alpha_dt = 1.0  # Instant update if dt=0 or tau=0
            x_new = x_old + alpha_dt * (x_raw - x_old)
        elif self._profile.smoothing_alpha is not None:
            # Alpha-based EMA: simple exponential smoothing
            alpha = self._profile.smoothing_alpha
            x_new = x_old + alpha * (x_raw - x_old)
        else:
            # No smoothing
            x_new = x_raw
        return x_new
    
    def _apply_hysteresis(self, x: float) -> float:
        """Apply hysteresis for boolean-like triggers."""
        if self._hysteresis_state is None:
            # Initialize state based on current value
            self._hysteresis_state = x >= ((self._profile.hysteresis_on + self._profile.hysteresis_off) / 2)
        
        if self._hysteresis_state:
            # Currently ON: turn OFF if below off threshold
            if x < self._profile.hysteresis_off:
                self._hysteresis_state = False
                return 0.0
            return 1.0
        else:
            # Currently OFF: turn ON if above on threshold
            if x > self._profile.hysteresis_on:
                self._hysteresis_state = True
                return 1.0
            return 0.0

