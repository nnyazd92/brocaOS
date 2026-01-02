"""
Property-based tests for RL signals.

Tests signal bounds, weight constraints, and invariants.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone

from broca.reasoning.rl_signals import RLSignalMetrics


class TestRLSignalProperties:
    """Property-based tests for RL signal properties."""
    
    @settings(deadline=None)
    @given(
        dissonance=st.floats(min_value=0.0, max_value=1.0),
        surprise=st.floats(min_value=0.0, max_value=1.0),
        curiosity=st.floats(min_value=0.0, max_value=1.0),
        info_gain=st.floats(min_value=0.0, max_value=1.0),
        coherence=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_all_signals_bounded(self, dissonance, surprise, curiosity, info_gain, coherence):
        """Property: All signal rewards are bounded [0, 1]."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=dissonance,
            surprise_reward=surprise,
            curiosity_reward=curiosity,
            information_gain_reward=info_gain,
            coherence_reward=coherence,
        )
        
        composite = metrics.compute_composite()
        
        # All individual signals should be bounded
        assert 0.0 <= metrics.dissonance_reward <= 1.0
        assert 0.0 <= metrics.surprise_reward <= 1.0
        assert 0.0 <= metrics.curiosity_reward <= 1.0
        assert 0.0 <= metrics.information_gain_reward <= 1.0
        assert 0.0 <= metrics.coherence_reward <= 1.0
        
        # Composite should be bounded
        assert 0.0 <= composite <= 1.0
    
    @settings(deadline=None)
    @given(
        weight_d=st.floats(min_value=0.0, max_value=1.0),
        weight_s=st.floats(min_value=0.0, max_value=1.0),
        weight_c=st.floats(min_value=0.0, max_value=1.0),
        weight_i=st.floats(min_value=0.0, max_value=1.0),
        weight_co=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_weights_normalized(self, weight_d, weight_s, weight_c, weight_i, weight_co):
        """Property: Weights are normalized to sum to ~1.0 after compute_composite."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            weight_dissonance=weight_d,
            weight_surprise=weight_s,
            weight_curiosity=weight_c,
            weight_info_gain=weight_i,
            weight_coherence=weight_co,
        )
        
        metrics.compute_composite()
        
        total_weight = (
            metrics.weight_dissonance +
            metrics.weight_surprise +
            metrics.weight_curiosity +
            metrics.weight_info_gain +
            metrics.weight_coherence
        )
        
        # Weights should sum to approximately 1.0 (within tolerance)
        # If all weights are zero, they'll be set to equal weights
        if total_weight > 0:
            assert abs(total_weight - 1.0) < 0.02  # Allow small floating point errors
    
    @settings(deadline=None)
    @given(
        reward1=st.floats(min_value=0.0, max_value=1.0),
        reward2=st.floats(min_value=0.0, max_value=1.0),
        reward3=st.floats(min_value=0.0, max_value=1.0),
        reward4=st.floats(min_value=0.0, max_value=1.0),
        reward5=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_composite_reward_weighted_average(self, reward1, reward2, reward3, reward4, reward5):
        """Property: Composite reward is a weighted average of component rewards."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=reward1,
            surprise_reward=reward2,
            curiosity_reward=reward3,
            information_gain_reward=reward4,
            coherence_reward=reward5,
            weight_dissonance=0.3,
            weight_surprise=0.2,
            weight_curiosity=0.2,
            weight_info_gain=0.15,
            weight_coherence=0.15,
        )
        
        composite = metrics.compute_composite()
        
        # Composite should be between min and max of component rewards
        min_reward = min(reward1, reward2, reward3, reward4, reward5)
        max_reward = max(reward1, reward2, reward3, reward4, reward5)
        
        eps = 1e-9
        assert (min_reward - eps) <= composite <= (max_reward + eps)
    
    @settings(deadline=None)
    @given(
        curiosity=st.floats(min_value=0.0, max_value=1.0),
        info_gain=st.floats(min_value=0.0, max_value=1.0),
        coherence=st.floats(min_value=0.0, max_value=1.0),
        surprise=st.floats(min_value=0.0, max_value=1.0),
        dissonance=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_exploration_balance_bounded(self, curiosity, info_gain, coherence, surprise, dissonance):
        """Property: Exploration-exploitation balance is bounded [0, 1]."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            curiosity_reward=curiosity,
            information_gain_reward=info_gain,
            coherence_reward=coherence,
            surprise_reward=surprise,
            dissonance_reward=dissonance,
        )
        
        balance = metrics.get_exploration_exploitation_balance()
        
        assert 0.0 <= balance <= 1.0
    
    @settings(deadline=None)
    @given(
        reward=st.floats(min_value=-1.0, max_value=2.0),  # Out of bounds values
    )
    def test_signals_clamped_to_bounds(self, reward):
        """Property: Signals are clamped to [0, 1] even if input is out of bounds."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=reward,
            surprise_reward=reward,
            curiosity_reward=reward,
            information_gain_reward=reward,
            coherence_reward=reward,
        )
        
        composite = metrics.compute_composite()
        
        # All signals should be clamped
        assert 0.0 <= metrics.dissonance_reward <= 1.0
        assert 0.0 <= metrics.surprise_reward <= 1.0
        assert 0.0 <= metrics.curiosity_reward <= 1.0
        assert 0.0 <= metrics.information_gain_reward <= 1.0
        assert 0.0 <= metrics.coherence_reward <= 1.0
        assert 0.0 <= composite <= 1.0
