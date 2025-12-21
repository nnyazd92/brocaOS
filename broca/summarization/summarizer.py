"""
Summarizer for generating session summaries from events.

Uses LLM to generate structured summaries with evidence pointers.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..llm import LLMClient, create_llm_client
from .models import SessionSummary, SummaryHeader, SummaryBlocks, EvidenceItem, ConfidenceLevel
from .token_estimator import estimate_tokens

logger = logging.getLogger(__name__)


class Summarizer:
    """
    LLM-based summarizer for conversation events.
    
    Generates structured summaries with evidence pointers and enforces size limits.
    """
    
    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        max_summary_tokens: int = 1200,
        max_block_tokens: int = 200
    ) -> None:
        """
        Initialize summarizer.
        
        Args:
            llm: Optional LLM client (uses default if not provided)
            max_summary_tokens: Maximum tokens for entire summary
            max_block_tokens: Maximum tokens per summary block
        """
        self.llm = llm or create_llm_client()
        self.max_summary_tokens = max_summary_tokens
        self.max_block_tokens = max_block_tokens
    
    def summarize_delta(
        self,
        session_id: str,
        events: List[Dict[str, Any]],
        previous_summary: Optional[SessionSummary] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Summarize a delta of events into structured summary updates.
        
        Args:
            session_id: Session identifier
            events: List of events to summarize
            previous_summary: Optional previous summary for context
            
        Returns:
            Dictionary with summary updates and extracted items, or None on failure
        """
        if not events:
            logger.debug("No events to summarize")
            return None
        
        try:
            # Build prompt
            prompt = self._build_summarization_prompt(session_id, events, previous_summary)
            
            # Call LLM
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a conversation summarizer. Generate structured summaries "
                        "with evidence pointers. Respond ONLY with valid JSON, no markdown code blocks, "
                        "no explanations. Your response must match the required schema exactly."
                    )
                },
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.chat(messages, temperature=0.3)
            content = self.llm.extract_assistant_content(response)
            
            if not content:
                logger.error("Empty response from LLM")
                return None
            
            # Parse JSON response
            result = self._parse_json_response(content)
            if not result:
                return None
            
            # Validate result
            validation_result = self._validate_summarization_result(result, events)
            if not validation_result["valid"]:
                logger.warning(f"Validation failed: {validation_result.get('errors')}")
                # Try once more with error feedback
                return self._retry_with_feedback(result, validation_result, prompt, messages)
            
            # Enforce size limits
            result = self._enforce_size_limits(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during summarization: {e}", exc_info=True)
            return None
    
    def _build_summarization_prompt(
        self,
        session_id: str,
        events: List[Dict[str, Any]],
        previous_summary: Optional[SessionSummary]
    ) -> str:
        """Build the prompt for summarization."""
        # Format events for prompt
        events_text = []
        for event in events:
            event_type = event.get("type", "unknown")
            event_id = event.get("event_id", "")
            
            if event_type == "user_message":
                events_text.append(f"[{event_id}] USER: {event.get('content', '')}")
            elif event_type == "assistant_message":
                events_text.append(f"[{event_id}] ASSISTANT: {event.get('content', '')}")
            elif event_type == "tool_call":
                tool_name = event.get("tool_name", "")
                tool_args = event.get("tool_args", {})
                events_text.append(f"[{event_id}] TOOL_CALL: {tool_name}({json.dumps(tool_args)})")
            elif event_type == "tool_result":
                tool_name = event.get("tool_name", "")
                # Truncate large tool results
                tool_result = event.get("tool_result", {})
                result_str = json.dumps(tool_result)[:500]  # Limit size
                events_text.append(f"[{event_id}] TOOL_RESULT: {tool_name} -> {result_str}")
        
        events_block = "\n".join(events_text)
        
        # Include previous summary context if available
        previous_context = ""
        if previous_summary:
            prev_blocks = previous_summary.summary_blocks
            previous_context = (
                f"\n\nPrevious summary context:\n"
                f"Current goal: {prev_blocks.current_goal}\n"
                f"What we built: {', '.join(prev_blocks.what_we_built[:3])}\n"
                f"Open questions: {', '.join(prev_blocks.open_questions[:3])}\n"
            )
        
        prompt = f"""Summarize the following conversation events and generate structured updates.

Events to summarize:
{events_block}
{previous_context}

Generate a JSON response with this exact structure:
{{
  "summary_patch": {{
    "current_goal": "1-3 sentence update to current goal",
    "what_we_built": ["bullet point 1", "bullet point 2"],
    "open_questions": ["question 1", "question 2"],
    "constraints": ["constraint 1"],
    "next_steps": ["step 1", "step 2"]
  }},
  "extracted": {{
    "facts_added": [{{"text": "fact", "confidence": "high|medium|low", "event_ids": ["evt_..."]}}],
    "facts_deprecated": [{{"text": "old fact", "event_ids": ["evt_..."]}}],
    "decisions_added": [{{"text": "decision", "reasoning": "...", "event_ids": ["evt_..."]}}],
    "decisions_deprecated": [{{"text": "old decision", "event_ids": ["evt_..."]}}],
    "tasks_added": [{{"id": "task_...", "description": "...", "event_ids": ["evt_..."]}}],
    "tasks_updated": [{{"id": "task_...", "status": "completed|in_progress|cancelled", "event_ids": ["evt_..."]}}]
  }},
  "conflicts": [{{"old_item_id": "...", "new_statement": "...", "resolution": "..."}}],
  "bookkeeping": {{
    "last_summarized_event_id": "{events[-1].get('event_id', '') if events else ''}",
    "new_last_summarized_event_id": "{events[-1].get('event_id', '') if events else ''}"
  }}
}}

Requirements:
- Each item in extracted must have at least one event_id from the events above
- Keep summaries concise (current_goal <= 200 tokens, each bullet <= 50 tokens)
- Mark confidence as "high" only if strongly supported by events, "medium" for inferred, "low" for uncertain
- List conflicts when new info contradicts old info
- Be factual and specific"""
        
        return prompt
    
    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            content = content.strip()
            
            # Extract JSON from markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                json_start = None
                json_end = None
                for i, line in enumerate(lines):
                    if line.strip().startswith("```json") or line.strip().startswith("```"):
                        if json_start is None:
                            json_start = i + 1
                        else:
                            json_end = i
                            break
                
                if json_start is not None and json_end is not None:
                    content = "\n".join(lines[json_start:json_end])
            
            # Try to find JSON object in content
            # Look for first { and last }
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                content = content[start_idx:end_idx + 1]
            
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}", exc_info=True)
            return None
    
    def _validate_summarization_result(
        self,
        result: Dict[str, Any],
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate summarization result.
        
        Args:
            result: Parsed JSON result from LLM
            events: Original events for validation
            
        Returns:
            Dictionary with "valid" boolean and optional "errors" list
        """
        errors = []
        
        # Check required top-level keys
        required_keys = ["summary_patch", "extracted", "bookkeeping"]
        for key in required_keys:
            if key not in result:
                errors.append(f"Missing required key: {key}")
        
        if "extracted" in result:
            extracted = result["extracted"]
            event_ids = {e.get("event_id") for e in events if e.get("event_id")}
            
            # Validate extracted items have valid event_ids
            for category in ["facts_added", "decisions_added", "tasks_added"]:
                items = extracted.get(category, [])
                for item in items:
                    item_event_ids = item.get("event_ids", [])
                    if not item_event_ids:
                        errors.append(f"{category} item missing event_ids: {item}")
                    else:
                        # Check that event_ids exist in events
                        invalid_ids = [eid for eid in item_event_ids if eid not in event_ids]
                        if invalid_ids:
                            errors.append(f"{category} item has invalid event_ids: {invalid_ids}")
        
        # Validate bookkeeping
        if "bookkeeping" in result:
            bookkeeping = result["bookkeeping"]
            if "new_last_summarized_event_id" not in bookkeeping:
                errors.append("bookkeeping missing new_last_summarized_event_id")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _retry_with_feedback(
        self,
        previous_result: Dict[str, Any],
        validation_result: Dict[str, Any],
        original_prompt: str,
        messages: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Retry summarization with validation error feedback."""
        errors_text = "\n".join(validation_result.get("errors", []))
        
        feedback_prompt = (
            f"{original_prompt}\n\n"
            f"Validation errors in previous attempt:\n{errors_text}\n\n"
            f"Please fix these errors and respond again with valid JSON."
        )
        
        messages[1]["content"] = feedback_prompt
        
        try:
            response = self.llm.chat(messages, temperature=0.2)
            content = self.llm.extract_assistant_content(response)
            
            if not content:
                return None
            
            result = self._parse_json_response(content)
            if result:
                validation_result = self._validate_summarization_result(result, [])
                if validation_result["valid"]:
                    result = self._enforce_size_limits(result)
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error in retry: {e}", exc_info=True)
            return None
    
    def _enforce_size_limits(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce token limits on summary blocks."""
        if "summary_patch" not in result:
            return result
        
        patch = result["summary_patch"]
        
        # Truncate current_goal if too long
        if "current_goal" in patch:
            current_goal = patch["current_goal"]
            if estimate_tokens(current_goal) > self.max_block_tokens:
                # Truncate to approximately max_block_tokens
                max_chars = self.max_block_tokens * 4
                patch["current_goal"] = current_goal[:max_chars] + "..."
        
        # Truncate list items
        for key in ["what_we_built", "open_questions", "constraints", "next_steps"]:
            if key in patch:
                items = patch[key]
                truncated_items = []
                for item in items:
                    if estimate_tokens(item) <= 50:  # Per-item limit
                        truncated_items.append(item)
                    else:
                        # Truncate item
                        max_chars = 50 * 4
                        truncated_items.append(item[:max_chars] + "...")
                patch[key] = truncated_items[:10]  # Limit number of items
        
        # Limit extracted items
        if "extracted" in result:
            extracted = result["extracted"]
            for key in ["facts_added", "decisions_added", "tasks_added"]:
                if key in extracted:
                    extracted[key] = extracted[key][:50]  # Limit to 50 items per category
        
        return result

