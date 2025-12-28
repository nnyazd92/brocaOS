"""
Unit tests for RL signal aggregator.

Tests signal computation, composite reward calculation, weight normalization,
and exploration-exploitation balance.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from broca.reasoning.rl_signals import RLSignalAggregator, RLSignalMetrics
from broca.reasoning.cognitive_dissonance import DissonanceMetrics


class TestRLSignalMetrics:
    """Test RLSignalMetrics dataclass."""
    
    def test_compute_composite_reward(self):
        """Test composite reward calculation."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.8,
            surprise_reward=0.7,
            curiosity_reward=0.6,
            information_gain_reward=0.5,
            coherence_reward=0.9,
            weight_dissonance=0.3,
            weight_surprise=0.2,
            weight_curiosity=0.2,
            weight_info_gain=0.15,
            weight_coherence=0.15,
        )
        
        composite = metrics.compute_composite()
        
        expected = (
            0.8 * 0.3 +
            0.7 * 0.2 +
            0.6 * 0.2 +
            0.5 * 0.15 +
            0.9 * 0.15
        )
        
        assert composite == pytest.approx(expected, abs=0.01)
        assert 0.0 <= composite <= 1.0
    
    def test_composite_reward_bounded(self):
        """Test that composite reward is bounded [0, 1]."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=1.5,  # Out of bounds
            surprise_reward=-0.5,  # Out of bounds
            curiosity_reward=0.5,
            information_gain_reward=0.5,
            coherence_reward=0.5,
        )
        
        composite = metrics.compute_composite()
        
        assert 0.0 <= composite <= 1.0
    
    def test_weight_normalization(self):
        """Test that weights are normalized to sum to 1.0."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            weight_dissonance=0.5,
            weight_surprise=0.5,
            weight_curiosity=0.5,
            weight_info_gain=0.5,
            weight_coherence=0.5,
        )
        
        metrics.compute_composite()
        
        total_weight = (
            metrics.weight_dissonance +
            metrics.weight_surprise +
            metrics.weight_curiosity +
            metrics.weight_info_gain +
            metrics.weight_coherence
        )
        
        assert total_weight == pytest.approx(1.0, abs=0.01)
    
    def test_zero_weights_handled(self):
        """Test that zero weights are handled gracefully."""
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            weight_dissonance=0.0,
            weight_surprise=0.0,
            weight_curiosity=0.0,
            weight_info_gain=0.0,
            weight_coherence=0.0,
        )
        
        composite = metrics.compute_composite()
        
        # Should use equal weights as fallback
        assert 0.0 <= composite <= 1.0
    
    def test_exploration_exploitation_balance(self):
        """Test exploration-exploitation balance calculation."""
        # High exploration (curiosity + info_gain)
        metrics_explore = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            curiosity_reward=0.9,
            information_gain_reward=0.9,
            coherence_reward=0.1,
            surprise_reward=0.1,
            dissonance_reward=0.1,
        )
        
        balance_explore = metrics_explore.get_exploration_exploitation_balance()
        assert balance_explore > 0.7  # Should favor exploration
        
        # High exploitation (coherence + low surprise + low dissonance)
        metrics_exploit = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            curiosity_reward=0.1,
            information_gain_reward=0.1,
            coherence_reward=0.9,
            surprise_reward=0.9,
            dissonance_reward=0.9,
        )
        
        balance_exploit = metrics_exploit.get_exploration_exploitation_balance()
        assert balance_exploit < 0.3  # Should favor exploitation


class TestRLSignalAggregator:
    """Test RLSignalAggregator class."""
    
    def test_compute_signals_with_dissonance(self):
        """Test signal computation with dissonance monitor."""
        # Create mock dissonance monitor
        mock_dissonance = Mock()
        mock_dissonance.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.3
        }
        
        aggregator = RLSignalAggregator(
            cognitive_dissonance_monitor=mock_dissonance
        )
        
        metrics = aggregator.compute_signals()
        
        # Dissonance reward = 1.0 - 0.3 = 0.7
        assert metrics.dissonance_reward == pytest.approx(0.7, abs=0.01)
        assert 0.0 <= metrics.dissonance_reward <= 1.0
    
    def test_compute_signals_with_affective(self):
        """Test signal computation with affective monitor."""
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.2,
            "curiosity_drive": 0.7,
            "coherence_pleasure": 0.8,
        }
        
        aggregator = RLSignalAggregator(
            affective_monitor=mock_affective
        )
        
        metrics = aggregator.compute_signals()
        
        # Surprise reward = 1.0 - 0.2 = 0.8
        assert metrics.surprise_reward == pytest.approx(0.8, abs=0.01)
        assert metrics.curiosity_reward == pytest.approx(0.7, abs=0.01)
        assert metrics.coherence_reward == pytest.approx(0.8, abs=0.01)
    
    def test_compute_signals_with_prediction_error(self):
        """Test signal computation with prediction error."""
        mock_predictive = Mock()
        mock_predictive._prediction_errors = [0.3, 0.4, 0.2]
        
        aggregator = RLSignalAggregator(
            predictive_interoception=mock_predictive
        )
        
        metrics = aggregator.compute_signals(prediction_error=0.25)
        
        # Should incorporate prediction error into surprise
        assert 0.0 <= metrics.surprise_reward <= 1.0
    
    def test_compute_signals_with_information_gain(self):
        """Test signal computation with information gain."""
        mock_epistemic = Mock()
        mock_epistemic.get_information_gain.return_value = 0.6
        
        aggregator = RLSignalAggregator(
            epistemic_bridge=mock_epistemic
        )
        
        metrics = aggregator.compute_signals(information_gain=0.6)
        
        assert metrics.information_gain_reward == pytest.approx(0.6, abs=0.01)
    
    def test_compute_signals_all_sources(self):
        """Test signal computation with all sources."""
        mock_dissonance = Mock()
        mock_dissonance.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.2
        }
        
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.3,
            "curiosity_drive": 0.6,
            "coherence_pleasure": 0.7,
        }
        
        mock_epistemic = Mock()
        mock_epistemic.get_information_gain.return_value = 0.5
        
        aggregator = RLSignalAggregator(
            cognitive_dissonance_monitor=mock_dissonance,
            affective_monitor=mock_affective,
            epistemic_bridge=mock_epistemic,
        )
        
        metrics = aggregator.compute_signals()
        
        assert metrics.dissonance_reward == pytest.approx(0.8, abs=0.01)
        assert metrics.surprise_reward == pytest.approx(0.7, abs=0.01)
        assert metrics.curiosity_reward == pytest.approx(0.6, abs=0.01)
        assert metrics.information_gain_reward == pytest.approx(0.5, abs=0.01)
        assert metrics.coherence_reward == pytest.approx(0.7, abs=0.01)
        
        # Composite should be computed
        assert 0.0 <= metrics.composite_reward <= 1.0
    
    def test_compute_signals_missing_sources(self):
        """Test signal computation when sources are missing."""
        aggregator = RLSignalAggregator()
        
        metrics = aggregator.compute_signals()
        
        # Should use default neutral values
        assert metrics.dissonance_reward == pytest.approx(0.5, abs=0.01)
        assert metrics.surprise_reward == pytest.approx(0.5, abs=0.01)
        assert metrics.curiosity_reward == pytest.approx(0.5, abs=0.01)
        assert metrics.information_gain_reward == pytest.approx(0.0, abs=0.01)
        assert metrics.coherence_reward == pytest.approx(0.5, abs=0.01)
    
    def test_get_exploration_exploitation_balance(self):
        """Test exploration-exploitation balance method."""
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.1,
            "curiosity_drive": 0.9,
            "coherence_pleasure": 0.1,
        }
        
        aggregator = RLSignalAggregator(affective_monitor=mock_affective)
        
        balance = aggregator.get_exploration_exploitation_balance()
        
        assert 0.0 <= balance <= 1.0
    
    def test_should_explore(self):
        """Test should_explore method."""
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.1,
            "curiosity_drive": 0.9,
            "coherence_pleasure": 0.1,
        }
        
        aggregator = RLSignalAggregator(affective_monitor=mock_affective)
        
        # High curiosity should trigger exploration
        should_explore = aggregator.should_explore(threshold=0.6)
        assert should_explore is True
        
        # Low curiosity should not trigger exploration
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.9,
            "curiosity_drive": 0.1,
            "coherence_pleasure": 0.9,
        }
        
        should_explore = aggregator.should_explore(threshold=0.6)
        assert should_explore is False
    
    def test_compute_signals_with_precomputed_values(self):
        """Test signal computation with pre-computed values."""
        aggregator = RLSignalAggregator()
        
        dissonance_metrics = DissonanceMetrics(
            timestamp=datetime.now(timezone.utc),
            overall_dissonance=0.4
        )
        
        metrics = aggregator.compute_signals(
            dissonance_metrics=dissonance_metrics,
            affective_state={"surprise": 0.2, "curiosity_drive": 0.6, "coherence_pleasure": 0.8},
            prediction_error=0.3,
            information_gain=0.5
        )
        
        assert metrics.dissonance_reward == pytest.approx(0.6, abs=0.01)
        assert metrics.surprise_reward > 0.0  # Should incorporate prediction error
        assert metrics.curiosity_reward == pytest.approx(0.6, abs=0.01)
        assert metrics.information_gain_reward == pytest.approx(0.5, abs=0.01)
        assert metrics.coherence_reward == pytest.approx(0.8, abs=0.01)

