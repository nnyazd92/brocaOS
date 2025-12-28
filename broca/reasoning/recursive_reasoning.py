"""
Recursive reasoning engine.

Implements recursive reasoning about reasoning processes with depth limits
and safety guards to prevent infinite recursion.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from .working_memory import WorkingMemory
    from .rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class RecursionState(Enum):
    """State of recursive reasoning."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DEPTH_LIMIT = "depth_limit"


@dataclass
class RecursiveReasoningTask:
    """A recursive reasoning task."""
    task_id: str
    question: str
    depth: int
    max_depth: int
    parent_task_id: Optional[str] = None
    state: RecursionState = RecursionState.PENDING
    result: Optional[Dict[str, Any]] = None
    reasoning_steps: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: float = 30.0


class RecursiveReasoningEngine:
    """
    Engine for recursive reasoning about reasoning processes.
    
    Allows the system to reason about its own reasoning with:
    - Depth limits to prevent infinite recursion
    - Timeout guards for safety
    - Reasoning trace tracking
    - Metacognitive reflection
    """
    
    def __init__(
        self,
        max_depth: int = 3,
        timeout_seconds: float = 30.0,
        working_memory: Optional["WorkingMemory"] = None,
        rule_engine: Optional["RuleEngine"] = None
    ):
        """
        Initialize recursive reasoning engine.
        
        Args:
            max_depth: Maximum recursion depth
            timeout_seconds: Timeout per recursive call
            working_memory: Optional working memory for context
            rule_engine: Optional rule engine for rule-based reasoning
        """
        self.max_depth = max_depth
        self.timeout_seconds = timeout_seconds
        self.working_memory = working_memory
        self.rule_engine = rule_engine
        
        # Active tasks tracking
        self.active_tasks: Dict[str, RecursiveReasoningTask] = {}
        self.task_history: List[RecursiveReasoningTask] = []
        self.next_task_id: int = 1
        
        # Safety: Track recursion depth to prevent stack overflow
        self._current_depth: int = 0
        self._max_observed_depth: int = 0
        
        logger.info(
            f"Initialized RecursiveReasoningEngine "
            f"(max_depth={max_depth}, timeout={timeout_seconds}s)"
        )
    
    def reason_recursively(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        depth: int = 0,
        parent_task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform recursive reasoning about a question.
        
        Args:
            question: Question to reason about
            context: Optional context dictionary
            depth: Current recursion depth
            parent_task_id: Optional parent task ID
            
        Returns:
            Reasoning result with answer and trace
        """
        # Safety check: depth limit
        if depth >= self.max_depth:
            logger.warning(f"Recursion depth limit reached ({depth} >= {self.max_depth})")
            return {
                "answer": "Recursion depth limit reached",
                "depth": depth,
                "state": RecursionState.DEPTH_LIMIT.value,
                "reasoning_steps": []
            }
        
        # Safety check: prevent stack overflow
        if self._current_depth >= self.max_depth:
            logger.warning(f"Current depth ({self._current_depth}) exceeds max depth")
            return {
                "answer": "Recursion safety limit reached",
                "depth": self._current_depth,
                "state": RecursionState.DEPTH_LIMIT.value,
                "reasoning_steps": []
            }
        
        # Create task
        task_id = f"recursive_task_{self.next_task_id}"
        self.next_task_id += 1
        
        task = RecursiveReasoningTask(
            task_id=task_id,
            question=question,
            depth=depth,
            max_depth=self.max_depth,
            parent_task_id=parent_task_id,
            timeout_seconds=self.timeout_seconds
        )
        
        self.active_tasks[task_id] = task
        task.state = RecursionState.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        self._current_depth += 1
        self._max_observed_depth = max(self._max_observed_depth, self._current_depth)
        
        try:
            # Perform reasoning
            result = self._perform_reasoning(task, context or {})
            
            task.result = result
            task.state = RecursionState.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            
            # Check if deeper reasoning is needed
            if result.get("needs_deeper_reasoning", False) and depth < self.max_depth - 1:
                # Recursively reason about the reasoning
                deeper_question = result.get("deeper_question", f"Why is '{result.get('answer', '')}' the answer?")
                deeper_result = self.reason_recursively(
                    question=deeper_question,
                    context={
                        "parent_answer": result.get("answer"),
                        "parent_confidence": result.get("confidence", 0.5),
                        **(context or {})
                    },
                    depth=depth + 1,
                    parent_task_id=task_id
                )
                
                # Integrate deeper reasoning
                result["deeper_reasoning"] = deeper_result
                result["final_confidence"] = self._compute_confidence(result, deeper_result)
                task.reasoning_steps.append({
                    "type": "recursive_deepening",
                    "depth": depth + 1,
                    "result": deeper_result
                })
            
            return result
            
        except TimeoutError:
            task.state = RecursionState.TIMEOUT
            task.completed_at = datetime.now(timezone.utc)
            logger.warning(f"Recursive reasoning task {task_id} timed out")
            return {
                "answer": "Reasoning timed out",
                "depth": depth,
                "state": RecursionState.TIMEOUT.value,
                "reasoning_steps": task.reasoning_steps
            }
        except Exception as e:
            task.state = RecursionState.FAILED
            task.completed_at = datetime.now(timezone.utc)
            logger.error(f"Error in recursive reasoning: {e}", exc_info=True)
            return {
                "answer": f"Reasoning failed: {str(e)}",
                "depth": depth,
                "state": RecursionState.FAILED.value,
                "reasoning_steps": task.reasoning_steps
            }
        finally:
            self._current_depth -= 1
            # Move to history
            self.task_history.append(task)
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Limit history size
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-1000:]
    
    def _perform_reasoning(
        self,
        task: RecursiveReasoningTask,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform actual reasoning step.
        
        Args:
            task: Recursive reasoning task
            context: Context dictionary
            
        Returns:
            Reasoning result
        """
        start_time = time.time()
        
        # Check timeout
        if time.time() - start_time > task.timeout_seconds:
            raise TimeoutError(f"Reasoning exceeded timeout of {task.timeout_seconds}s")
        
        # Step 1: Analyze the question
        analysis = self._analyze_question(task.question, context)
        task.reasoning_steps.append({
            "type": "question_analysis",
            "step": analysis
        })
        
        # Step 2: Retrieve relevant knowledge (if working memory available)
        relevant_knowledge = []
        if self.working_memory:
            relevant_knowledge = self._retrieve_relevant_knowledge(task.question, context)
            task.reasoning_steps.append({
                "type": "knowledge_retrieval",
                "items_count": len(relevant_knowledge)
            })
        
        # Step 3: Apply reasoning rules (if rule engine available)
        reasoning_result = None
        if self.rule_engine and self.working_memory:
            # Create temporary working memory items for reasoning
            for knowledge_item in relevant_knowledge[:3]:  # Limit to 3 items
                self.working_memory.add({
                    "type": "reasoning_context",
                    "content": knowledge_item,
                    "source": "recursive_reasoning"
                })
            
            # Execute reasoning cycle
            try:
                cycle_results = self.rule_engine.execute_cycle(
                    self.working_memory,
                    max_rules=3  # Limit rules for recursive reasoning
                )
                reasoning_result = {
                    "rules_fired": len(cycle_results),
                    "results": cycle_results
                }
                task.reasoning_steps.append({
                    "type": "rule_based_reasoning",
                    "result": reasoning_result
                })
            except Exception as e:
                logger.warning(f"Error in rule-based reasoning: {e}")
        
        # Step 4: Synthesize answer
        answer = self._synthesize_answer(
            task.question,
            analysis,
            relevant_knowledge,
            reasoning_result,
            context
        )
        
        # Step 5: Assess confidence and need for deeper reasoning
        confidence = self._assess_confidence(answer, analysis, relevant_knowledge)
        needs_deeper = confidence < 0.7 and task.depth < task.max_depth - 1
        
        result = {
            "answer": answer,
            "confidence": confidence,
            "depth": task.depth,
            "reasoning_steps_count": len(task.reasoning_steps),
            "needs_deeper_reasoning": needs_deeper,
            "deeper_question": f"What are the assumptions and reasoning steps behind '{answer}'?" if needs_deeper else None
        }
        
        return result
    
    def _analyze_question(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the question to understand what reasoning is needed."""
        # Simple analysis - could be enhanced with LLM
        analysis = {
            "question_type": "general",  # Could be: factual, logical, procedural, etc.
            "complexity": "medium",
            "requires_knowledge": True,
            "requires_reasoning": True
        }
        
        # Detect question type
        question_lower = question.lower()
        if any(word in question_lower for word in ["why", "how", "what causes"]):
            analysis["question_type"] = "causal"
            analysis["complexity"] = "high"
        elif any(word in question_lower for word in ["what", "which", "who"]):
            analysis["question_type"] = "factual"
            analysis["complexity"] = "low"
        elif any(word in question_lower for word in ["should", "ought", "better"]):
            analysis["question_type"] = "normative"
            analysis["complexity"] = "high"
        
        return analysis
    
    def _retrieve_relevant_knowledge(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge from working memory."""
        if not self.working_memory:
            return []
        
        # Simple keyword-based retrieval
        # In a full implementation, this would use semantic search
        relevant = self.working_memory.retrieve(
            pattern={"type": "reasoning_context"},
            min_activation=0.3
        )
        
        return relevant[:5]  # Limit to 5 items
    
    def _synthesize_answer(
        self,
        question: str,
        analysis: Dict[str, Any],
        relevant_knowledge: List[Dict[str, Any]],
        reasoning_result: Optional[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Synthesize an answer from analysis and knowledge."""
        # Simple synthesis - in full implementation, would use LLM or more sophisticated logic
        if reasoning_result and reasoning_result.get("results"):
            # Use rule-based reasoning result
            results = reasoning_result["results"]
            if results:
                return f"Based on reasoning rules: {str(results[0].get('content', 'No specific answer'))}"
        
        if relevant_knowledge:
            # Use relevant knowledge
            return f"Based on available knowledge: {str(relevant_knowledge[0].get('content', 'No specific answer'))}"
        
        # Default answer
        return f"Reasoning about: {question} (analysis: {analysis.get('question_type', 'general')})"
    
    def _assess_confidence(
        self,
        answer: str,
        analysis: Dict[str, Any],
        relevant_knowledge: List[Dict[str, Any]]
    ) -> float:
        """Assess confidence in the answer."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have relevant knowledge
        if relevant_knowledge:
            confidence += 0.2 * min(1.0, len(relevant_knowledge) / 3.0)
        
        # Decrease confidence for complex questions
        if analysis.get("complexity") == "high":
            confidence -= 0.1
        elif analysis.get("complexity") == "low":
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _compute_confidence(
        self,
        parent_result: Dict[str, Any],
        deeper_result: Dict[str, Any]
    ) -> float:
        """Compute final confidence after deeper reasoning."""
        parent_conf = parent_result.get("confidence", 0.5)
        deeper_conf = deeper_result.get("final_confidence") or deeper_result.get("confidence", 0.5)
        
        # Weighted average: deeper reasoning has more weight
        final_conf = 0.3 * parent_conf + 0.7 * deeper_conf
        
        return max(0.0, min(1.0, final_conf))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about recursive reasoning."""
        if not self.task_history:
            return {"status": "no_data"}
        
        completed = [t for t in self.task_history if t.state == RecursionState.COMPLETED]
        failed = [t for t in self.task_history if t.state == RecursionState.FAILED]
        timeout = [t for t in self.task_history if t.state == RecursionState.TIMEOUT]
        depth_limit = [t for t in self.task_history if t.state == RecursionState.DEPTH_LIMIT]
        
        avg_depth = sum(t.depth for t in self.task_history) / len(self.task_history) if self.task_history else 0.0
        
        return {
            "total_tasks": len(self.task_history),
            "completed": len(completed),
            "failed": len(failed),
            "timeout": len(timeout),
            "depth_limit": len(depth_limit),
            "success_rate": len(completed) / len(self.task_history) if self.task_history else 0.0,
            "avg_depth": avg_depth,
            "max_observed_depth": self._max_observed_depth,
            "active_tasks": len(self.active_tasks)
        }

