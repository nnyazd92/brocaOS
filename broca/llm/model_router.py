"""
Intelligent model routing for multi-model reasoning.

Routes tasks to appropriate LLM models based on task characteristics.
Implements escalation from cheaper to more powerful models based on feedback metrics.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque

if TYPE_CHECKING:
    from . import LLMClient
    from ..reasoning.feedback_loop import FeedbackMetrics

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks for model routing."""
    REASONING = "reasoning"
    PLANNING = "planning"
    CRITICISM = "criticism"
    CREATIVE = "creative"
    FACTUAL = "factual"
    CODE = "code"
    GENERAL = "general"


@dataclass
class ModelCapability:
    """Capabilities of a model."""
    model_name: str
    task_types: List[TaskType]
    strength_reasoning: float = 0.5
    strength_planning: float = 0.5
    strength_creativity: float = 0.5
    strength_factual: float = 0.5
    cost_per_token: float = 0.0
    latency_ms: float = 0.0


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a specific model."""
    model_name: str
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    recent_successes: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_confidence: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_dissonance: deque = field(default_factory=lambda: deque(maxlen=100))
    last_escalation_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate from recent requests."""
        if len(self.recent_successes) + len(self.recent_errors) == 0:
            return 1.0  # Default to success if no data
        total = len(self.recent_successes) + len(self.recent_errors)
        return len(self.recent_successes) / total if total > 0 else 1.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate from recent requests."""
        if len(self.recent_successes) + len(self.recent_errors) == 0:
            return 0.0  # Default to no errors if no data
        total = len(self.recent_successes) + len(self.recent_errors)
        return len(self.recent_errors) / total if total > 0 else 0.0
    
    @property
    def avg_confidence(self) -> float:
        """Calculate average confidence from recent requests."""
        if not self.recent_confidence:
            return 0.5  # Default confidence
        return sum(self.recent_confidence) / len(self.recent_confidence)
    
    @property
    def avg_dissonance(self) -> float:
        """Calculate average cognitive dissonance from recent requests."""
        if not self.recent_dissonance:
            return 0.0  # Default no dissonance
        return sum(self.recent_dissonance) / len(self.recent_dissonance)


@dataclass
class EscalationPolicy:
    """Policy for model escalation based on metrics."""
    success_rate_threshold: float = 0.7
    error_rate_threshold: float = 0.3
    confidence_threshold: float = 0.5
    dissonance_threshold: float = 0.3
    min_attempts_before_escalation: int = 3
    escalation_cooldown_seconds: float = 60.0


class ModelRouter:
    """
    Intelligent model router with escalation support.
    
    Routes tasks to appropriate models based on:
    - Task type and characteristics
    - Model capabilities
    - Cost and latency considerations
    - Performance feedback and escalation policies
    """
    
    def __init__(
        self,
        models: Optional[Dict[str, "LLMClient"]] = None,
        capabilities: Optional[Dict[str, ModelCapability]] = None,
        escalation_enabled: bool = True,
        escalation_chain: Optional[List[str]] = None,
        escalation_policy: Optional[EscalationPolicy] = None
    ):
        """
        Initialize model router.
        
        Args:
            models: Dictionary of model_name -> LLMClient
            capabilities: Dictionary of model_name -> ModelCapability
            escalation_enabled: Whether escalation is enabled
            escalation_chain: Ordered list of models from cheapest to most powerful
            escalation_policy: Policy for escalation decisions
        """
        self.models = models or {}
        self.capabilities = capabilities or {}
        self.escalation_enabled = escalation_enabled
        self.escalation_policy = escalation_policy or EscalationPolicy()
        
        # Default escalation chain: cheapest to most powerful
        self.escalation_chain = escalation_chain or ["deepseek-chat", "gpt-5-nano", "gpt-5-mini"]
        
        # Performance tracking per model
        self.performance_tracker: Dict[str, ModelPerformanceMetrics] = {}
        for model_name in self.models.keys():
            self.performance_tracker[model_name] = ModelPerformanceMetrics(model_name=model_name)
        
        # Current model in escalation chain (starts at cheapest)
        self.current_model_index = 0
        
        # Default capabilities if not provided
        if not self.capabilities:
            self._initialize_default_capabilities()
        
        logger.info(f"Initialized ModelRouter with {len(self.models)} models, escalation: {escalation_enabled}")
    
    def _initialize_default_capabilities(self):
        """Initialize default model capabilities."""
        # Default capabilities for supported models
        # Removed gpt-4 and gpt-3.5-turbo per requirements
        default_caps = {
            "deepseek-chat": ModelCapability(
                model_name="deepseek-chat",
                task_types=[TaskType.REASONING, TaskType.CODE, TaskType.GENERAL],
                strength_reasoning=0.8,
                strength_planning=0.7,
                strength_creativity=0.6,
                strength_factual=0.7,
                cost_per_token=0.0001,  # Very cheap
                latency_ms=200.0  # Fast
            ),
            "gpt-5-nano": ModelCapability(
                model_name="gpt-5-nano",
                task_types=[TaskType.REASONING, TaskType.PLANNING, TaskType.FACTUAL, TaskType.GENERAL],
                strength_reasoning=0.75,
                strength_planning=0.7,
                strength_creativity=0.65,
                strength_factual=0.75,
                cost_per_token=0.0002,  # Cheap
                latency_ms=150.0  # Very fast
            ),
            "gpt-5-mini": ModelCapability(
                model_name="gpt-5-mini",
                task_types=[TaskType.REASONING, TaskType.PLANNING, TaskType.CRITICISM, TaskType.CREATIVE, TaskType.FACTUAL],
                strength_reasoning=0.85,
                strength_planning=0.8,
                strength_creativity=0.75,
                strength_factual=0.85,
                cost_per_token=0.0005,  # Mid-tier
                latency_ms=300.0  # Moderate
            )
        }
        
        # Only add capabilities for models we have
        for model_name in self.models.keys():
            if model_name in default_caps:
                self.capabilities[model_name] = default_caps[model_name]
            else:
                # Generic capability
                self.capabilities[model_name] = ModelCapability(
                    model_name=model_name,
                    task_types=[TaskType.GENERAL],
                    strength_reasoning=0.5,
                    strength_planning=0.5,
                    strength_creativity=0.5,
                    strength_factual=0.5
                )
    
    def route_task(
        self,
        task_description: str,
        task_type: Optional[TaskType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Route a task to the best model.
        
        Args:
            task_description: Description of the task
            task_type: Optional explicit task type
            context: Optional context (cost_sensitive, latency_sensitive, etc.)
            
        Returns:
            Model name to use, or None if no suitable model
        """
        if not self.models:
            logger.warning("No models available for routing")
            return None
        
        # Infer task type if not provided
        if task_type is None:
            task_type = self._infer_task_type(task_description)
        
        # Score each model for this task
        model_scores = {}
        for model_name, capability in self.capabilities.items():
            if model_name not in self.models:
                continue
            
            score = self._score_model(capability, task_type, context or {})
            model_scores[model_name] = score
        
        if not model_scores:
            return None
        
        # Select best model
        best_model = max(model_scores.items(), key=lambda x: x[1])[0]
        
        logger.debug(
            f"Routed task '{task_description[:50]}...' (type: {task_type.value}) "
            f"to model: {best_model} (score: {model_scores[best_model]:.2f})"
        )
        
        return best_model
    
    def _infer_task_type(self, task_description: str) -> TaskType:
        """Infer task type from description."""
        desc_lower = task_description.lower()
        
        # Check for reasoning keywords
        if any(word in desc_lower for word in ["reason", "analyze", "deduce", "infer", "logic"]):
            return TaskType.REASONING
        
        # Check for planning keywords
        if any(word in desc_lower for word in ["plan", "strategy", "sequence", "steps"]):
            return TaskType.PLANNING
        
        # Check for criticism keywords
        if any(word in desc_lower for word in ["critic", "review", "evaluate", "assess"]):
            return TaskType.CRITICISM
        
        # Check for creative keywords
        if any(word in desc_lower for word in ["create", "generate", "imagine", "design"]):
            return TaskType.CREATIVE
        
        # Check for factual keywords
        if any(word in desc_lower for word in ["fact", "information", "what is", "define"]):
            return TaskType.FACTUAL
        
        # Check for code keywords
        if any(word in desc_lower for word in ["code", "program", "function", "class", "python"]):
            return TaskType.CODE
        
        return TaskType.GENERAL
    
    def _score_model(
        self,
        capability: ModelCapability,
        task_type: TaskType,
        context: Dict[str, Any]
    ) -> float:
        """Score a model for a given task."""
        # Base score from capability
        if task_type == TaskType.REASONING:
            base_score = capability.strength_reasoning
        elif task_type == TaskType.PLANNING:
            base_score = capability.strength_planning
        elif task_type == TaskType.CREATIVE:
            base_score = capability.strength_creativity
        elif task_type == TaskType.FACTUAL:
            base_score = capability.strength_factual
        else:
            base_score = 0.5  # Generic
        
        # Check if model supports this task type
        if task_type not in capability.task_types and TaskType.GENERAL not in capability.task_types:
            base_score *= 0.5  # Penalty for unsupported task type
        
        # Adjust for cost if cost-sensitive
        if context.get("cost_sensitive", False) and capability.cost_per_token > 0:
            # Prefer cheaper models
            cost_penalty = min(0.3, capability.cost_per_token * 0.01)
            base_score -= cost_penalty
        
        # Adjust for latency if latency-sensitive
        if context.get("latency_sensitive", False) and capability.latency_ms > 0:
            # Prefer faster models
            latency_penalty = min(0.2, capability.latency_ms / 1000.0 * 0.1)
            base_score -= latency_penalty
        
        return max(0.0, min(1.0, base_score))
    
    def get_model(self, model_name: str) -> Optional["LLMClient"]:
        """Get LLM client for a model."""
        return self.models.get(model_name)
    
    def register_model(
        self,
        model_name: str,
        client: "LLMClient",
        capability: Optional[ModelCapability] = None
    ):
        """Register a model."""
        self.models[model_name] = client
        if capability:
            self.capabilities[model_name] = capability
        else:
            # Create default capability
            self.capabilities[model_name] = ModelCapability(
                model_name=model_name,
                task_types=[TaskType.GENERAL]
            )
        
        # Initialize performance tracking if not exists
        if model_name not in self.performance_tracker:
            self.performance_tracker[model_name] = ModelPerformanceMetrics(model_name=model_name)
        
        logger.info(f"Registered model: {model_name}")
    
    def get_current_model(self) -> Optional[str]:
        """Get the current model in the escalation chain."""
        if not self.escalation_enabled or not self.escalation_chain:
            return None
        
        # Find first available model in chain
        for i in range(self.current_model_index, len(self.escalation_chain)):
            model_name = self.escalation_chain[i]
            if model_name in self.models:
                self.current_model_index = i
                return model_name
        
        # Fallback to last available model
        for model_name in reversed(self.escalation_chain):
            if model_name in self.models:
                return model_name
        
        return None
    
    def escalate_model(self) -> Optional[str]:
        """Move to next model in escalation chain."""
        if not self.escalation_enabled or not self.escalation_chain:
            return None
        
        if self.current_model_index >= len(self.escalation_chain) - 1:
            # Already at max, return current
            return self.get_current_model()
        
        # Move to next model
        self.current_model_index += 1
        next_model = self.get_current_model()
        
        if next_model:
            # Record escalation time
            if next_model in self.performance_tracker:
                self.performance_tracker[next_model].last_escalation_time = datetime.now(timezone.utc)
            logger.info(f"Escalated to model: {next_model}")
        
        return next_model
    
    def should_escalate(
        self,
        current_model: str,
        feedback_metrics: Optional["FeedbackMetrics"] = None,
        confidence: Optional[float] = None,
        dissonance: Optional[float] = None
    ) -> bool:
        """
        Check if escalation criteria are met.
        
        Args:
            current_model: Current model name
            feedback_metrics: Optional feedback metrics from FeedbackLoopManager
            confidence: Optional confidence score
            dissonance: Optional cognitive dissonance score
            
        Returns:
            True if should escalate, False otherwise
        """
        if not self.escalation_enabled:
            return False
        
        # Get performance metrics for current model
        if current_model not in self.performance_tracker:
            # Initialize if missing
            self.performance_tracker[current_model] = ModelPerformanceMetrics(model_name=current_model)
        
        metrics = self.performance_tracker[current_model]
        
        # Check minimum attempts
        if metrics.request_count < self.escalation_policy.min_attempts_before_escalation:
            return False
        
        # Check cooldown
        if metrics.last_escalation_time:
            time_since = (datetime.now(timezone.utc) - metrics.last_escalation_time).total_seconds()
            if time_since < self.escalation_policy.escalation_cooldown_seconds:
                return False
        
        # Check combined criteria
        should_escalate = False
        
        # Check success/error rate from performance tracker
        if metrics.success_rate < self.escalation_policy.success_rate_threshold:
            should_escalate = True
            logger.debug(f"Escalation triggered: success_rate {metrics.success_rate:.2f} < {self.escalation_policy.success_rate_threshold}")
        
        if metrics.error_rate > self.escalation_policy.error_rate_threshold:
            should_escalate = True
            logger.debug(f"Escalation triggered: error_rate {metrics.error_rate:.2f} > {self.escalation_policy.error_rate_threshold}")
        
        # Check feedback metrics if provided
        if feedback_metrics:
            if feedback_metrics.success_rate < self.escalation_policy.success_rate_threshold:
                should_escalate = True
            if feedback_metrics.error_rate > self.escalation_policy.error_rate_threshold:
                should_escalate = True
        
        # Check confidence
        if confidence is not None and confidence < self.escalation_policy.confidence_threshold:
            should_escalate = True
            logger.debug(f"Escalation triggered: confidence {confidence:.2f} < {self.escalation_policy.confidence_threshold}")
        
        # Check cognitive dissonance
        if dissonance is not None and dissonance > self.escalation_policy.dissonance_threshold:
            should_escalate = True
            logger.debug(f"Escalation triggered: dissonance {dissonance:.2f} > {self.escalation_policy.dissonance_threshold}")
        
        # Also check average metrics from tracker
        if metrics.avg_confidence < self.escalation_policy.confidence_threshold:
            should_escalate = True
        
        if metrics.avg_dissonance > self.escalation_policy.dissonance_threshold:
            should_escalate = True
        
        return should_escalate
    
    def track_response_quality(
        self,
        model_name: str,
        success: bool = True,
        confidence: Optional[float] = None,
        dissonance: Optional[float] = None
    ):
        """
        Track response quality for a model.
        
        Args:
            model_name: Model that generated the response
            success: Whether the response was successful
            confidence: Optional confidence score
            dissonance: Optional cognitive dissonance score
        """
        if model_name not in self.performance_tracker:
            self.performance_tracker[model_name] = ModelPerformanceMetrics(model_name=model_name)
        
        metrics = self.performance_tracker[model_name]
        metrics.request_count += 1
        
        if success:
            metrics.success_count += 1
            metrics.recent_successes.append(datetime.now(timezone.utc))
        else:
            metrics.error_count += 1
            metrics.recent_errors.append(datetime.now(timezone.utc))
        
        if confidence is not None:
            metrics.recent_confidence.append(confidence)
        
        if dissonance is not None:
            metrics.recent_dissonance.append(dissonance)
    
    def route_task_with_escalation(
        self,
        task_description: str,
        task_type: Optional[TaskType] = None,
        context: Optional[Dict[str, Any]] = None,
        feedback_metrics: Optional["FeedbackMetrics"] = None,
        confidence: Optional[float] = None,
        dissonance: Optional[float] = None
    ) -> Optional[str]:
        """
        Route a task with escalation support.
        
        Args:
            task_description: Description of the task
            task_type: Optional explicit task type
            context: Optional context (cost_sensitive, latency_sensitive, etc.)
            feedback_metrics: Optional feedback metrics for escalation
            confidence: Optional confidence score for escalation
            dissonance: Optional cognitive dissonance for escalation
            
        Returns:
            Model name to use, or None if no suitable model
        """
        # If escalation enabled, check current model and potentially escalate
        if self.escalation_enabled:
            current_model = self.get_current_model()
            if current_model and self.should_escalate(
                current_model, feedback_metrics, confidence, dissonance
            ):
                escalated_model = self.escalate_model()
                if escalated_model:
                    return escalated_model
                # If escalation failed, use current
                return current_model
            elif current_model:
                return current_model
        
        # Fall back to standard routing
        return self.route_task(task_description, task_type, context)

