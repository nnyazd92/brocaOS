"""
Procedural learning from tool execution patterns.

Learns reusable procedures from successful tool call sequences,
generalizes them to similar situations, and enables automatic
application of learned skills.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class ProcedureType(Enum):
    """Types of learned procedures."""
    TOOL_SEQUENCE = "tool_sequence"      # Sequence of tool calls
    PARAMETER_TUNING = "parameter_tuning" # Optimal parameter values
    DECISION_PATTERN = "decision_pattern" # Decision-making patterns
    ERROR_RECOVERY = "error_recovery"    # Error handling procedures


@dataclass
class ToolCall:
    """A single tool call in a procedure."""
    
    tool_name: str
    parameters: Dict[str, Any]
    result_pattern: Optional[Dict[str, Any]] = None  # Expected result pattern
    execution_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result_pattern": self.result_pattern,
            "execution_time_ms": self.execution_time_ms,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ToolCall:
        return cls(
            tool_name=data["tool_name"],
            parameters=data["parameters"],
            result_pattern=data.get("result_pattern"),
            execution_time_ms=data.get("execution_time_ms"),
        )


@dataclass
class ContextPattern:
    """Pattern that triggers procedure application."""
    
    memory_patterns: List[Dict[str, Any]] = field(default_factory=list)  # Patterns in working memory
    goal_patterns: List[Dict[str, Any]] = field(default_factory=list)    # Patterns in active goals
    state_patterns: List[Dict[str, Any]] = field(default_factory=list)   # Patterns in system state
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_patterns": self.memory_patterns,
            "goal_patterns": self.goal_patterns,
            "state_patterns": self.state_patterns,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextPattern:
        return cls(
            memory_patterns=data.get("memory_patterns", []),
            goal_patterns=data.get("goal_patterns", []),
            state_patterns=data.get("state_patterns", []),
        )


@dataclass
class LearnedProcedure:
    """
    A learned procedure that can be automatically applied.
    
    Represents a sequence of tool calls that has been successful
    in specific contexts, with associated success metrics and
    generalization patterns.
    """
    
    name: str
    procedure_type: ProcedureType
    tool_calls: List[ToolCall]
    context_pattern: ContextPattern
    
    # Learning metrics
    success_count: int = 0
    failure_count: int = 0
    total_executions: int = 0
    average_execution_time_ms: Optional[int] = None
    
    # Generalization
    generalization_patterns: List[Dict[str, Any]] = field(default_factory=list)
    applicable_domains: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_applied: Optional[datetime] = None
    last_success: Optional[datetime] = None
    
    # Learning parameters
    confidence: float = 0.5  # 0.0 to 1.0
    learning_rate: float = 0.1
    
    # Cognitive dissonance integration
    dissonance_reduction_score: float = 0.0  # Average dissonance reduction when applied (positive = reduces dissonance)
    dissonance_effectiveness_count: int = 0  # Number of times dissonance was measured
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "procedure_type": self.procedure_type.value,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "context_pattern": self.context_pattern.to_dict(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_executions": self.total_executions,
            "average_execution_time_ms": self.average_execution_time_ms,
            "generalization_patterns": self.generalization_patterns,
            "applicable_domains": self.applicable_domains,
            "created_at": self.created_at.isoformat(),
            "last_applied": self.last_applied.isoformat() if self.last_applied else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "confidence": self.confidence,
            "learning_rate": self.learning_rate,
            "dissonance_reduction_score": self.dissonance_reduction_score,
            "dissonance_effectiveness_count": self.dissonance_effectiveness_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LearnedProcedure:
        return cls(
            name=data["name"],
            procedure_type=ProcedureType(data["procedure_type"]),
            tool_calls=[ToolCall.from_dict(tc) for tc in data["tool_calls"]],
            context_pattern=ContextPattern.from_dict(data["context_pattern"]),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            total_executions=data.get("total_executions", 0),
            average_execution_time_ms=data.get("average_execution_time_ms"),
            generalization_patterns=data.get("generalization_patterns", []),
            applicable_domains=data.get("applicable_domains", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            last_applied=datetime.fromisoformat(data["last_applied"]) if data.get("last_applied") else None,
            last_success=datetime.fromisoformat(data["last_success"]) if data.get("last_success") else None,
            confidence=data.get("confidence", 0.5),
            learning_rate=data.get("learning_rate", 0.1),
            dissonance_reduction_score=data.get("dissonance_reduction_score", 0.0),
            dissonance_effectiveness_count=data.get("dissonance_effectiveness_count", 0),
        )
    
    def success_rate(self) -> float:
        """Calculate success rate of this procedure."""
        if self.total_executions == 0:
            return 0.0
        return self.success_count / self.total_executions
    
    def update_success(self, execution_time_ms: Optional[int] = None):
        """Record a successful execution."""
        self.success_count += 1
        self.total_executions += 1
        self.last_applied = datetime.now(timezone.utc)
        self.last_success = self.last_applied
        
        # Update average execution time
        if execution_time_ms is not None:
            if self.average_execution_time_ms is None:
                self.average_execution_time_ms = execution_time_ms
            else:
                # Exponential moving average
                self.average_execution_time_ms = (
                    self.learning_rate * execution_time_ms +
                    (1 - self.learning_rate) * self.average_execution_time_ms
                )
        
        # Increase confidence based on success
        self.confidence = min(1.0, self.confidence + self.learning_rate * 0.1)
    
    def update_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.total_executions += 1
        self.last_applied = datetime.now(timezone.utc)
        
        # Decrease confidence based on failure
        self.confidence = max(0.1, self.confidence - self.learning_rate * 0.2)
    
    def update_dissonance_effectiveness(self, dissonance_reduction: float):
        """
        Update dissonance reduction score based on application result.
        
        Args:
            dissonance_reduction: Change in dissonance (positive = reduction, negative = increase)
        """
        self.dissonance_effectiveness_count += 1
        
        # Update using exponential moving average
        if self.dissonance_effectiveness_count == 1:
            self.dissonance_reduction_score = dissonance_reduction
        else:
            self.dissonance_reduction_score = (
                self.learning_rate * dissonance_reduction +
                (1.0 - self.learning_rate) * self.dissonance_reduction_score
            )
        
        # Adjust confidence based on dissonance effectiveness
        if dissonance_reduction > 0.0:  # Reduced dissonance
            self.confidence = min(1.0, self.confidence + self.learning_rate * 0.05)
        elif dissonance_reduction < -0.1:  # Increased dissonance significantly
            self.confidence = max(0.1, self.confidence - self.learning_rate * 0.1)


class ProceduralLearner:
    """
    Learns procedures from tool execution patterns.
    
    Observes successful tool call sequences, extracts patterns,
    creates reusable procedures, and suggests them for similar
    future situations.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.procedures: Dict[str, LearnedProcedure] = {}
        self.observation_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 100
        
        # Pattern extraction settings
        self.min_sequence_length = 2
        self.min_success_rate = 0.7
        self.confidence_threshold = 0.6
        
        # Default procedures
        self._add_default_procedures()
        
        logger.info("Initialized ProceduralLearner")
    
    def _add_default_procedures(self):
        """Add default procedures based on common patterns."""
        # Default: File examination procedure
        file_exam_procedure = LearnedProcedure(
            name="examine_codebase_structure",
            procedure_type=ProcedureType.TOOL_SEQUENCE,
            tool_calls=[
                ToolCall(
                    tool_name="terminal",
                    parameters={"command": "find . -name '*.py' -type f | head -20"}
                ),
                ToolCall(
                    tool_name="terminal",
                    parameters={"command": "ls -la ./broca/"}
                ),
            ],
            context_pattern=ContextPattern(
                goal_patterns=[{"type": "goal", "name": "analyze_codebase"}],
                memory_patterns=[{"type": "task", "domain": "code_analysis"}],
            ),
            confidence=0.8,
        )
        self.procedures[file_exam_procedure.name] = file_exam_procedure
        
        # Default: Memory search procedure
        memory_search_procedure = LearnedProcedure(
            name="search_related_memories",
            procedure_type=ProcedureType.TOOL_SEQUENCE,
            tool_calls=[
                ToolCall(
                    tool_name="retrieve_memories",
                    parameters={"query": "{{topic}}", "limit": 5}
                ),
            ],
            context_pattern=ContextPattern(
                memory_patterns=[{"type": "task", "needs_information": True}],
            ),
            confidence=0.7,
        )
        self.procedures[memory_search_procedure.name] = memory_search_procedure
    
    def observe_tool_call(self, tool_call: Dict[str, Any], result: Dict[str, Any]):
        """
        Observe a tool call and its result for learning.
        
        Args:
            tool_call: Tool call dictionary with name and parameters
            result: Result dictionary with success/error information
        """
        observation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_call": tool_call,
            "result": result,
            "success": result.get("success", False),
        }
        
        self.observation_buffer.append(observation)
        
        # Limit buffer size
        if len(self.observation_buffer) > self.max_buffer_size:
            self.observation_buffer = self.observation_buffer[-self.max_buffer_size:]
        
        logger.debug(f"Observed tool call: {tool_call.get('name', 'unknown')}")
    
    def extract_patterns(self, context: Dict[str, Any] = None, dissonance_context: Optional[Dict[str, Any]] = None) -> List[LearnedProcedure]:
        """
        Extract patterns from recent observations and create new procedures.
        
        Args:
            context: Current context (working memory, goals, state)
            dissonance_context: Optional dissonance context with metrics (for filtering by dissonance effectiveness)
            
        Returns:
            List of newly created procedures
        """
        if len(self.observation_buffer) < self.min_sequence_length:
            return []
        
        new_procedures = []
        
        # Group observations by session/context
        successful_sequences = self._extract_successful_sequences()
        
        # Filter sequences by dissonance effectiveness if context provided
        if dissonance_context:
            successful_sequences = self._filter_sequences_by_dissonance(successful_sequences, dissonance_context)
        
        for sequence in successful_sequences:
            # Create procedure from successful sequence
            procedure = self._create_procedure_from_sequence(sequence, context)
            if procedure:
                # Initialize dissonance reduction score if available
                if dissonance_context:
                    avg_dissonance_reduction = dissonance_context.get("average_dissonance_reduction", 0.0)
                    procedure.dissonance_reduction_score = avg_dissonance_reduction
                    procedure.dissonance_effectiveness_count = 1
                
                self.procedures[procedure.name] = procedure
                new_procedures.append(procedure)
                logger.info(f"Created new procedure: {procedure.name}")
        
        return new_procedures
    
    def _filter_sequences_by_dissonance(self, sequences: List[List[Dict[str, Any]]], dissonance_context: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """
        Filter sequences based on dissonance effectiveness.
        
        Prefer sequences that occur during low-dissonance periods or that reduce dissonance.
        """
        filtered = []
        min_dissonance_threshold = dissonance_context.get("min_dissonance_threshold", 0.3)
        require_dissonance_reduction = dissonance_context.get("require_dissonance_reduction", False)
        
        for sequence in sequences:
            # Check if sequence was associated with low dissonance or dissonance reduction
            sequence_avg_dissonance = dissonance_context.get("sequence_dissonance", {}).get(str(id(sequence)), 1.0)
            
            if sequence_avg_dissonance <= min_dissonance_threshold:
                filtered.append(sequence)
            elif not require_dissonance_reduction:
                # Include all sequences if not requiring reduction
                filtered.append(sequence)
        
        return filtered
    
    def _extract_successful_sequences(self) -> List[List[Dict[str, Any]]]:
        """Extract successful tool call sequences from observations."""
        sequences = []
        current_sequence = []
        
        for obs in self.observation_buffer:
            if obs["success"]:
                current_sequence.append(obs)
            else:
                # End of sequence on failure
                if len(current_sequence) >= self.min_sequence_length:
                    sequences.append(current_sequence.copy())
                current_sequence = []
        
        # Add final sequence if successful
        if len(current_sequence) >= self.min_sequence_length:
            sequences.append(current_sequence)
        
        return sequences
    
    def _create_procedure_from_sequence(self, sequence: List[Dict[str, Any]], 
                                       context: Dict[str, Any]) -> Optional[LearnedProcedure]:
        """Create a procedure from a successful tool call sequence."""
        if not sequence:
            return None
        
        # Extract tool calls
        tool_calls = []
        for obs in sequence:
            tool_call_data = obs["tool_call"]
            tool_calls.append(ToolCall(
                tool_name=tool_call_data.get("name", "unknown"),
                parameters=tool_call_data.get("parameters", {}),
                result_pattern=self._extract_result_pattern(obs["result"]),
            ))
        
        # Generate procedure name
        tool_names = [tc.tool_name for tc in tool_calls]
        name_hash = hashlib.md5(str(tool_names).encode()).hexdigest()[:8]
        procedure_name = f"procedure_{name_hash}"
        
        # Extract context patterns from provided context
        context_pattern = ContextPattern()
        if context:
            context_pattern.memory_patterns = context.get("memory_patterns", [])
            context_pattern.goal_patterns = context.get("goal_patterns", [])
            context_pattern.state_patterns = context.get("state_patterns", [])
        
        # Create procedure
        procedure = LearnedProcedure(
            name=procedure_name,
            procedure_type=ProcedureType.TOOL_SEQUENCE,
            tool_calls=tool_calls,
            context_pattern=context_pattern,
            success_count=1,
            total_executions=1,
            confidence=0.6,  # Initial confidence for new procedures
        )
        
        return procedure
    
    def _extract_result_pattern(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract pattern from successful result."""
        if not result.get("success"):
            return None
        
        # Extract key success indicators
        pattern = {}
        if "data" in result:
            # Try to extract structure from data
            data = result["data"]
            if isinstance(data, dict):
                # Include keys that indicate success
                for key in ["result", "output", "response", "success"]:
                    if key in data:
                        pattern[key] = "present"
        elif "output" in result:
            pattern["output"] = "non_empty"
        
        return pattern if pattern else None
    
    def get_applicable_procedures(self, context: Dict[str, Any]) -> List[LearnedProcedure]:
        """
        Get procedures applicable to current context.
        
        Args:
            context: Current context with memory, goals, state patterns
            
        Returns:
            List of applicable procedures sorted by confidence
        """
        applicable = []
        
        for procedure in self.procedures.values():
            if self._procedure_applicable(procedure, context):
                applicable.append(procedure)
        
        # Sort by combined score: confidence, success rate, and dissonance reduction
        # Procedures that reduce dissonance get priority boost
        applicable.sort(
            key=lambda p: (
                p.confidence,
                p.success_rate(),
                max(0.0, p.dissonance_reduction_score)  # Boost for positive dissonance reduction
            ),
            reverse=True
        )
        
        return applicable
    
    def _procedure_applicable(self, procedure: LearnedProcedure, 
                             context: Dict[str, Any]) -> bool:
        """Check if procedure is applicable to current context."""
        # Check confidence threshold
        if procedure.confidence < self.confidence_threshold:
            return False
        
        # Extract context components
        memory_items = context.get("memory_items", [])
        active_goals = context.get("active_goals", [])
        system_state = context.get("system_state", {})
        
        # Check memory patterns
        for pattern in procedure.context_pattern.memory_patterns:
            if not self._pattern_matches_any(pattern, memory_items):
                return False
        
        # Check goal patterns
        for pattern in procedure.context_pattern.goal_patterns:
            if not self._pattern_matches_any(pattern, active_goals):
                return False
        
        # Check state patterns
        for pattern in procedure.context_pattern.state_patterns:
            if not self._pattern_matches(pattern, system_state):
                return False
        
        return True
    
    def _pattern_matches(self, pattern: Dict[str, Any], item: Dict[str, Any]) -> bool:
        """Check if pattern matches item."""
        for key, value in pattern.items():
            if key not in item:
                return False
            if isinstance(value, dict) and isinstance(item[key], dict):
                if not self._pattern_matches(value, item[key]):
                    return False
            elif value != item[key]:
                return False
        return True
    
    def _pattern_matches_any(self, pattern: Dict[str, Any], items: List[Dict[str, Any]]) -> bool:
        """Check if pattern matches any item in list."""
        for item in items:
            if self._pattern_matches(pattern, item):
                return True
        return False
    
    def filter_by_dissonance_effectiveness(
        self,
        procedures: List[LearnedProcedure],
        min_dissonance_reduction: float = 0.0,
        min_effectiveness_count: int = 1
    ) -> List[LearnedProcedure]:
        """
        Filter procedures by dissonance reduction effectiveness.
        
        Args:
            procedures: List of procedures to filter
            min_dissonance_reduction: Minimum average dissonance reduction to include
            min_effectiveness_count: Minimum number of effectiveness measurements
            
        Returns:
            Filtered list of procedures that meet effectiveness criteria
        """
        filtered = []
        
        for procedure in procedures:
            if (procedure.dissonance_effectiveness_count >= min_effectiveness_count and
                procedure.dissonance_reduction_score >= min_dissonance_reduction):
                filtered.append(procedure)
            elif procedure.dissonance_effectiveness_count == 0:
                # Include procedures that haven't been measured yet (unknown effectiveness)
                filtered.append(procedure)
        
        return filtered
    
    def apply_procedure(self, procedure_name: str, 
                       parameter_bindings: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Apply a learned procedure with optional parameter bindings.
        
        Args:
            procedure_name: Name of procedure to apply
            parameter_bindings: Values to substitute in procedure parameters
            
        Returns:
            List of tool call dictionaries ready for execution
        """
        if procedure_name not in self.procedures:
            raise ValueError(f"Procedure not found: {procedure_name}")
        
        procedure = self.procedures[procedure_name]
        tool_calls = []
        
        for tool_call in procedure.tool_calls:
            # Apply parameter bindings
            parameters = self._apply_bindings(tool_call.parameters, parameter_bindings)
            
            tool_calls.append({
                "name": tool_call.tool_name,
                "parameters": parameters,
            })
        
        return tool_calls
    
    def _apply_bindings(self, parameters: Dict[str, Any], 
                       bindings: Dict[str, Any]) -> Dict[str, Any]:
        """Apply parameter bindings to template parameters."""
        if not bindings:
            return parameters
        
        import json
        
        # Convert to string for template substitution
        params_str = json.dumps(parameters)
        
        for key, value in bindings.items():
            placeholder = "{{" + key + "}}"
            if placeholder in params_str:
                params_str = params_str.replace(placeholder, json.dumps(value)[1:-1])
        
        return json.loads(params_str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert learner to dictionary representation."""
        return {
            "procedures": {name: proc.to_dict() for name, proc in self.procedures.items()},
            "observation_buffer": self.observation_buffer[-50:],  # Last 50 observations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProceduralLearner:
        """Create learner from dictionary representation."""
        learner = cls()
        learner.procedures = {
            name: LearnedProcedure.from_dict(proc_data) 
            for name, proc_data in data.get("procedures", {}).items()
        }
        learner.observation_buffer = data.get("observation_buffer", [])
        return learner
