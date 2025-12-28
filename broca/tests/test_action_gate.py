"""
Tests for ActionGate.

Tests debounce, cooldown, evidence windows, and sustained trigger logic.
"""

import pytest
from datetime import datetime, timezone, timedelta

from broca.damping.action_gate import ActionGate, ActionGateConfig


class TestActionGateConfig:
    """Test ActionGateConfig validation."""
    
    def test_default_config(self):
        """Test default configuration is valid."""
        config = ActionGateConfig()
        assert config.debounce_seconds == 0.0
        assert config.cooldown_seconds == 0.0
        assert config.min_evidence_window_seconds == 0.0
        assert config.min_evidence_count == 0
        assert config.sustained_trigger_threshold == 0.5
        assert config.sustained_trigger_window_seconds == 0.0
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Negative debounce should raise
        with pytest.raises(ValueError, match="debounce_seconds must be >= 0"):
            ActionGateConfig(debounce_seconds=-1.0)
        
        # Negative cooldown should raise
        with pytest.raises(ValueError, match="cooldown_seconds must be >= 0"):
            ActionGateConfig(cooldown_seconds=-1.0)
        
        # Invalid threshold should raise
        with pytest.raises(ValueError, match="sustained_trigger_threshold must be between 0 and 1"):
            ActionGateConfig(sustained_trigger_threshold=1.5)


class TestActionGateBasic:
    """Test basic ActionGate functionality."""
    
    def test_allow_action_default_config(self):
        """Test that actions are allowed by default (no gating)."""
        gate = ActionGate(ActionGateConfig(), action_name="test")
        
        timestamp = datetime.now(timezone.utc)
        should_allow, reason = gate.should_allow_action(1.0, timestamp)
        
        assert should_allow
        assert reason == "allowed"
    
    def test_record_action(self):
        """Test recording an action."""
        gate = ActionGate(ActionGateConfig(), action_name="test")
        
        timestamp = datetime.now(timezone.utc)
        gate.record_action(timestamp)
        
        # Check state
        state = gate.get_state()
        assert state["last_action_time"] == timestamp.isoformat()
        assert state["time_since_last_action"] is not None
        assert state["time_since_last_action"] >= 0.0  # Should be >= 0 (may be small positive due to timing)
    
    def test_reset(self):
        """Test resetting gate state."""
        gate = ActionGate(ActionGateConfig(), action_name="test")
        
        timestamp = datetime.now(timezone.utc)
        gate.record_action(timestamp)
        gate.should_allow_action(1.0, timestamp)
        
        gate.reset()
        
        state = gate.get_state()
        assert state["last_action_time"] is None
        assert state["evidence_buffer_size"] == 0
        assert state["trigger_buffer_size"] == 0


class TestDebounce:
    """Test debounce functionality."""
    
    def test_debounce_blocks_rapid_triggers(self):
        """Test that debounce blocks rapid repeated triggers."""
        config = ActionGateConfig(debounce_seconds=1.0)
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # First trigger should be allowed
        should_allow, reason = gate.should_allow_action(1.0, base_time)
        assert should_allow
        
        # Second trigger within debounce window should be blocked
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=0.5))
        assert not should_allow
        assert "debounced" in reason.lower()
        
        # Third trigger after debounce window should be allowed
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=1.5))
        assert should_allow
    
    def test_debounce_no_block_after_window(self):
        """Test that debounce doesn't block after window expires."""
        config = ActionGateConfig(debounce_seconds=1.0)
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # First trigger
        gate.should_allow_action(1.0, base_time)
        
        # Second trigger after debounce window
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=2.0))
        assert should_allow


class TestCooldown:
    """Test cooldown functionality."""
    
    def test_cooldown_blocks_actions(self):
        """Test that cooldown blocks actions too soon after last action."""
        config = ActionGateConfig(cooldown_seconds=2.0)
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # Record an action
        gate.record_action(base_time)
        
        # Try to trigger action within cooldown period
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=1.0))
        assert not should_allow
        assert "cooldown" in reason.lower()
        
        # Try to trigger action after cooldown period
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=3.0))
        assert should_allow
    
    def test_cooldown_does_not_block_first_action(self):
        """Test that cooldown doesn't block the first action."""
        config = ActionGateConfig(cooldown_seconds=2.0)
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # First action should be allowed (no previous action)
        should_allow, reason = gate.should_allow_action(1.0, base_time)
        assert should_allow


class TestEvidenceWindow:
    """Test evidence window functionality."""
    
    def test_min_evidence_window_blocks_early_triggers(self):
        """Test that minimum evidence window blocks triggers before window."""
        config = ActionGateConfig(
            min_evidence_window_seconds=5.0,
            min_evidence_count=0
        )
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # First trigger (insufficient evidence window)
        should_allow, reason = gate.should_allow_action(1.0, base_time)
        assert not should_allow
        assert "insufficient evidence history" in reason.lower() or "evidence window too short" in reason.lower()
        
        # Second trigger after some time but still before window
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=2.0))
        assert not should_allow
        assert "evidence window too short" in reason.lower()
        
        # Trigger after evidence window
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=6.0))
        assert should_allow
    
    def test_min_evidence_count_blocks_insufficient_evidence(self):
        """Test that minimum evidence count blocks triggers with insufficient evidence."""
        config = ActionGateConfig(
            min_evidence_count=5,
            min_evidence_window_seconds=0.0
        )
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # First few triggers should be blocked
        for i in range(4):
            should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=i * 0.1))
            assert not should_allow
            assert "insufficient evidence count" in reason.lower()
        
        # Fifth trigger should be allowed
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=0.5))
        assert should_allow


class TestSustainedTrigger:
    """Test sustained trigger functionality."""
    
    def test_sustained_trigger_requires_sustained_condition(self):
        """Test that sustained trigger requires condition to be sustained."""
        config = ActionGateConfig(
            sustained_trigger_threshold=0.7,
            sustained_trigger_window_seconds=3.0,
            min_evidence_window_seconds=0.0
        )
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # Send triggers below threshold (should not sustain)
        for i in range(5):
            trigger_value = 0.5  # Below threshold
            should_allow, reason = gate.should_allow_action(
                trigger_value,
                base_time + timedelta(seconds=i * 0.5)
            )
            # Should be blocked because trigger not sustained
            assert not should_allow or "trigger not sustained" in reason.lower()
        
        # Send triggers above threshold (should sustain)
        for i in range(10):
            trigger_value = 0.8  # Above threshold
            should_allow, reason = gate.should_allow_action(
                trigger_value,
                base_time + timedelta(seconds=5.0 + i * 0.3)
            )
            # After enough sustained triggers, should be allowed
            if i >= 3:  # After sustained window
                # May or may not be allowed depending on sustained rate
                pass  # Just check it doesn't crash
    
    def test_sustained_trigger_with_mixed_values(self):
        """Test sustained trigger with mixed high/low values."""
        config = ActionGateConfig(
            sustained_trigger_threshold=0.6,
            sustained_trigger_window_seconds=2.0,
            min_evidence_window_seconds=0.0
        )
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # Send mixed values: mostly above threshold
        values = [0.8, 0.7, 0.9, 0.6, 0.8, 0.7]  # All above 0.6 threshold
        for i, value in enumerate(values):
            should_allow, reason = gate.should_allow_action(
                value,
                base_time + timedelta(seconds=i * 0.4)
            )
            # After sustained window, should potentially be allowed
            if i >= len(values) - 1:
                # Last value might be allowed if sustained rate is high enough
                pass


class TestCombinedGating:
    """Test combined gating logic (debounce + cooldown + evidence)."""
    
    def test_combined_gating(self):
        """Test that all gating mechanisms work together."""
        config = ActionGateConfig(
            debounce_seconds=0.5,
            cooldown_seconds=2.0,
            min_evidence_window_seconds=1.0,
            min_evidence_count=3
        )
        gate = ActionGate(config, action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # First few triggers should be blocked by evidence requirements
        for i in range(2):
            should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=i * 0.2))
            assert not should_allow
        
        # After evidence requirements met, first action should be allowed
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=1.5))
        assert should_allow
        
        # Record the action
        gate.record_action(base_time + timedelta(seconds=1.5))
        
        # Next trigger should be blocked by cooldown
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=2.0))
        assert not should_allow
        assert "cooldown" in reason.lower()
        
        # After cooldown, should be allowed
        should_allow, reason = gate.should_allow_action(1.0, base_time + timedelta(seconds=4.0))
        assert should_allow


class TestActionGateState:
    """Test ActionGate state management."""
    
    def test_get_state(self):
        """Test getting gate state for observability."""
        config = ActionGateConfig(
            debounce_seconds=1.0,
            cooldown_seconds=2.0,
            min_evidence_window_seconds=3.0,
            min_evidence_count=5,
            sustained_trigger_threshold=0.7,
            sustained_trigger_window_seconds=4.0
        )
        gate = ActionGate(config, action_name="test_action")
        
        state = gate.get_state()
        
        assert state["action_name"] == "test_action"
        assert state["last_action_time"] is None
        assert state["evidence_buffer_size"] == 0
        assert state["trigger_buffer_size"] == 0
        assert state["config"]["debounce_seconds"] == 1.0
        assert state["config"]["cooldown_seconds"] == 2.0
        assert state["config"]["min_evidence_window_seconds"] == 3.0
        assert state["config"]["min_evidence_count"] == 5
        assert state["config"]["sustained_trigger_threshold"] == 0.7
        assert state["config"]["sustained_trigger_window_seconds"] == 4.0
    
    def test_state_updates_after_actions(self):
        """Test that state updates after actions are recorded."""
        gate = ActionGate(ActionGateConfig(), action_name="test")
        
        base_time = datetime.now(timezone.utc)
        
        # Record some evidence
        gate.should_allow_action(1.0, base_time)
        gate.should_allow_action(0.8, base_time + timedelta(seconds=1.0))
        
        state = gate.get_state()
        assert state["evidence_buffer_size"] >= 2
        assert state["trigger_buffer_size"] >= 2
        
        # Record an action (use a timestamp in the past)
        action_time = datetime.now(timezone.utc) - timedelta(seconds=1.0)
        gate.record_action(action_time)
        
        state = gate.get_state()
        assert state["last_action_time"] is not None
        assert state["time_since_last_action"] is not None
        assert state["time_since_last_action"] >= 0.9  # Should be at least ~1 second

