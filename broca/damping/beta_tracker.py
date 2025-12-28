"""
Beta posterior tracker for toolchain success rates.

Uses Bayesian Beta distribution to track success rates with proper
damping and uncertainty quantification.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BetaSuccessTracker:
    """
    Beta posterior tracker for success rates.
    
    Uses Beta distribution (Beta(a, b)) where:
    - a = prior_a + successes
    - b = prior_b + failures
    
    Provides:
    - Mean (a/(a+b)) as damped success estimate
    - Variance as noise/uncertainty signal
    """
    
    def __init__(
        self,
        prior_a: float = 2.0,
        prior_b: float = 2.0
    ):
        """
        Initialize Beta tracker.
        
        Args:
            prior_a: Prior alpha parameter (default: 2.0, mild prior)
            prior_b: Prior beta parameter (default: 2.0, mild prior)
        """
        self._prior_a = prior_a
        self._prior_b = prior_b
        self._a = prior_a  # Current alpha (prior + successes)
        self._b = prior_b  # Current beta (prior + failures)
        
        logger.debug(f"Initialized BetaSuccessTracker with prior Beta({prior_a}, {prior_b})")
    
    def record_success(self) -> None:
        """Record a successful event."""
        self._a += 1.0
        logger.debug(f"Recorded success: Beta({self._a:.2f}, {self._b:.2f})")
    
    def record_failure(self) -> None:
        """Record a failed event."""
        self._b += 1.0
        logger.debug(f"Recorded failure: Beta({self._a:.2f}, {self._b:.2f})")
    
    def get_mean(self) -> float:
        """
        Get mean of Beta distribution (damped success estimate).
        
        Returns:
            Mean = a/(a+b)
        """
        if self._a + self._b == 0:
            return 0.5  # Default to neutral
        
        return self._a / (self._a + self._b)
    
    def get_variance(self) -> float:
        """
        Get variance of Beta distribution.
        
        Returns:
            Variance = ab/((a+b)^2 * (a+b+1))
        """
        total = self._a + self._b
        if total == 0:
            return 0.25  # Maximum variance for uniform prior
        
        variance = (self._a * self._b) / ((total ** 2) * (total + 1))
        return variance
    
    def get_noise_estimate(self) -> float:
        """
        Get noise estimate (variance as noise signal).
        
        Returns:
            Variance (higher = more uncertainty/noise)
        """
        return self.get_variance()
    
    def get_total_observations(self) -> int:
        """
        Get total number of observations (successes + failures).
        
        Returns:
            Total observations (excluding prior)
        """
        return int((self._a - self._prior_a) + (self._b - self._prior_b))
    
    def reset(self) -> None:
        """Reset tracker to prior state."""
        self._a = self._prior_a
        self._b = self._prior_b
        logger.debug("Reset BetaSuccessTracker to prior state")
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "prior_a": self._prior_a,
            "prior_b": self._prior_b,
            "a": self._a,
            "b": self._b,
            "mean": self.get_mean(),
            "variance": self.get_variance(),
            "total_observations": self.get_total_observations()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BetaSuccessTracker":
        """Create tracker from dictionary representation."""
        tracker = cls(
            prior_a=data.get("prior_a", 2.0),
            prior_b=data.get("prior_b", 2.0)
        )
        tracker._a = data.get("a", tracker._prior_a)
        tracker._b = data.get("b", tracker._prior_b)
        return tracker

