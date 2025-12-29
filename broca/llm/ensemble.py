"""
Multi-model ensemble reasoning.

Implements ensemble reasoning using multiple LLM models with voting,
consensus, and specialized roles.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from . import LLMClient
    from .model_router import ModelRouter, TaskType

logger = logging.getLogger(__name__)


class EnsembleStrategy(Enum):
    """Strategies for ensemble reasoning."""
    VOTING = "voting"              # Majority vote
    CONSENSUS = "consensus"        # Require agreement
    WEIGHTED = "weighted"          # Weighted combination
    SPECIALIZED = "specialized"    # Different models for different roles


@dataclass
class EnsembleResult:
    """Result from ensemble reasoning."""
    answer: str
    confidence: float
    model_results: List[Dict[str, Any]] = field(default_factory=list)
    consensus_level: float = 0.0
    strategy_used: str = ""


class LLMEnsemble:
    """
    Multi-model ensemble for reasoning.
    
    Combines outputs from multiple LLM models using various strategies.
    """
    
    def __init__(
        self,
        model_router: Optional["ModelRouter"] = None,
        default_strategy: EnsembleStrategy = EnsembleStrategy.WEIGHTED
    ):
        """
        Initialize LLM ensemble.
        
        Args:
            model_router: Optional ModelRouter for model selection
            default_strategy: Default ensemble strategy
        """
        self.model_router = model_router
        self.default_strategy = default_strategy
        
        logger.info(f"Initialized LLMEnsemble (strategy: {default_strategy.value})")
    
    def reason_ensemble(
        self,
        prompt: str,
        task_type: Optional["TaskType"] = None,
        strategy: Optional[EnsembleStrategy] = None,
        models: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> EnsembleResult:
        """
        Perform ensemble reasoning.
        
        Args:
            prompt: Input prompt
            task_type: Optional task type
            strategy: Optional ensemble strategy (defaults to default_strategy)
            models: Optional list of model names to use (if None, uses router)
            context: Optional context
            
        Returns:
            EnsembleResult with combined answer
        """
        strategy = strategy or self.default_strategy
        
        # Select models
        if models is None and self.model_router:
            # Use router to select best model(s)
            primary_model = self.model_router.route_task(prompt, task_type, context)
            models = [primary_model] if primary_model else []
        elif models is None:
            # Fallback: use all available models
            if self.model_router:
                models = list(self.model_router.models.keys())
            else:
                models = []
        
        if not models:
            logger.warning("No models available for ensemble reasoning")
            return EnsembleResult(
                answer="No models available",
                confidence=0.0,
                strategy_used=strategy.value
            )
        
        # Get results from each model
        model_results = []
        for model_name in models:
            if not self.model_router:
                continue
            
            client = self.model_router.get_model(model_name)
            if not client:
                continue
            
            try:
                # Call model
                response = client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3  # Lower temperature for more consistent results
                )
                
                model_results.append({
                    "model": model_name,
                    "response": response,
                    "confidence": 0.7  # Default confidence
                })
                
            except Exception as e:
                logger.error(f"Error calling model {model_name}: {e}", exc_info=True)
                continue
        
        if not model_results:
            return EnsembleResult(
                answer="No valid model responses",
                confidence=0.0,
                strategy_used=strategy.value
            )
        
        # Combine results based on strategy
        if strategy == EnsembleStrategy.VOTING:
            result = self._combine_voting(model_results)
        elif strategy == EnsembleStrategy.CONSENSUS:
            result = self._combine_consensus(model_results)
        elif strategy == EnsembleStrategy.WEIGHTED:
            result = self._combine_weighted(model_results, context)
        elif strategy == EnsembleStrategy.SPECIALIZED:
            result = self._combine_specialized(model_results, task_type)
        else:
            result = self._combine_weighted(model_results, context)
        
        result.model_results = model_results
        result.strategy_used = strategy.value
        
        return result
    
    def _combine_voting(self, model_results: List[Dict[str, Any]]) -> EnsembleResult:
        """Combine results using majority voting."""
        # Extract answers
        answers = [r["response"] for r in model_results]
        
        # Simple voting: most common answer
        answer_counts = {}
        for answer in answers:
            # Normalize answer (simple string matching)
            normalized = answer.strip().lower()[:100]  # First 100 chars
            answer_counts[normalized] = answer_counts.get(normalized, 0) + 1
        
        # Get most common answer
        if answer_counts:
            winning_answer = max(answer_counts.items(), key=lambda x: x[1])[0]
            consensus_level = answer_counts[winning_answer] / len(answers)
            
            # Find original answer
            for result in model_results:
                if result["response"].strip().lower()[:100] == winning_answer:
                    return EnsembleResult(
                        answer=result["response"],
                        confidence=consensus_level,
                        consensus_level=consensus_level
                    )
        
        # Fallback: use first result
        return EnsembleResult(
            answer=model_results[0]["response"],
            confidence=0.5,
            consensus_level=1.0 / len(model_results)
        )
    
    def _combine_consensus(self, model_results: List[Dict[str, Any]]) -> EnsembleResult:
        """Combine results requiring consensus."""
        if len(model_results) == 1:
            return EnsembleResult(
                answer=model_results[0]["response"],
                confidence=0.7,
                consensus_level=1.0
            )
        
        # Check for agreement (simple similarity check)
        answers = [r["response"] for r in model_results]
        
        # Count similar answers
        similar_groups = []
        for answer in answers:
            # Check if similar to any existing group
            added = False
            for group in similar_groups:
                if self._answers_similar(answer, group[0]):
                    group.append(answer)
                    added = True
                    break
            
            if not added:
                similar_groups.append([answer])
        
        # Find largest group
        largest_group = max(similar_groups, key=len)
        consensus_level = len(largest_group) / len(answers)
        
        # Require at least 50% agreement for consensus
        if consensus_level >= 0.5:
            return EnsembleResult(
                answer=largest_group[0],
                confidence=consensus_level,
                consensus_level=consensus_level
            )
        else:
            # No consensus
            return EnsembleResult(
                answer=model_results[0]["response"],  # Use first as fallback
                confidence=0.3,
                consensus_level=consensus_level
            )
    
    def _combine_weighted(
        self,
        model_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> EnsembleResult:
        """Combine results using weighted average."""
        # Weight by confidence
        total_weight = 0.0
        weighted_answer = ""
        
        for result in model_results:
            weight = result.get("confidence", 0.7)
            total_weight += weight
            # Simple weighted combination (in practice, would use more sophisticated merging)
            if not weighted_answer:
                weighted_answer = result["response"]
            else:
                # Combine answers (simplified - would use LLM for better merging)
                weighted_answer = f"{weighted_answer}\n\n{result['response']}"
        
        avg_confidence = total_weight / len(model_results) if model_results else 0.0
        
        return EnsembleResult(
            answer=weighted_answer,
            confidence=avg_confidence,
            consensus_level=1.0  # All models considered
        )
    
    def _combine_specialized(
        self,
        model_results: List[Dict[str, Any]],
        task_type: Optional["TaskType"]
    ) -> EnsembleResult:
        """Combine results using specialized roles."""
        # For specialized strategy, use the result from the most appropriate model
        # In a full implementation, would assign roles (reasoner, critic, planner, etc.)
        
        if task_type == TaskType.REASONING:
            # Prefer reasoning-strong models
            best_result = max(
                model_results,
                key=lambda r: r.get("confidence", 0.5)
            )
        else:
            # Use first result
            best_result = model_results[0]
        
        return EnsembleResult(
            answer=best_result["response"],
            confidence=best_result.get("confidence", 0.7),
            consensus_level=1.0
        )
    
    def _answers_similar(self, answer1: str, answer2: str, threshold: float = 0.7) -> bool:
        """Check if two answers are similar."""
        # Simple similarity check (in practice, would use embeddings or more sophisticated comparison)
        a1_lower = answer1.strip().lower()
        a2_lower = answer2.strip().lower()
        
        # Check if one contains the other (simple heuristic)
        if len(a1_lower) > 0 and len(a2_lower) > 0:
            if a1_lower in a2_lower or a2_lower in a1_lower:
                return True
            
            # Check word overlap
            words1 = set(a1_lower.split())
            words2 = set(a2_lower.split())
            if words1 and words2:
                overlap = len(words1 & words2) / len(words1 | words2)
                return overlap >= threshold
        
        return False

