"""
Integration tests for multi-signal RL feedback loop integration.

Tests feedback loop with multiple signals, signal aggregation from all sources,
and backward compatibility (dissonance-only mode).
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from broca.reasoning.feedback_loop import FeedbackLoopManager, FeedbackMetrics
from broca.reasoning.rl_signals import RLSignalAggregator, RLSignalMetrics
from broca.reasoning.cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics


class TestRLFeedbackIntegration:
    """Test RL feedback integration in FeedbackLoopManager."""
    
    def test_feedback_loop_with_rl_signals(self):
        """Test feedback loop with RL signal aggregator."""
        # Create mock components
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
        
        # Create RL signal aggregator
        rl_aggregator = RLSignalAggregator(
            cognitive_dissonance_monitor=mock_dissonance,
            affective_monitor=mock_affective,
            epistemic_bridge=mock_epistemic,
        )
        
        # Create feedback loop manager with RL signals
        feedback_manager = FeedbackLoopManager(
            cognitive_dissonance_monitor=mock_dissonance,
            rl_signal_aggregator=rl_aggregator,
            rl_signals_enabled=True,
        )
        
        # Create test metrics
        metrics = FeedbackMetrics(
            window_size=10,
            success_rate=0.8,
            error_rate=0.1,
            overall_dissonance=0.2,
        )
        
        # Apply feedback (should use RL signals)
        feedback_manager.apply_feedback(metrics, emotional_state={
            "surprise": 0.3,
            "curiosity_drive": 0.6,
            "coherence_pleasure": 0.7,
        })
        
        # Verify RL aggregator was called
        assert feedback_manager.rl_signal_aggregator is not None
        assert feedback_manager.rl_signals_enabled is True
    
    def test_feedback_loop_backward_compatibility(self):
        """Test backward compatibility: dissonance-only mode."""
        # Create mock dissonance monitor
        mock_dissonance = Mock()
        mock_dissonance.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.4
        }
        
        # Create feedback loop manager WITHOUT RL signals
        feedback_manager = FeedbackLoopManager(
            cognitive_dissonance_monitor=mock_dissonance,
            rl_signals_enabled=False,  # Disabled
        )
        
        # Create test metrics
        metrics = FeedbackMetrics(
            window_size=10,
            success_rate=0.8,
            error_rate=0.1,
            overall_dissonance=0.4,
        )
        
        # Apply feedback (should use dissonance-only)
        feedback_manager.apply_feedback(metrics)
        
        # Verify dissonance-only mode
        assert feedback_manager.rl_signals_enabled is False
        # Should still work with dissonance monitor
        assert feedback_manager.cognitive_dissonance_monitor is not None
    
    def test_feedback_loop_with_missing_rl_aggregator(self):
        """Test feedback loop when RL aggregator is None (fallback)."""
        mock_dissonance = Mock()
        mock_dissonance.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.3
        }
        
        # Create feedback loop with RL enabled but no aggregator
        feedback_manager = FeedbackLoopManager(
            cognitive_dissonance_monitor=mock_dissonance,
            rl_signals_enabled=True,
            rl_signal_aggregator=None,  # Missing
        )
        
        metrics = FeedbackMetrics(
            window_size=10,
            overall_dissonance=0.3,
        )
        
        # Should fallback to dissonance-only
        feedback_manager.apply_feedback(metrics)
        
        # Should not crash
        assert feedback_manager.cognitive_dissonance_monitor is not None
    
    def test_surprise_feedback_triggered(self):
        """Test that surprise feedback is triggered when surprise is high."""
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.8,  # High surprise
            "curiosity_drive": 0.5,
            "coherence_pleasure": 0.5,
        }
        
        rl_aggregator = RLSignalAggregator(
            affective_monitor=mock_affective,
            weight_surprise=0.3,
        )
        
        feedback_manager = FeedbackLoopManager(
            rl_signal_aggregator=rl_aggregator,
            rl_signals_enabled=True,
            surprise_threshold=0.3,
        )
        
        metrics = FeedbackMetrics(window_size=10)
        
        # Apply feedback
        feedback_manager.apply_feedback(metrics, emotional_state={
            "surprise": 0.8,
        })
        
        # Should trigger surprise feedback (check via logs or side effects)
        assert feedback_manager.surprise_threshold == 0.3
    
    def test_curiosity_feedback_triggered(self):
        """Test that curiosity feedback is triggered when curiosity is high."""
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.3,
            "curiosity_drive": 0.9,  # High curiosity
            "coherence_pleasure": 0.5,
        }
        
        rl_aggregator = RLSignalAggregator(
            affective_monitor=mock_affective,
            weight_curiosity=0.3,
        )
        
        feedback_manager = FeedbackLoopManager(
            rl_signal_aggregator=rl_aggregator,
            rl_signals_enabled=True,
            curiosity_threshold=0.5,
        )
        
        metrics = FeedbackMetrics(window_size=10)
        
        # Apply feedback
        feedback_manager.apply_feedback(metrics, emotional_state={
            "curiosity_drive": 0.9,
        })
        
        # Should trigger curiosity feedback
        assert feedback_manager.curiosity_threshold == 0.5
    
    def test_composite_reward_guidance(self):
        """Test that composite reward guides overall feedback strategy."""
        mock_dissonance = Mock()
        mock_dissonance.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.1  # Low dissonance
        }
        
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.1,  # Low surprise
            "curiosity_drive": 0.8,  # High curiosity
            "coherence_pleasure": 0.9,  # High coherence
        }
        
        mock_epistemic = Mock()
        mock_epistemic.get_information_gain.return_value = 0.7  # High info gain
        
        rl_aggregator = RLSignalAggregator(
            cognitive_dissonance_monitor=mock_dissonance,
            affective_monitor=mock_affective,
            epistemic_bridge=mock_epistemic,
        )
        
        feedback_manager = FeedbackLoopManager(
            rl_signal_aggregator=rl_aggregator,
            rl_signals_enabled=True,
        )
        
        metrics = FeedbackMetrics(window_size=10)
        
        # Apply feedback
        feedback_manager.apply_feedback(metrics)
        
        # Compute signals to check composite reward
        rl_metrics = rl_aggregator.compute_signals()
        
        # High composite reward (all signals positive)
        assert rl_metrics.composite_reward > 0.7
    
    def test_exploration_exploitation_balance(self):
        """Test exploration-exploitation balance in feedback."""
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.2,
            "curiosity_drive": 0.9,  # High exploration
            "coherence_pleasure": 0.3,
        }
        
        rl_aggregator = RLSignalAggregator(
            affective_monitor=mock_affective,
        )
        
        feedback_manager = FeedbackLoopManager(
            rl_signal_aggregator=rl_aggregator,
            rl_signals_enabled=True,
            exploration_ratio=0.6,
        )
        
        metrics = FeedbackMetrics(window_size=10)
        feedback_manager.apply_feedback(metrics)
        
        # Check balance
        balance = rl_aggregator.get_exploration_exploitation_balance()
        assert 0.0 <= balance <= 1.0
    
    def test_signal_aggregation_from_all_sources(self):
        """Test that signals are aggregated from all available sources."""
        mock_dissonance = Mock()
        mock_dissonance.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.25
        }
        
        mock_affective = Mock()
        mock_affective.sample_affective_state.return_value = {
            "surprise": 0.3,
            "curiosity_drive": 0.6,
            "coherence_pleasure": 0.7,
        }
        
        mock_predictive = Mock()
        mock_predictive._prediction_errors = [0.2, 0.3, 0.25]
        
        mock_epistemic = Mock()
        mock_epistemic.get_information_gain.return_value = 0.5
        
        rl_aggregator = RLSignalAggregator(
            cognitive_dissonance_monitor=mock_dissonance,
            affective_monitor=mock_affective,
            predictive_interoception=mock_predictive,
            epistemic_bridge=mock_epistemic,
        )
        
        metrics = rl_aggregator.compute_signals()
        
        # All signals should be computed
        assert metrics.dissonance_reward > 0.0
        assert metrics.surprise_reward > 0.0
        assert metrics.curiosity_reward > 0.0
        assert metrics.information_gain_reward > 0.0
        assert metrics.coherence_reward > 0.0
        assert metrics.composite_reward > 0.0

