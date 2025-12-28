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
        declarative_memory: Optional["DeclarativeMemoryInterface"] = None
    ):
        """
        Initialize rule engine.
        
        Args:
            rule_system: Optional ProductionRuleSystem instance
            declarative_memory: Optional DeclarativeMemoryInterface for memory integration
        """
        self.rule_system = rule_system or ProductionRuleSystem()
        self.declarative_memory = declarative_memory
    
    def match_rules(self, working_memory: WorkingMemory) -> List[ProductionRule]:
        """
        Find rules whose conditions match working memory.
        
        Returns sorted list of matching rules.
        """
        matched_rules = []
        for rule in self.rule_system.rules:
            try:
                if rule.matches(working_memory):
                    matched_rules.append(rule)
            except Exception as e:
                logger.error(f"Error matching rule '{rule.name}': {e}")
                continue
        
        # Sort by priority (highest first), then strength
        matched_rules.sort(key=lambda r: (r.priority, r.strength), reverse=True)
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
                results = rule.execute(working_memory)
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
        results = self.execute_rules(rules_to_fire, working_memory)
        
        # Post-cycle: Store inference results to declarative memory
        if self.declarative_memory and results:
            self._store_cycle_results(rules_to_fire, results)
        
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
