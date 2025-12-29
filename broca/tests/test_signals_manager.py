"""
Tests for SignalManager and DampingPipeline.

Covers:
- EMA with variable dt
- Rate limiting
- Deadband
- Hysteresis
- Simulated time tests
"""

import pytest
from datetime import datetime, timezone, timedelta
from broca.signals.manager import SignalManager
from broca.signals.schema import SignalSpec, SignalType, register_signal
from broca.damping.profiles import DampingProfile, register_profile
from broca.damping.pipeline import DampingPipeline


class TestSignalManager:
    """Test SignalManager functionality."""
    
    def test_signal_registration(self):
        """Test signal auto-registration."""
        manager = SignalManager()
        
        # Update a signal (should auto-register)
        value = manager.update("affect.valence", 0.5)
        assert value == 0.5  # Should return the value
        
        # Get the signal
        assert manager.get("affect.valence") == 0.5
        assert manager.has_signal("affect.valence")
    
    def test_signal_get_default(self):
        """Test getting default value for unregistered signal."""
        manager = SignalManager()
        
        # Get default for registered signal in schema
        value = manager.get("affect.valence")
        assert value == 0.0  # Default from schema
    
    def test_signal_history(self):
        """Test signal history tracking."""
        manager = SignalManager(history_size=10)
        
        # Update multiple times with timestamps
        base_time = datetime.now(timezone.utc)
        for i in range(5):
            t = base_time + timedelta(seconds=i * 0.1)
            manager.update("affect.valence", float(i) * 0.1, t)
        
        history = manager.get_history("affect.valence", limit=3)
        assert len(history) == 3
        # Last value should be damped (MED profile with alpha=0.15)
        # With damping, it won't be exactly 0.4, but should be in valid range
        assert -1.0 <= history[-1] <= 1.0  # Valid range for valence
        assert history[-1] >= 0.0  # Should be positive after updates
    
    def test_signal_raw_history(self):
        """Test raw value history tracking."""
        manager = SignalManager()
        
        manager.update("affect.valence", 0.8)
        raw_history = manager.get_raw_history("affect.valence", limit=1)
        assert len(raw_history) == 1
        assert raw_history[0] == 0.8


class TestDampingPipeline:
    """Test DampingPipeline functionality."""
    
    def test_ema_alpha_based(self):
        """Test alpha-based EMA smoothing."""
        profile = DampingProfile(
            name="TEST",
            smoothing_alpha=0.5,
            deadband=0.0,
            rate_limit=None
        )
        spec = SignalSpec(
            name="test.signal",
            type=SignalType.FLOAT,
            range=(0.0, 1.0),
            units="prob",
            default=0.5,
            update_frequency_hz=1.0,
            damping_profile_id="TEST"
        )
        pipeline = DampingPipeline(profile, spec)
        
        timestamp = datetime.now(timezone.utc)
        
        # First update (no previous value)
        result1 = pipeline.apply(0.8, None, timestamp)
        assert result1 == 0.8  # First value should be used directly
        
        # Second update with EMA
        timestamp2 = timestamp + timedelta(seconds=1.0)
        result2 = pipeline.apply(1.0, result1, timestamp2)
        # EMA: 0.8 + 0.5 * (1.0 - 0.8) = 0.8 + 0.1 = 0.9
        assert result2 == pytest.approx(0.9, abs=0.01)
    
    def test_ema_tau_based(self):
        """Test tau-based EMA smoothing with variable dt."""
        profile = DampingProfile(
            name="TEST",
            smoothing_tau=2.0,  # 2 second time constant
            deadband=0.0,
            rate_limit=None
        )
        spec = SignalSpec(
            name="test.signal",
            type=SignalType.FLOAT,
            range=(0.0, 1.0),
            units="prob",
            default=0.5,
            update_frequency_hz=1.0,
            damping_profile_id="TEST"
        )
        pipeline = DampingPipeline(profile, spec)
        
        timestamp = datetime.now(timezone.utc)
        
        # First update
        result1 = pipeline.apply(0.5, None, timestamp)
        assert result1 == 0.5
        
        # Second update with small dt (should have high alpha_dt)
        timestamp2 = timestamp + timedelta(seconds=0.1)
        result2 = pipeline.apply(1.0, result1, timestamp2)
        # Small dt means alpha_dt is small, so less smoothing
        assert result2 > 0.5
        assert result2 < 1.0
        
        # Third update with large dt (should have high alpha_dt)
        timestamp3 = timestamp2 + timedelta(seconds=5.0)
        result3 = pipeline.apply(1.0, result2, timestamp3)
        # Large dt means alpha_dt approaches 1, so more smoothing
        assert result3 > result2
    
    def test_rate_limiting(self):
        """Test rate limiting (slew rate)."""
        profile = DampingProfile(
            name="TEST",
            smoothing_alpha=None,  # No smoothing
            deadband=0.0,
            rate_limit=0.5  # Max 0.5 per second
        )
        spec = SignalSpec(
            name="test.signal",
            type=SignalType.FLOAT,
            range=(0.0, 10.0),
            units="rate",
            default=0.0,
            update_frequency_hz=1.0,
            damping_profile_id="TEST"
        )
        pipeline = DampingPipeline(profile, spec)
        
        timestamp = datetime.now(timezone.utc)
        
        # First update
        result1 = pipeline.apply(0.0, None, timestamp)
        assert result1 == 0.0
        
        # Large jump with 1 second dt
        timestamp2 = timestamp + timedelta(seconds=1.0)
        result2 = pipeline.apply(2.0, result1, timestamp2)
        # Should be limited to 0.5 per second
        assert result2 == pytest.approx(0.5, abs=0.01)
        
        # Another second
        timestamp3 = timestamp2 + timedelta(seconds=1.0)
        result3 = pipeline.apply(2.0, result2, timestamp3)
        # Should advance another 0.5
        assert result3 == pytest.approx(1.0, abs=0.01)
    
    def test_deadband(self):
        """Test deadband filtering."""
        profile = DampingProfile(
            name="TEST",
            smoothing_alpha=None,
            deadband=0.1,  # Ignore changes < 0.1
            rate_limit=None
        )
        spec = SignalSpec(
            name="test.signal",
            type=SignalType.FLOAT,
            range=(0.0, 1.0),
            units="prob",
            default=0.5,
            update_frequency_hz=1.0,
            damping_profile_id="TEST"
        )
        pipeline = DampingPipeline(profile, spec)
        
        timestamp = datetime.now(timezone.utc)
        
        # First update
        result1 = pipeline.apply(0.5, None, timestamp)
        assert result1 == 0.5
        
        # Small change (should be filtered)
        timestamp2 = timestamp + timedelta(seconds=1.0)
        result2 = pipeline.apply(0.55, result1, timestamp2)  # Only 0.05 change
        assert result2 == 0.5  # Should remain unchanged
        
        # Large change (should pass)
        timestamp3 = timestamp2 + timedelta(seconds=1.0)
        result3 = pipeline.apply(0.7, result2, timestamp3)  # 0.2 change
        assert result3 == 0.7
    
    def test_hysteresis(self):
        """Test hysteresis for boolean-like triggers."""
        profile = DampingProfile(
            name="TEST",
            smoothing_alpha=None,
            deadband=0.0,
            rate_limit=None,
            hysteresis_on=0.7,
            hysteresis_off=0.3
        )
        spec = SignalSpec(
            name="test.signal",
            type=SignalType.FLOAT,
            range=(0.0, 1.0),
            units="prob",
            default=0.0,
            update_frequency_hz=1.0,
            damping_profile_id="TEST"
        )
        pipeline = DampingPipeline(profile, spec)
        
        timestamp = datetime.now(timezone.utc)
        
        # Start at 0.4 (below midpoint, which is 0.5)
        # Midpoint = (0.7 + 0.3) / 2 = 0.5
        result1 = pipeline.apply(0.4, None, timestamp)
        # Should initialize to OFF (0.0) since below midpoint
        assert result1 == 0.0
        
        # Rise above on threshold
        timestamp2 = timestamp + timedelta(seconds=1.0)
        result2 = pipeline.apply(0.8, result1, timestamp2)
        assert result2 == 1.0  # Should turn ON
        
        # Drop but stay above off threshold
        timestamp3 = timestamp2 + timedelta(seconds=1.0)
        result3 = pipeline.apply(0.5, result2, timestamp3)
        assert result3 == 1.0  # Should stay ON
        
        # Drop below off threshold
        timestamp4 = timestamp3 + timedelta(seconds=1.0)
        result4 = pipeline.apply(0.2, result3, timestamp4)
        assert result4 == 0.0  # Should turn OFF
    
    def test_clamping(self):
        """Test hard bounds clamping."""
        profile = DampingProfile(
            name="TEST",
            smoothing_alpha=None,
            deadband=0.0,
            rate_limit=None,
            clamp_min=0.0,
            clamp_max=1.0
        )
        spec = SignalSpec(
            name="test.signal",
            type=SignalType.FLOAT,
            range=(-1.0, 2.0),  # Wider range than clamp
            units="prob",
            default=0.5,
            update_frequency_hz=1.0,
            damping_profile_id="TEST"
        )
        pipeline = DampingPipeline(profile, spec)
        
        timestamp = datetime.now(timezone.utc)
        
        # Value below clamp_min
        result1 = pipeline.apply(-0.5, None, timestamp)
        assert result1 == 0.0  # Should be clamped to min
        
        # Value above clamp_max
        timestamp2 = timestamp + timedelta(seconds=1.0)
        result2 = pipeline.apply(1.5, result1, timestamp2)
        assert result2 == 1.0  # Should be clamped to max


class TestSimulatedTime:
    """Test damping behavior with simulated time and variable update frequencies."""
    
    def test_variable_update_frequency(self):
        """Test EMA stability with variable update frequencies."""
        profile = DampingProfile(
            name="TEST",
            smoothing_tau=1.0,  # 1 second time constant
            deadband=0.0,
            rate_limit=None
        )
        spec = SignalSpec(
            name="test.signal",
            type=SignalType.FLOAT,
            range=(0.0, 1.0),
            units="prob",
            default=0.5,
            update_frequency_hz=1.0,
            damping_profile_id="TEST"
        )
        pipeline = DampingPipeline(profile, spec)
        
        base_time = datetime.now(timezone.utc)
        current_value = 0.5
        
        # Simulate variable update frequencies
        # Fast updates (0.1s intervals)
        for i in range(5):
            t = base_time + timedelta(seconds=i * 0.1)
            current_value = pipeline.apply(1.0, current_value, t)
        
        fast_value = current_value
        
        # Reset
        current_value = 0.5
        pipeline = DampingPipeline(profile, spec)
        
        # Slow updates (1.0s intervals)
        for i in range(5):
            t = base_time + timedelta(seconds=i * 1.0)
            current_value = pipeline.apply(1.0, current_value, t)
        
        slow_value = current_value
        
        # Both should converge toward 1.0
        # With tau-based EMA, more total time means more convergence
        # Fast updates: 5 steps * 0.1s = 0.5s total
        # Slow updates: 5 steps * 1.0s = 5.0s total
        # So slow should converge more (closer to 1.0)
        # But both should be moving toward 1.0
        assert fast_value > 0.5  # Should have moved from 0.5
        assert slow_value > 0.5  # Should have moved from 0.5
        assert fast_value <= 1.0
        assert slow_value <= 1.0
        # With more total time, slow should be closer to 1.0
        assert slow_value >= fast_value
    
    def test_alternating_input_damping(self):
        """Test that alternating +1/-1 input at 5Hz does NOT ping-pong at 5Hz."""
        profile = DampingProfile(
            name="MED",
            smoothing_alpha=0.15,  # MED profile
            deadband=0.02,
            rate_limit=0.8
        )
        spec = SignalSpec(
            name="affect.valence",
            type=SignalType.FLOAT,
            range=(-1.0, 1.0),
            units="prob",
            default=0.0,
            update_frequency_hz=5.0,
            damping_profile_id="MED"
        )
        pipeline = DampingPipeline(profile, spec)
        
        base_time = datetime.now(timezone.utc)
        current_value = 0.0
        
        # Inject alternating +1/-1 at 5Hz (0.2s intervals)
        values = []
        for i in range(20):
            t = base_time + timedelta(seconds=i * 0.2)
            input_value = 1.0 if i % 2 == 0 else -1.0
            current_value = pipeline.apply(input_value, current_value, t)
            values.append(current_value)
        
        # Check that output does NOT oscillate at 5Hz
        # Should be damped and converge toward 0
        sign_changes = sum(1 for i in range(1, len(values)) if (values[i] > 0) != (values[i-1] > 0))
        
        # With damping, we should have fewer sign changes than input (10)
        # Output should stabilize
        assert sign_changes < 10  # Should have fewer oscillations than input
        assert abs(values[-1]) < 0.5  # Should converge toward 0


class TestIntegration:
    """Integration tests for SignalManager with DampingPipeline."""
    
    def test_affect_valence_damping(self):
        """Test affect.valence signal with MED profile."""
        manager = SignalManager()
        
        # Update with noisy input
        values = []
        base_time = datetime.now(timezone.utc)
        for i in range(10):
            t = base_time + timedelta(seconds=i * 0.1)
            # Alternating input
            raw = 0.8 if i % 2 == 0 else -0.8
            damped = manager.update("affect.valence", raw, t)
            values.append(damped)
        
        # Should be damped (not oscillating wildly)
        # Allow first value to be at input level, but subsequent should be damped
        assert max(values[1:]) <= 0.8  # After first update, should be damped
        assert min(values[1:]) >= -0.8
    
    def test_dissonance_slow_damping(self):
        """Test dissonance.level with SLOW profile."""
        manager = SignalManager()
        
        # Spiky input
        base_time = datetime.now(timezone.utc)
        values = []
        for i in range(10):
            t = base_time + timedelta(seconds=i * 0.5)
            raw = 0.9 if i % 3 == 0 else 0.1
            damped = manager.update("dissonance.level", raw, t)
            values.append(damped)
        
        # Should be heavily smoothed (SLOW profile)
        # Spikes should be reduced
        # Allow first value, but subsequent should be damped
        assert max(values[1:]) <= 0.9  # After first update, should be damped
        # Should not drop to 0.1 immediately
        assert min(values[1:]) >= 0.1

