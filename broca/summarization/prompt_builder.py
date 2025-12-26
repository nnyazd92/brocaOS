"""
Prompt builder for constructing prompts from summaries and retrieval.

Builds prompts from session_summary.json, user_profile.json, project_state.json,
retrieval notes, and last K raw turns instead of full message history.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .storage import SummaryStorage
from .models import SessionSummary, ProjectState
from ..config import config

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Builds prompts from summaries and retrieval instead of full history.
    
    Constructs prompts from:
    - Session summary (rolling summary)
    - User profile (stable preferences)
    - Project state (system/project facts)
    - Retrieval notes (targeted snippets)
    - Last K raw turns (for immediate coherence)
    """
    
    def __init__(
        self,
        summary_storage: SummaryStorage,
        last_turns_count: int = 3
    ) -> None:
        """
        Initialize prompt builder.
        
        Args:
            summary_storage: SummaryStorage instance
            last_turns_count: Number of recent turns to include for coherence
        """
        self.summary_storage = summary_storage
        self.last_turns_count = last_turns_count
        logger.debug(f"Initialized PromptBuilder with last_turns_count={last_turns_count}")
    
    def build_context(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Build context string from summaries and last K turns.
        
        Args:
            session_id: Session identifier
            messages: Full message history
            system_prompt: Optional base system prompt (usually None to avoid duplication)
            
        Returns:
            Context string to include in prompt (summary context, not including base system prompt)
            Truncated to max_summary_context_size if needed.
        """
        parts = []
        
        # 1. Base system prompt (only if explicitly provided)
        if system_prompt:
            parts.append(system_prompt)
        
        # 2. Session summary (historical context)
        summary = self.summary_storage.load_session_summary(session_id)
        if summary:
            summary_text = self._format_summary(summary)
            if summary_text:
                # Wrap with disclaimer that this is historical context, not current requirements
                summary_section = (
                    "## Session Summary (Historical Context)\n\n"
                    "The following is historical context from earlier in this conversation. "
                    "These goals and steps may be outdated or completed. Use them as context "
                    "but prioritize the current user request and recent conversation turns.\n\n"
                    f"{summary_text}"
                )
                parts.append(summary_section)
        
        # 3. Project state (if available)
        project_state = self.summary_storage.load_project_state()
        if project_state and (project_state.repo_paths or project_state.enabled_modules):
            project_text = self._format_project_state(project_state)
            if project_text:
                parts.append(f"## Project Context\n{project_text}")
        
        # Note: Last K turns are handled separately by filtering messages before LLM call
        # They are not included in the system prompt context to keep it focused on summaries
        
        result = "\n\n".join(parts)
        
        # Apply size limit
        max_size = config.storage.max_summary_context_size
        original_size = len(result)
        if original_size > max_size:
            # Truncate from the end, preserving structure
            truncated = result[:max_size]
            # Try to truncate at a section boundary
            last_section = truncated.rfind("##")
            if last_section > max_size * 0.7:  # Only if we're keeping most of it
                truncated = truncated[:last_section].rstrip()
            else:
                # Truncate at last newline
                last_newline = truncated.rfind("\n")
                if last_newline > max_size * 0.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def _format_summary(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context."""
        blocks = summary.summary_blocks
        lines = []
        
        if blocks.current_goal:
            lines.append(f"Previous Goal Context: {blocks.current_goal} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                lines.append(f"  - {item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                lines.append(f"  - {item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                lines.append(f"  - {item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                lines.append(f"  - {item}")
        
        return "\n".join(lines) if lines else ""
    
    def _format_project_state(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def _get_last_turns(
        self,
        messages: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Get last K turns from messages (excluding system messages).
        
        Args:
            messages: Full message list
            count: Number of turns to return
            
        Returns:
            List of messages from last K turns
        """
        # Filter out system messages
        non_system = [m for m in messages if m.get("role") != "system"]
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def _format_turns(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""

