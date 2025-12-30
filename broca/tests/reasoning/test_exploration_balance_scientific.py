"""
TDD Tests for scientifically rigorous exploration-exploitation balance.

Based on Active Inference theory:
- Exploration (epistemic value): driven by uncertainty, curiosity, prediction error
- Exploitation (pragmatic value): driven by confidence, coherence, low dissonance

Key insight: The balance should use RAW signal values, not inverted reward values.

References:
- Friston, K. (2010). The free-energy principle: a unified brain theory?
- Schwartenbeck et al. (2019). Computational mechanisms of curiosity and goal-directed exploration
- Gottlieb et al. (2013). Information-seeking, curiosity, and attention: computational and neural mechanisms
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import MagicMock


class TestExplorationBalanceFormula:
    """Tests for the mathematical correctness of exploration balance."""

    def test_high_curiosity_high_info_gain_yields_exploration(self):
        """When curiosity and info_gain are high, balance should favor exploration."""
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.5,  # Moderate
            surprise_reward=0.5,  # Moderate
            curiosity_reward=0.9,  # HIGH curiosity (exploration signal)
            information_gain_reward=0.8,  # HIGH info gain (exploration signal)
            coherence_reward=0.3,  # Low coherence (supports exploration)
            # Raw values should drive the balance
            curiosity_raw=0.9,
            info_gain_raw=0.8,
            raw_surprise=0.7,  # High surprise (exploration)
            prediction_error_raw=0.6,  # High prediction error (exploration)
            coherence_raw=0.3,  # Low coherence (supports exploration)
            dissonance_raw=0.6,  # High dissonance (exploration)
        )

        balance = metrics.get_exploration_exploitation_balance()

        # Should strongly favor exploration (> 0.5)
        assert balance > 0.6, f"High exploration signals should yield balance > 0.6, got {balance}"

    def test_high_coherence_low_uncertainty_yields_exploitation(self):
        """When coherence is high and uncertainty low, balance should favor exploitation."""
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.9,  # High (low dissonance)
            surprise_reward=0.9,  # High (low surprise)
            curiosity_reward=0.2,  # Low curiosity
            information_gain_reward=0.1,  # Low info gain
            coherence_reward=0.9,  # HIGH coherence (exploitation)
            # Raw values
            curiosity_raw=0.2,
            info_gain_raw=0.1,
            raw_surprise=0.1,  # Low surprise (exploitation)
            prediction_error_raw=0.1,  # Low prediction error (exploitation)
            coherence_raw=0.9,  # High coherence (exploitation)
            dissonance_raw=0.1,  # Low dissonance (exploitation)
        )

        balance = metrics.get_exploration_exploitation_balance()

        # Should favor exploitation (< 0.5)
        assert balance < 0.4, f"High exploitation signals should yield balance < 0.4, got {balance}"

    def test_balanced_signals_yield_moderate_balance(self):
        """When signals are balanced, balance should be near 0.5."""
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.5,
            surprise_reward=0.5,
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
            # Raw values - all moderate
            curiosity_raw=0.5,
            info_gain_raw=0.5,
            raw_surprise=0.5,
            prediction_error_raw=0.5,
            coherence_raw=0.5,
            dissonance_raw=0.5,
        )

        balance = metrics.get_exploration_exploitation_balance()

        # Should be near 0.5 (balanced)
        assert 0.4 <= balance <= 0.6, f"Balanced signals should yield balance near 0.5, got {balance}"


class TestExplorationBalanceRawInputs:
    """Tests ensuring exploration balance uses RAW values, not inverted rewards."""

    def test_uses_raw_surprise_not_surprise_reward(self):
        """
        High raw_surprise should increase exploration.
        surprise_reward = 1 - raw_surprise (inverted), so we must use raw_surprise.
        """
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        # High raw surprise, but surprise_reward is low (inverted)
        metrics_high_surprise = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.5,
            surprise_reward=0.2,  # Low reward (high surprise inverted)
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
            raw_surprise=0.8,  # HIGH raw surprise → should explore
            curiosity_raw=0.5,
            info_gain_raw=0.5,
            prediction_error_raw=0.5,
            coherence_raw=0.5,
            dissonance_raw=0.5,
        )

        metrics_low_surprise = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.5,
            surprise_reward=0.8,  # High reward (low surprise inverted)
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
            raw_surprise=0.2,  # LOW raw surprise → should exploit
            curiosity_raw=0.5,
            info_gain_raw=0.5,
            prediction_error_raw=0.5,
            coherence_raw=0.5,
            dissonance_raw=0.5,
        )

        balance_high = metrics_high_surprise.get_exploration_exploitation_balance()
        balance_low = metrics_low_surprise.get_exploration_exploitation_balance()

        # High raw surprise should yield higher exploration balance
        assert balance_high > balance_low, \
            f"High raw_surprise ({balance_high}) should yield more exploration than low ({balance_low})"

    def test_uses_raw_dissonance_not_dissonance_reward(self):
        """
        High dissonance_raw should increase exploration (world model is wrong).
        dissonance_reward = 1 - dissonance_raw (inverted).
        """
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        # High dissonance = need to explore to resolve
        metrics_high_diss = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.2,  # Low reward (high dissonance inverted)
            surprise_reward=0.5,
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
            dissonance_raw=0.8,  # HIGH dissonance → explore to resolve
            raw_surprise=0.5,
            curiosity_raw=0.5,
            info_gain_raw=0.5,
            prediction_error_raw=0.5,
            coherence_raw=0.5,
        )

        metrics_low_diss = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.8,  # High reward (low dissonance)
            surprise_reward=0.5,
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
            dissonance_raw=0.2,  # LOW dissonance → exploit
            raw_surprise=0.5,
            curiosity_raw=0.5,
            info_gain_raw=0.5,
            prediction_error_raw=0.5,
            coherence_raw=0.5,
        )

        balance_high = metrics_high_diss.get_exploration_exploitation_balance()
        balance_low = metrics_low_diss.get_exploration_exploitation_balance()

        assert balance_high > balance_low, \
            f"High dissonance ({balance_high}) should yield more exploration than low ({balance_low})"

    def test_prediction_error_drives_exploration(self):
        """High prediction error should increase exploration (world model is wrong)."""
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        metrics_high_pe = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.5,
            surprise_reward=0.5,
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
            prediction_error_raw=0.9,  # HIGH prediction error → explore
            raw_surprise=0.5,
            curiosity_raw=0.5,
            info_gain_raw=0.5,
            coherence_raw=0.5,
            dissonance_raw=0.5,
        )

        metrics_low_pe = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.5,
            surprise_reward=0.5,
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
            prediction_error_raw=0.1,  # LOW prediction error → exploit
            raw_surprise=0.5,
            curiosity_raw=0.5,
            info_gain_raw=0.5,
            coherence_raw=0.5,
            dissonance_raw=0.5,
        )

        balance_high = metrics_high_pe.get_exploration_exploitation_balance()
        balance_low = metrics_low_pe.get_exploration_exploitation_balance()

        assert balance_high > balance_low, \
            f"High prediction_error ({balance_high}) should yield more exploration than low ({balance_low})"


class TestExplorationBalanceActiveInference:
    """Tests based on Active Inference expected free energy decomposition."""

    def test_epistemic_value_increases_exploration(self):
        """
        In Active Inference: G = G_epistemic + G_pragmatic
        G_epistemic (information gain) should drive exploration.
        """
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        # High epistemic value (info_gain, curiosity, uncertainty)
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.5,
            surprise_reward=0.5,
            curiosity_reward=0.9,  # Epistemic
            information_gain_reward=0.9,  # Epistemic
            coherence_reward=0.5,
            curiosity_raw=0.9,
            info_gain_raw=0.9,
            raw_surprise=0.5,
            prediction_error_raw=0.5,
            coherence_raw=0.5,
            dissonance_raw=0.5,
        )

        balance = metrics.get_exploration_exploitation_balance()

        # High epistemic value → exploration
        assert balance > 0.5, f"High epistemic value should favor exploration, got {balance}"

    def test_pragmatic_value_increases_exploitation(self):
        """
        G_pragmatic (goal-directed value) should drive exploitation.
        High coherence + low dissonance = world model is good, exploit it.
        """
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        # High pragmatic value (coherence, low dissonance, low surprise)
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.9,
            surprise_reward=0.9,
            curiosity_reward=0.2,
            information_gain_reward=0.2,
            coherence_reward=0.9,  # Pragmatic
            curiosity_raw=0.2,
            info_gain_raw=0.2,
            raw_surprise=0.1,  # Low surprise (pragmatic)
            prediction_error_raw=0.1,  # Low PE (pragmatic)
            coherence_raw=0.9,  # High coherence (pragmatic)
            dissonance_raw=0.1,  # Low dissonance (pragmatic)
        )

        balance = metrics.get_exploration_exploitation_balance()

        # High pragmatic value → exploitation
        assert balance < 0.5, f"High pragmatic value should favor exploitation, got {balance}"


class TestExplorationBalanceBoundedness:
    """Property-based tests for balance bounds."""

    @given(
        curiosity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        info_gain=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        surprise=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        coherence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        dissonance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_balance_always_bounded_0_1(self, curiosity, info_gain, surprise, coherence, dissonance):
        """Exploration balance should always be in [0, 1]."""
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=1.0 - dissonance,
            surprise_reward=1.0 - surprise,
            curiosity_reward=curiosity,
            information_gain_reward=info_gain,
            coherence_reward=coherence,
            curiosity_raw=curiosity,
            info_gain_raw=info_gain,
            raw_surprise=surprise,
            prediction_error_raw=surprise * 0.5,  # Correlate with surprise
            coherence_raw=coherence,
            dissonance_raw=dissonance,
        )

        balance = metrics.get_exploration_exploitation_balance()

        assert 0.0 <= balance <= 1.0, f"Balance {balance} out of bounds"


class TestExplorationBalanceGracefulDegradation:
    """Tests for handling missing raw values."""

    def test_falls_back_to_reward_values_when_raw_missing(self):
        """When raw values are None, should gracefully fall back to reward values."""
        from broca.reasoning.rl_signals import RLSignalMetrics
        from datetime import datetime, timezone

        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.7,
            surprise_reward=0.6,
            curiosity_reward=0.8,
            information_gain_reward=0.5,
            coherence_reward=0.4,
            # All raw values are None (default)
        )

        balance = metrics.get_exploration_exploitation_balance()

        # Should not crash, should return valid balance
        assert 0.0 <= balance <= 1.0, f"Balance {balance} should be valid even with missing raw values"

