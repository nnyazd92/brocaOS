"""
Consistency layer middleware that intercepts responses and orchestrates
consistency checking and self-model updates.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
import logging

from .model import SelfModel
from .storage import SelfModelSQLiteStorage
from .consistency import ConsistencyChecker, ConsistencyResult
from .updater import SelfModelUpdater
from ..llm.deepseek_client import DeepSeekClient

if TYPE_CHECKING:
    from ..damping.action_gate import ActionGate
    from ..signals.manager import SignalManager

logger = logging.getLogger(__name__)


class ConsistencyLayer:
    """
    Middleware that intercepts LLM responses and ensures consistency with self-model.
    
    Orchestrates:
    - Consistency checking
    - Self-model updates when inconsistencies are found
    - Recursive re-checking after updates
    - Response regeneration if needed
    """
    
    def __init__(
        self,
        self_model: SelfModel,
        storage: SelfModelSQLiteStorage,
        checker: Optional[ConsistencyChecker] = None,
        updater: Optional[SelfModelUpdater] = None,
        strict_mode: bool = False,
        auto_update: bool = True,
        max_iterations: int = 3,
        action_gate: Optional["ActionGate"] = None,
        signal_manager: Optional["SignalManager"] = None,
    ) -> None:
        """
        Initialize consistency layer.
        
        Args:
            self_model: Current self-model instance
            storage: SelfModelSQLiteStorage for persisting updates
            checker: Optional ConsistencyChecker (creates default if None)
            updater: Optional SelfModelUpdater (creates default if None)
            strict_mode: If True, block inconsistent responses; if False, warn only
            auto_update: If True, automatically update self-model on inconsistencies
            max_iterations: Maximum number of update/check iterations
            action_gate: Optional ActionGate for gating self-model updates
            signal_manager: Optional SignalManager for getting trigger signals (dissonance)
        """
        self.self_model = self_model
        self.storage = storage
        self.checker = checker or ConsistencyChecker()
        self.updater = updater or SelfModelUpdater()
        self.strict_mode = strict_mode
        self.auto_update = auto_update
        self.max_iterations = max_iterations
        self._action_gate = action_gate
        self._signal_manager = signal_manager
        
        logger.info(
            f"Initialized ConsistencyLayer (strict_mode={strict_mode}, "
            f"auto_update={auto_update}, max_iterations={max_iterations})"
        )
    
    def set_action_gate(self, action_gate: Optional["ActionGate"]) -> None:
        """Set the action gate for self-model updates."""
        self._action_gate = action_gate
    
    def set_signal_manager(self, signal_manager: Optional["SignalManager"]) -> None:
        """Set the signal manager for getting trigger signals."""
        self._signal_manager = signal_manager
    
    def check_response(
        self,
        response: str,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, bool, Optional[ConsistencyResult]]:
        """
        Check response for consistency and update self-model if needed.
        
        Args:
            response: LLM response to check
            conversation_context: Optional conversation context
            
        Returns:
            Tuple of (final_response, was_updated, consistency_result)
            - final_response: The response (possibly modified or regenerated)
            - was_updated: Whether self-model was updated
            - consistency_result: The final consistency result
        """
        if not self.self_model:
            logger.warning("No self-model available, skipping consistency check")
            return response, False, None
        
        iteration = 0
        current_response = response
        was_updated = False
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Check consistency
            logger.debug(f"Consistency check iteration {iteration}")
            consistency_result = self.checker.validate(
                current_response,
                self.self_model,
                conversation_context,
            )
            
            # If consistent, we're done
            if consistency_result.is_consistent:
                logger.info(f"Response is consistent after {iteration} iteration(s)")
                
                # Record consistency confirmation as epistemic event
                if self.self_model.epistemic_layer:
                    try:
                        from broca.self_model.epistemic.models import (
                            SourceType, SourceMetadata, VerificationRecord
                        )
                        from broca.self_model.epistemic.ids import generate_knowledge_id
                        from datetime import datetime, timezone
                        
                        # Record consistency confirmation
                        knowledge_id = generate_knowledge_id("consistency_check", "response_consistent")
                        verification = VerificationRecord(
                            timestamp=datetime.now(timezone.utc),
                            verification_type="consistency_check",
                            result="confirmed",
                            confidence_delta=0.05,  # Slight confidence boost
                            new_evidence=[SourceMetadata(
                                source_type=SourceType.LOGICAL_INFERENCE,
                                inference_type="consistency_check",
                                logical_strength=0.9
                            )]
                        )
                        self.self_model.epistemic_layer.add_verification_record(knowledge_id, verification)
                    except Exception as e:
                        logger.warning(f"Error recording epistemic confirmation: {e}", exc_info=True)
                
                if was_updated:
                    # Save updated model
                    self.storage.save(self.self_model)
                return current_response, was_updated, consistency_result
            
            # Inconsistent - log violations
            logger.warning(
                f"Response inconsistent (iteration {iteration}): "
                f"{len(consistency_result.violations)} violation(s), "
                f"severity={consistency_result.severity:.2f}"
            )
            
            for violation in consistency_result.violations:
                logger.debug(
                    f"Violation: {violation.get('type')} - {violation.get('description')}"
                )
            
            # Record violations as epistemic events and update confidence if epistemic layer available
            if self.self_model.epistemic_layer:
                try:
                    from broca.self_model.epistemic.models import (
                        SourceType, SourceMetadata, VerificationRecord
                    )
                    from broca.self_model.epistemic.ids import generate_knowledge_id
                    from broca.self_model.epistemic.engine import MetacognitiveEngine
                    from datetime import datetime, timezone
                    
                    # Create engine for confidence updates
                    engine = MetacognitiveEngine(epistemic_layer=self.self_model.epistemic_layer)
                    
                    # Record each violation as a verification event and update confidence
                    for violation in consistency_result.violations:
                        # Generate knowledge ID from violation description
                        violation_desc = violation.get('description', 'unknown')
                        knowledge_id = generate_knowledge_id("consistency_violation", violation_desc)
                        
                        # Create source metadata for the violation
                        violation_source = SourceMetadata(
                            source_type=SourceType.LOGICAL_INFERENCE,
                            inference_type="consistency_check",
                            logical_strength=1.0 - consistency_result.severity,
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                        # Update confidence using workflow
                        # Evidence strength is inverse of severity (higher severity = lower confidence)
                        evidence_strength = 1.0 - consistency_result.severity
                        engine.confidence_update_workflow(
                            knowledge_id=knowledge_id,
                            new_evidence=violation_source,
                            evidence_strength=evidence_strength
                        )
                except Exception as e:
                    logger.warning(f"Error recording epistemic violation: {e}", exc_info=True)
            
            # Update self-model if auto_update is enabled
            if self.auto_update:
                # Check action gate if available
                should_update = True
                if self._action_gate and self._signal_manager:
                    from datetime import datetime, timezone
                    # Get dissonance level as trigger signal (0.0-1.0)
                    dissonance_level = self._signal_manager.get("dissonance.level", default=0.0)
                    if not isinstance(dissonance_level, (int, float)):
                        dissonance_level = float(dissonance_level) if dissonance_level is not None else 0.0
                    
                    should_update, reason = self._action_gate.should_allow_action(
                        trigger_value=dissonance_level,
                        timestamp=datetime.now(timezone.utc)
                    )
                    if not should_update:
                        logger.debug(f"Self-model update gated: {reason}")
                
                if should_update:
                    logger.info("Updating self-model to resolve inconsistencies")
                    updated_model = self.updater.update_from_violations(
                        consistency_result,
                        self.self_model,
                        current_response,
                    )
                    
                    # Check if model actually changed
                    if updated_model.metadata.get("version") != self.self_model.metadata.get("version"):
                        self.self_model = updated_model
                        was_updated = True
                        logger.info(
                            f"Self-model updated to version {updated_model.metadata.get('version')}"
                        )
                        
                        # Record action in gate
                        if self._action_gate:
                            from datetime import datetime, timezone
                            self._action_gate.record_action(datetime.now(timezone.utc))
                        
                        # Save updated model
                        self.storage.save(self.self_model)
                        
                        # Continue loop to re-check with updated model
                        continue
                    else:
                        logger.debug("Self-model update did not change version, stopping iterations")
                        break
                else:
                    logger.debug("Self-model update blocked by action gate")
                    break
            else:
                # Not auto-updating, break out of loop
                logger.debug("Auto-update disabled, stopping iterations")
                break
        
        # After iterations, handle final result
        if not consistency_result.is_consistent:
            if self.strict_mode:
                logger.warning(
                    "Strict mode enabled: response is inconsistent but max iterations reached. "
                    "Consider blocking response or regenerating."
                )
                # In strict mode, we might want to block or modify the response
                # For now, we'll just log a warning
            else:
                logger.info(
                    "Response is inconsistent but non-strict mode: allowing response with warning"
                )
        
        if was_updated:
            # Save final model state
            self.storage.save(self.self_model)
        
        return current_response, was_updated, consistency_result
    
    def update_self_model(self, new_model: SelfModel) -> None:
        """
        Update the self-model (e.g., from external source).
        
        Args:
            new_model: New self-model instance
        """
        self.self_model = new_model
        self.storage.save(new_model)
        logger.info(f"Self-model updated to version {new_model.metadata.get('version')}")
    
    def get_self_model(self) -> SelfModel:
        """
        Get the current self-model.
        
        If epistemic_layer is None but epistemic data exists in database,
        loads it on-demand (lazy loading).
        
        Returns:
            Current SelfModel instance with epistemic_layer loaded if available
        """
        # Lazy load epistemic layer if missing but data exists in database
        if self.self_model.epistemic_layer is None and self.storage:
            try:
                # Reload model from storage to get epistemic layer if it exists
                # This uses the existing loading logic that checks for data from previous versions
                reloaded_model = self.storage.load()
                if reloaded_model and reloaded_model.epistemic_layer is not None:
                    # Update self_model with loaded epistemic_layer
                    self.self_model.epistemic_layer = reloaded_model.epistemic_layer
                    knowledge_count = len(reloaded_model.epistemic_layer.knowledge_sources)
                    logger.info(
                        f"Lazy-loaded epistemic layer with {knowledge_count} knowledge items "
                        f"for self-model version {self.self_model.metadata.get('version', 'unknown')}"
                    )
            except Exception as e:
                logger.warning(f"Failed to lazy-load epistemic layer: {e}", exc_info=True)
                # Continue with None epistemic_layer if loading fails
        
        return self.self_model

