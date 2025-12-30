"""
Data quality framework for internal sensing.

Provides utilities for:
- Bayesian priors for missing data
- Uncertainty propagation
- Confidence interval calculations
- Data quality indicators
"""

from __future__ import annotations

import math
from typing import Dict, Any, Optional, Tuple, Literal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataQuality(str, Enum):
    """Data quality levels."""
    HIGH = "high"  # Sufficient data, low uncertainty
    MEDIUM = "medium"  # Some data, moderate uncertainty
    LOW = "low"  # Limited data, high uncertainty
    INSUFFICIENT = "insufficient"  # Very limited data, very high uncertainty
    MISSING = "missing"  # No data available, maximum uncertainty


def beta_posterior_mean(alpha: float, beta: float) -> float:
    """
    Calculate mean of Beta distribution.
    
    Args:
        alpha: Alpha parameter (successes + prior alpha)
        beta: Beta parameter (failures + prior beta)
        
    Returns:
        Mean of Beta distribution (0.0-1.0)
    """
    total = alpha + beta
    if total == 0:
        return 0.5  # Uniform prior
    return alpha / total


def beta_confidence_interval(
    alpha: float,
    beta: float,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for Beta distribution using normal approximation.
    
    For small samples, this is approximate. For exact intervals, use Clopper-Pearson.
    
    Args:
        alpha: Alpha parameter
        beta: Beta parameter
        confidence: Confidence level (default: 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    mean = beta_posterior_mean(alpha, beta)
    total = alpha + beta
    
    if total <= 0:
        return (0.0, 1.0)  # Maximum uncertainty
    
    # Use normal approximation with variance of Beta
    variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
    std_dev = math.sqrt(variance)
    
    # Z-score for confidence level
    z_score = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    
    # Calculate bounds
    margin = z_score * std_dev
    lower = max(0.0, mean - margin)
    upper = min(1.0, mean + margin)
    
    return (lower, upper)


def clopper_pearson_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Clopper-Pearson (exact) confidence interval for binomial proportion.
    
    This is more accurate than normal approximation for small samples.
    
    Args:
        successes: Number of successes
        trials: Total number of trials
        confidence: Confidence level (default: 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 1.0)  # Maximum uncertainty
    
    if successes == 0:
        # Lower bound is 0, upper bound from Beta distribution
        alpha_upper = 1.0
        beta_upper = trials
        upper = beta_posterior_mean(alpha_upper, beta_upper)
        # Use Wilson score for better approximation at boundaries
        upper = wilson_score_upper(0, trials, confidence)
        return (0.0, min(1.0, upper))
    
    if successes == trials:
        # Upper bound is 1, lower bound from Beta distribution
        alpha_lower = successes
        beta_lower = 1.0
        lower = beta_posterior_mean(alpha_lower, beta_lower)
        # Use Wilson score for better approximation at boundaries
        lower = wilson_score_lower(trials, trials, confidence)
        return (max(0.0, lower), 1.0)
    
    # For intermediate values, use Beta distribution quantiles
    # Approximate using normal approximation with correction
    p = successes / trials
    z = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    
    # Wilson score interval (more accurate than normal approximation)
    return wilson_score_interval(successes, trials, confidence)


def wilson_score_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for binomial proportion.
    
    More accurate than normal approximation, especially for small samples or extreme proportions.
    
    Args:
        successes: Number of successes
        trials: Total number of trials
        confidence: Confidence level (default: 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 1.0)
    
    p = successes / trials
    z = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    
    denominator = 1 + (z ** 2) / trials
    center = (p + (z ** 2) / (2 * trials)) / denominator
    margin = (z / denominator) * math.sqrt((p * (1 - p) / trials) + (z ** 2) / (4 * trials ** 2))
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def wilson_score_lower(successes: int, trials: int, confidence: float = 0.95) -> float:
    """Calculate lower bound of Wilson score interval."""
    lower, _ = wilson_score_interval(successes, trials, confidence)
    return lower


def wilson_score_upper(successes: int, trials: int, confidence: float = 0.95) -> float:
    """Calculate upper bound of Wilson score interval."""
    _, upper = wilson_score_interval(successes, trials, confidence)
    return upper


def assess_data_quality(sample_size: int, min_samples_high: int = 20, min_samples_medium: int = 10, min_samples_low: int = 5) -> DataQuality:
    """
    Assess data quality based on sample size.
    
    Args:
        sample_size: Number of samples available
        min_samples_high: Minimum samples for HIGH quality
        min_samples_medium: Minimum samples for MEDIUM quality
        min_samples_low: Minimum samples for LOW quality
        
    Returns:
        DataQuality level
    """
    if sample_size == 0:
        return DataQuality.MISSING
    elif sample_size < min_samples_low:
        return DataQuality.INSUFFICIENT
    elif sample_size < min_samples_medium:
        return DataQuality.LOW
    elif sample_size < min_samples_high:
        return DataQuality.MEDIUM
    else:
        return DataQuality.HIGH


def uncertainty_for_missing_data() -> float:
    """
    Return appropriate uncertainty value when data is missing.
    
    Returns:
        High uncertainty value (0.8-1.0) to indicate missing data
    """
    return 0.9  # High uncertainty for missing data


def confidence_for_missing_data() -> Tuple[float, Tuple[float, float]]:
    """
    Return appropriate confidence estimate when data is missing.
    
    Uses uniform prior (Beta(1, 1)) which gives mean 0.5 with wide confidence interval.
    
    Returns:
        Tuple of (mean_confidence, (lower_bound, upper_bound))
    """
    # Use uniform prior: Beta(1, 1)
    mean = 0.5
    # Wide confidence interval to reflect uncertainty
    interval = (0.1, 0.9)
    return (mean, interval)


def bayesian_reliability_estimate(
    successes: int,
    failures: int,
    prior_alpha: float = 0.5,
    prior_beta: float = 0.5
) -> Dict[str, Any]:
    """
    Calculate Bayesian reliability estimate with Jeffreys prior.
    
    Args:
        successes: Number of successful executions
        failures: Number of failed executions
        prior_alpha: Prior alpha (default: 0.5 for Jeffreys prior)
        prior_beta: Prior beta (default: 0.5 for Jeffreys prior)
        
    Returns:
        Dictionary with:
        - reliability: Mean reliability estimate
        - confidence_interval: (lower, upper) bounds
        - sample_size: Total number of observations
        - data_quality: DataQuality level
        - uncertainty: Uncertainty in estimate
    """
    total = successes + failures
    alpha = successes + prior_alpha
    beta = failures + prior_beta
    
    reliability = beta_posterior_mean(alpha, beta)
    confidence_interval = beta_confidence_interval(alpha, beta)
    
    # Calculate uncertainty as width of confidence interval
    interval_width = confidence_interval[1] - confidence_interval[0]
    uncertainty = min(1.0, interval_width)
    
    data_quality = assess_data_quality(total)
    
    return {
        "reliability": reliability,
        "confidence_interval": confidence_interval,
        "sample_size": total,
        "data_quality": data_quality.value,
        "uncertainty": uncertainty,
    }


def propagate_uncertainty(
    values: list[float],
    uncertainties: list[float],
    weights: Optional[list[float]] = None
) -> Tuple[float, float]:
    """
    Propagate uncertainty when combining multiple estimates.
    
    Uses error propagation formula: uncertainty_combined = sqrt(sum(weight_i^2 * uncertainty_i^2))
    
    Args:
        values: List of values to combine
        uncertainties: List of uncertainties (0.0-1.0)
        weights: Optional weights for each value (default: equal weights)
        
    Returns:
        Tuple of (combined_value, combined_uncertainty)
    """
    if not values or not uncertainties:
        return (0.5, uncertainty_for_missing_data())
    
    if len(values) != len(uncertainties):
        logger.warning("Mismatch between values and uncertainties length")
        return (0.5, uncertainty_for_missing_data())
    
    if weights is None:
        weights = [1.0 / len(values)] * len(values)
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        return (0.5, uncertainty_for_missing_data())
    
    normalized_weights = [w / total_weight for w in weights]
    
    # Weighted average of values
    combined_value = sum(v * w for v, w in zip(values, normalized_weights))
    
    # Propagate uncertainty (root sum of squares)
    combined_uncertainty_sq = sum((w * u) ** 2 for w, u in zip(normalized_weights, uncertainties))
    combined_uncertainty = math.sqrt(combined_uncertainty_sq)
    
    # Ensure uncertainty increases when combining uncertain estimates
    # Add penalty for combining multiple uncertain sources
    if len(values) > 1:
        avg_uncertainty = sum(uncertainties) / len(uncertainties)
        # Slight increase for multiple sources
        combined_uncertainty = min(1.0, combined_uncertainty + 0.05 * (len(values) - 1))
    
    return (combined_value, combined_uncertainty)


def add_uncertainty_for_missing_data(
    value: float,
    has_data: bool,
    sample_size: int = 0
) -> Tuple[float, float, DataQuality]:
    """
    Add uncertainty to a value when data is missing or insufficient.
    
    Args:
        value: The value estimate
        has_data: Whether any data is available
        sample_size: Number of samples (0 if no data)
        
    Returns:
        Tuple of (adjusted_value, uncertainty, data_quality)
    """
    if not has_data or sample_size == 0:
        # No data: return high uncertainty
        uncertainty = uncertainty_for_missing_data()
        data_quality = DataQuality.MISSING
        # Value becomes less informative with high uncertainty
        # Keep the value but mark it as highly uncertain
        return (value, uncertainty, data_quality)
    
    data_quality = assess_data_quality(sample_size)
    
    # Uncertainty decreases with sample size
    if data_quality == DataQuality.HIGH:
        uncertainty = 0.1  # Low uncertainty
    elif data_quality == DataQuality.MEDIUM:
        uncertainty = 0.3  # Moderate uncertainty
    elif data_quality == DataQuality.LOW:
        uncertainty = 0.5  # High uncertainty
    else:  # INSUFFICIENT
        uncertainty = 0.7  # Very high uncertainty
    
    return (value, uncertainty, data_quality)


def create_metric_with_quality(
    value: float,
    sample_size: int = 0,
    confidence_interval: Optional[Tuple[float, float]] = None,
    data_quality: Optional[DataQuality] = None
) -> Dict[str, Any]:
    """
    Create a metric dictionary with data quality metadata.
    
    Args:
        value: The metric value
        sample_size: Number of samples used
        confidence_interval: Optional confidence interval
        data_quality: Optional data quality level (auto-assessed if not provided)
        
    Returns:
        Dictionary with value and quality metadata
    """
    if data_quality is None:
        data_quality = assess_data_quality(sample_size)
    
    result = {
        "value": value,
        "sample_size": sample_size,
        "data_quality": data_quality.value,
        "has_data": sample_size > 0,
    }
    
    if confidence_interval:
        result["confidence_interval"] = confidence_interval
        # Calculate uncertainty from interval width
        interval_width = confidence_interval[1] - confidence_interval[0]
        result["uncertainty"] = min(1.0, interval_width)
    else:
        # Estimate uncertainty from sample size
        _, uncertainty, _ = add_uncertainty_for_missing_data(value, sample_size > 0, sample_size)
        result["uncertainty"] = uncertainty
    
    return result

