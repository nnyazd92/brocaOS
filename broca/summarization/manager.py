"""
Summarization manager orchestrating the summarization pipeline.

Handles triggers, validation, merging, and storage coordination.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .event_logger import EventLogger
from .summarizer import Summarizer
from .storage import SummaryStorage
from .validation import SummarizationValidator
from .models import (
    SessionSummary,
    SummaryHeader,
    SummaryBlocks,
    TasksFile,
    Task,
    ProjectState,
    EvidenceItem,
    ConfidenceLevel
)
from .token_estimator import estimate_tokens, estimate_messages_tokens, estimate_prompt_tokens
from .prompt_builder import PromptBuilder
from ..config import config

logger = logging.getLogger(__name__)


class SummarizationManager:
    """
    Manages the summarization pipeline.
    
    Handles triggers, delta window gathering, summarizer invocation, and merge logic.
    """
    
    def __init__(
        self,
        event_logger: EventLogger,
        summary_storage: SummaryStorage,
        summarizer: Optional[Summarizer] = None,
        trigger_turns: Optional[int] = None,
        trigger_token_threshold: Optional[float] = None,
        context_window_size: Optional[int] = None
    ) -> None:
        """
        Initialize summarization manager.
        
        Args:
            event_logger: EventLogger instance
            summary_storage: SummaryStorage instance
            summarizer: Optional Summarizer instance (creates default if not provided)
            trigger_turns: Number of turns before triggering summarization (defaults to config)
            trigger_token_threshold: Token usage threshold (0.0-1.0) to trigger summarization (defaults to config)
            context_window_size: Context window size in tokens (defaults to config)
        """
        self.event_logger = event_logger
        self.summary_storage = summary_storage
        self.summarizer = summarizer or Summarizer(
            max_summary_tokens=config.summarization.max_summary_tokens,
            max_block_tokens=config.summarization.max_block_tokens
        )
        self.validator = SummarizationValidator(event_logger)
        self.trigger_turns = trigger_turns if trigger_turns is not None else config.summarization.trigger_turns
        self.trigger_token_threshold = trigger_token_threshold if trigger_token_threshold is not None else config.summarization.trigger_token_threshold
        self.context_window_size = context_window_size if context_window_size is not None else config.summarization.context_window_size
        
        logger.debug(
            f"Initialized SummarizationManager: trigger_turns={self.trigger_turns}, "
            f"trigger_token_threshold={self.trigger_token_threshold}, "
            f"context_window_size={self.context_window_size}"
        )
    
    def should_summarize(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        turns_since_last_summary: int
    ) -> bool:
        """
        Check if summarization should be triggered.
        
        Args:
            session_id: Session identifier
            messages: Current conversation messages
            turns_since_last_summary: Number of turns since last summarization
            
        Returns:
            True if summarization should be triggered
        """
        # Check if auto-trigger is enabled (disabled by default)
        from ..config import config
        if not config.summarization.auto_trigger_enabled:
            return False  # Manual summarization only
        
        # Check turn-based trigger
        if turns_since_last_summary >= self.trigger_turns:
            logger.debug(f"Trigger: turn count ({turns_since_last_summary} >= {self.trigger_turns})")
            return True
        
        # Check token-based trigger (estimate actual prompt size that will be sent)
        estimated_tokens = self._estimate_actual_prompt_tokens(session_id, messages)
        
        # Threshold is percentage of context window
        token_usage = estimated_tokens / self.context_window_size
        
        if token_usage >= self.trigger_token_threshold:
            logger.debug(
                f"Trigger: token usage ({token_usage:.3f} >= {self.trigger_token_threshold})"
            )
            return True
        
        return False
    
    def _estimate_actual_prompt_tokens(
        self,
        session_id: str,
        messages: List[Dict[str, Any]]
    ) -> int:
        """
        Estimate tokens for the actual prompt that will be sent to LLM.
        
        When a summary exists, only filtered messages (summary + last K turns) are sent.
        This method estimates tokens based on what will actually be sent, not the full message history.
        
        Args:
            session_id: Session identifier
            messages: Full conversation messages
            
        Returns:
            Estimated token count for the actual prompt payload
        """
        # Check if summary exists for this session
        try:
            summary = self.summary_storage.load_session_summary(session_id)
            if not summary:
                # No summary exists yet - estimate from full messages
                return estimate_messages_tokens(messages)
        except Exception as e:
            logger.debug(f"Error checking for summary, using full messages: {e}")
            # Fall back to full message estimation
            return estimate_messages_tokens(messages)
        
        # Summary exists - estimate from filtered payload (summary + last K turns)
        total_tokens = 0
        
        # 1. Estimate tokens for summary context
        try:
            prompt_builder = PromptBuilder(
                summary_storage=self.summary_storage,
                last_turns_count=config.summarization.last_turns_count
            )
            summary_context = prompt_builder.build_context(session_id, messages, system_prompt=None)
            if summary_context:
                total_tokens += estimate_tokens(summary_context)
        except Exception as e:
            logger.debug(f"Error estimating summary context tokens: {e}")
        
        # 2. Estimate tokens for filtered messages (last K turns)
        # Use same logic as ConversationSession._get_filtered_messages()
        try:
            last_turns_count = config.summarization.last_turns_count
            if not isinstance(last_turns_count, int):
                last_turns_count = 3  # Default
            
            # Get system message (if exists) - this will be included
            system_message = None
            if messages and messages[0].get("role") == "system":
                system_message = messages[0]
            
            # Get last K turns (non-system messages)
            non_system_messages = [m for m in messages if m.get("role") != "system"]
            
            # Estimate: each turn is typically 2-4 messages (user + assistant + possibly tool calls)
            # Take last current_turns*4 messages as a conservative estimate
            turns_to_keep = last_turns_count * 4
            start_idx = max(0, len(non_system_messages) - turns_to_keep)
            last_turns = non_system_messages[start_idx:]
            
            # Build filtered message list: system message + last turns
            filtered_messages = []
            if system_message:
                filtered_messages.append(system_message)
            filtered_messages.extend(last_turns)
            
            # Estimate tokens for filtered messages
            total_tokens += estimate_messages_tokens(filtered_messages)
            
        except Exception as e:
            logger.debug(f"Error estimating filtered message tokens: {e}")
            # Fall back to full message estimation
            return estimate_messages_tokens(messages)
        
        return total_tokens
    
    def maybe_summarize(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        turns_since_last_summary: int = 0
    ) -> Optional[SessionSummary]:
        """
        Conditionally summarize if triggers are met.
        
        Args:
            session_id: Session identifier
            messages: Current conversation messages
            turns_since_last_summary: Number of turns since last summarization
            
        Returns:
            Updated SessionSummary if summarization occurred, None otherwise
        """
        if not self.should_summarize(session_id, messages, turns_since_last_summary):
            return None
        
        return self.summarize(session_id)
    
    def summarize(self, session_id: str) -> Optional[SessionSummary]:
        """
        Summarize events for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated SessionSummary if successful, None otherwise
        """
        try:
            # Load previous summary
            previous_summary = self.summary_storage.load_session_summary(session_id)
            
            # Determine delta window (events to summarize)
            if previous_summary and previous_summary.header.last_summarized_event_id:
                last_event_id = previous_summary.header.last_summarized_event_id
                events = self.event_logger.get_events_after(session_id, last_event_id)
            else:
                # First summarization - summarize all events
                events = self.event_logger.get_events(session_id)
            
            if not events:
                logger.debug(f"No new events to summarize for session {session_id}")
                return previous_summary
            
            logger.info(
                f"Summarizing {len(events)} events for session {session_id} "
                f"(after event {previous_summary.header.last_summarized_event_id if previous_summary else 'none'})"
            )
            
            # Call summarizer
            result = self.summarizer.summarize_delta(session_id, events, previous_summary)
            if not result:
                logger.warning(f"Summarizer returned no result for session {session_id}")
                return previous_summary
            
            # Merge results into summary
            updated_summary = self._merge_summary_updates(
                session_id,
                previous_summary,
                result,
                events[-1].get("event_id") if events else None
            )
            
            if not updated_summary:
                logger.warning(f"Failed to merge summary updates for session {session_id}")
                return previous_summary
            
            # Validate summary for drift
            drift_result = self.validator.detect_drift(session_id, updated_summary, events)
            if drift_result["has_drift"]:
                logger.warning(
                    f"Drift detected in summary for session {session_id}: "
                    f"{len(drift_result['missing_event_ids'])} missing event IDs"
                )
            
            # Check compression ratio
            compression_result = self.validator.check_compression_ratio(events, updated_summary)
            if not compression_result["meets_threshold"]:
                logger.debug(
                    f"Low compression ratio for session {session_id}: "
                    f"{compression_result['compression_ratio']:.2f}x"
                )
            
            # Save updated summary
            self.summary_storage.save_session_summary(session_id, updated_summary)
            
            # Update tasks if any
            if "extracted" in result and "tasks_added" in result["extracted"]:
                self._update_tasks(session_id, result["extracted"])
            
            logger.info(f"Successfully summarized session {session_id}, revision {updated_summary.header.revision}")
            return updated_summary
            
        except Exception as e:
            logger.error(f"Error during summarization for session {session_id}: {e}", exc_info=True)
            return None
    
    def _merge_summary_updates(
        self,
        session_id: str,
        previous_summary: Optional[SessionSummary],
        result: Dict[str, Any],
        latest_event_id: Optional[str]
    ) -> Optional[SessionSummary]:
        """
        Merge summarization updates into existing or new summary.
        
        Args:
            session_id: Session identifier
            previous_summary: Previous summary (None for first summarization)
            result: Summarization result from LLM
            latest_event_id: Latest event ID that was summarized
            
        Returns:
            Merged SessionSummary
        """
        try:
            summary_patch = result.get("summary_patch", {})
            extracted = result.get("extracted", {})
            bookkeeping = result.get("bookkeeping", {})
            conflicts = result.get("conflicts", [])
            
            # Create or update header
            # Ensure we always have a valid event ID with proper fallback chain
            new_last_summarized_event_id = bookkeeping.get("new_last_summarized_event_id")
            if not new_last_summarized_event_id:
                # Fallback to latest_event_id from events that were summarized
                new_last_summarized_event_id = latest_event_id or ""
            
            if previous_summary:
                header = previous_summary.header
                header.last_updated_at = datetime.now(timezone.utc).isoformat()
                # Use new ID, or fall back to previous value if somehow empty
                header.last_summarized_event_id = new_last_summarized_event_id or header.last_summarized_event_id or ""
                header.revision += 1
                # Increment summarization cycle count for gradual pruning
                header.summarization_cycle_count += 1
            else:
                header = SummaryHeader(
                    session_id=session_id,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    last_updated_at=datetime.now(timezone.utc).isoformat(),
                    last_summarized_event_id=new_last_summarized_event_id or "",
                    revision=0,
                    scope=f"Session {session_id}",
                    summarization_cycle_count=0  # First summarization, cycle count starts at 0
                )
            
            # Merge summary blocks
            if previous_summary:
                blocks = previous_summary.summary_blocks
            else:
                blocks = SummaryBlocks()
            
            # Update blocks with patch
            if "current_goal" in summary_patch:
                blocks.current_goal = summary_patch["current_goal"]
            if "what_we_built" in summary_patch:
                # Append new items
                blocks.what_we_built.extend(summary_patch["what_we_built"])
                # Keep only last 20 items
                blocks.what_we_built = blocks.what_we_built[-20:]
            if "open_questions" in summary_patch:
                blocks.open_questions.extend(summary_patch["open_questions"])
                blocks.open_questions = blocks.open_questions[-20:]
            if "constraints" in summary_patch:
                blocks.constraints.extend(summary_patch["constraints"])
                blocks.constraints = blocks.constraints[-20:]
            if "next_steps" in summary_patch:
                blocks.next_steps.extend(summary_patch["next_steps"])
                
                # Filter out completed tasks (defensive check)
                completed_task_ids = set()
                for task_update in extracted.get("tasks_updated", []):
                    if isinstance(task_update, dict) and task_update.get("status") == "completed":
                        task_id = task_update.get("id")
                        if task_id:
                            completed_task_ids.add(task_id.lower())
                
                # Filter next_steps: remove items that match completed task patterns
                # Simple heuristic: if next_step contains task_id or vice versa
                filtered_next_steps = []
                for step in blocks.next_steps:
                    if not isinstance(step, str):
                        # Skip non-string items
                        continue
                    step_lower = step.lower()
                    is_completed = any(
                        task_id in step_lower or step_lower in task_id 
                        for task_id in completed_task_ids
                    )
                    if not is_completed:
                        filtered_next_steps.append(step)
                
                blocks.next_steps = filtered_next_steps[-20:]  # Keep last 20
            
            # Build evidence list
            evidence = []
            if previous_summary:
                evidence = previous_summary.evidence.copy()
            
            # Add evidence for new claims
            for fact in extracted.get("facts_added", []):
                evidence.append(EvidenceItem(
                    claim=fact.get("text", ""),
                    event_ids=fact.get("event_ids", [])
                ))
            
            for decision in extracted.get("decisions_added", []):
                evidence.append(EvidenceItem(
                    claim=decision.get("text", ""),
                    event_ids=decision.get("event_ids", [])
                ))
            
            # Cap evidence list to prevent unbounded growth
            max_evidence_items = 50  # Keep most recent 50 items
            if len(evidence) > max_evidence_items:
                evidence = evidence[-max_evidence_items:]
                logger.debug(f"Capped evidence list to {max_evidence_items} items (kept most recent)")
            
            # Update confidence (simplified - could be more sophisticated)
            confidence = ConfidenceLevel()
            if "current_goal" in summary_patch:
                # Determine confidence from extracted facts
                facts = extracted.get("facts_added", [])
                if facts:
                    confidences = [f.get("confidence", "medium") for f in facts]
                    if any(c == "high" for c in confidences):
                        confidence.current_goal = "high"
                    elif any(c == "medium" for c in confidences):
                        confidence.current_goal = "medium"
                    else:
                        confidence.current_goal = "low"
            
            # Create updated summary
            summary = SessionSummary(
                header=header,
                summary_blocks=blocks,
                evidence=evidence,
                confidence=confidence
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error merging summary updates: {e}", exc_info=True)
            return None
    
    def _update_tasks(self, session_id: str, extracted: Dict[str, Any]) -> None:
        """Update tasks file with new tasks from summarization."""
        try:
            tasks_file = self.summary_storage.load_tasks(session_id)
            
            # Add new tasks
            for task_data in extracted.get("tasks_added", []):
                task = Task(
                    id=task_data.get("id", f"task_{len(tasks_file.tasks)}"),
                    description=task_data.get("description", ""),
                    status="pending",
                    evidence_event_ids=task_data.get("event_ids", []),
                    created_at=datetime.now(timezone.utc).isoformat()
                )
                tasks_file.tasks.append(task)
            
            # Update existing tasks
            for task_update in extracted.get("tasks_updated", []):
                task_id = task_update.get("id")
                new_status = task_update.get("status", "pending")
                
                for task in tasks_file.tasks:
                    if task.id == task_id:
                        task.status = new_status
                        if task_update.get("event_ids"):
                            task.evidence_event_ids.extend(task_update["event_ids"])
                        break
            
            # Save updated tasks
            self.summary_storage.save_tasks(session_id, tasks_file)
            
        except Exception as e:
            logger.warning(f"Error updating tasks: {e}", exc_info=True)

