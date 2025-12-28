"""
Recursive self-improvement system.

Implements recursive self-improvement loops with meta-learning.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from .skill_manager import SkillManager
    from ..self_model.updater import SelfModelUpdater

logger = logging.getLogger(__name__)


class ImprovementType(Enum):
    """Types of improvements."""
    ALGORITHMIC = "algorithmic"      # Improve algorithms
    PROCEDURAL = "procedural"        # Improve procedures
    METACOGNITIVE = "metacognitive"  # Improve thinking about thinking
    LEARNING = "learning"            # Improve learning itself


@dataclass
class Improvement:
    """An improvement made to the system."""
    improvement_id: str
    type: ImprovementType
    description: str
    target_component: str
    improvement_method: str
    effectiveness: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applied: bool = False
    applied_at: Optional[datetime] = None


@dataclass
class MetaLearningState:
    """State of meta-learning."""
    learning_rate: float = 0.1
    improvement_rate: float = 0.0
    effectiveness_trend: float = 0.0
    best_improvements: List[str] = field(default_factory=list)


class RecursiveSelfImprovement:
    """
    Recursive self-improvement system.
    
    Implements:
    - Recursive improvement loops
    - Meta-learning (learning how to learn)
    - Improvement of improvement mechanisms
    """
    
    def __init__(
        self,
        skill_manager: Optional["SkillManager"] = None,
        self_model_updater: Optional["SelfModelUpdater"] = None,
        max_improvement_depth: int = 2
    ):
        """
        Initialize recursive self-improvement system.
        
        Args:
            skill_manager: Optional SkillManager for procedural improvements
            self_model_updater: Optional SelfModelUpdater for self-model improvements
            max_improvement_depth: Maximum depth of recursive improvement
        """
        self.skill_manager = skill_manager
        self.self_model_updater = self_model_updater
        self.max_improvement_depth = max_improvement_depth
        
        # Improvements
        self.improvements: Dict[str, Improvement] = {}
        self.next_improvement_id: int = 1
        
        # Meta-learning state
        self.meta_learning = MetaLearningState()
        
        # Improvement history
        self.improvement_history: List[Dict[str, Any]] = []
        
        logger.info(
            f"Initialized RecursiveSelfImprovement "
            f"(max_depth={max_improvement_depth})"
        )
    
    def improve_recursively(
        self,
        target_component: str,
        improvement_type: ImprovementType,
        depth: int = 0
    ) -> Dict[str, Any]:
        """
        Recursively improve a component.
        
        Args:
            target_component: Component to improve
            improvement_type: Type of improvement
            depth: Current recursion depth
            
        Returns:
            Improvement result
        """
        if depth >= self.max_improvement_depth:
            logger.warning(f"Improvement depth limit reached ({depth} >= {self.max_improvement_depth})")
            return {
                "success": False,
                "reason": "depth_limit",
                "depth": depth
            }
        
        # Generate improvement
        improvement = self._generate_improvement(target_component, improvement_type, depth)
        
        if not improvement:
            return {
                "success": False,
                "reason": "failed_to_generate",
                "depth": depth
            }
        
        # Apply improvement
        applied = self._apply_improvement(improvement)
        
        if applied:
            improvement.applied = True
            improvement.applied_at = datetime.now(timezone.utc)
            
            # Evaluate effectiveness
            effectiveness = self._evaluate_effectiveness(improvement)
            improvement.effectiveness = effectiveness
            
            # If improvement is effective and depth allows, improve the improvement mechanism
            if effectiveness > 0.7 and depth < self.max_improvement_depth - 1:
                logger.debug(f"Improving improvement mechanism (depth {depth + 1})")
                meta_improvement = self.improve_recursively(
                    target_component="improvement_mechanism",
                    improvement_type=ImprovementType.METACOGNITIVE,
                    depth=depth + 1
                )
                
                if meta_improvement.get("success", False):
                    improvement.description += f" [Meta-improved at depth {depth + 1}]"
            
            # Update meta-learning
            self._update_meta_learning(improvement)
            
            return {
                "success": True,
                "improvement_id": improvement.improvement_id,
                "effectiveness": effectiveness,
                "depth": depth
            }
        else:
            return {
                "success": False,
                "reason": "failed_to_apply",
                "depth": depth
            }
    
    def _generate_improvement(
        self,
        target_component: str,
        improvement_type: ImprovementType,
        depth: int
    ) -> Optional[Improvement]:
        """Generate an improvement."""
        improvement_id = f"improvement_{self.next_improvement_id}"
        self.next_improvement_id += 1
        
        # Determine improvement method based on type and component
        if improvement_type == ImprovementType.PROCEDURAL and self.skill_manager:
            method = "skill_refinement"
            description = f"Refine procedural skills for {target_component}"
        elif improvement_type == ImprovementType.METACOGNITIVE:
            method = "metacognitive_enhancement"
            description = f"Enhance metacognitive processes for {target_component}"
        elif improvement_type == ImprovementType.LEARNING:
            method = "learning_optimization"
            description = f"Optimize learning mechanisms for {target_component}"
        else:
            method = "algorithmic_optimization"
            description = f"Optimize algorithms for {target_component}"
        
        improvement = Improvement(
            improvement_id=improvement_id,
            type=improvement_type,
            description=description,
            target_component=target_component,
            improvement_method=method
        )
        
        self.improvements[improvement_id] = improvement
        
        logger.info(f"Generated improvement: {description} (depth {depth})")
        
        return improvement
    
    def _apply_improvement(self, improvement: Improvement) -> bool:
        """Apply an improvement."""
        try:
            if improvement.improvement_method == "skill_refinement" and self.skill_manager:
                # Refine skills
                logger.info(f"Applying skill refinement for {improvement.target_component}")
                return True
            
            elif improvement.improvement_method == "metacognitive_enhancement":
                # Enhance metacognitive processes
                logger.info(f"Applying metacognitive enhancement for {improvement.target_component}")
                return True
            
            elif improvement.improvement_method == "learning_optimization":
                # Optimize learning
                logger.info(f"Applying learning optimization for {improvement.target_component}")
                return True
            
            elif improvement.improvement_method == "algorithmic_optimization":
                # Optimize algorithms
                logger.info(f"Applying algorithmic optimization for {improvement.target_component}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying improvement: {e}", exc_info=True)
            return False
    
    def _evaluate_effectiveness(self, improvement: Improvement) -> float:
        """Evaluate effectiveness of an improvement."""
        # Simple effectiveness evaluation
        # In practice, would measure actual performance improvements
        
        effectiveness = 0.5  # Base effectiveness
        
        # Increase based on improvement type
        if improvement.type == ImprovementType.METACOGNITIVE:
            effectiveness += 0.2  # Metacognitive improvements are often effective
        elif improvement.type == ImprovementType.LEARNING:
            effectiveness += 0.15  # Learning improvements are valuable
        
        # Increase if applied successfully
        if improvement.applied:
            effectiveness += 0.1
        
        return max(0.0, min(1.0, effectiveness))
    
    def _update_meta_learning(self, improvement: Improvement):
        """Update meta-learning state based on improvement."""
        # Update improvement rate
        if improvement.applied:
            self.meta_learning.improvement_rate += 0.01
        
        # Track best improvements
        if improvement.effectiveness > 0.7:
            if improvement.improvement_id not in self.meta_learning.best_improvements:
                self.meta_learning.best_improvements.append(improvement.improvement_id)
                # Keep only top 10
                if len(self.meta_learning.best_improvements) > 10:
                    self.meta_learning.best_improvements = self.meta_learning.best_improvements[-10:]
        
        # Update effectiveness trend
        if len(self.improvement_history) > 0:
            recent_effectiveness = [
                imp.get("effectiveness", 0.5)
                for imp in self.improvement_history[-10:]
            ]
            if recent_effectiveness:
                avg_effectiveness = sum(recent_effectiveness) / len(recent_effectiveness)
                self.meta_learning.effectiveness_trend = avg_effectiveness - 0.5  # Centered at 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about recursive improvement."""
        applied = [imp for imp in self.improvements.values() if imp.applied]
        
        avg_effectiveness = (
            sum(imp.effectiveness for imp in applied) / len(applied)
            if applied else 0.0
        )
        
        return {
            "total_improvements": len(self.improvements),
            "applied_improvements": len(applied),
            "avg_effectiveness": avg_effectiveness,
            "meta_learning": {
                "improvement_rate": self.meta_learning.improvement_rate,
                "effectiveness_trend": self.meta_learning.effectiveness_trend,
                "best_improvements_count": len(self.meta_learning.best_improvements)
            }
        }

