"""
Tests for CognitiveStateMonitor.

Tests cognitive state tracking including confidence, coherence, attention, and uncertainty.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest

from broca.internal_sensing.cognitive_state import CognitiveStateMonitor


class TestCognitiveStateInitialization:
    """Test CognitiveStateMonitor initialization."""
    
    def test_initialization(self):
        """
        Test that monitor initializes with default cognitive states.
        
        Rationale: Ensures monitor starts with proper default state.
        """
        monitor = CognitiveStateMonitor()
        
        assert monitor.states is not None
        assert "confidence_level" in monitor.states
        assert "conceptual_coherence" in monitor.states
        assert "attention_allocation" in monitor.states
        assert "processing_depth" in monitor.states
        assert "uncertainty_tracking" in monitor.states
        
        # Check default values (should never be None)
        assert monitor.states["confidence_level"] == 0.5  # Moderate default
        assert monitor.states["conceptual_coherence"] == 0.5  # Moderate default
        assert monitor.states["processing_depth"] == 1.0  # Minimal depth default
        assert monitor.states["uncertainty_tracking"] == 0.0  # No uncertainty default


class TestConfidenceTracking:
    """Test confidence tracking functionality."""
    
    def test_confidence_tracking(self):
        """
        Test that confidence levels are tracked per response.
        
        Rationale: Ensures confidence is properly recorded.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_confidence("response_1", 0.8)
        monitor.record_confidence("response_2", 0.6)
        
        assert monitor.states["confidence_level"] > 0.0
        assert len(monitor._confidence_history) == 2
    
    def test_confidence_averaging(self):
        """
        Test that confidence level is averaged over recent responses.
        
        Rationale: Ensures confidence reflects recent performance.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_confidence("r1", 0.9)
        monitor.record_confidence("r2", 0.7)
        monitor.record_confidence("r3", 0.8)
        
        avg_confidence = monitor._calculate_average_confidence()
        
        assert isinstance(avg_confidence, float)
        assert 0.0 <= avg_confidence <= 1.0
        assert 0.7 <= avg_confidence <= 0.9  # Should be in this range
    
    def test_confidence_none_when_no_history(self):
        """
        Test that confidence returns None when no history available.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        monitor = CognitiveStateMonitor()
        
        avg_confidence = monitor._calculate_average_confidence()
        
        assert avg_confidence is None


class TestConfidenceCalibration:
    """Test confidence calibration functionality."""
    
    def test_confidence_calibration(self):
        """
        Test that calibration accuracy is measured.
        
        Rationale: Ensures confidence matches actual accuracy.
        """
        monitor = CognitiveStateMonitor()
        
        # Record confidence and actual outcome
        monitor.record_confidence("r1", 0.8)
        monitor.record_confidence_outcome("r1", correct=True)
        
        monitor.record_confidence("r2", 0.6)
        monitor.record_confidence_outcome("r2", correct=False)
        
        calibration = monitor._calculate_calibration()
        
        assert isinstance(calibration, float)
        assert 0.0 <= calibration <= 1.0
    
    def test_calibration_perfect(self):
        """
        Test that perfect calibration gives high score.
        
        Rationale: Ensures calibration calculation is accurate.
        """
        monitor = CognitiveStateMonitor()
        
        # Perfect calibration: high confidence = correct, low confidence = incorrect
        monitor.record_confidence("r1", 0.9)
        monitor.record_confidence_outcome("r1", correct=True)
        
        monitor.record_confidence("r2", 0.3)
        monitor.record_confidence_outcome("r2", correct=False)
        
        calibration = monitor._calculate_calibration()
        
        # Should be high for perfect calibration
        assert calibration > 0.7
    
    def test_calibration_none_when_no_data(self):
        """
        Test that calibration returns None when no data available.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        monitor = CognitiveStateMonitor()
        
        calibration = monitor._calculate_calibration()
        
        assert calibration is None


class TestConceptualCoherence:
    """Test conceptual coherence tracking."""
    
    def test_conceptual_coherence(self):
        """
        Test that logical consistency is measured.
        
        Rationale: Ensures coherence tracking works.
        """
        monitor = CognitiveStateMonitor()
        
        # Record reasoning steps
        monitor.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
        monitor.record_reasoning_step("step2", {"premise": "B", "conclusion": "C"})
        
        coherence = monitor._calculate_coherence()
        
        assert isinstance(coherence, float)
        assert 0.0 <= coherence <= 1.0
    
    def test_coherence_inconsistent(self):
        """
        Test that inconsistent reasoning reduces coherence.
        
        Rationale: Ensures coherence detects contradictions.
        """
        monitor = CognitiveStateMonitor()
        
        # Record contradictory reasoning
        monitor.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
        monitor.record_reasoning_step("step2", {"premise": "A", "conclusion": "not B"})
        
        coherence = monitor._calculate_coherence()
        
        # Should be lower for inconsistent reasoning
        assert coherence < 0.8
    
    def test_coherence_default_when_insufficient_steps(self):
        """
        Test that coherence returns default when insufficient reasoning steps.
        
        Rationale: Ensures unavailable data uses default value.
        """
        monitor = CognitiveStateMonitor()
        
        coherence = monitor._calculate_coherence()
        
        assert coherence == 0.5  # Default value
        
        # One step is not enough
        monitor.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
        coherence = monitor._calculate_coherence()
        
        assert coherence == 0.5  # Default value (needs at least 2 steps)


class TestAttentionAllocation:
    """Test attention allocation tracking."""
    
    def test_attention_allocation(self):
        """
        Test that focus distribution is tracked.
        
        Rationale: Ensures attention patterns are monitored.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_attention("topic1", 0.6)
        monitor.record_attention("topic2", 0.4)
        
        allocation = monitor.states["attention_allocation"]
        
        assert isinstance(allocation, dict)
        assert "topic1" in allocation
        assert allocation["topic1"] == 0.6
    
    def test_attention_normalization(self):
        """
        Test that attention values are normalized.
        
        Rationale: Ensures attention sums to reasonable values.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_attention("t1", 0.5)
        monitor.record_attention("t2", 0.3)
        monitor.record_attention("t3", 0.2)
        
        allocation = monitor.states["attention_allocation"]
        total = sum(allocation.values())
        
        # Should be normalized (sum <= 1.0)
        assert total <= 1.0


class TestProcessingDepth:
    """Test processing depth tracking."""
    
    def test_processing_depth(self):
        """
        Test that depth of analysis is measured.
        
        Rationale: Ensures processing depth is tracked.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_processing_depth("operation1", 3)  # 3 levels deep
        monitor.record_processing_depth("operation2", 5)  # 5 levels deep
        
        avg_depth = monitor._calculate_average_depth()
        
        assert isinstance(avg_depth, float)
        assert avg_depth >= 0.0
        assert avg_depth >= 3.0  # Should be at least 3
    
    def test_processing_depth_normalization(self):
        """
        Test that processing depth is normalized to 0-1.
        
        Rationale: Ensures depth values are normalized.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_processing_depth("op1", 10)
        
        normalized = monitor._normalize_depth(10)
        
        assert 0.0 <= normalized <= 1.0
    
    def test_processing_depth_none_when_no_operations(self):
        """
        Test that processing depth returns None when no operations recorded.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        monitor = CognitiveStateMonitor()
        
        avg_depth = monitor._calculate_average_depth()
        
        assert avg_depth is None


class TestUncertaintyTracking:
    """Test uncertainty tracking functionality."""
    
    def test_uncertainty_tracking(self):
        """
        Test that awareness of unknowns is tracked.
        
        Rationale: Ensures uncertainty is properly monitored.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_uncertainty("question1", 0.7)  # 70% uncertain
        monitor.record_uncertainty("question2", 0.3)  # 30% uncertain
        
        uncertainty = monitor.states["uncertainty_tracking"]
        
        assert isinstance(uncertainty, float)
        assert 0.0 <= uncertainty <= 1.0
    
    def test_uncertainty_averaging(self):
        """
        Test that uncertainty is averaged over recent queries.
        
        Rationale: Ensures uncertainty reflects recent awareness.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_uncertainty("q1", 0.8)
        monitor.record_uncertainty("q2", 0.6)
        monitor.record_uncertainty("q3", 0.4)
        
        avg_uncertainty = monitor._calculate_average_uncertainty()
        
        assert 0.4 <= avg_uncertainty <= 0.8
    
    def test_uncertainty_none_when_no_data(self):
        """
        Test that uncertainty returns None when no data recorded.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        monitor = CognitiveStateMonitor()
        
        avg_uncertainty = monitor._calculate_average_uncertainty()
        
        assert avg_uncertainty is None


class TestReasoningPatterns:
    """Test reasoning pattern tracking."""
    
    def test_reasoning_patterns(self):
        """
        Test that heuristics and algorithms are logged.
        
        Rationale: Ensures reasoning strategies are tracked.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.record_reasoning_pattern("heuristic", "pattern1")
        monitor.record_reasoning_pattern("algorithm", "pattern2")
        
        patterns = monitor._get_reasoning_patterns()
        
        assert isinstance(patterns, list)
        assert len(patterns) >= 2


class TestCognitiveStateSampling:
    """Test cognitive state sampling functionality."""
    
    def test_cognitive_state_sampling(self):
        """
        Test that cognitive state can be sampled.
        
        Rationale: Ensures complete cognitive state can be captured.
        """
        monitor = CognitiveStateMonitor()
        
        # Set up some state
        monitor.record_confidence("r1", 0.7)
        monitor.record_attention("topic1", 0.5)
        
        sample = monitor.sample_cognitive_state()
        
        assert isinstance(sample, dict)
        assert "confidence_level" in sample
        assert "conceptual_coherence" in sample
        assert "attention_allocation" in sample
        assert "processing_depth" in sample
        assert "uncertainty_tracking" in sample
        assert "timestamp" in sample


class TestCognitiveHistory:
    """Test cognitive history maintenance."""
    
    def test_cognitive_history(self):
        """
        Test that history of cognitive states is maintained.
        
        Rationale: Ensures historical data is available.
        """
        monitor = CognitiveStateMonitor(history_window=5)
        
        # Sample multiple times
        for i in range(10):
            monitor.sample_cognitive_state()
        
        history = monitor.get_history()
        
        assert isinstance(history, list)
        assert len(history) <= 5  # Should respect history window
        assert len(history) > 0
    
    def test_cognitive_history_timestamp(self):
        """
        Test that history entries have timestamps.
        
        Rationale: Ensures temporal information is preserved.
        """
        monitor = CognitiveStateMonitor()
        
        monitor.sample_cognitive_state()
        history = monitor.get_history()
        
        assert len(history) > 0
        assert "timestamp" in history[0]
        assert isinstance(history[0]["timestamp"], float)

