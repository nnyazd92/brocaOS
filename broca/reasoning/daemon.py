"""
Autonomous reasoning daemon.

Runs reasoning cycles independently, maintains state, and implements
feedback loops for continuous improvement.
"""

from __future__ import annotations

import signal
import threading
import time
import logging
import queue
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from enum import Enum

if TYPE_CHECKING:
    from .integration_tool import ReasoningTool
    from .state_manager import ReasoningStateManager
    from .feedback_loop import FeedbackLoopManager
    from .self_model_feedback import SelfModelFeedbackLoop
    from ..learning.integration_tool import LearningTool

logger = logging.getLogger(__name__)


class DaemonStatus(Enum):
    """Status of reasoning daemon."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"


class ReasoningDaemon:
    """
    Autonomous reasoning daemon.
    
    Runs reasoning cycles independently with:
    - Hybrid triggering (time-based + event acceleration)
    - State persistence
    - Feedback loop integration
    - Graceful shutdown
    """
    
    def __init__(
        self,
        reasoning_tool: "ReasoningTool",
        state_manager: Optional["ReasoningStateManager"] = None,
        feedback_loop_manager: Optional["FeedbackLoopManager"] = None,
        self_model_feedback_loop: Optional["SelfModelFeedbackLoop"] = None,
        learning_tool: Optional["LearningTool"] = None,
        affect_monitor: Optional[Any] = None,
        cycle_delay_seconds: float = 30.0,
        event_acceleration_enabled: bool = True,
        max_cycles_per_minute: int = 10,
        max_rules_per_cycle: int = 5
    ):
        """
        Initialize reasoning daemon.
        
        Args:
            reasoning_tool: ReasoningTool instance to use for cycles
            state_manager: Optional state manager for persistence
            feedback_loop_manager: Optional feedback loop manager
            self_model_feedback_loop: Optional self model feedback loop for updates
            learning_tool: Optional learning tool for learning-reasoning integration
            affect_monitor: Optional ComputationalAffectMonitor for emotional state integration
            cycle_delay_seconds: Base delay between cycles
            event_acceleration_enabled: Enable event-based acceleration
            max_cycles_per_minute: Maximum cycles per minute (rate limiting)
            max_rules_per_cycle: Maximum number of rules to fire per cycle
        """
        self.reasoning_tool = reasoning_tool
        self.state_manager = state_manager
        self.feedback_loop_manager = feedback_loop_manager
        self.self_model_feedback_loop = self_model_feedback_loop
        self.learning_tool = learning_tool
        self.affect_monitor = affect_monitor
        
        self.cycle_delay = cycle_delay_seconds
        self.base_cycle_delay = cycle_delay_seconds
        self.event_acceleration_enabled = event_acceleration_enabled
        self.max_cycles_per_minute = max_cycles_per_minute
        self.min_cycle_interval = 60.0 / max_cycles_per_minute  # Minimum seconds between cycles
        self.max_rules_per_cycle = max_rules_per_cycle
        
        # State
        self.status = DaemonStatus.STOPPED
        self.shutdown_requested = False
        self.paused = False
        self._lock = threading.RLock()
        
        # Event queue for event-based acceleration
        self.event_queue: queue.Queue = queue.Queue()
        self.last_cycle_time = 0.0
        self.cycle_count = 0
        self.cycle_history: List[Dict[str, Any]] = []
        
        # Thread management
        self._daemon_thread: Optional[threading.Thread] = None
        
        logger.info(f"Initialized ReasoningDaemon (delay={cycle_delay_seconds}s, max_cycles/min={max_cycles_per_minute})")
    
    def start(self) -> bool:
        """
        Start daemon in background thread.
        
        Returns:
            True if started successfully, False otherwise
        """
        with self._lock:
            if self.status == DaemonStatus.RUNNING:
                logger.warning("Daemon is already running")
                return False
            
            if self.status == DaemonStatus.SHUTTING_DOWN:
                logger.warning("Daemon is shutting down, cannot start")
                return False
            
            # Set up signal handlers
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # Load state if available
            if self.state_manager:
                try:
                    self.state_manager.load_state(
                        rule_system=self.reasoning_tool.rule_system,
                        goal_manager=self.reasoning_tool.goal_manager,
                        working_memory=self.reasoning_tool.rule_system.working_memory
                    )
                    logger.info("Loaded state from state manager")
                except Exception as e:
                    logger.error(f"Failed to load state: {e}", exc_info=True)
            
            # Start daemon thread
            self.shutdown_requested = False
            self.paused = False
            self.status = DaemonStatus.RUNNING
            
            self._daemon_thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="ReasoningDaemon"
            )
            self._daemon_thread.start()
            
            logger.info("Reasoning daemon started")
            return True
    
    def stop(self) -> bool:
        """
        Stop daemon gracefully.
        
        Returns:
            True if stopped successfully
        """
        with self._lock:
            if self.status == DaemonStatus.STOPPED:
                return True
            
            logger.info("Stopping reasoning daemon...")
            self.shutdown_requested = True
            self.status = DaemonStatus.SHUTTING_DOWN
            
            # Wait for thread to finish (with timeout)
            if self._daemon_thread and self._daemon_thread.is_alive():
                self._daemon_thread.join(timeout=5.0)
                if self._daemon_thread.is_alive():
                    logger.warning("Daemon thread did not stop within timeout")
            
            # Save state before stopping
            if self.state_manager:
                try:
                    self.state_manager.save_state(
                        rule_system=self.reasoning_tool.rule_system,
                        goal_manager=self.reasoning_tool.goal_manager,
                        working_memory=self.reasoning_tool.rule_system.working_memory,
                        force=True
                    )
                    logger.info("Saved state before stopping")
                except Exception as e:
                    logger.error(f"Failed to save state: {e}", exc_info=True)
            
            self.status = DaemonStatus.STOPPED
            logger.info("Reasoning daemon stopped")
            return True
    
    def pause(self) -> bool:
        """Pause daemon (cycles stop, but state is maintained)."""
        with self._lock:
            if self.status != DaemonStatus.RUNNING:
                return False
            self.paused = True
            self.status = DaemonStatus.PAUSED
            logger.info("Reasoning daemon paused")
            return True
    
    def resume(self) -> bool:
        """Resume daemon from pause."""
        with self._lock:
            if self.status != DaemonStatus.PAUSED:
                return False
            self.paused = False
            self.status = DaemonStatus.RUNNING
            logger.info("Reasoning daemon resumed")
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get daemon status information."""
        with self._lock:
            return {
                "status": self.status.value,
                "cycle_count": self.cycle_count,
                "last_cycle_time": self.last_cycle_time,
                "cycle_delay": self.cycle_delay,
                "base_cycle_delay": self.base_cycle_delay,
                "pending_events": self.event_queue.qsize(),
                "paused": self.paused
            }
    
    def notify_event(self, event_type: str, event_data: Optional[Dict[str, Any]] = None):
        """
        Notify daemon of an event (for event-based acceleration).
        
        Args:
            event_type: Type of event (STATE_CHANGED, GOAL_READY, etc.)
            event_data: Optional event data
        """
        if not self.event_acceleration_enabled:
            return
        
        event = {
            "type": event_type,
            "data": event_data or {},
            "timestamp": time.time()
        }
        
        try:
            self.event_queue.put_nowait(event)
            logger.debug(f"Queued event: {event_type}")
        except queue.Full:
            logger.warning(f"Event queue full, dropping event: {event_type}")
    
    def _signal_handler(self, signum: int, frame: Any):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def _run_loop(self):
        """Main daemon loop (runs in background thread)."""
        logger.info("Reasoning daemon loop started")
        
        try:
            while not self.shutdown_requested:
                # Check if paused
                if self.paused:
                    time.sleep(1.0)
                    continue
                
                # Check for events (non-blocking)
                event_triggered = False
                if self.event_acceleration_enabled:
                    try:
                        event = self.event_queue.get_nowait()
                        event_triggered = True
                        logger.debug(f"Processing event: {event['type']}")
                        # Accelerate cycle (reduce delay)
                        self.cycle_delay = max(self.min_cycle_interval, self.base_cycle_delay * 0.3)
                    except queue.Empty:
                        pass
                
                # Calculate delay (reset to base if no events for a while)
                current_time = time.time()
                if not event_triggered and current_time - self.last_cycle_time > self.base_cycle_delay * 2:
                    self.cycle_delay = self.base_cycle_delay
                
                # Check rate limiting
                time_since_last_cycle = current_time - self.last_cycle_time
                if time_since_last_cycle < self.min_cycle_interval:
                    sleep_time = self.min_cycle_interval - time_since_last_cycle
                    time.sleep(sleep_time)
                    continue
                
                # Execute cycle
                cycle_success = self._execute_cycle()
                
                if cycle_success:
                    self.cycle_count += 1
                    self.last_cycle_time = time.time()
                else:
                    logger.warning("Cycle failed, will retry after delay")
                
                # Wait before next cycle
                if not self.shutdown_requested:
                    sleep_time = self.cycle_delay
                    logger.debug(f"Waiting {sleep_time:.1f}s before next cycle...")
                    time.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"Unexpected error in daemon loop: {e}", exc_info=True)
        finally:
            with self._lock:
                self.status = DaemonStatus.STOPPED
            logger.info("Reasoning daemon loop ended")
    
    def _execute_cycle(self) -> bool:
        """
        Execute one reasoning cycle.
        
        Returns:
            True if cycle executed successfully, False otherwise
        """
        try:
            cycle_start_time = time.time()
            
            # Get ready goals
            ready_goals = self.reasoning_tool.goal_manager.get_ready_goals()
            
            if not ready_goals:
                logger.debug("No ready goals, skipping cycle")
                return True  # Not an error, just nothing to do
            
            # Execute reasoning cycle
            cycle_results = self.reasoning_tool.rule_engine.execute_cycle(
                working_memory=self.reasoning_tool.rule_system.working_memory,
                max_rules=self.max_rules_per_cycle
            )
            
            cycle_duration = time.time() - cycle_start_time
            
            # Evaluate outcomes with feedback loop
            cycle_outcome = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration": cycle_duration,
                "rules_fired": len(cycle_results),
                "results": cycle_results,
                "goals_processed": len(ready_goals)
            }
            
            metrics = None
            if self.feedback_loop_manager:
                try:
                    # Ensure cognitive dissonance history is populated with "real" measurements.
                    # Without this, consumers (RL signals, goal progress) will see has_data=False and
                    # fall back to neutral defaults (e.g., dissonance_reward=0.5).
                    if getattr(self.feedback_loop_manager, "cognitive_dissonance_monitor", None):
                        try:
                            # Best-effort: convert ready goals to dicts if needed.
                            reasoning_goals = []
                            for g in (ready_goals or []):
                                if isinstance(g, dict):
                                    reasoning_goals.append(g)
                                else:
                                    reasoning_goals.append({
                                        "name": getattr(g, "name", str(g)),
                                        "priority": getattr(g, "priority", None),
                                        "description": getattr(g, "description", None),
                                        "status": getattr(getattr(g, "status", None), "value", getattr(g, "status", None)),
                                    })

                            self.feedback_loop_manager.cognitive_dissonance_monitor.measure_dissonance(
                                response=None,
                                tool_usage=cycle_results if isinstance(cycle_results, list) else None,
                                reasoning_goals=reasoning_goals if reasoning_goals else None,
                                conversation_context=None,
                            )
                        except Exception as e:
                            logger.warning(f"Failed to measure cognitive dissonance in daemon cycle: {e}", exc_info=True)

                    metrics = self.feedback_loop_manager.evaluate_cycle_outcomes(cycle_outcome)
                    self.feedback_loop_manager.apply_feedback(metrics)
                except Exception as e:
                    logger.error(f"Error in feedback loop: {e}", exc_info=True)
            
            # Cognitive dissonance monitoring and self model updates
            if self.self_model_feedback_loop:
                try:
                    # Increment cycle count for periodic updates
                    self.self_model_feedback_loop.increment_cycle_count()
                    
                    # Get current dissonance metrics (if available from feedback loop or monitor)
                    dissonance_metrics = None
                    if self.feedback_loop_manager and metrics and hasattr(metrics, 'overall_dissonance'):
                        # Create a simple DissonanceMetrics from feedback metrics
                        from .cognitive_dissonance import DissonanceMetrics
                        dissonance_metrics = DissonanceMetrics(
                            timestamp=datetime.now(timezone.utc),
                            logical_dissonance=getattr(metrics, 'logical_dissonance', 0.0),
                            factual_dissonance=getattr(metrics, 'factual_dissonance', 0.0),
                            behavioral_dissonance=getattr(metrics, 'behavioral_dissonance', 0.0),
                            goal_dissonance=getattr(metrics, 'goal_dissonance', 0.0),
                            overall_dissonance=getattr(metrics, 'overall_dissonance', 0.0)
                        )
                    elif hasattr(self.feedback_loop_manager, 'cognitive_dissonance_monitor') and self.feedback_loop_manager.cognitive_dissonance_monitor:
                        # Get from monitor directly
                        dissonance_data = self.feedback_loop_manager.cognitive_dissonance_monitor.get_aggregated_dissonance()
                        from .cognitive_dissonance import DissonanceMetrics
                        dissonance_metrics = DissonanceMetrics(
                            timestamp=datetime.now(timezone.utc),
                            logical_dissonance=dissonance_data.get("logical_dissonance", 0.0),
                            factual_dissonance=dissonance_data.get("factual_dissonance", 0.0),
                            behavioral_dissonance=dissonance_data.get("behavioral_dissonance", 0.0),
                            goal_dissonance=dissonance_data.get("goal_dissonance", 0.0),
                            overall_dissonance=dissonance_data.get("overall_dissonance", 0.0)
                        )
                    
                    # Check if update should be triggered
                    if dissonance_metrics and self.self_model_feedback_loop.should_update(dissonance_metrics):
                        self.self_model_feedback_loop.trigger_update(
                            dissonance_metrics=dissonance_metrics,
                            response=None,  # No response available in cycle context
                            conversation_context=None
                        )
                except Exception as e:
                    logger.error(f"Error in self model feedback loop: {e}", exc_info=True)
            
            # Learning system integration with emotional state
            if self.learning_tool:
                try:
                    # Get emotional state from affect monitor if available
                    emotional_state = None
                    if self.affect_monitor:
                        try:
                            emotional_state = self.affect_monitor.sample_affective_state()
                        except Exception as e:
                            logger.debug(f"Error sampling emotional state from affect monitor: {e}")
                    
                    # Observe cycle outcomes for learning with emotional context
                    cycle_context = {
                        "cycle_outcome": cycle_outcome,
                        "dissonance": getattr(metrics, 'overall_dissonance', None) if metrics else None,
                        "success_rate": getattr(metrics, 'success_rate', None) if metrics else None
                    }
                    
                    # Include emotional state in learning context
                    if emotional_state:
                        cycle_context["emotional_state"] = emotional_state
                    
                    # If we have dissonance metrics, learn from them
                    if dissonance_metrics and emotional_state:
                        # Update affect monitor from dissonance
                        if self.affect_monitor:
                            try:
                                dissonance_dict = {
                                    "overall_dissonance": dissonance_metrics.overall_dissonance,
                                    "logical_dissonance": dissonance_metrics.logical_dissonance,
                                    "factual_dissonance": dissonance_metrics.factual_dissonance,
                                    "behavioral_dissonance": dissonance_metrics.behavioral_dissonance,
                                    "goal_dissonance": dissonance_metrics.goal_dissonance,
                                    "timestamp": dissonance_metrics.timestamp
                                }
                                self.affect_monitor.update_from_dissonance(dissonance_dict)
                            except Exception as e:
                                logger.debug(f"Error updating affect from dissonance: {e}", exc_info=True)
                    
                    # Get learned procedures/skills for future cycles
                    # (Would be used in next cycle's goal achievement)
                    
                except Exception as e:
                    logger.debug(f"Error in learning system integration: {e}", exc_info=True)
            
            # Record cycle in history
            self.cycle_history.append(cycle_outcome)
            if len(self.cycle_history) > 100:
                self.cycle_history = self.cycle_history[-100:]
            
            # Save state
            if self.state_manager:
                try:
                    self.state_manager.mark_changed()
                    self.state_manager.save_state(
                        rule_system=self.reasoning_tool.rule_system,
                        goal_manager=self.reasoning_tool.goal_manager,
                        working_memory=self.reasoning_tool.rule_system.working_memory
                    )
                except Exception as e:
                    logger.error(f"Error saving state: {e}", exc_info=True)
            
            logger.debug(f"Cycle executed successfully (duration: {cycle_duration:.2f}s, rules: {len(cycle_results)})")
            return True
            
        except Exception as e:
            logger.error(f"Error executing reasoning cycle: {e}", exc_info=True)
            return False

