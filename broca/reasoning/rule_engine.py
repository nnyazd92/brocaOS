"""
Rule engine for matching and executing production rules.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from .production_rules import ProductionRule, ProductionRuleSystem
from .working_memory import WorkingMemory

if TYPE_CHECKING:
    from .declarative_memory import DeclarativeMemoryInterface
    from .llm_pattern_matcher import LLMPatternMatcher
    from .loop_detector import LoopDetector

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Engine for matching and executing production rules.
    
    Separates rule matching logic from rule execution for
    better modularity and testing.
    """
    
    def __init__(
        self,
        rule_system: Optional[ProductionRuleSystem] = None,
        declarative_memory: Optional["DeclarativeMemoryInterface"] = None,
        pattern_matcher: Optional["LLMPatternMatcher"] = None,
        working_memory: Optional[WorkingMemory] = None,
        loop_detector: Optional["LoopDetector"] = None
    ):
        """
        Initialize rule engine.
        
        Args:
            rule_system: Optional ProductionRuleSystem instance
            declarative_memory: Optional DeclarativeMemoryInterface for memory integration
            pattern_matcher: Optional LLMPatternMatcher for semantic pattern matching
            working_memory: Optional WorkingMemory instance (if None, uses rule_system's WM)
        """
        # Initialize pattern matcher if not provided
        if pattern_matcher is None:
            try:
                from .llm_pattern_matcher import LLMPatternMatcher
                from ..llm import create_llm_client
                from ..config import config
                
                llm_client = create_llm_client(
                    model=config.reasoning.llm_pattern_matching_model,
                    provider="openai",  # Always use OpenAI for pattern matching
                )
                pattern_matcher = LLMPatternMatcher(
                    llm_client=llm_client,
                    model=config.reasoning.llm_pattern_matching_model
                )
                logger.info(f"Initialized LLM pattern matcher with model: {config.reasoning.llm_pattern_matching_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM pattern matcher: {e}. Pattern matching will use legacy dict matching.")
                pattern_matcher = None
        
        self.pattern_matcher = pattern_matcher
        
        # Initialize rule system with pattern matcher
        if rule_system is None:
            rule_system = ProductionRuleSystem(pattern_matcher=pattern_matcher)
        else:
            # Set pattern matcher on existing rule system
            rule_system.pattern_matcher = pattern_matcher
            # Update all existing rules
            for rule in rule_system.rules:
                rule.pattern_matcher = pattern_matcher
        
        self.rule_system = rule_system
        self.declarative_memory = declarative_memory
        
        # Set pattern matcher on working memory if provided
        if working_memory is not None:
            working_memory.pattern_matcher = pattern_matcher
        elif rule_system.working_memory is not None:
            rule_system.working_memory.pattern_matcher = pattern_matcher
        
        # Initialize loop detector if not provided and enabled in config
        if loop_detector is None:
            try:
                from .loop_detector import LoopDetector
                from ..config import config
                
                if config.reasoning.loop_detection_enabled:
                    loop_detector = LoopDetector(
                        history_window=config.reasoning.loop_detection_history_window,
                        time_window_seconds=config.reasoning.loop_detection_time_window,
                        max_tool_queue_size=config.reasoning.tool_queue_max_size,
                        max_tool_retries=config.reasoning.tool_queue_max_retries
                    )
                    logger.info("Initialized loop detector")
                else:
                    logger.debug("Loop detection disabled in config")
                    loop_detector = None
            except Exception as e:
                logger.warning(f"Failed to initialize loop detector: {e}. Loop detection disabled.")
                loop_detector = None
        
        self.loop_detector = loop_detector
    
    def match_rules(self, working_memory: WorkingMemory) -> List[ProductionRule]:
        """
        Find rules whose conditions match working memory.
        
        Uses batched pattern matching if LLM pattern matcher is available.
        
        Returns sorted list of matching rules.
        """
        # If we have an LLM pattern matcher, we can batch pattern matching
        # However, the batching is handled internally by the pattern matcher
        # when rules call _pattern_matches, so we just need to ensure
        # the pattern matcher is set on all rules
        matched_rules = []
        for rule in self.rule_system.rules:
            # Ensure pattern matcher is set on rule
            if self.pattern_matcher is not None:
                rule.pattern_matcher = self.pattern_matcher
            
            try:
                if rule.matches(working_memory):
                    matched_rules.append(rule)
            except Exception as e:
                logger.error(f"Error matching rule '{rule.name}': {e}")
                continue
        
        # Sort by priority (highest first), then strength
        matched_rules.sort(key=lambda r: (r.priority, r.strength), reverse=True)
        top_priority = matched_rules[0].priority if matched_rules else 0.0
        
        logger.info(
            f"Rule engine matched rules: evaluated={len(self.rule_system.rules)}, "
            f"matched={len(matched_rules)}, "
            f"top_priority={top_priority:.3f}, "
            f"llm_pattern_matching={self.pattern_matcher is not None}",
            extra={
                "event": "rule_engine_rules_matched",
                "evaluated_count": len(self.rule_system.rules),
                "matched_count": len(matched_rules),
                "matched_rule_names": [r.name for r in matched_rules],
                "top_priority": top_priority,
                "llm_pattern_matching": self.pattern_matcher is not None,
            }
        )
        
        return matched_rules
    
    def execute_rules(self, rules: List[ProductionRule], 
                     working_memory: WorkingMemory) -> List[Dict[str, Any]]:
        """
        Execute a list of rules.
        
        Returns list of action results.
        """
        all_results = []
        
        for rule in rules:
            try:
                # Pass loop detector in context
                context = {"loop_detector": self.loop_detector} if self.loop_detector else {}
                results = rule.execute(working_memory, context=context)
                all_results.extend(results)
                
                # Record in history
                self.rule_system.rule_history.append({
                    "timestamp": rule.last_fired.isoformat() if rule.last_fired else "",
                    "rule": rule.name,
                    "results": results
                })
                
                # Limit history size
                if len(self.rule_system.rule_history) > 100:
                    self.rule_system.rule_history = self.rule_system.rule_history[-100:]
                    
            except Exception as e:
                logger.error(f"Error executing rule '{rule.name}': {e}")
                continue
        
        return all_results
    
    def execute_cycle(self, working_memory: WorkingMemory, 
                     max_rules: int = 5) -> List[Dict[str, Any]]:
        """
        Execute one reasoning cycle.
        
        Pre-cycle: Trigger declarative memory retrieval based on current WM state
        During cycle: Use retrieved context for rule matching
        Post-cycle: Store inference results to declarative memory
        
        Returns list of action results from fired rules.
        """
        # Pre-cycle: Trigger declarative memory retrieval
        if self.declarative_memory and working_memory.spreading_activation:
            try:
                working_memory.refresh_from_declarative_memory(limit=5)
            except Exception as e:
                logger.error(f"Error in pre-cycle memory retrieval: {e}", exc_info=True)
        
        # Match and execute rules
        matched_rules = self.match_rules(working_memory)
        if not matched_rules:
            return []
        
        # Limit number of rules to fire
        rules_to_fire = matched_rules[:max_rules]
        
        # Check for loops before firing rules
        if self.loop_detector is not None:
            # Check tool queue first
            queue_allowed, queue_reason = self.loop_detector.check_tool_queue(working_memory.tool_queue)
            if not queue_allowed:
                logger.error(f"Tool queue blocked by loop detector: {queue_reason}")
                return []  # Don't fire any rules if queue is blocked
            
            # Filter out rules that would create loops
            allowed_rules = []
            for rule in rules_to_fire:
                allowed, reason = self.loop_detector.check_rule_firing(rule, working_memory)
                if allowed:
                    allowed_rules.append(rule)
                else:
                    logger.warning(f"Rule '{rule.name}' blocked by loop detector: {reason}")
            
            rules_to_fire = allowed_rules
        
        # Note: Z3 validation has been removed. Use the z3_validate tool instead
        # for LLM-driven logical validation when needed.
        
        results = self.execute_rules(rules_to_fire, working_memory)
        
        # Record rule firings for loop detection
        if self.loop_detector is not None and rules_to_fire:
            # Re-match rules to see which ones are now enabled
            try:
                enabled_rules = self.match_rules(working_memory)
                for rule in rules_to_fire:
                    self.loop_detector.record_rule_firing(rule, working_memory, enabled_rules)
            except Exception as e:
                logger.error(f"Error recording rule firing for loop detection: {e}", exc_info=True)
        
        # Post-cycle: Store inference results to declarative memory
        stored_count = 0
        if self.declarative_memory and results:
            try:
                self._store_cycle_results(rules_to_fire, results)
                stored_count = len(results)
            except Exception as e:
                logger.error(f"Error storing cycle results: {e}", exc_info=True)
        
        logger.info(
            f"Rule engine cycle complete: matched={len(matched_rules)}, "
            f"fired={len(rules_to_fire)}, results={len(results)}, "
            f"stored_to_memory={stored_count}",
            extra={
                "event": "rule_engine_cycle_complete",
                "matched_count": len(matched_rules),
                "fired_count": len(rules_to_fire),
                "results_count": len(results),
                "stored_to_memory": stored_count,
                "fired_rule_names": [r.name for r in rules_to_fire],
                "llm_pattern_matching": self.pattern_matcher is not None,
            }
        )
        
        return results
    
    def _store_cycle_results(
        self,
        fired_rules: List[ProductionRule],
        results: List[Dict[str, Any]]
    ):
        """
        Store rule execution results to declarative memory.
        
        Args:
            fired_rules: List of rules that fired
            results: List of action results from rule execution
        """
        if not self.declarative_memory:
            return
        
        try:
            # Store rule execution results
            for rule in fired_rules:
                rule_results = [r for r in results if r.get("type")]  # Filter relevant results
                
                self.declarative_memory.store_rule_execution(
                    rule_name=rule.name,
                    results=rule_results,
                    context=f"Priority: {rule.priority}, Strength: {rule.strength}"
                )
            
            # Store inference results (results with type "add_to_memory" that are inferences)
            for result in results:
                if result.get("type") == "add_to_memory":
                    content = result.get("content", {})
                    if isinstance(content, dict) and content.get("type") == "inference":
                        inference_text = content.get("content") or content.get("description") or str(content)
                        if inference_text:
                            self.declarative_memory.store_inference(
                                inference=inference_text,
                                context=f"From rule execution cycle",
                                importance=0.7
                            )
                            
        except Exception as e:
            logger.error(f"Error storing cycle results to declarative memory: {e}", exc_info=True)
