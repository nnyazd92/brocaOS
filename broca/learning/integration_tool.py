"""
Integration tool for learning system.

Provides a tool interface for the LLM to interact with the
procedural learning system, skill management, and experience logging.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..config import config
from .procedural_learning import ProceduralLearner, LearnedProcedure, ProcedureType, ToolCall, ContextPattern
from .skill_manager import SkillManager, Skill, SkillType
from .experience_logger import ExperienceLogger, Experience
from .pattern_extractor import PatternExtractor
from .pattern_extractor import PatternExtractor

logger = logging.getLogger(__name__)


class LearningTool:
    """
    Tool for LLM to interact with learning system.
    
    Provides operations to:
    - Observe tool calls for learning
    - Extract patterns and create procedures
    - Manage skills and proficiency
    - Log experiences for reinforcement learning
    - Get learning suggestions based on context
    """
    
    def __init__(
        self,
        procedural_learner: Optional[ProceduralLearner] = None,
        skill_manager: Optional[SkillManager] = None,
        experience_logger: Optional[ExperienceLogger] = None,
        pattern_extractor: Optional[PatternExtractor] = None,
        skills_storage_path: Optional[str] = None,
        experiences_storage_path: Optional[str] = None,
    ):
        """
        Initialize learning tool.
        
        Args:
            procedural_learner: Procedural learner (creates default if None)
            skill_manager: Skill manager (creates default if None)
            experience_logger: Experience logger (creates default if None)
            pattern_extractor: Pattern extractor (creates default if None)
            skills_storage_path: Path for skill persistence (defaults to data/skills.json)
            experiences_storage_path: Path for experience persistence (defaults to data/experiences.json)
        """
        self.procedural_learner = procedural_learner or ProceduralLearner()
        
        # Initialize skill manager with persistence if not provided
        if skill_manager is None:
            self.skill_manager = SkillManager(storage_path=skills_storage_path)
        else:
            self.skill_manager = skill_manager
        
        # Initialize experience logger with persistence if not provided
        if experience_logger is None:
            self.experience_logger = ExperienceLogger(storage_path=experiences_storage_path)
        else:
            self.experience_logger = experience_logger
        
        self.pattern_extractor = pattern_extractor or PatternExtractor()
        
        # Signal manager for damping (optional)
        self._signal_manager: Optional[Any] = None
        
        logger.info("Initialized LearningTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "learning"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Interact with the learning system to improve BrocaOS's capabilities over time. "
            "Use this tool to observe successful tool executions, learn reusable procedures, "
            "manage skills, and get suggestions based on learned patterns. "
            "The learning system enables BrocaOS to improve its performance automatically "
            "by learning from experience and applying successful patterns in similar situations."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": [
                        "observe_tool_call",
                        "extract_patterns",
                        "get_applicable_procedures",
                        "get_applicable_skills",
                        "apply_procedure",
                        "create_skill",
                        "update_skill_experience",
                        "log_experience",
                        "get_learning_suggestions",
                        "get_learning_state",
                        "get_top_skills",
                        "suggest_actions_for_context",
                        "clear_observations"
                    ]
                },
                "tool_call": {
                    "type": "object",
                    "description": "Tool call to observe (for observe_tool_call action)"
                },
                "result": {
                    "type": "object",
                    "description": "Result of tool call (for observe_tool_call action)"
                },
                "context": {
                    "type": "object",
                    "description": "Current context for pattern extraction or suggestions"
                },
                "procedure_name": {
                    "type": "string",
                    "description": "Name of procedure (for apply_procedure action)"
                },
                "parameter_bindings": {
                    "type": "object",
                    "description": "Parameter bindings for procedure application"
                },
                "skill": {
                    "type": "object",
                    "description": "Skill to create (for create_skill action)"
                },
                "skill_name": {
                    "type": "string",
                    "description": "Name of skill (for update_skill_experience action)"
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether skill application was successful"
                },
                "improvement": {
                    "type": "number",
                    "description": "Improvement amount for skill update (0.0-1.0)"
                },
                "experience": {
                    "type": "object",
                    "description": "Experience to log (for log_experience action)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Limit for results (e.g., top skills limit)",
                    "default": 10
                }
            },
            "required": ["action"]
        }
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute learning tool action.
        
        Args:
            action: Action to perform
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with results
        """
        try:
            if action == "observe_tool_call":
                # Extract only expected parameters, ignore others like 'context'
                tool_call = kwargs.get("tool_call")
                result = kwargs.get("result")
                return self._observe_tool_call(tool_call=tool_call, result=result)
            elif action == "extract_patterns":
                return self._extract_patterns(**kwargs)
            elif action == "get_applicable_procedures":
                return self._get_applicable_procedures(**kwargs)
            elif action == "get_applicable_skills":
                return self._get_applicable_skills(**kwargs)
            elif action == "apply_procedure":
                return self._apply_procedure(**kwargs)
            elif action == "create_skill":
                return self._create_skill(**kwargs)
            elif action == "update_skill_experience":
                return self._update_skill_experience(**kwargs)
            elif action == "log_experience":
                return self._log_experience(**kwargs)
            elif action == "get_learning_suggestions":
                return self._get_learning_suggestions(**kwargs)
            elif action == "get_learning_state":
                return self._get_learning_state(**kwargs)
            elif action == "get_top_skills":
                return self._get_top_skills(**kwargs)
            elif action == "suggest_actions_for_context":
                return self._suggest_actions_for_context(**kwargs)
            elif action == "clear_observations":
                return self._clear_observations(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.error(f"Error executing learning action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _observe_tool_call(self, tool_call: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Observe a tool call and its result for learning."""
        # Validate required parameters
        if tool_call is None:
            return {
                "success": False,
                "error": "tool_call parameter is required but was None"
            }
        if result is None:
            return {
                "success": False,
                "error": "result parameter is required but was None"
            }
        
        self.procedural_learner.observe_tool_call(tool_call, result)
        
        # Also log as experience
        experience = {
            "type": "tool_execution",
            "tool_name": tool_call.get("name", "unknown"),
            "parameters": tool_call.get("parameters", {}),
            "result": result,
            "success": result.get("success", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.experience_logger.log_experience(experience)
        
        # Update toolchain success rate signal if SignalManager available
        # Use Beta tracker for proper Bayesian damping
        tool_name = tool_call.get("name", "unknown")
        success = result.get("success", False)
        if self._signal_manager:
            try:
                # Use record_tool_success which handles Beta tracking automatically
                self._signal_manager.record_tool_success(tool_name, success)
            except Exception as e:
                logger.debug(f"Error updating toolchain success rate signal: {e}")
        
        return {
            "success": True,
            "message": "Observed tool call for learning",
            "tool_call": tool_call.get("name", "unknown"),
            "success": result.get("success", False),
        }
    
    def observe_with_dissonance(
        self,
        tool_call: Dict[str, Any],
        result: Dict[str, Any],
        dissonance_before: Optional[float] = None,
        dissonance_after: Optional[float] = None,
        emotional_state: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Observe a tool call with dissonance context for learning.
        
        Args:
            tool_call: Tool call dictionary
            result: Result dictionary
            dissonance_before: Dissonance before tool execution
            dissonance_after: Dissonance after tool execution
            emotional_state: Optional emotional state dictionary
        """
        # Observe normally
        observe_result = self._observe_tool_call(tool_call, result)
        
        # If dissonance data available, extract patterns with dissonance context
        if dissonance_before is not None and dissonance_after is not None:
            dissonance_reduction = dissonance_before - dissonance_after
            dissonance_context = {
                "average_dissonance": (dissonance_before + dissonance_after) / 2.0,
                "dissonance_reduction": dissonance_reduction,
                "is_low_dissonance": dissonance_after < 0.3
            }
            
            # Include emotional state if available
            if emotional_state:
                dissonance_context["emotional_state"] = emotional_state
            
            # Update procedure dissonance scores if procedure was applied
            # (This would need procedure tracking in the tool call)
            observe_result["dissonance_context"] = dissonance_context
        
        return observe_result
    
    def observe_with_emotion(
        self,
        tool_call: Dict[str, Any],
        result: Dict[str, Any],
        emotional_state: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Observe a tool call with emotional state context.
        
        Args:
            tool_call: Tool call dictionary
            result: Result dictionary
            emotional_state: Current emotional state dictionary
        """
        # Observe normally
        observe_result = self._observe_tool_call(tool_call, result)
        
        # Adjust learning rate based on emotional state (higher negative valence → increased learning)
        valence = emotional_state.get("valence", 0.0)
        if valence < -0.3:
            # Negative valence: increase learning rate (learn from mistakes)
            learning_rate_multiplier = 1.0 + abs(valence) * 0.5  # Up to 1.5x learning rate
            observe_result["emotional_learning_adjustment"] = {
                "learning_rate_multiplier": learning_rate_multiplier,
                "reason": "negative_valence_increases_learning"
            }
            logger.debug(f"Emotional state adjusts learning: valence={valence:.2f}, multiplier={learning_rate_multiplier:.2f}")
        
        return observe_result
    
    def _extract_patterns(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract patterns from recent observations."""
        new_procedures = self.procedural_learner.extract_patterns(context)
        
        return {
            "success": True,
            "message": f"Extracted {len(new_procedures)} new procedure(s)",
            "new_procedures": [proc.to_dict() for proc in new_procedures],
            "total_procedures": len(self.procedural_learner.procedures),
        }
    
    def _get_applicable_procedures(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get procedures applicable to current context."""
        procedures = self.procedural_learner.get_applicable_procedures(context)
        
        return {
            "success": True,
            "procedures": [proc.to_dict() for proc in procedures],
            "count": len(procedures),
        }
    
    def _get_applicable_skills(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get skills applicable to current context."""
        skills = self.skill_manager.get_applicable_skills(context)
        
        return {
            "success": True,
            "skills": [skill.to_dict() for skill in skills],
            "count": len(skills),
        }
    
    def _apply_procedure(self, procedure_name: str, 
                        parameter_bindings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply a learned procedure."""
        try:
            tool_calls = self.procedural_learner.apply_procedure(procedure_name, parameter_bindings)
            
            return {
                "success": True,
                "procedure_name": procedure_name,
                "tool_calls": tool_calls,
                "count": len(tool_calls),
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def _create_skill(self, skill: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new skill."""
        try:
            # Validate skill structure
            if "name" not in skill:
                return {"success": False, "error": "Skill must have a name"}
            if "description" not in skill:
                return {"success": False, "error": "Skill must have a description"}
            
            # Convert to Skill object
            skill_obj = Skill(
                name=skill["name"],
                skill_type=SkillType(skill.get("skill_type", "analytical")),
                description=skill["description"],
                proficiency_level=skill.get("proficiency_level", 0.0),
                confidence=skill.get("confidence", 0.5),
                trigger_patterns=skill.get("trigger_patterns", []),
                required_context=skill.get("required_context", []),
                excluded_context=skill.get("excluded_context", []),
                learning_rate=skill.get("learning_rate", 0.1),
                decay_rate=skill.get("decay_rate", 0.01),
            )
            
            if self.skill_manager.add_skill(skill_obj):
                return {
                    "success": True,
                    "message": f"Created skill: {skill['name']}",
                    "skill_name": skill["name"],
                    "skill": skill_obj.to_dict(),
                }
            else:
                return {
                    "success": False,
                    "error": f"Skill '{skill['name']}' already exists",
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to create skill: {str(e)}"}
    
    def _update_skill_experience(self, skill_name: str, success: bool, 
                               improvement: float = 0.01) -> Dict[str, Any]:
        """Update skill based on experience outcome."""
        self.skill_manager.update_skill_from_experience(skill_name, success, improvement)
        
        return {
            "success": True,
            "message": f"Updated skill '{skill_name}' with {'success' if success else 'failure'}",
            "skill_name": skill_name,
            "success": success,
            "improvement": improvement,
        }
    
    def _log_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Log an experience for learning."""
        self.experience_logger.log_experience(experience)
        
        return {
            "success": True,
            "message": "Logged experience",
            "experience_type": experience.get("type", "unknown"),
        }
    
    def _get_learning_suggestions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get learning suggestions based on context."""
        suggestions = []
        
        # Get current dissonance from context if available
        current_dissonance = context.get("dissonance")
        
        # Get applicable procedures (filtered by dissonance effectiveness if high dissonance)
        procedures = self.procedural_learner.get_applicable_procedures(context)
        
        # Filter procedures by dissonance effectiveness if dissonance is high
        if current_dissonance and current_dissonance > 0.5:
            procedures = self.procedural_learner.filter_by_dissonance_effectiveness(
                procedures,
                min_dissonance_reduction=0.0,
                min_effectiveness_count=1
            )
        
        for proc in procedures[:3]:  # Top 3 procedures
            suggestions.append({
                "type": "procedure",
                "name": proc.name,
                "description": f"Apply learned procedure '{proc.name}'",
                "confidence": proc.confidence,
                "success_rate": proc.success_rate(),
                "dissonance_reduction_score": getattr(proc, 'dissonance_reduction_score', 0.0),
            })
        
        # Get applicable skills
        skills = self.skill_manager.get_applicable_skills(context)
        for skill in skills[:3]:  # Top 3 skills
            skill_suggestions = self.skill_manager.suggest_skill_actions(skill, context)
            # Add dissonance impact to suggestions
            for suggestion in skill_suggestions:
                suggestion["dissonance_impact"] = getattr(skill, 'average_dissonance_impact', 0.0)
            suggestions.extend(skill_suggestions)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "count": len(suggestions),
        }
    
    def learn_from_dissonance_reduction(
        self,
        pattern_id: str,
        dissonance_before: float,
        dissonance_after: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Learn from a pattern that reduced dissonance.
        
        Args:
            pattern_id: Identifier for the pattern/procedure/skill
            dissonance_before: Dissonance before pattern application
            dissonance_after: Dissonance after pattern application
            context: Optional context
            
        Returns:
            Learning result dictionary
        """
        dissonance_reduction = dissonance_before - dissonance_after
        
        # Update procedure if it exists
        if pattern_id in self.procedural_learner.procedures:
            procedure = self.procedural_learner.procedures[pattern_id]
            procedure.update_dissonance_effectiveness(dissonance_reduction)
        
        # Update skill if it exists
        skill = self.skill_manager.get_skill(pattern_id)
        if skill:
            skill.update_from_dissonance(dissonance_before, dissonance_after)
        
        return {
            "success": True,
            "pattern_id": pattern_id,
            "dissonance_reduction": dissonance_reduction,
            "message": f"Updated learning for pattern '{pattern_id}'"
        }
    
    def _get_learning_state(self) -> Dict[str, Any]:
        """Get current learning system state."""
        return {
            "success": True,
            "state": {
                "procedural_learner": {
                    "total_procedures": len(self.procedural_learner.procedures),
                    "observation_buffer_size": len(self.procedural_learner.observation_buffer),
                },
                "skill_manager": {
                    "total_skills": len(self.skill_manager.skills),
                    "top_skills": [s.to_dict() for s in self.skill_manager.get_top_skills(5)],
                },
                "experience_logger": {
                    "total_experiences": len(self.experience_logger.experiences),
                },
            }
        }
    
    def _get_top_skills(self, limit: int = 10) -> Dict[str, Any]:
        """Get top skills by proficiency."""
        skills = self.skill_manager.get_top_skills(limit)
        
        return {
            "success": True,
            "skills": [skill.to_dict() for skill in skills],
            "count": len(skills),
        }
    
    def _suggest_actions_for_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest actions for given context."""
        return self._get_learning_suggestions(context)
    
    def _clear_observations(self) -> Dict[str, Any]:
        """Clear observation buffer."""
        self.procedural_learner.observation_buffer = []
        
        return {
            "success": True,
            "message": "Cleared observation buffer",
        }
    
    def auto_extract_patterns_if_ready(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Automatically extract patterns if enough observations are available.
        
        Called periodically or after certain thresholds are met.
        
        Args:
            context: Optional context for pattern extraction
            
        Returns:
            List of newly created procedure dictionaries
        """
        # Check if we have enough observations
        if len(self.procedural_learner.observation_buffer) >= self.procedural_learner.min_sequence_length * 2:
            try:
                new_procedures = self.procedural_learner.extract_patterns(context)
                if new_procedures:
                    logger.info(f"Auto-extracted {len(new_procedures)} new procedure(s) from observations")
                return [proc.to_dict() for proc in new_procedures]
            except Exception as e:
                logger.debug(f"Error in auto pattern extraction: {e}", exc_info=True)
        return []
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return f"Error: {error}"
        
        # Format based on action result structure
        message = result.get("message", "")
        
        # If there's a message, use it
        if message:
            return message
        
        # Format specific result types
        if "new_procedures" in result:
            # For extract_patterns
            new_procedures = result.get("new_procedures", [])
            count = len(new_procedures)
            total = result.get("total_procedures", 0)
            return f"Extracted {count} new procedure(s) (total: {total})"
        elif "procedures" in result:
            procedures = result.get("procedures", [])
            count = len(procedures)
            return f"Found {count} applicable procedure(s)"
        elif "skills" in result:
            skills = result.get("skills", [])
            count = len(skills)
            return f"Found {count} applicable skill(s)"
        elif "suggestions" in result:
            suggestions = result.get("suggestions", [])
            count = len(suggestions)
            return f"Generated {count} learning suggestion(s)"
        elif "procedure_name" in result:
            # For apply_procedure
            proc_name = result.get("procedure_name", "unknown")
            tool_calls_count = result.get("count", 0)
            return f"Procedure '{proc_name}' applied: {tool_calls_count} tool call(s) generated"
        elif "skill" in result or "skill_name" in result:
            # For create_skill or update_skill_experience
            skill = result.get("skill", {})
            skill_name = skill.get("name", result.get("skill_name", "unknown")) if isinstance(skill, dict) else result.get("skill_name", "unknown")
            return f"Skill '{skill_name}' updated successfully"
        elif "state" in result:
            # For get_learning_state
            return "Learning system state retrieved successfully"
        elif "tool_call" in result:
            # For observe_tool_call
            tool_name = result.get("tool_call", "unknown")
            return f"Observed tool call: {tool_name}"
        else:
            # Generic success message
            return "Learning operation completed successfully"