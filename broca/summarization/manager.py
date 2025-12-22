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
from .token_estimator import estimate_messages_tokens, estimate_prompt_tokens
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
        # Check turn-based trigger
        if turns_since_last_summary >= self.trigger_turns:
            logger.debug(f"Trigger: turn count ({turns_since_last_summary} >= {self.trigger_turns})")
            return True
        
        # Check token-based trigger (estimate current prompt size)
        # This is a simplified check - in practice, you'd need to estimate the full prompt
        # including system prompt, world state, etc.
        estimated_tokens = estimate_messages_tokens(messages)
        
        # Threshold is percentage of context window
        token_usage = estimated_tokens / self.context_window_size
        
        if token_usage >= self.trigger_token_threshold:
            logger.debug(
                f"Trigger: token usage ({token_usage:.3f} >= {self.trigger_token_threshold})"
            )
            return True
        
        return False
    
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
            if previous_summary:
                header = previous_summary.header
                header.last_updated_at = datetime.now(timezone.utc).isoformat()
                header.last_summarized_event_id = bookkeeping.get(
                    "new_last_summarized_event_id",
                    latest_event_id or ""
                )
                header.revision += 1
            else:
                header = SummaryHeader(
                    session_id=session_id,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    last_updated_at=datetime.now(timezone.utc).isoformat(),
                    last_summarized_event_id=bookkeeping.get(
                        "new_last_summarized_event_id",
                        latest_event_id or ""
                    ),
                    revision=0,
                    scope=f"Session {session_id}"
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
                blocks.next_steps = blocks.next_steps[-20:]
            
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

