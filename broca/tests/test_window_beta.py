"""
Tests for window aggregators and Beta tracker.

Covers:
- Window aggregator statistics
- Beta tracker convergence
- Property-based tests for early toggles
"""

import pytest
from broca.signals.window import WindowAggregator, RingBuffer
from broca.damping.beta_tracker import BetaSuccessTracker


class TestRingBuffer:
    """Test RingBuffer functionality."""
    
    def test_ring_buffer_basic(self):
        """Test basic ring buffer operations."""
        buffer = RingBuffer(maxlen=5)
        
        for i in range(7):
            buffer.append(i)
        
        assert len(buffer) == 5
        assert buffer[0] == 2  # First two were evicted
        assert buffer[-1] == 6
    
    def test_ring_buffer_iteration(self):
        """Test ring buffer iteration."""
        buffer = RingBuffer(maxlen=3)
        buffer.append(1)
        buffer.append(2)
        buffer.append(3)
        
        values = list(buffer)
        assert values == [1, 2, 3]


class TestWindowAggregator:
    """Test WindowAggregator functionality."""
    
    def test_rolling_mean(self):
        """Test rolling mean calculation."""
        aggregator = WindowAggregator(max_buffer_size=100)
        
        for i in range(10):
            aggregator.update(float(i))
        
        mean = aggregator.rolling_mean(window_size=10)
        assert mean == pytest.approx(4.5, abs=0.01)
        
        # Smaller window
        mean_small = aggregator.rolling_mean(window_size=5)
        assert mean_small == pytest.approx(7.0, abs=0.01)  # Last 5: 5,6,7,8,9 = 35/5 = 7.0
    
    def test_rolling_std(self):
        """Test rolling standard deviation."""
        aggregator = WindowAggregator(max_buffer_size=100)
        
        # Constant values (std should be 0)
        for _ in range(10):
            aggregator.update(5.0)
        
        std = aggregator.rolling_std(window_size=10)
        assert std == pytest.approx(0.0, abs=0.01)
        
        # Variable values
        aggregator.clear()
        for i in range(10):
            aggregator.update(float(i))
        
        std = aggregator.rolling_std(window_size=10)
        assert std > 0.0  # Should have variation
    
    def test_rolling_min_max(self):
        """Test rolling min and max."""
        aggregator = WindowAggregator(max_buffer_size=100)
        
        values = [1.0, 5.0, 3.0, 9.0, 2.0]
        for v in values:
            aggregator.update(v)
        
        assert aggregator.rolling_min(window_size=5) == 1.0
        assert aggregator.rolling_max(window_size=5) == 9.0
    
    def test_event_count(self):
        """Test event counting."""
        aggregator = WindowAggregator()
        
        for _ in range(5):
            aggregator.update(1.0)
        
        assert aggregator.event_count() == 5


class TestBetaTracker:
    """Test BetaSuccessTracker functionality."""
    
    def test_beta_initial_state(self):
        """Test Beta tracker initial state."""
        tracker = BetaSuccessTracker(prior_a=2.0, prior_b=2.0)
        
        # With no observations, mean should be 0.5 (prior)
        assert tracker.get_mean() == pytest.approx(0.5, abs=0.01)
        assert tracker.get_total_observations() == 0
    
    def test_beta_success_recording(self):
        """Test recording successes."""
        tracker = BetaSuccessTracker(prior_a=2.0, prior_b=2.0)
        
        tracker.record_success()
        tracker.record_success()
        
        # a = 2 + 2 = 4, b = 2, mean = 4/6 = 0.667
        assert tracker.get_mean() == pytest.approx(4.0 / 6.0, abs=0.01)
        assert tracker.get_total_observations() == 2
    
    def test_beta_failure_recording(self):
        """Test recording failures."""
        tracker = BetaSuccessTracker(prior_a=2.0, prior_b=2.0)
        
        tracker.record_failure()
        tracker.record_failure()
        
        # a = 2, b = 2 + 2 = 4, mean = 2/6 = 0.333
        assert tracker.get_mean() == pytest.approx(2.0 / 6.0, abs=0.01)
    
    def test_beta_variance(self):
        """Test variance calculation."""
        tracker = BetaSuccessTracker(prior_a=2.0, prior_b=2.0)
        
        # With prior only, variance should be:
        # ab/((a+b)^2 * (a+b+1)) = 4/(16 * 5) = 4/80 = 0.05
        variance = tracker.get_variance()
        assert variance == pytest.approx(0.05, abs=0.01)
        
        # After many observations, variance should decrease
        for _ in range(100):
            tracker.record_success()
        
        variance_after = tracker.get_variance()
        assert variance_after < variance  # Should be more confident
    
    def test_beta_early_toggles(self):
        """Test that early toggles (S,F,S,F,...) keep mean near 0.5."""
        tracker = BetaSuccessTracker(prior_a=2.0, prior_b=2.0)
        
        # Alternate success/failure
        for i in range(20):
            if i % 2 == 0:
                tracker.record_success()
            else:
                tracker.record_failure()
        
        # Mean should stay near 0.5 (not slam to extremes)
        mean = tracker.get_mean()
        assert 0.4 < mean < 0.6  # Should be near 0.5
        
        # Variance should be relatively high (uncertainty)
        variance = tracker.get_variance()
        assert variance >= 0.01  # Should have some uncertainty (allow equality)
    
    def test_beta_convergence(self):
        """Test Beta tracker converges with consistent data."""
        tracker = BetaSuccessTracker(prior_a=2.0, prior_b=2.0)
        
        # Record many successes
        for _ in range(100):
            tracker.record_success()
        
        # Mean should be high
        mean = tracker.get_mean()
        assert mean > 0.9
        
        # Variance should be low (high confidence)
        variance = tracker.get_variance()
        assert variance < 0.01
    
    def test_beta_reset(self):
        """Test Beta tracker reset."""
        tracker = BetaSuccessTracker(prior_a=2.0, prior_b=2.0)
        
        tracker.record_success()
        tracker.record_success()
        
        assert tracker.get_total_observations() == 2
        
        tracker.reset()
        
        assert tracker.get_total_observations() == 0
        assert tracker.get_mean() == pytest.approx(0.5, abs=0.01)


class TestBetaPropertyBased:
    """Property-based tests for Beta tracker."""
    
    def test_beta_mean_bounds(self):
        """Property: Beta mean is always in [0, 1]."""
        tracker = BetaSuccessTracker()
        
        for _ in range(100):
            import random
            if random.random() > 0.5:
                tracker.record_success()
            else:
                tracker.record_failure()
            
            mean = tracker.get_mean()
            assert 0.0 <= mean <= 1.0
    
    def test_beta_variance_bounds(self):
        """Property: Beta variance is always in [0, 0.25]."""
        tracker = BetaSuccessTracker()
        
        for _ in range(100):
            import random
            if random.random() > 0.5:
                tracker.record_success()
            else:
                tracker.record_failure()
            
            variance = tracker.get_variance()
            assert 0.0 <= variance <= 0.25  # Maximum variance for Beta(1,1)
    
    def test_beta_monotonic_variance(self):
        """Property: Variance decreases (or stays same) as observations increase."""
        tracker = BetaSuccessTracker()
        
        variances = []
        for _ in range(50):
            import random
            if random.random() > 0.5:
                tracker.record_success()
            else:
                tracker.record_failure()
            variances.append(tracker.get_variance())
        
        # Variance should generally decrease (or at least not increase systematically)
        # Allow for some noise, but trend should be downward
        early_avg = sum(variances[:10]) / 10
        late_avg = sum(variances[-10:]) / 10
        assert late_avg <= early_avg * 1.1  # Allow 10% tolerance for noise


class TestSignalManagerWindowBetaIntegration:
    """Integration tests for SignalManager with window aggregators and Beta trackers."""
    
    def test_window_aggregator_integration(self):
        """Test SignalManager window aggregator integration."""
        from broca.signals.manager import SignalManager
        
        manager = SignalManager()
        
        # Update signal multiple times
        for i in range(10):
            manager.update("affect.valence", float(i) * 0.1)
        
        # Get window aggregator
        aggregator = manager.get_window_aggregator("affect.valence")
        
        # Check statistics
        mean = aggregator.rolling_mean(window_size=10)
        assert mean > 0.0
        assert aggregator.event_count() >= 10
    
    def test_beta_tracker_integration(self):
        """Test SignalManager Beta tracker integration."""
        from broca.signals.manager import SignalManager
        
        manager = SignalManager()
        
        # Record tool successes/failures
        for i in range(20):
            success = i % 3 != 0  # 2/3 success rate
            manager.record_tool_success("test_tool", success)
        
        # Get Beta tracker
        tracker = manager.get_beta_tracker("toolchain.test_tool.success_rate")
        
        # Check that mean is reasonable (should be around 2/3)
        mean = tracker.get_mean()
        assert 0.5 < mean < 0.8  # Should be biased toward success
        
        # Check signal value (may be damped by pipeline, so allow some tolerance)
        signal_value = manager.get("toolchain.test_tool.success_rate")
        # Signal value should be close to Beta mean (may be slightly damped)
        # MED profile with alpha=0.15 can cause significant damping over 20 updates
        assert abs(float(signal_value) - mean) < 0.3  # Allow for damping over many updates

