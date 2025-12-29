"""
Plan-Forecast-Replan-Execute-Assess Loop (PFREA Loop)

Forces Broca to always follow:
1. PLAN: Create a plan before executing actions
2. FORECAST: Validate feasibility and predict outcomes via dry-run simulation
3. RE-PLAN: Revise plan based on forecast results (if needed)
4. EXECUTE: Execute planned actions
5. ASSESS: Evaluate results and learn
6. RECURSE: Use assessment to form new plan (if needed)
"""

from __future__ import annotations

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Import PFREA tracker types (optional - will fail gracefully if not available)
try:
    from .pfrea_tracker import PFREAEventType, get_pfrea_tracker
    PFREA_TRACKER_AVAILABLE = True
except ImportError:
    PFREA_TRACKER_AVAILABLE = False
    PFREAEventType = None  # type: ignore
    get_pfrea_tracker = None  # type: ignore


class LoopPhase(Enum):
    """Current phase of the PFREA loop."""
    PLAN = "plan"
    FORECAST = "forecast"
    RE_PLAN = "re_plan"
    EXECUTE = "execute"  # Renamed from ACTION for clarity
    ASSESS = "assess"
    COMPLETE = "complete"


@dataclass
class Plan:
    """A plan for achieving a goal."""
    goal: str
    steps: List[Dict[str, Any]]  # List of planned actions
    assumptions: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    plan_id: str = field(default_factory=lambda: f"plan_{datetime.now(timezone.utc).timestamp()}")
    z3_verification: Optional[Dict[str, Any]] = field(default=None)  # Z3 validation results
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": self.steps,
            "assumptions": self.assumptions,
            "expected_outcomes": self.expected_outcomes,
            "created_at": self.created_at.isoformat(),
            "plan_id": self.plan_id,
            "z3_verification": self.z3_verification,
        }


@dataclass
class ActionExecution:
    """Record of an action execution."""
    plan_id: str
    step_index: int
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "step_index": self.step_index,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Forecast:
    """Forecast of plan feasibility and predicted outcomes."""
    plan_id: str
    feasibility_score: float  # 0.0 to 1.0
    predicted_outcomes: List[str] = field(default_factory=list)
    identified_risks: List[str] = field(default_factory=list)
    validation_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    should_replan: bool = False
    replan_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "feasibility_score": self.feasibility_score,
            "predicted_outcomes": self.predicted_outcomes,
            "identified_risks": self.identified_risks,
            "validation_issues": self.validation_issues,
            "recommendations": self.recommendations,
            "should_replan": self.should_replan,
            "replan_reason": self.replan_reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Assessment:
    """Assessment of plan execution results."""
    plan_id: str
    goal_achieved: bool
    success_rate: float  # 0.0 to 1.0
    failures: List[Dict[str, Any]] = field(default_factory=list)
    learnings: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    should_replan: bool = False
    replan_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal_achieved": self.goal_achieved,
            "success_rate": self.success_rate,
            "failures": self.failures,
            "learnings": self.learnings,
            "next_steps": self.next_steps,
            "should_replan": self.should_replan,
            "replan_reason": self.replan_reason,
            "timestamp": self.timestamp.isoformat(),
        }


class PlanForecastReplanExecuteAssessLoop:
    """
    Enforces PLAN->FORECAST->RE-PLAN->EXECUTE->ASSESS loop for all task execution.
    
    Prevents mindless repetition by:
    1. Requiring explicit planning before actions
    2. Forecasting plan feasibility and outcomes before execution
    3. Re-planning based on forecast results when needed
    4. Tracking all action executions
    5. Forcing assessment after actions
    6. Learning from failures to inform next plan
    """
    
    # Backward compatibility alias
    PlanExecuteAssessLoop = None  # Will be set at end of file
    
    def __init__(
        self,
        goal_manager: Optional[Any] = None,
        skill_manager: Optional[Any] = None,
        experience_logger: Optional[Any] = None,
        max_replan_attempts: int = 3,
        require_planning: bool = True,
        success_threshold: float = 0.8,
        track_failed_patterns: bool = True,
        max_failed_patterns: int = 10,
        z3_validator: Optional[Any] = None,
    ):
        self.goal_manager = goal_manager
        self.skill_manager = skill_manager
        self.experience_logger = experience_logger
        self.max_replan_attempts = max_replan_attempts
        self.require_planning = require_planning
        self.success_threshold = success_threshold
        self.track_failed_patterns = track_failed_patterns
        self.max_failed_patterns = max_failed_patterns
        
        # Initialize Z3 validator if not provided
        if z3_validator is None:
            try:
                from .z3_validator import Z3LogicalValidator
                from .config import ReasoningConfig
                
                # Instantiate ReasoningConfig to access instance attributes
                config = ReasoningConfig()
                
                self.z3_validator = Z3LogicalValidator(
                    enable_z3=config.z3_validation_enabled,
                    timeout=config.z3_validation_timeout,
                    max_constraints=config.z3_max_constraints
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Z3 validator: {e}", exc_info=True)
                self.z3_validator = None
        else:
            self.z3_validator = z3_validator
        
        # Current state
        self.current_phase: Optional[LoopPhase] = None
        self.current_plan: Optional[Plan] = None
        self.current_forecast: Optional[Forecast] = None
        self.current_goal: Optional[str] = None
        self.execution_history: List[ActionExecution] = []
        self.assessment_history: List[Assessment] = []
        self.forecast_history: List[Forecast] = []
        self.replan_count: int = 0
        
        # Track failed patterns to prevent loops
        self.failed_patterns: List[Dict[str, Any]] = []  # Patterns that didn't work
        
        # Initialize PFREA tracker for compliance monitoring
        self._tracker = None
        if PFREA_TRACKER_AVAILABLE and get_pfrea_tracker:
            try:
                from .config import ReasoningConfig
                if getattr(ReasoningConfig, 'pfrea_metrics_enabled', True):
                    self._tracker = get_pfrea_tracker()
            except Exception as e:
                logger.debug(f"PFREA tracker not available: {e}")
        
        logger.info(
            "Initialized PlanForecastReplanExecuteAssessLoop",
            extra={
                "event": "pfrea_initialized",
                "z3_enabled": self.z3_validator is not None and (self.z3_validator.enabled if hasattr(self.z3_validator, 'enabled') else False),
                "tracker_enabled": self._tracker is not None,
            }
        )
    
    def should_require_plan(self, user_message: str, has_tool_calls: bool) -> bool:
        """
        Determine if planning should be required before tool execution.
        
        Always returns True when planning is required (mandatory PFREA).
        
        Args:
            user_message: User's message
            has_tool_calls: Whether LLM wants to make tool calls
            
        Returns:
            True if planning should be enforced
        """
        # Always require planning if not enabled (mandatory PFREA)
        if not self.require_planning:
            result = True
            reason = "planning_always_required"
        # If we're in ASSESS phase and replan needed, require plan
        elif self.current_phase == LoopPhase.ASSESS:
            # Check if last assessment indicated replan needed
            if self.assessment_history:
                last_assessment = self.assessment_history[-1]
                if last_assessment.should_replan:
                    result = True
                    reason = "assessment_indicates_replan"
                else:
                    result = False
                    reason = "assessment_no_replan_needed"
            else:
                result = False
                reason = "no_assessment_history"
        # If we're in FORECAST phase and re-plan recommended, require plan
        elif self.current_phase == LoopPhase.FORECAST and self.current_forecast:
            if self.current_forecast.should_replan:
                result = True
                reason = "forecast_indicates_replan"
            else:
                result = False
                reason = "forecast_no_replan_needed"
        # If we have no current plan and LLM wants to make tool calls, require plan
        elif self.current_plan is None and has_tool_calls:
            result = True
            reason = "no_plan_with_tool_calls"
        # If current plan is complete, require new plan
        elif self.current_plan and self.current_phase == LoopPhase.COMPLETE:
            result = True
            reason = "plan_complete_need_new"
        # If we're starting fresh (no phase set), require plan
        elif self.current_phase is None:
            result = True
            reason = "no_phase_set"
        else:
            result = False
            reason = "plan_not_required"
        
        # Log enforcement check
        if self._tracker and PFREAEventType:
            self._tracker.record_event(
                event_type=PFREAEventType.ENFORCEMENT,
                phase=self.current_phase.value if self.current_phase else None,
                plan_id=self.current_plan.plan_id if self.current_plan else None,
                context={
                    "check_type": "should_require_plan",
                    "result": result,
                    "reason": reason,
                    "has_tool_calls": has_tool_calls,
                }
            )
        
        logger.debug(
            f"PFREA: Planning requirement check: {result} (reason: {reason})",
            extra={
                "event": "pfrea_enforcement_check",
                "check_type": "should_require_plan",
                "result": result,
                "reason": reason,
                "current_phase": self.current_phase.value if self.current_phase else None,
                "has_plan": self.current_plan is not None,
                "has_tool_calls": has_tool_calls,
            }
        )
        
        return result
    
    def should_require_forecast(self) -> bool:
        """
        Determine if forecast should be required.
        
        Returns:
            True if forecast should be enforced
        """
        # If we have a plan but no forecast, require forecast
        if self.current_plan and not self.current_forecast:
            return True
        
        # If we're in PLAN phase and plan is complete, require forecast
        if self.current_phase == LoopPhase.PLAN and self.current_plan:
            return True
        
        # If we just completed RE_PLAN, require forecast for new plan
        if self.current_phase == LoopPhase.RE_PLAN and self.current_plan:
            return True
        
        return False
    
    def should_require_replan(self) -> bool:
        """
        Determine if re-planning should be required after forecast.
        
        Returns:
            True if re-planning should be enforced
        """
        if not self.current_forecast:
            return False
        
        return self.current_forecast.should_replan
    
    def can_execute_actions(self, forecast_enabled: bool = True) -> bool:
        """
        Determine if actions can be executed.
        
        Returns True only when:
        - Plan exists
        - Forecast exists (if enabled)
        - Not in PLAN, FORECAST, or RE_PLAN phase
        - In EXECUTE phase or transitioning from FORECAST/RE_PLAN to EXECUTE
        
        Args:
            forecast_enabled: Whether forecast is required before execution
            
        Returns:
            True if actions can be executed
        """
        # Must have a plan
        if not self.current_plan:
            result = False
            reason = "no_plan"
        # If forecast is enabled, must have a forecast
        elif forecast_enabled and not self.current_forecast:
            result = False
            reason = "no_forecast"
        # Cannot execute if in planning phases
        elif self.current_phase in [LoopPhase.PLAN, LoopPhase.FORECAST, LoopPhase.RE_PLAN]:
            result = False
            reason = f"in_planning_phase_{self.current_phase.value}"
        # Can execute if in EXECUTE phase
        elif self.current_phase == LoopPhase.EXECUTE:
            result = True
            reason = "in_execute_phase"
        else:
            result = False
            reason = f"phase_not_executable_{self.current_phase.value if self.current_phase else 'none'}"
        
        # Log execution check
        logger.debug(
            f"PFREA: Execution check: {result} (reason: {reason})",
            extra={
                "event": "pfrea_execution_check",
                "result": result,
                "reason": reason,
                "forecast_enabled": forecast_enabled,
                "has_plan": self.current_plan is not None,
                "has_forecast": self.current_forecast is not None,
                "current_phase": self.current_phase.value if self.current_phase else None,
                "plan_id": self.current_plan.plan_id if self.current_plan else None,
            }
        )
        
        # Track execution check
        if self._tracker and PFREAEventType:
            self._tracker.record_event(
                event_type=PFREAEventType.ENFORCEMENT,
                phase=self.current_phase.value if self.current_phase else None,
                plan_id=self.current_plan.plan_id if self.current_plan else None,
                context={
                    "check_type": "can_execute_actions",
                    "result": result,
                    "reason": reason,
                    "forecast_enabled": forecast_enabled,
                }
            )
            
            # Record violation if execution attempted without proper phases
            if not result and self.current_plan:
                violation_type = "execution_blocked"
                if reason == "no_plan":
                    violation_type = "execution_without_plan"
                elif reason == "no_forecast":
                    violation_type = "execution_without_forecast"
                
                self._tracker.record_violation(
                    violation_type=violation_type,
                    description=f"Execution blocked: {reason}",
                    plan_id=self.current_plan.plan_id,
                    context={"forecast_enabled": forecast_enabled}
                )
        
        return result
    
    def extract_plan_from_response(self, response_text: str) -> Optional[Plan]:
        """
        Extract plan from LLM response text.
        
        Looks for structured plan format in response.
        """
        if not response_text:
            return None
        
        # Try to extract plan from structured format
        # Look for "Plan:" or "## Plan" sections
        plan_patterns = [
            r"##\s*Plan[:\s]*(.*?)(?=##|$)",
            r"Plan[:\s]*(.*?)(?=Action|Execute|$)",
            r"Planning[:\s]*(.*?)(?=Action|Execute|$)",
        ]
        
        plan_text = None
        for pattern in plan_patterns:
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                plan_text = match.group(1).strip()
                break
        
        if not plan_text:
            return None
        
        # Try to parse steps from plan
        steps = self._parse_plan_steps(plan_text)
        if steps:
            # Extract goal
            goal_match = re.search(r"\*\*Goal:\*\*\s*(.+?)(?=\*\*|$)", plan_text, re.IGNORECASE | re.DOTALL)
            goal = goal_match.group(1).strip() if goal_match else (self.current_goal or "User request")
            
            # Extract assumptions
            assumptions_match = re.search(r"\*\*Assumptions?:\*\*\s*(.+?)(?=\*\*|$)", plan_text, re.IGNORECASE | re.DOTALL)
            assumptions = []
            if assumptions_match:
                assumptions_text = assumptions_match.group(1).strip()
                assumptions = [a.strip() for a in assumptions_text.split('\n') if a.strip() and a.strip().startswith('-')]
                assumptions = [a.lstrip('- ').strip() for a in assumptions]
            
            # Extract expected outcomes
            outcomes_match = re.search(r"\*\*Expected\s+Outcomes?:\*\*\s*(.+?)(?=\*\*|$)", plan_text, re.IGNORECASE | re.DOTALL)
            expected_outcomes = []
            if outcomes_match:
                outcomes_text = outcomes_match.group(1).strip()
                expected_outcomes = [o.strip() for o in outcomes_text.split('\n') if o.strip() and o.strip().startswith('-')]
                expected_outcomes = [o.lstrip('- ').strip() for o in expected_outcomes]
            
            plan = Plan(
                goal=goal,
                steps=steps,
                assumptions=assumptions,
                expected_outcomes=expected_outcomes,
            )
            
            # Verify plan with Z3
            z3_results = self.verify_plan_with_z3(plan)
            plan.z3_verification = z3_results
            
            # Log plan extraction
            logger.info(
                f"PFREA: Plan extracted: {plan.plan_id}",
                extra={
                    "event": "pfrea_plan_extracted",
                    "plan_id": plan.plan_id,
                    "goal": goal,
                    "steps_count": len(steps),
                    "assumptions_count": len(assumptions),
                    "z3_verified": z3_results.get("is_logically_sound", True) if z3_results else None,
                    "z3_issues": len(z3_results.get("logical_issues", [])) if z3_results else 0,
                }
            )
            
            # Track plan extraction
            if self._tracker and PFREAEventType:
                self._tracker.record_event(
                    event_type=PFREAEventType.PLAN_EXTRACTED,
                    phase=LoopPhase.PLAN.value,
                    plan_id=plan.plan_id,
                    context={
                        "goal": goal,
                        "steps_count": len(steps),
                        "assumptions_count": len(assumptions),
                        "z3_verified": z3_results.get("is_logically_sound", True) if z3_results else None,
                    }
                )
            
            return plan
        
        return None
    
    def verify_plan_with_z3(self, plan: Plan) -> Dict[str, Any]:
        """
        Verify plan logic using Z3 validator.
        
        This method is mandatory but non-blocking - it always returns results
        even if Z3 is unavailable or fails.
        
        Args:
            plan: Plan to verify
            
        Returns:
            Dictionary with Z3 validation results (never raises exceptions)
        """
        if not self.z3_validator:
            return {
                "is_logically_sound": True,  # Default to sound if Z3 unavailable
                "logical_issues": [],
                "recommendations": [],
                "missing_preconditions": [],
                "contradictions": [],
                "warnings": ["Z3 validator not available"],
            }
        
        try:
            return self.z3_validator.validate_plan_logic(plan)
        except Exception as e:
            logger.warning(f"Z3 plan verification failed (non-blocking): {e}")
            # Return non-blocking result - never fail the plan
            return {
                "is_logically_sound": True,  # Default to sound on error
                "logical_issues": [],
                "recommendations": [],
                "missing_preconditions": [],
                "contradictions": [],
                "warnings": [f"Z3 verification error: {str(e)}"],
            }
    
    def _parse_plan_steps(self, plan_text: str) -> List[Dict[str, Any]]:
        """Parse plan text into structured steps."""
        steps = []
        lines = plan_text.split('\n')
        
        current_step = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for numbered steps or bullet points
            step_match = re.match(r'^(\d+)[\.\)]\s*(.+)', line)
            if step_match:
                if current_step:
                    steps.append(current_step)
                current_step = {
                    "description": step_match.group(2),
                    "tool": None,
                    "arguments": {},
                }
            elif current_step and (line.startswith('-') or line.startswith('*')):
                # Sub-item of current step
                current_step["description"] += f"\n{line}"
        
        if current_step:
            steps.append(current_step)
        
        return steps
    
    def extract_forecast_from_response(self, response_text: str) -> Optional[Forecast]:
        """
        Extract forecast from LLM response text.
        
        Looks for structured forecast format in response.
        """
        if not response_text or not self.current_plan:
            return None
        
        # Try to extract forecast from structured format
        forecast_patterns = [
            r"##\s*Forecast[:\s]*(.*?)(?=##|$)",
            r"Forecast[:\s]*(.*?)(?=Re-plan|Replan|Execute|$)",
            r"Feasibility[:\s]*(.*?)(?=Re-plan|Replan|Execute|$)",
        ]
        
        forecast_text = None
        for pattern in forecast_patterns:
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                forecast_text = match.group(1).strip()
                break
        
        if not forecast_text:
            return None
        
        # Extract feasibility score
        feasibility_score = 0.5  # Default
        score_match = re.search(r"(?:feasibility|score)[:\s]*([0-9.]+)", forecast_text, re.IGNORECASE)
        if score_match:
            try:
                feasibility_score = float(score_match.group(1))
                # Normalize to 0.0-1.0 range
                if feasibility_score > 1.0:
                    feasibility_score = feasibility_score / 100.0
                feasibility_score = max(0.0, min(1.0, feasibility_score))
            except ValueError:
                pass
        
        # Extract predicted outcomes
        outcomes_match = re.search(r"\*\*Predicted\s+Outcomes?:\*\*\s*(.+?)(?=\*\*|$)", forecast_text, re.IGNORECASE | re.DOTALL)
        predicted_outcomes = []
        if outcomes_match:
            outcomes_text = outcomes_match.group(1).strip()
            predicted_outcomes = [o.strip() for o in outcomes_text.split('\n') if o.strip() and (o.strip().startswith('-') or o.strip().startswith('*'))]
            predicted_outcomes = [o.lstrip('-* ').strip() for o in predicted_outcomes]
        
        # Extract identified risks
        risks_match = re.search(r"\*\*Risks?:\*\*\s*(.+?)(?=\*\*|$)", forecast_text, re.IGNORECASE | re.DOTALL)
        identified_risks = []
        if risks_match:
            risks_text = risks_match.group(1).strip()
            identified_risks = [r.strip() for r in risks_text.split('\n') if r.strip() and (r.strip().startswith('-') or r.strip().startswith('*'))]
            identified_risks = [r.lstrip('-* ').strip() for r in identified_risks]
        
        # Extract validation issues
        issues_match = re.search(r"\*\*Issues?:\*\*\s*(.+?)(?=\*\*|$)", forecast_text, re.IGNORECASE | re.DOTALL)
        validation_issues = []
        if issues_match:
            issues_text = issues_match.group(1).strip()
            validation_issues = [i.strip() for i in issues_text.split('\n') if i.strip() and (i.strip().startswith('-') or i.strip().startswith('*'))]
            validation_issues = [i.lstrip('-* ').strip() for i in validation_issues]
        
        # Extract recommendations
        recommendations_match = re.search(r"\*\*Recommendations?:\*\*\s*(.+?)(?=\*\*|$)", forecast_text, re.IGNORECASE | re.DOTALL)
        recommendations = []
        if recommendations_match:
            recs_text = recommendations_match.group(1).strip()
            recommendations = [r.strip() for r in recs_text.split('\n') if r.strip() and (r.strip().startswith('-') or r.strip().startswith('*'))]
            recommendations = [r.lstrip('-* ').strip() for r in recommendations]
        
        # Determine if re-planning is recommended
        should_replan = False
        replan_reason = None
        
        # Check for explicit re-plan recommendation
        replan_match = re.search(r"(?:should|must|need)\s+(?:re-plan|replan|revise|modify)", forecast_text, re.IGNORECASE)
        if replan_match:
            should_replan = True
            replan_reason = "Forecast indicates plan needs revision"
        
        # Low feasibility score suggests re-planning
        if feasibility_score < 0.5:
            should_replan = True
            replan_reason = f"Low feasibility score ({feasibility_score:.2f}) indicates plan needs revision"
        
        # Multiple validation issues suggest re-planning
        if len(validation_issues) > 2:
            should_replan = True
            replan_reason = f"Multiple validation issues ({len(validation_issues)}) identified"
        
        # Log forecast extraction
        logger.info(
            f"PFREA: Forecast extracted for plan {self.current_plan.plan_id}",
            extra={
                "event": "pfrea_forecast_extracted",
                "plan_id": self.current_plan.plan_id,
                "feasibility_score": feasibility_score,
                "should_replan": should_replan,
                "risks_count": len(identified_risks),
                "issues_count": len(validation_issues),
                "recommendations_count": len(recommendations),
            }
        )
        
        # Track forecast extraction
        if self._tracker and PFREAEventType:
            self._tracker.record_event(
                event_type=PFREAEventType.FORECAST_EXTRACTED,
                phase=LoopPhase.FORECAST.value,
                plan_id=self.current_plan.plan_id,
                context={
                    "feasibility_score": feasibility_score,
                    "should_replan": should_replan,
                    "risks_count": len(identified_risks),
                    "issues_count": len(validation_issues),
                }
            )
        
        # Automatically include Z3 validation results if available
        if self.current_plan and self.current_plan.z3_verification:
            z3_verification = self.current_plan.z3_verification
            
            # Add Z3 logical issues to validation_issues
            if z3_verification.get("logical_issues"):
                for issue in z3_verification["logical_issues"]:
                    if issue not in validation_issues:
                        validation_issues.append(f"Z3: {issue}")
            
            # Add Z3 recommendations to recommendations
            if z3_verification.get("recommendations"):
                for rec in z3_verification["recommendations"]:
                    if rec not in recommendations:
                        recommendations.append(f"Z3: {rec}")
            
            # If Z3 found critical logical issues, suggest replanning (but don't block)
            if not z3_verification.get("is_logically_sound", True):
                if not should_replan:
                    # Soft suggestion - don't force replan but indicate it's recommended
                    if len(z3_verification.get("logical_issues", [])) > 0:
                        should_replan = True
                        replan_reason = f"Z3 logical verification found issues (recommended to revise, but not required)"
        
        return Forecast(
            plan_id=self.current_plan.plan_id,
            feasibility_score=feasibility_score,
            predicted_outcomes=predicted_outcomes,
            identified_risks=identified_risks,
            validation_issues=validation_issues,
            recommendations=recommendations,
            should_replan=should_replan,
            replan_reason=replan_reason,
        )
    
    def enforce_forecast_phase(self, plan: Plan) -> str:
        """
        Enforce forecast phase by injecting forecast directive.
        
        Args:
            plan: The plan to forecast
            
        Returns:
            Forecast directive message
        """
        # Log forecast phase enforcement
        logger.info(
            f"PFREA: Enforcing forecast phase for plan {plan.plan_id}",
            extra={
                "event": "pfrea_forecast_enforced",
                "plan_id": plan.plan_id,
                "steps_count": len(plan.steps),
                "z3_verified": plan.z3_verification.get("is_logically_sound", True) if plan.z3_verification else None,
            }
        )
        
        # Track phase transition to FORECAST
        if self._tracker and PFREAEventType:
            old_phase = self.current_phase.value if self.current_phase else None
            self._tracker.record_phase_transition(
                from_phase=old_phase,
                to_phase=LoopPhase.FORECAST.value,
                plan_id=plan.plan_id,
                reason="plan_extracted"
            )
        
        forecast_directive = (
            f"\n\n[SYSTEM DIRECTIVE - FORECAST REQUIRED - DO NOT USE TOOLS]\n"
            f"Plan {plan.plan_id} has been created. Before executing ANY actions or using ANY tools, you MUST provide a forecast.\n\n"
            f"CRITICAL: You must provide the forecast in your text response. DO NOT use any tools. DO NOT make any tool calls.\n"
            f"Simply provide your forecast analysis in the response text below.\n\n"
        )
        
        # Include Z3 verification results if available
        if plan.z3_verification:
            z3_verification = plan.z3_verification
            forecast_directive += "**Z3 Logical Verification Results (Informational - Not Blocking):**\n"
            if z3_verification.get("is_logically_sound", True):
                forecast_directive += "- Status: Plan is logically sound\n"
            else:
                forecast_directive += "- Status: Plan has logical issues (consider revising)\n"
            
            if z3_verification.get("logical_issues"):
                forecast_directive += f"- Logical Issues: {', '.join(z3_verification['logical_issues'][:3])}\n"
            if z3_verification.get("recommendations"):
                forecast_directive += f"- Z3 Recommendations: {', '.join(z3_verification['recommendations'][:3])}\n"
            if z3_verification.get("warnings"):
                forecast_directive += f"- Warnings: {', '.join(z3_verification['warnings'][:2])}\n"
            forecast_directive += "\n"
            forecast_directive += "NOTE: Z3 verification is informational only. You can still proceed with execution even if logical issues are found.\n\n"
        
        forecast_directive += (
            f"Your forecast must include:\n"
            f"1. **Feasibility Score**: A score from 0.0 to 1.0 indicating how feasible the plan is\n"
            f"2. **Predicted Outcomes**: What you expect to happen if this plan is executed\n"
            f"3. **Identified Risks**: Potential issues or risks with this plan\n"
            f"4. **Validation Issues**: Any problems with assumptions, dependencies, or resource requirements\n"
            f"5. **Recommendations**: Suggestions for improving the plan\n\n"
            f"Format your forecast as:\n"
            f"## Forecast\n"
            f"**Feasibility Score**: [0.0-1.0]\n"
            f"**Predicted Outcomes:**\n"
            f"- [First expected outcome]\n"
            f"- [Second expected outcome]\n"
            f"**Risks:**\n"
            f"- [First risk]\n"
            f"- [Second risk]\n"
            f"**Issues:**\n"
            f"- [First validation issue]\n"
            f"**Recommendations:**\n"
            f"- [First recommendation]\n\n"
            f"After providing your forecast, the system will determine if re-planning is needed.\n"
            f"DO NOT execute any tool calls. DO NOT use any tools. Provide your forecast analysis in text only."
        )
        
        return forecast_directive
    
    def should_replan_after_forecast(self, forecast: Forecast) -> bool:
        """
        Determine if re-planning is needed after forecast.
        
        Args:
            forecast: The forecast to analyze
            
        Returns:
            True if re-planning is recommended
        """
        # LLM already decided via forecast.should_replan
        return forecast.should_replan
    
    def enforce_planning_phase(self, user_message: str, is_replan: bool = False, forecast: Optional[Forecast] = None) -> str:
        """
        Enforce planning phase by injecting planning directive.
        
        Args:
            user_message: User's message
            is_replan: Whether this is a re-planning request
            forecast: Previous forecast if re-planning (for context)
        
        Returns:
            Modified user message with planning requirement
        """
        # Log planning phase enforcement
        logger.info(
            f"PFREA: Enforcing planning phase (replan={is_replan})",
            extra={
                "event": "pfrea_planning_enforced",
                "is_replan": is_replan,
                "current_phase": self.current_phase.value if self.current_phase else None,
                "plan_id": self.current_plan.plan_id if self.current_plan else None,
                "forecast_available": forecast is not None,
            }
        )
        
        if is_replan:
            planning_directive = (
                "\n\n[SYSTEM DIRECTIVE - RE-PLANNING REQUIRED]\n"
                "Based on the forecast, you MUST create a NEW and IMPROVED plan. Your response must include:\n"
                "1. A clear goal statement (may be the same or updated)\n"
                "2. A step-by-step plan that addresses the issues identified in the forecast\n"
                "3. Assumptions you're making (updated based on forecast insights)\n"
                "4. Expected outcomes for each step\n\n"
            )
            
            if forecast:
                planning_directive += (
                    f"**Forecast Context:**\n"
                    f"- Feasibility Score: {forecast.feasibility_score:.2f}\n"
                )
                if forecast.validation_issues:
                    planning_directive += f"- Issues: {', '.join(forecast.validation_issues[:3])}\n"
                if forecast.identified_risks:
                    planning_directive += f"- Risks: {', '.join(forecast.identified_risks[:3])}\n"
                if forecast.recommendations:
                    planning_directive += f"- Recommendations: {', '.join(forecast.recommendations[:3])}\n"
                planning_directive += "\n"
            
            # Include Z3 verification results from previous plan if available
            if self.current_plan and self.current_plan.z3_verification:
                z3_verification = self.current_plan.z3_verification
                if not z3_verification.get("is_logically_sound", True):
                    planning_directive += "**Previous Plan Z3 Logical Verification:**\n"
                    planning_directive += "- Status: Plan had logical issues\n"
                    if z3_verification.get("logical_issues"):
                        planning_directive += f"- Issues: {', '.join(z3_verification['logical_issues'][:3])}\n"
                    if z3_verification.get("recommendations"):
                        planning_directive += f"- Z3 Recommendations: {', '.join(z3_verification['recommendations'][:3])}\n"
                    planning_directive += "\n"
            
            planning_directive += (
                "Format your plan as:\n"
                "## Plan\n"
                "**Goal:** [clear statement of what you're trying to achieve]\n"
                "**Steps:**\n"
                "1. [First action with tool name and purpose]\n"
                "2. [Second action...]\n"
                "**Assumptions:** [list assumptions]\n"
                "**Expected Outcomes:** [what you expect to achieve]\n\n"
                "Your new plan should:\n"
                "1. Address the issues identified in the forecast\n"
                "2. Incorporate the recommendations provided\n"
                "3. Use a different approach if the previous plan had significant risks\n\n"
                "After providing your plan, a forecast will be generated before execution.\n"
                "DO NOT execute any tool calls until you have provided a complete plan."
            )
        else:
            planning_directive = (
                "\n\n[SYSTEM DIRECTIVE - PLANNING REQUIRED]\n"
                "Before executing any actions, you MUST create a plan. Your response must include:\n"
                "1. A clear goal statement\n"
                "2. A step-by-step plan with specific actions\n"
                "3. Assumptions you're making\n"
                "4. Expected outcomes for each step\n\n"
                "Format your plan as:\n"
                "## Plan\n"
                "**Goal:** [clear statement of what you're trying to achieve]\n"
                "**Steps:**\n"
                "1. [First action with tool name and purpose]\n"
                "2. [Second action...]\n"
                "**Assumptions:** [list assumptions]\n"
                "**Expected Outcomes:** [what you expect to achieve]\n\n"
                "After providing your plan, a forecast will be generated before execution.\n"
                "DO NOT execute any tool calls until you have provided a complete plan."
            )
        
        # Include failed patterns if we have them
        if self.failed_patterns and self.track_failed_patterns:
            failed_info = "\n**Previous Failed Approaches:**\n"
            for pattern in self.failed_patterns[-3:]:  # Last 3 failures
                failed_info += f"- {pattern.get('description', 'Previous attempt failed')}\n"
            planning_directive = failed_info + planning_directive
        
        return user_message + planning_directive
    
    def record_action_execution(
        self,
        plan_id: str,
        step_index: int,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        success: bool,
    ):
        """Record an action execution."""
        execution = ActionExecution(
            plan_id=plan_id,
            step_index=step_index,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
        )
        self.execution_history.append(execution)
        
        # Update phase if not already in EXECUTE
        old_phase = self.current_phase
        if self.current_phase != LoopPhase.EXECUTE:
            self.current_phase = LoopPhase.EXECUTE
            # Track phase transition
            if self._tracker and PFREAEventType:
                self._tracker.record_phase_transition(
                    from_phase=old_phase.value if old_phase else None,
                    to_phase=LoopPhase.EXECUTE.value,
                    plan_id=plan_id,
                    reason="action_execution_started"
                )
        
        # Track action recording
        if self._tracker and PFREAEventType:
            self._tracker.record_event(
                event_type=PFREAEventType.ACTION_RECORDED,
                phase=LoopPhase.EXECUTE.value,
                plan_id=plan_id,
                context={
                    "step_index": step_index,
                    "tool_name": tool_name,
                    "success": success,
                }
            )
        
        logger.info(
            f"PFREA: Recorded action execution: {tool_name} (plan={plan_id}, step={step_index}, success={success})",
            extra={
                "event": "pfrea_action_recorded",
                "plan_id": plan_id,
                "step_index": step_index,
                "tool_name": tool_name,
                "success": success,
            }
        )
    
    def assess_execution(self, plan: Plan, executions: List[ActionExecution]) -> Assessment:
        """
        Assess the execution of a plan.
        
        Args:
            plan: The plan that was executed
            executions: List of action executions for this plan
            
        Returns:
            Assessment of the execution
        """
        if not executions:
            return Assessment(
                plan_id=plan.plan_id,
                goal_achieved=False,
                success_rate=0.0,
                should_replan=True,
                replan_reason="No actions were executed",
            )
        
        # Calculate success rate
        successful = sum(1 for e in executions if e.success)
        success_rate = successful / len(executions) if executions else 0.0
        
        # Ensure success_rate is in valid range
        success_rate = max(0.0, min(1.0, success_rate))
        
        # Identify failures
        failures = []
        for execution in executions:
            if not execution.success:
                failures.append({
                    "step_index": execution.step_index,
                    "tool_name": execution.tool_name,
                    "error": execution.result.get("error", "Unknown error"),
                    "result": execution.result,
                })
        
        # Extract learnings from failures
        learnings = []
        for failure in failures:
            learning = (
                f"Step {failure['step_index']} failed: {failure['tool_name']} "
                f"failed with: {failure.get('error', 'unknown error')}"
            )
            learnings.append(learning)
        
        # Determine if goal was achieved
        goal_achieved = success_rate >= self.success_threshold and len(failures) == 0
        
        # Determine if we should replan
        should_replan = not goal_achieved and self.replan_count < self.max_replan_attempts
        
        replan_reason = None
        if should_replan:
            if failures:
                replan_reason = f"Plan failed with {len(failures)} failures. Need different approach."
            elif success_rate < 0.5:
                replan_reason = f"Low success rate ({success_rate:.2f}). Need to revise plan."
        
        # Generate next steps
        next_steps = []
        if should_replan:
            next_steps.append("Create a new plan incorporating learnings from failures")
            if failures:
                next_steps.append(f"Avoid repeating failed approach: {failures[0].get('tool_name', 'previous method')}")
        
        assessment = Assessment(
            plan_id=plan.plan_id,
            goal_achieved=goal_achieved,
            success_rate=success_rate,
            failures=failures,
            learnings=learnings,
            next_steps=next_steps,
            should_replan=should_replan,
            replan_reason=replan_reason,
        )
        
        self.assessment_history.append(assessment)
        
        # Track phase transition to ASSESS
        old_phase = self.current_phase
        self.current_phase = LoopPhase.ASSESS
        if self._tracker and PFREAEventType:
            self._tracker.record_phase_transition(
                from_phase=old_phase.value if old_phase else None,
                to_phase=LoopPhase.ASSESS.value,
                plan_id=plan.plan_id,
                reason="execution_completed"
            )
            
            # Track assessment generation
            self._tracker.record_event(
                event_type=PFREAEventType.ASSESSMENT_GENERATED,
                phase=LoopPhase.ASSESS.value,
                plan_id=plan.plan_id,
                context={
                    "goal_achieved": goal_achieved,
                    "success_rate": success_rate,
                    "failures_count": len(failures),
                    "should_replan": should_replan,
                }
            )
        
        # Record failed pattern if plan failed
        if not goal_achieved and self.track_failed_patterns:
            self.failed_patterns.append({
                "plan_id": plan.plan_id,
                "description": f"Plan with {len(plan.steps)} steps failed",
                "failures": failures,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            # Limit failed patterns history
            if len(self.failed_patterns) > self.max_failed_patterns:
                self.failed_patterns = self.failed_patterns[-self.max_failed_patterns:]
        
        logger.info(
            f"PFREA: Assessed plan {plan.plan_id}: success_rate={success_rate:.2f}, "
            f"goal_achieved={goal_achieved}, should_replan={should_replan}",
            extra={
                "event": "pfrea_assessment_generated",
                "plan_id": plan.plan_id,
                "goal_achieved": goal_achieved,
                "success_rate": success_rate,
                "failures_count": len(failures),
                "should_replan": should_replan,
                "replan_reason": replan_reason,
            }
        )
        
        return assessment
    
    def enforce_assessment_phase(self, assessment: Assessment) -> str:
        """
        Enforce assessment phase by injecting assessment directive.
        
        Returns:
            Directive message for LLM to assess and potentially replan
        """
        assessment_directive = (
            f"\n\n[SYSTEM DIRECTIVE - ASSESSMENT REQUIRED]\n"
            f"Plan {assessment.plan_id} execution completed. Assessment:\n"
            f"- Success Rate: {assessment.success_rate:.1%}\n"
            f"- Goal Achieved: {'Yes' if assessment.goal_achieved else 'No'}\n"
        )
        
        if assessment.failures:
            assessment_directive += f"- Failures: {len(assessment.failures)}\n"
            for failure in assessment.failures[:3]:  # Show first 3
                assessment_directive += f"  * Step {failure['step_index']}: {failure['tool_name']} - {failure.get('error', 'failed')}\n"
        
        if assessment.learnings:
            assessment_directive += f"\n**Learnings:**\n"
            for learning in assessment.learnings[:5]:  # Show first 5
                assessment_directive += f"- {learning}\n"
        
        if assessment.should_replan:
            assessment_directive += (
                f"\n**ACTION REQUIRED:** You MUST create a NEW plan. "
                f"Reason: {assessment.replan_reason}\n"
                f"Your new plan should:\n"
                f"1. Address the failures identified above\n"
                f"2. Use a different approach than the failed plan\n"
                f"3. Incorporate the learnings listed above\n\n"
                f"Provide your new plan in the same format as before.\n"
            )
            self.replan_count += 1
        else:
            assessment_directive += (
                f"\n**Status:** Plan execution complete. "
                f"{'Goal achieved!' if assessment.goal_achieved else 'Goal not fully achieved, but max replan attempts reached.'}\n"
            )
            self.current_phase = LoopPhase.COMPLETE
        
        return assessment_directive
    
    def reset_for_new_goal(self, goal: str):
        """Reset loop state for a new goal."""
        self.current_goal = goal
        self.current_plan = None
        self.current_forecast = None
        self.current_phase = None
        self.execution_history = []
        self.replan_count = 0
        logger.info(f"Reset PFREA loop for new goal: {goal}")
    
    def get_loop_state(self) -> Dict[str, Any]:
        """Get current loop state for debugging."""
        return {
            "current_phase": self.current_phase.value if self.current_phase else None,
            "current_plan_id": self.current_plan.plan_id if self.current_plan else None,
            "current_forecast_id": self.current_forecast.plan_id if self.current_forecast else None,
            "current_goal": self.current_goal,
            "replan_count": self.replan_count,
            "executions_count": len(self.execution_history),
            "assessments_count": len(self.assessment_history),
            "forecasts_count": len(self.forecast_history),
            "failed_patterns_count": len(self.failed_patterns),
        }
    
    def check_compliance(self) -> Optional[Dict[str, Any]]:
        """
        Check PFREA compliance and log warnings if needed.
        
        Returns:
            Warning dictionary if compliance issues detected, None otherwise
        """
        if not self._tracker:
            return None
        
        try:
            from .config import ReasoningConfig
            compliance_threshold = getattr(ReasoningConfig, 'pfrea_compliance_threshold', 0.95)
            violation_threshold = getattr(ReasoningConfig, 'pfrea_violation_alert_threshold', 10)
            
            return self._tracker.check_compliance_and_warn(
                compliance_threshold=compliance_threshold,
                violation_alert_threshold=violation_threshold,
            )
        except Exception as e:
            logger.debug(f"Error checking PFREA compliance: {e}")
            return None


# Backward compatibility alias
PlanExecuteAssessLoop = PlanForecastReplanExecuteAssessLoop

