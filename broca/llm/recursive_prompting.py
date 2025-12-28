"""
Recursive prompting system.

Implements LLM reasoning about LLM outputs with chain-of-thought
and self-reflection capabilities.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from . import LLMClient
    from .ensemble import LLMEnsemble, EnsembleStrategy

logger = logging.getLogger(__name__)


class ReflectionType(Enum):
    """Types of reflection."""
    SELF_CRITIQUE = "self_critique"
    REASONING_TRACE = "reasoning_trace"
    CONFIDENCE_ASSESSMENT = "confidence_assessment"
    ERROR_DETECTION = "error_detection"


@dataclass
class ReasoningStep:
    """A step in chain-of-thought reasoning."""
    step_number: int
    thought: str
    confidence: float = 0.5
    reasoning_type: str = "general"


@dataclass
class RecursivePromptingResult:
    """Result from recursive prompting."""
    final_answer: str
    reasoning_steps: List[ReasoningStep]
    reflections: List[Dict[str, Any]]
    confidence: float
    depth: int
    iterations: int


class RecursivePromptingSystem:
    """
    Recursive prompting system for self-reflective reasoning.
    
    Implements:
    - Chain-of-thought reasoning
    - Self-reflection on outputs
    - Iterative refinement
    - Confidence calibration
    """
    
    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        ensemble: Optional["LLMEnsemble"] = None,
        max_iterations: int = 3,
        max_depth: int = 2
    ):
        """
        Initialize recursive prompting system.
        
        Args:
            llm_client: Optional LLMClient for reasoning
            ensemble: Optional LLMEnsemble for multi-model reasoning
            max_iterations: Maximum iterations for refinement
            max_depth: Maximum recursion depth
        """
        self.llm_client = llm_client
        self.ensemble = ensemble
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        
        logger.info(
            f"Initialized RecursivePromptingSystem "
            f"(max_iterations={max_iterations}, max_depth={max_depth})"
        )
    
    def reason_with_reflection(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        depth: int = 0
    ) -> RecursivePromptingResult:
        """
        Perform reasoning with self-reflection.
        
        Args:
            question: Question to reason about
            context: Optional context
            depth: Current recursion depth
            
        Returns:
            RecursivePromptingResult with reasoning trace
        """
        if depth >= self.max_depth:
            logger.warning(f"Recursion depth limit reached ({depth} >= {self.max_depth})")
            return RecursivePromptingResult(
                final_answer="Depth limit reached",
                reasoning_steps=[],
                reflections=[],
                confidence=0.0,
                depth=depth,
                iterations=0
            )
        
        reasoning_steps = []
        reflections = []
        current_answer = ""
        confidence = 0.5
        
        # Iterative refinement
        for iteration in range(self.max_iterations):
            # Step 1: Generate reasoning
            reasoning_prompt = self._build_reasoning_prompt(
                question,
                current_answer,
                reasoning_steps,
                iteration
            )
            
            reasoning_response = self._call_llm(reasoning_prompt)
            if not reasoning_response:
                break
            
            # Extract reasoning step
            step = self._extract_reasoning_step(reasoning_response, iteration)
            reasoning_steps.append(step)
            
            # Update answer
            current_answer = step.thought
            
            # Step 2: Self-reflection
            if iteration < self.max_iterations - 1:  # Don't reflect on last iteration
                reflection = self._reflect_on_reasoning(
                    question,
                    current_answer,
                    reasoning_steps,
                    depth
                )
                reflections.append(reflection)
                
                # Check if reflection suggests deeper reasoning
                if reflection.get("needs_deeper_reasoning", False) and depth < self.max_depth - 1:
                    # Recursively reason about the reasoning
                    deeper_result = self.reason_with_reflection(
                        question=reflection.get("deeper_question", "Why is this reasoning correct?"),
                        context={
                            "parent_reasoning": reasoning_steps,
                            "parent_answer": current_answer,
                            **(context or {})
                        },
                        depth=depth + 1
                    )
                    
                    # Integrate deeper reasoning
                    reflections.append({
                        "type": "recursive_deepening",
                        "depth": depth + 1,
                        "result": {
                            "answer": deeper_result.final_answer,
                            "confidence": deeper_result.confidence
                        }
                    })
                    
                    # Update confidence based on deeper reasoning
                    confidence = 0.7 * confidence + 0.3 * deeper_result.confidence
            
            # Step 3: Assess confidence
            confidence = self._assess_confidence(current_answer, reasoning_steps, reflections)
            
            # Step 4: Check if we should continue
            if confidence > 0.8 and iteration > 0:
                # High confidence, can stop early
                break
        
        return RecursivePromptingResult(
            final_answer=current_answer,
            reasoning_steps=reasoning_steps,
            reflections=reflections,
            confidence=confidence,
            depth=depth,
            iterations=iteration + 1
        )
    
    def _build_reasoning_prompt(
        self,
        question: str,
        current_answer: str,
        reasoning_steps: List[ReasoningStep],
        iteration: int
    ) -> str:
        """Build prompt for reasoning step."""
        prompt = f"Question: {question}\n\n"
        
        if reasoning_steps:
            prompt += "Previous reasoning steps:\n"
            for step in reasoning_steps:
                prompt += f"  Step {step.step_number}: {step.thought}\n"
            prompt += "\n"
        
        if current_answer:
            prompt += f"Current answer: {current_answer}\n\n"
        
        if iteration == 0:
            prompt += "Think step by step about this question. What is your reasoning?"
        else:
            prompt += "Refine your reasoning. What additional thoughts or corrections do you have?"
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM with prompt."""
        if self.ensemble:
            # Use ensemble
            result = self.ensemble.reason_ensemble(
                prompt=prompt,
                task_type=None,  # Will be inferred
                strategy=None  # Use default
            )
            return result.answer
        elif self.llm_client:
            # Use single client
            try:
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return self.llm_client.extract_assistant_content(response)
            except Exception as e:
                logger.error(f"Error calling LLM: {e}", exc_info=True)
                return None
        else:
            logger.warning("No LLM client or ensemble available")
            return None
    
    def _extract_reasoning_step(self, response: str, step_number: int) -> ReasoningStep:
        """Extract reasoning step from LLM response."""
        # Simple extraction - in practice would use more sophisticated parsing
        return ReasoningStep(
            step_number=step_number + 1,
            thought=response.strip(),
            confidence=0.7,  # Default confidence
            reasoning_type="chain_of_thought"
        )
    
    def _reflect_on_reasoning(
        self,
        question: str,
        current_answer: str,
        reasoning_steps: List[ReasoningStep],
        depth: int
    ) -> Dict[str, Any]:
        """Reflect on the reasoning process."""
        reflection_prompt = f"""You are reflecting on your own reasoning process.

Original question: {question}

Your reasoning steps:
"""
        for step in reasoning_steps:
            reflection_prompt += f"  {step.step_number}. {step.thought}\n"
        
        reflection_prompt += f"""
Current answer: {current_answer}

Reflect on your reasoning:
1. Are there any logical errors or gaps?
2. Is the reasoning sound?
3. What assumptions are you making?
4. Do you need to think deeper about any aspect?

Provide your reflection:"""
        
        reflection_response = self._call_llm(reflection_prompt)
        
        if not reflection_response:
            return {
                "type": ReflectionType.SELF_CRITIQUE.value,
                "content": "No reflection available",
                "needs_deeper_reasoning": False
            }
        
        # Analyze reflection for deeper reasoning needs
        needs_deeper = any(word in reflection_response.lower() for word in [
            "uncertain", "not sure", "need to think", "assumption", "gap", "error"
        ])
        
        deeper_question = None
        if needs_deeper:
            deeper_question = f"What are the assumptions and reasoning behind: {current_answer}?"
        
        return {
            "type": ReflectionType.SELF_CRITIQUE.value,
            "content": reflection_response,
            "needs_deeper_reasoning": needs_deeper,
            "deeper_question": deeper_question
        }
    
    def _assess_confidence(
        self,
        answer: str,
        reasoning_steps: List[ReasoningStep],
        reflections: List[Dict[str, Any]]
    ) -> float:
        """Assess confidence in the answer."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence with more reasoning steps
        if reasoning_steps:
            confidence += 0.1 * min(1.0, len(reasoning_steps) / 3.0)
        
        # Decrease confidence if reflections indicate issues
        for reflection in reflections:
            if reflection.get("needs_deeper_reasoning", False):
                confidence -= 0.1
        
        # Increase confidence if no negative reflections
        if not any(r.get("needs_deeper_reasoning", False) for r in reflections):
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))

