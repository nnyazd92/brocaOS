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
                        "You are a conversation summarizer that maintains accurate task and goal tracking. "
                        "CRITICAL: When a task is completed (evidence shows it was finished), you MUST:\n"
                        "1. Add it to 'tasks_updated' with status='completed'\n"
                        "2. Remove it from 'next_steps' (only include steps that are still pending/in-progress)\n"
                        "3. Move completed work to 'what_we_built' if it represents completed deliverables\n\n"
                        "Do NOT include completed tasks in 'next_steps'. Only list tasks that are genuinely "
                        "still pending or in progress. If events show a task was completed, mark it complete "
                        "and remove it from next steps immediately.\n\n"
                        "Generate structured summaries with evidence pointers. Respond ONLY with valid JSON, "
                        "no markdown code blocks, no explanations. Your response must match the required schema exactly."
                    )
                },
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.chat(messages, temperature=1.0)
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
                return self._retry_with_feedback(result, validation_result, prompt, messages, events)
            
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
            next_steps_str = ', '.join(prev_blocks.next_steps[:5]) if prev_blocks.next_steps else "None"
            previous_context = (
                f"\n\nPrevious summary context:\n"
                f"Current goal: {prev_blocks.current_goal}\n"
                f"What we built: {', '.join(prev_blocks.what_we_built[:3])}\n"
                f"Open questions: {', '.join(prev_blocks.open_questions[:3])}\n"
                f"Next steps (from previous summary - REMOVE completed ones): {next_steps_str}\n"
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
- Be factual and specific

CRITICAL TASK MANAGEMENT RULES:
1. TASK COMPLETION: If events show a task was completed (user confirms, tool succeeds, goal achieved):
   - Add to "tasks_updated" with status="completed" and relevant event_ids
   - DO NOT include it in "next_steps" (only pending/in-progress tasks belong there)
   - If it represents a deliverable, add to "what_we_built"

2. NEXT_STEPS CURATION: The "next_steps" field should ONLY contain:
   - Tasks that are genuinely still pending (not started or in progress)
   - Steps that need to be done next
   - DO NOT include steps that were completed in the events you're summarizing

3. PREVIOUS CONTEXT: Review the "Next steps" from previous summary above. For each:
   - If events show it was completed: mark it in "tasks_updated" as completed, remove from "next_steps"
   - If events show it's still pending: keep it in "next_steps" (or update if status changed)
   - If events show it was cancelled: mark it in "tasks_updated" as cancelled, remove from "next_steps"

4. TASK TRACKING: When you see task completion indicators (success messages, "done", "completed", 
   successful tool results, user confirmation), explicitly mark those tasks as completed in "tasks_updated"."""
        
        return prompt
    
    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling markdown code blocks and trailing text."""
        try:
            content = content.strip()
            
            # First try: Extract JSON from markdown code blocks if present
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
            
            # Second try: Use bracket-matching to find largest balanced JSON object
            json_str = self._extract_largest_json_object(content)
            if json_str:
                result = json.loads(json_str)
                return result
            
            # Fallback: Try parsing the whole content (might work for simple cases)
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}", exc_info=True)
            return None
    
    def _extract_largest_json_object(self, content: str) -> Optional[str]:
        """
        Extract largest balanced JSON object from content using bracket matching.
        
        Handles nested objects, strings with braces, and escaped characters correctly.
        Finds all JSON objects and returns the largest one.
        """
        objects = []
        i = 0
        
        while i < len(content):
            # Find next opening brace
            start_idx = content.find('{', i)
            if start_idx < 0:
                break
            
            # Extract balanced object starting from this position
            depth = 0
            in_string = False
            escape_next = False
            found = False
            
            for j in range(start_idx, len(content)):
                char = content[j]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if in_string:
                    continue
                
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        obj_str = content[start_idx:j+1]
                        objects.append(obj_str)
                        i = j + 1
                        found = True
                        break
            
            if not found:
                break
        
        if not objects:
            return None
        
        # Return the largest object
        return max(objects, key=len)
    
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
            
            # Validate extracted items have valid event_ids (hard error)
            for category in ["facts_added", "decisions_added", "tasks_added"]:
                items = extracted.get(category, [])
                for item in items:
                    item_event_ids = item.get("event_ids", [])
                    if not item_event_ids:
                        # Hard error: missing event_ids with example format
                        item_text = item.get("text", item.get("description", str(item)))
                        errors.append(
                            f"{category} item missing event_ids: {item_text}. "
                            f"Required format: {{\"text\": \"...\", \"event_ids\": [\"evt_1\", \"evt_2\"]}}"
                        )
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
        messages: List[Dict[str, str]],
        events: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Retry summarization with validation error feedback."""
        errors = validation_result.get("errors", [])
        errors_text = "\n".join(errors)
        
        # Enhance feedback for missing event_ids
        missing_event_id_errors = [e for e in errors if "missing event_ids" in e.lower()]
        if missing_event_id_errors:
            # Add focused feedback for missing event_ids
            event_ids_list = [e.get("event_id") for e in events if e.get("event_id")]
            example_event_ids = event_ids_list[:3] if event_ids_list else ["evt_1", "evt_2"]
            errors_text += (
                f"\n\nIMPORTANT: Each item in 'extracted' must include 'event_ids' array. "
                f"Available event_ids from events: {example_event_ids}. "
                f"Example format: {{\"text\": \"fact text\", \"event_ids\": [\"{example_event_ids[0]}\"]}}"
            )
        
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
                # Fix: Use original events list for validation, not empty list
                validation_result = self._validate_summarization_result(result, events)
                if validation_result["valid"]:
                    result = self._enforce_size_limits(result)
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error in retry: {e}", exc_info=True)
            return None
    
    def _enforce_size_limits(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce token limits on summary blocks and global summary budget."""
        if "summary_patch" not in result:
            return result
        
        patch = result["summary_patch"]
        
        # Ensure patch is a dict
        if not isinstance(patch, dict):
            return result
        
        # Phase 1: Block-level truncation (existing behavior)
        # Truncate current_goal if too long
        if "current_goal" in patch and isinstance(patch["current_goal"], str):
            current_goal = patch["current_goal"]
            if estimate_tokens(current_goal) > self.max_block_tokens:
                # Truncate to approximately max_block_tokens
                max_chars = self.max_block_tokens * 4
                patch["current_goal"] = current_goal[:max_chars] + "..."
        
        # Truncate list items
        for key in ["what_we_built", "open_questions", "constraints", "next_steps"]:
            if key in patch and isinstance(patch[key], list):
                items = patch[key]
                truncated_items = []
                for item in items:
                    if isinstance(item, str):
                        if estimate_tokens(item) <= 50:  # Per-item limit
                            truncated_items.append(item)
                        else:
                            # Truncate item
                            max_chars = 50 * 4
                            truncated_items.append(item[:max_chars] + "...")
                patch[key] = truncated_items[:10]  # Limit number of items
        
        # Limit extracted items
        if "extracted" in result and isinstance(result["extracted"], dict):
            extracted = result["extracted"]
            for key in ["facts_added", "decisions_added", "tasks_added"]:
                if key in extracted and isinstance(extracted[key], list):
                    extracted[key] = extracted[key][:50]  # Limit to 50 items per category
        
        # Phase 2: Global token budget enforcement
        total_tokens = estimate_tokens(result)
        if total_tokens > self.max_summary_tokens:
            # Apply aggressive compression
            result = self._compress_aggressively(result, total_tokens)
            
            # Final check - if still over limit, apply final truncation
            final_tokens = estimate_tokens(result)
            if final_tokens > self.max_summary_tokens:
                logger.warning(
                    f"Summary still exceeds token budget after compression: "
                    f"{final_tokens} > {self.max_summary_tokens}. Applying final truncation."
                )
                result = self._apply_final_truncation(result)
        
        return result
    
    def _compress_aggressively(self, result: Dict[str, Any], current_tokens: int) -> Dict[str, Any]:
        """
        Apply aggressive compression to reduce token count.
        
        Priority order:
        1. Preserve: bookkeeping, event_ids in extracted items
        2. Compress: summary_patch text fields (current_goal, list items)
        3. Reduce: Number of items in lists
        4. Truncate: Text content in extracted items (keep event_ids)
        5. Remove: Least important extracted items if necessary
        """
        target_reduction = current_tokens - self.max_summary_tokens
        reduction_ratio = self.max_summary_tokens / current_tokens if current_tokens > 0 else 1.0
        
        # Compress summary_patch text fields
        if "summary_patch" in result and isinstance(result["summary_patch"], dict):
            patch = result["summary_patch"]
            
            # Aggressively truncate current_goal
            if "current_goal" in patch and isinstance(patch["current_goal"], str) and patch["current_goal"]:
                goal_tokens = estimate_tokens(patch["current_goal"])
                if goal_tokens > 0:
                    # Reduce by at least the reduction ratio
                    target_goal_tokens = int(goal_tokens * reduction_ratio * 0.8)  # 80% of target
                    max_chars = max(50, target_goal_tokens * 4)  # At least 50 chars
                    if len(patch["current_goal"]) > max_chars:
                        patch["current_goal"] = patch["current_goal"][:max_chars] + "..."
            
            # Reduce list lengths more aggressively
            for key in ["what_we_built", "open_questions", "constraints", "next_steps"]:
                if key in patch and isinstance(patch[key], list) and patch[key]:
                    items = patch[key]
                    # Reduce number of items
                    target_count = max(1, int(len(items) * reduction_ratio * 0.7))
                    items = items[:target_count]
                    
                    # Truncate remaining items more aggressively
                    truncated_items = []
                    for item in items:
                        if isinstance(item, str):
                            item_tokens = estimate_tokens(item)
                            if item_tokens > 30:  # More aggressive threshold
                                target_item_tokens = int(item_tokens * reduction_ratio * 0.7)
                                max_chars = max(30, target_item_tokens * 4)
                                truncated_items.append(item[:max_chars] + "...")
                            else:
                                truncated_items.append(item)
                        else:
                            truncated_items.append(item)
                    patch[key] = truncated_items
        
        # Compress extracted items (preserve event_ids)
        if "extracted" in result and isinstance(result["extracted"], dict):
            extracted = result["extracted"]
            
            # Priority order: facts_added, decisions_added, tasks_added
            categories = ["facts_added", "decisions_added", "tasks_added"]
            for category in categories:
                if category in extracted and isinstance(extracted[category], list) and extracted[category]:
                    items = extracted[category]
                    
                    # Reduce number of items
                    target_count = max(1, int(len(items) * reduction_ratio * 0.8))
                    items = items[:target_count]
                    
                    # Truncate text fields while preserving event_ids
                    compressed_items = []
                    for item in items:
                        compressed_item = item.copy()
                        
                        # Preserve event_ids
                        if "event_ids" not in compressed_item:
                            compressed_item["event_ids"] = []
                        
                        # Truncate text fields
                        if "text" in compressed_item:
                            text = compressed_item["text"]
                            text_tokens = estimate_tokens(text)
                            if text_tokens > 20:
                                target_text_tokens = int(text_tokens * reduction_ratio * 0.7)
                                max_chars = max(20, target_text_tokens * 4)
                                compressed_item["text"] = text[:max_chars] + "..."
                        
                        if "description" in compressed_item:
                            desc = compressed_item["description"]
                            desc_tokens = estimate_tokens(desc)
                            if desc_tokens > 20:
                                target_desc_tokens = int(desc_tokens * reduction_ratio * 0.7)
                                max_chars = max(20, target_desc_tokens * 4)
                                compressed_item["description"] = desc[:max_chars] + "..."
                        
                        if "reasoning" in compressed_item:
                            reasoning = compressed_item["reasoning"]
                            reasoning_tokens = estimate_tokens(reasoning)
                            if reasoning_tokens > 20:
                                target_reasoning_tokens = int(reasoning_tokens * reduction_ratio * 0.7)
                                max_chars = max(20, target_reasoning_tokens * 4)
                                compressed_item["reasoning"] = reasoning[:max_chars] + "..."
                        
                        compressed_items.append(compressed_item)
                    
                    extracted[category] = compressed_items
        
        return result
    
    def _apply_final_truncation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply final aggressive truncation when compression isn't enough.
        
        This is a last resort to ensure we're under the limit.
        """
        # Keep reducing until under limit
        max_iterations = 10
        for iteration in range(max_iterations):
            total_tokens = estimate_tokens(result)
            if total_tokens <= self.max_summary_tokens:
                break
            
            # Calculate how much we need to reduce
            excess = total_tokens - self.max_summary_tokens
            reduction_factor = self.max_summary_tokens / total_tokens
            
            # Aggressively truncate summary_patch
            if "summary_patch" in result and isinstance(result["summary_patch"], dict):
                patch = result["summary_patch"]
                
                if "current_goal" in patch and isinstance(patch["current_goal"], str) and patch["current_goal"]:
                    goal_len = len(patch["current_goal"])
                    new_len = max(10, int(goal_len * reduction_factor * 0.5))
                    patch["current_goal"] = patch["current_goal"][:new_len] + "..."
                
                # Reduce all lists to minimal size
                for key in ["what_we_built", "open_questions", "constraints", "next_steps"]:
                    if key in patch and isinstance(patch[key], list) and patch[key]:
                        patch[key] = patch[key][:1]  # Keep only first item
                        if patch[key] and isinstance(patch[key][0], str):
                            item = patch[key][0]
                            new_len = max(10, int(len(item) * reduction_factor * 0.5))
                            patch[key][0] = item[:new_len] + "..."
            
            # Aggressively reduce extracted items
            if "extracted" in result and isinstance(result["extracted"], dict):
                extracted = result["extracted"]
                for category in ["facts_added", "decisions_added", "tasks_added"]:
                    if category in extracted and isinstance(extracted[category], list) and extracted[category]:
                        # Keep only first item, truncate heavily
                        items = extracted[category][:1]
                        if items:
                            item = items[0].copy()
                            # Preserve event_ids
                            if "event_ids" not in item:
                                item["event_ids"] = []
                            
                            # Heavily truncate text
                            for text_key in ["text", "description", "reasoning"]:
                                if text_key in item and item[text_key]:
                                    text = item[text_key]
                                    new_len = max(5, int(len(text) * reduction_factor * 0.3))
                                    item[text_key] = text[:new_len] + "..."
                            
                            extracted[category] = [item]
        
        return result

