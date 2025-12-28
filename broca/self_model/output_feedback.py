"""
Output Feedback System for Self-Model.

Monitors outputs and actions, detects patterns, and triggers self-model updates
based on system behavior. Creates bidirectional feedback: output -> self-model, self-model -> output.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import SelfModel


@dataclass
class OutputEvent:
    """Represents an output event for feedback."""
    timestamp: datetime
    event_type: str  # "response", "tool_execution", "action"
    content: str
    metadata: Dict[str, Any]


@dataclass
class Pattern:
    """Detected pattern from output events."""
    pattern_type: str
    description: str
    confidence: float
    frequency: int
    examples: List[OutputEvent]
    suggested_updates: Optional[Dict[str, Any]] = None


class OutputMonitor:
    """
    Monitors LLM responses and tool executions.
    
    Tracks output events for pattern detection and feedback.
    """
    
    def __init__(self, history_window: int = 100):
        """
        Initialize output monitor.
        
        Args:
            history_window: Number of events to keep in history
        """
        self.history_window = history_window
        self.event_history: deque[OutputEvent] = deque(maxlen=history_window)
        logger.info("Initialized OutputMonitor")
    
    def record_response(
        self,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an LLM response.
        
        Args:
            response: LLM response text
            metadata: Optional metadata about the response
        """
        event = OutputEvent(
            timestamp=datetime.now(timezone.utc),
            event_type="response",
            content=response,
            metadata=metadata or {}
        )
        self.event_history.append(event)
    
    def record_tool_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a tool execution.
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Tool execution result
            metadata: Optional metadata
        """
        event = OutputEvent(
            timestamp=datetime.now(timezone.utc),
            event_type="tool_execution",
            content=f"Tool: {tool_name}",
            metadata={
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                **(metadata or {})
            }
        )
        self.event_history.append(event)
    
    def get_recent_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 20
    ) -> List[OutputEvent]:
        """
        Get recent events, optionally filtered by type.
        
        Args:
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        events = list(self.event_history)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]


class PatternDetector:
    """
    Detects patterns in outputs that should influence self-model.
    
    Analyzes event history to identify recurring patterns, inconsistencies,
    or behavioral changes that warrant self-model updates.
    """
    
    def __init__(self):
        """Initialize pattern detector."""
        logger.info("Initialized PatternDetector")
    
    def detect_patterns(
        self,
        events: List[OutputEvent]
    ) -> List[Pattern]:
        """
        Detect patterns in output events.
        
        Args:
            events: List of output events to analyze
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Pattern: Frequent tool usage (suggests capability)
        tool_patterns = self._detect_tool_usage_patterns(events)
        patterns.extend(tool_patterns)
        
        # Pattern: Consistent response style (suggests behavioral pattern)
        style_patterns = self._detect_response_style_patterns(events)
        patterns.extend(style_patterns)
        
        # Pattern: Repeated failures (suggests knowledge boundary)
        failure_patterns = self._detect_failure_patterns(events)
        patterns.extend(failure_patterns)
        
        return patterns
    
    def _detect_tool_usage_patterns(
        self,
        events: List[OutputEvent]
    ) -> List[Pattern]:
        """Detect patterns in tool usage."""
        patterns = []
        
        tool_events = [e for e in events if e.event_type == "tool_execution"]
        if len(tool_events) < 3:
            return patterns
        
        # Count tool usage
        tool_counts: Dict[str, int] = {}
        for event in tool_events:
            tool_name = event.metadata.get("tool_name", "unknown")
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        # If a tool is used frequently, suggest it as a capability
        total_tools = len(tool_events)
        for tool_name, count in tool_counts.items():
            frequency = count / total_tools if total_tools > 0 else 0.0
            if frequency > 0.2:  # Used in >20% of tool calls
                pattern = Pattern(
                    pattern_type="frequent_tool_usage",
                    description=f"Frequently uses tool: {tool_name}",
                    confidence=min(1.0, frequency),
                    frequency=count,
                    examples=tool_events[-5:],
                    suggested_updates={
                        "capabilities": [f"Can use {tool_name} tool effectively"]
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_response_style_patterns(
        self,
        events: List[OutputEvent]
    ) -> List[Pattern]:
        """Detect patterns in response style."""
        patterns = []
        
        response_events = [e for e in events if e.event_type == "response"]
        if len(response_events) < 5:
            return patterns
        
        # Simple heuristic: check response length patterns
        lengths = [len(e.content) for e in response_events]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        # Detect if consistently verbose or concise
        if avg_length > 500:
            pattern = Pattern(
                pattern_type="response_style",
                description="Tends to provide detailed, verbose responses",
                confidence=0.7,
                frequency=len(response_events),
                examples=response_events[-3:],
                suggested_updates={
                    "capabilities": ["Provides detailed explanations and thorough responses"]
                }
            )
            patterns.append(pattern)
        elif avg_length < 100:
            pattern = Pattern(
                pattern_type="response_style",
                description="Tends to provide concise, direct responses",
                confidence=0.7,
                frequency=len(response_events),
                examples=response_events[-3:],
                suggested_updates={
                    "capabilities": ["Provides concise, direct responses"]
                }
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_failure_patterns(
        self,
        events: List[OutputEvent]
    ) -> List[Pattern]:
        """Detect patterns of repeated failures."""
        patterns = []
        
        tool_events = [e for e in events if e.event_type == "tool_execution"]
        if len(tool_events) < 3:
            return patterns
        
        # Check for repeated failures
        failure_tools: Dict[str, int] = {}
        for event in tool_events:
            result = event.metadata.get("result", {})
            if not result.get("success", True):
                tool_name = event.metadata.get("tool_name", "unknown")
                failure_tools[tool_name] = failure_tools.get(tool_name, 0) + 1
        
        # If a tool fails frequently, suggest knowledge boundary
        for tool_name, failure_count in failure_tools.items():
            total_uses = sum(1 for e in tool_events if e.metadata.get("tool_name") == tool_name)
            if total_uses > 0:
                failure_rate = failure_count / total_uses
                if failure_rate > 0.5:  # Fails >50% of the time
                    pattern = Pattern(
                        pattern_type="repeated_failure",
                        description=f"Frequently fails when using tool: {tool_name}",
                        confidence=min(1.0, failure_rate),
                        frequency=failure_count,
                        examples=[e for e in tool_events if e.metadata.get("tool_name") == tool_name][-3:],
                        suggested_updates={
                            "knowledge_boundaries": {
                                f"tool_usage_{tool_name}": f"Limited effectiveness with {tool_name} tool"
                            }
                        }
                    )
                    patterns.append(pattern)
        
        return patterns


class FeedbackAggregator:
    """
    Aggregates feedback from multiple sources.
    
    Combines feedback from responses, tool usage, consistency violations,
    and user feedback (if available).
    """
    
    def __init__(self):
        """Initialize feedback aggregator."""
        self.feedback_sources: List[Dict[str, Any]] = []
        logger.info("Initialized FeedbackAggregator")
    
    def add_feedback(
        self,
        source: str,
        feedback_data: Dict[str, Any]
    ) -> None:
        """
        Add feedback from a source.
        
        Args:
            source: Source identifier (e.g., "consistency_violation", "tool_failure")
            feedback_data: Feedback data dictionary
        """
        self.feedback_sources.append({
            "source": source,
            "timestamp": datetime.now(timezone.utc),
            "data": feedback_data
        })
    
    def aggregate_feedback(
        self,
        pattern_detector: PatternDetector,
        output_monitor: OutputMonitor
    ) -> List[Pattern]:
        """
        Aggregate feedback from all sources.
        
        Args:
            pattern_detector: Pattern detector instance
            output_monitor: Output monitor instance
            
        Returns:
            List of aggregated patterns
        """
        # Get patterns from output events
        recent_events = output_monitor.get_recent_events(limit=50)
        patterns = pattern_detector.detect_patterns(recent_events)
        
        # Add patterns from other feedback sources
        for feedback in self.feedback_sources:
            source = feedback["source"]
            data = feedback["data"]
            
            if source == "consistency_violation":
                # Create pattern from consistency violation
                violation = data.get("violation", {})
                pattern = Pattern(
                    pattern_type="consistency_violation",
                    description=violation.get("description", "Consistency violation detected"),
                    confidence=violation.get("severity", 0.5),
                    frequency=1,
                    examples=[],
                    suggested_updates=data.get("suggested_updates")
                )
                patterns.append(pattern)
        
        return patterns


class SelfModelShaping:
    """
    Uses self-model to shape/guide outputs.
    
    Provides guidance based on current self-model state for response generation.
    """
    
    def __init__(self, self_model: "SelfModel"):
        """
        Initialize self-model shaping.
        
        Args:
            self_model: Self-model instance
        """
        self.self_model = self_model
        logger.info("Initialized SelfModelShaping")
    
    def get_shaping_guidance(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get guidance for output generation based on self-model.
        
        Args:
            context: Optional context for shaping
            
        Returns:
            Dictionary with shaping guidance
        """
        guidance = {
            "capabilities": [cap.get("text", str(cap)) for cap in self.self_model.capabilities[:10]],
            "constraints": {
                k: v.get("value", str(v))
                for k, v in list(self.self_model.constraints.items())[:10]
            },
            "knowledge_boundaries": {
                k: v.get("value", str(v))
                for k, v in list(self.self_model.knowledge_boundaries.items())[:5]
            }
        }
        
        return guidance


class OutputFeedbackSystem:
    """
    Main system coordinating output feedback and self-model shaping.
    
    Combines output monitoring, pattern detection, feedback aggregation,
    and self-model shaping into a unified system.
    """
    
    def __init__(
        self,
        self_model: "SelfModel",
        history_window: int = 100
    ):
        """
        Initialize output feedback system.
        
        Args:
            self_model: Self-model instance
            history_window: History window for output monitoring
        """
        self.self_model = self_model
        self.output_monitor = OutputMonitor(history_window=history_window)
        self.pattern_detector = PatternDetector()
        self.feedback_aggregator = FeedbackAggregator()
        self.self_model_shaping = SelfModelShaping(self_model)
        
        logger.info("Initialized OutputFeedbackSystem")
    
    def record_output(
        self,
        output_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an output (response or tool execution).
        
        Args:
            output_type: Type of output ("response" or "tool_execution")
            content: Output content
            metadata: Optional metadata
        """
        if output_type == "response":
            self.output_monitor.record_response(content, metadata)
        elif output_type == "tool_execution":
            tool_name = metadata.get("tool_name", "unknown") if metadata else "unknown"
            params = metadata.get("parameters", {}) if metadata else {}
            result = metadata.get("result", {}) if metadata else {}
            self.output_monitor.record_tool_execution(tool_name, params, result, metadata)
    
    def get_detected_patterns(
        self,
        min_confidence: float = 0.5
    ) -> List[Pattern]:
        """
        Get detected patterns from output history.
        
        Args:
            min_confidence: Minimum confidence threshold for patterns
            
        Returns:
            List of detected patterns
        """
        patterns = self.feedback_aggregator.aggregate_feedback(
            self.pattern_detector,
            self.output_monitor
        )
        
        # Filter by confidence
        return [p for p in patterns if p.confidence >= min_confidence]
    
    def get_shaping_guidance(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get guidance for shaping outputs based on self-model.
        
        Args:
            context: Optional context
            
        Returns:
            Shaping guidance dictionary
        """
        return self.self_model_shaping.get_shaping_guidance(context)
    
    def add_consistency_feedback(
        self,
        violation: Dict[str, Any],
        suggested_updates: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add feedback from consistency violations.
        
        Args:
            violation: Violation dictionary
            suggested_updates: Optional suggested self-model updates
        """
        self.feedback_aggregator.add_feedback(
            "consistency_violation",
            {
                "violation": violation,
                "suggested_updates": suggested_updates
            }
        )

