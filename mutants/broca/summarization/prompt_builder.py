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
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


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
    
    def xǁPromptBuilderǁ__init____mutmut_orig(
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
    
    def xǁPromptBuilderǁ__init____mutmut_1(
        self,
        summary_storage: SummaryStorage,
        last_turns_count: int = 4
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
    
    def xǁPromptBuilderǁ__init____mutmut_2(
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
        self.summary_storage = None
        self.last_turns_count = last_turns_count
        logger.debug(f"Initialized PromptBuilder with last_turns_count={last_turns_count}")
    
    def xǁPromptBuilderǁ__init____mutmut_3(
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
        self.last_turns_count = None
        logger.debug(f"Initialized PromptBuilder with last_turns_count={last_turns_count}")
    
    def xǁPromptBuilderǁ__init____mutmut_4(
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
        logger.debug(None)
    
    xǁPromptBuilderǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPromptBuilderǁ__init____mutmut_1': xǁPromptBuilderǁ__init____mutmut_1, 
        'xǁPromptBuilderǁ__init____mutmut_2': xǁPromptBuilderǁ__init____mutmut_2, 
        'xǁPromptBuilderǁ__init____mutmut_3': xǁPromptBuilderǁ__init____mutmut_3, 
        'xǁPromptBuilderǁ__init____mutmut_4': xǁPromptBuilderǁ__init____mutmut_4
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPromptBuilderǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁPromptBuilderǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁPromptBuilderǁ__init____mutmut_orig)
    xǁPromptBuilderǁ__init____mutmut_orig.__name__ = 'xǁPromptBuilderǁ__init__'
    
    def xǁPromptBuilderǁbuild_context__mutmut_orig(
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_1(
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
        parts = None
        
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_2(
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
            parts.append(None)
        
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_3(
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
        summary = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_4(
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
        summary = self.summary_storage.load_session_summary(None)
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_5(
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
            summary_text = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_6(
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
            summary_text = self._format_summary(None)
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_7(
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
                summary_section = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_8(
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
                    "XX## Session Summary (Historical Context)\n\nXX"
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_9(
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
                    "## session summary (historical context)\n\n"
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_10(
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
                    "## SESSION SUMMARY (HISTORICAL CONTEXT)\n\n"
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_11(
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
                    "XXThe following is historical context from earlier in this conversation. XX"
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_12(
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
                    "the following is historical context from earlier in this conversation. "
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_13(
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
                    "THE FOLLOWING IS HISTORICAL CONTEXT FROM EARLIER IN THIS CONVERSATION. "
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_14(
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
                    "XXThese goals and steps may be outdated or completed. Use them as context XX"
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_15(
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
                    "these goals and steps may be outdated or completed. use them as context "
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_16(
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
                    "THESE GOALS AND STEPS MAY BE OUTDATED OR COMPLETED. USE THEM AS CONTEXT "
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_17(
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
                    "XXbut prioritize the current user request and recent conversation turns.\n\nXX"
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_18(
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
                    "BUT PRIORITIZE THE CURRENT USER REQUEST AND RECENT CONVERSATION TURNS.\n\n"
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_19(
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
                parts.append(None)
        
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_20(
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
        project_state = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_21(
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
        if project_state or (project_state.repo_paths or project_state.enabled_modules):
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_22(
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
        if project_state and (project_state.repo_paths and project_state.enabled_modules):
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_23(
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
            project_text = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_24(
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
            project_text = self._format_project_state(None)
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_25(
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
                parts.append(None)
        
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_26(
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
        
        result = None
        
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_27(
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
        
        result = "\n\n".join(None)
        
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_28(
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
        
        result = "XX\n\nXX".join(parts)
        
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_29(
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
        max_size = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_30(
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
        original_size = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_31(
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
        if original_size >= max_size:
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_32(
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
            truncated = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_33(
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
            last_section = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_34(
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
            last_section = truncated.rfind(None)
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_35(
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
            last_section = truncated.find("##")
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_36(
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
            last_section = truncated.rfind("XX##XX")
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_37(
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
            if last_section >= max_size * 0.7:  # Only if we're keeping most of it
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_38(
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
            if last_section > max_size / 0.7:  # Only if we're keeping most of it
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_39(
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
            if last_section > max_size * 1.7:  # Only if we're keeping most of it
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_40(
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
                truncated = None
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_41(
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
                truncated = truncated[:last_section].lstrip()
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
    
    def xǁPromptBuilderǁbuild_context__mutmut_42(
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
                last_newline = None
                if last_newline > max_size * 0.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_43(
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
                last_newline = truncated.rfind(None)
                if last_newline > max_size * 0.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_44(
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
                last_newline = truncated.find("\n")
                if last_newline > max_size * 0.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_45(
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
                last_newline = truncated.rfind("XX\nXX")
                if last_newline > max_size * 0.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_46(
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
                if last_newline >= max_size * 0.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_47(
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
                if last_newline > max_size / 0.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_48(
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
                if last_newline > max_size * 1.8:
                    truncated = truncated[:last_newline]
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_49(
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
                    truncated = None
            result = truncated + "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_50(
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
            result = None
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_51(
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
            result = truncated - "\n\n[Summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_52(
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
            result = truncated + "XX\n\n[Summary context truncated due to size limit]XX"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_53(
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
            result = truncated + "\n\n[summary context truncated due to size limit]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_54(
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
            result = truncated + "\n\n[SUMMARY CONTEXT TRUNCATED DUE TO SIZE LIMIT]"
            logger.warning(
                f"Summary context truncated from {original_size} to {len(result)} characters "
                f"(limit: {max_size})"
            )
        
        return result
    
    def xǁPromptBuilderǁbuild_context__mutmut_55(
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
                None
            )
        
        return result
    
    xǁPromptBuilderǁbuild_context__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPromptBuilderǁbuild_context__mutmut_1': xǁPromptBuilderǁbuild_context__mutmut_1, 
        'xǁPromptBuilderǁbuild_context__mutmut_2': xǁPromptBuilderǁbuild_context__mutmut_2, 
        'xǁPromptBuilderǁbuild_context__mutmut_3': xǁPromptBuilderǁbuild_context__mutmut_3, 
        'xǁPromptBuilderǁbuild_context__mutmut_4': xǁPromptBuilderǁbuild_context__mutmut_4, 
        'xǁPromptBuilderǁbuild_context__mutmut_5': xǁPromptBuilderǁbuild_context__mutmut_5, 
        'xǁPromptBuilderǁbuild_context__mutmut_6': xǁPromptBuilderǁbuild_context__mutmut_6, 
        'xǁPromptBuilderǁbuild_context__mutmut_7': xǁPromptBuilderǁbuild_context__mutmut_7, 
        'xǁPromptBuilderǁbuild_context__mutmut_8': xǁPromptBuilderǁbuild_context__mutmut_8, 
        'xǁPromptBuilderǁbuild_context__mutmut_9': xǁPromptBuilderǁbuild_context__mutmut_9, 
        'xǁPromptBuilderǁbuild_context__mutmut_10': xǁPromptBuilderǁbuild_context__mutmut_10, 
        'xǁPromptBuilderǁbuild_context__mutmut_11': xǁPromptBuilderǁbuild_context__mutmut_11, 
        'xǁPromptBuilderǁbuild_context__mutmut_12': xǁPromptBuilderǁbuild_context__mutmut_12, 
        'xǁPromptBuilderǁbuild_context__mutmut_13': xǁPromptBuilderǁbuild_context__mutmut_13, 
        'xǁPromptBuilderǁbuild_context__mutmut_14': xǁPromptBuilderǁbuild_context__mutmut_14, 
        'xǁPromptBuilderǁbuild_context__mutmut_15': xǁPromptBuilderǁbuild_context__mutmut_15, 
        'xǁPromptBuilderǁbuild_context__mutmut_16': xǁPromptBuilderǁbuild_context__mutmut_16, 
        'xǁPromptBuilderǁbuild_context__mutmut_17': xǁPromptBuilderǁbuild_context__mutmut_17, 
        'xǁPromptBuilderǁbuild_context__mutmut_18': xǁPromptBuilderǁbuild_context__mutmut_18, 
        'xǁPromptBuilderǁbuild_context__mutmut_19': xǁPromptBuilderǁbuild_context__mutmut_19, 
        'xǁPromptBuilderǁbuild_context__mutmut_20': xǁPromptBuilderǁbuild_context__mutmut_20, 
        'xǁPromptBuilderǁbuild_context__mutmut_21': xǁPromptBuilderǁbuild_context__mutmut_21, 
        'xǁPromptBuilderǁbuild_context__mutmut_22': xǁPromptBuilderǁbuild_context__mutmut_22, 
        'xǁPromptBuilderǁbuild_context__mutmut_23': xǁPromptBuilderǁbuild_context__mutmut_23, 
        'xǁPromptBuilderǁbuild_context__mutmut_24': xǁPromptBuilderǁbuild_context__mutmut_24, 
        'xǁPromptBuilderǁbuild_context__mutmut_25': xǁPromptBuilderǁbuild_context__mutmut_25, 
        'xǁPromptBuilderǁbuild_context__mutmut_26': xǁPromptBuilderǁbuild_context__mutmut_26, 
        'xǁPromptBuilderǁbuild_context__mutmut_27': xǁPromptBuilderǁbuild_context__mutmut_27, 
        'xǁPromptBuilderǁbuild_context__mutmut_28': xǁPromptBuilderǁbuild_context__mutmut_28, 
        'xǁPromptBuilderǁbuild_context__mutmut_29': xǁPromptBuilderǁbuild_context__mutmut_29, 
        'xǁPromptBuilderǁbuild_context__mutmut_30': xǁPromptBuilderǁbuild_context__mutmut_30, 
        'xǁPromptBuilderǁbuild_context__mutmut_31': xǁPromptBuilderǁbuild_context__mutmut_31, 
        'xǁPromptBuilderǁbuild_context__mutmut_32': xǁPromptBuilderǁbuild_context__mutmut_32, 
        'xǁPromptBuilderǁbuild_context__mutmut_33': xǁPromptBuilderǁbuild_context__mutmut_33, 
        'xǁPromptBuilderǁbuild_context__mutmut_34': xǁPromptBuilderǁbuild_context__mutmut_34, 
        'xǁPromptBuilderǁbuild_context__mutmut_35': xǁPromptBuilderǁbuild_context__mutmut_35, 
        'xǁPromptBuilderǁbuild_context__mutmut_36': xǁPromptBuilderǁbuild_context__mutmut_36, 
        'xǁPromptBuilderǁbuild_context__mutmut_37': xǁPromptBuilderǁbuild_context__mutmut_37, 
        'xǁPromptBuilderǁbuild_context__mutmut_38': xǁPromptBuilderǁbuild_context__mutmut_38, 
        'xǁPromptBuilderǁbuild_context__mutmut_39': xǁPromptBuilderǁbuild_context__mutmut_39, 
        'xǁPromptBuilderǁbuild_context__mutmut_40': xǁPromptBuilderǁbuild_context__mutmut_40, 
        'xǁPromptBuilderǁbuild_context__mutmut_41': xǁPromptBuilderǁbuild_context__mutmut_41, 
        'xǁPromptBuilderǁbuild_context__mutmut_42': xǁPromptBuilderǁbuild_context__mutmut_42, 
        'xǁPromptBuilderǁbuild_context__mutmut_43': xǁPromptBuilderǁbuild_context__mutmut_43, 
        'xǁPromptBuilderǁbuild_context__mutmut_44': xǁPromptBuilderǁbuild_context__mutmut_44, 
        'xǁPromptBuilderǁbuild_context__mutmut_45': xǁPromptBuilderǁbuild_context__mutmut_45, 
        'xǁPromptBuilderǁbuild_context__mutmut_46': xǁPromptBuilderǁbuild_context__mutmut_46, 
        'xǁPromptBuilderǁbuild_context__mutmut_47': xǁPromptBuilderǁbuild_context__mutmut_47, 
        'xǁPromptBuilderǁbuild_context__mutmut_48': xǁPromptBuilderǁbuild_context__mutmut_48, 
        'xǁPromptBuilderǁbuild_context__mutmut_49': xǁPromptBuilderǁbuild_context__mutmut_49, 
        'xǁPromptBuilderǁbuild_context__mutmut_50': xǁPromptBuilderǁbuild_context__mutmut_50, 
        'xǁPromptBuilderǁbuild_context__mutmut_51': xǁPromptBuilderǁbuild_context__mutmut_51, 
        'xǁPromptBuilderǁbuild_context__mutmut_52': xǁPromptBuilderǁbuild_context__mutmut_52, 
        'xǁPromptBuilderǁbuild_context__mutmut_53': xǁPromptBuilderǁbuild_context__mutmut_53, 
        'xǁPromptBuilderǁbuild_context__mutmut_54': xǁPromptBuilderǁbuild_context__mutmut_54, 
        'xǁPromptBuilderǁbuild_context__mutmut_55': xǁPromptBuilderǁbuild_context__mutmut_55
    }
    
    def build_context(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPromptBuilderǁbuild_context__mutmut_orig"), object.__getattribute__(self, "xǁPromptBuilderǁbuild_context__mutmut_mutants"), args, kwargs, self)
        return result 
    
    build_context.__signature__ = _mutmut_signature(xǁPromptBuilderǁbuild_context__mutmut_orig)
    xǁPromptBuilderǁbuild_context__mutmut_orig.__name__ = 'xǁPromptBuilderǁbuild_context'
    
    def xǁPromptBuilderǁ_format_summary__mutmut_orig(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_1(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = None
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_2(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = None
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_3(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = None  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_4(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 501  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_5(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item and len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_6(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_7(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) < max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_8(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = None  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_9(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size + 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_10(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 21]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_11(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = None
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_12(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(None)
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_13(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.find(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_14(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind("XX XX")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_15(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space >= max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_16(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size / 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_17(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 1.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_18(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = None
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_19(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated - " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_20(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + "XX [truncated]XX"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_21(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [TRUNCATED]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_22(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = None
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_23(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(None)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_24(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(None)
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_25(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append(None)
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_26(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("XXWhat Was Built (Historical):XX")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_27(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("what was built (historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_28(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("WHAT WAS BUILT (HISTORICAL):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_29(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[+5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_30(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-6:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_31(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = None
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_32(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(None)
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_33(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(None))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_34(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(None)
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_35(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append(None)
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_36(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("XXPrevious Open Questions (may be resolved):XX")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_37(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("previous open questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_38(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("PREVIOUS OPEN QUESTIONS (MAY BE RESOLVED):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_39(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[+5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_40(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-6:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_41(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = None
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_42(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(None)
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_43(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(None))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_44(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(None)
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_45(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append(None)
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_46(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("XXPrevious Constraints (may no longer apply):XX")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_47(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("previous constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_48(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("PREVIOUS CONSTRAINTS (MAY NO LONGER APPLY):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_49(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[+5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_50(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-6:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_51(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = None
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_52(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(None)
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_53(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(None))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_54(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(None)
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_55(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append(None)
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_56(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("XXPreviously Planned Steps (may be completed or outdated):XX")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_57(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("previously planned steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_58(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("PREVIOUSLY PLANNED STEPS (MAY BE COMPLETED OR OUTDATED):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_59(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[+5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_60(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-6:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_61(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = None
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_62(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(None)
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_63(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(None))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_64(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(None)
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_65(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(None) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_66(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "XX\nXX".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_summary__mutmut_67(self, summary: SessionSummary) -> str:
        """Format session summary for prompt as historical context.
        
        Enforces per-item size limits (500 chars) to prevent unbounded growth.
        """
        blocks = summary.summary_blocks
        lines = []
        max_item_size = 500  # Maximum characters per item to prevent unbounded growth
        
        def truncate_item(item: str, max_size: int = max_item_size) -> str:
            """Truncate an item to max_size, preserving structure."""
            if not item or len(item) <= max_size:
                return item
            truncated = item[:max_size - 20]  # Leave room for truncation marker
            # Try to truncate at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_size * 0.8:
                truncated = truncated[:last_space]
            return truncated + " [truncated]"
        
        if blocks.current_goal:
            goal_text = truncate_item(blocks.current_goal)
            lines.append(f"Previous Goal Context: {goal_text} (may be outdated or completed)")
        
        if blocks.what_we_built:
            lines.append("What Was Built (Historical):")
            for item in blocks.what_we_built[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.open_questions:
            lines.append("Previous Open Questions (may be resolved):")
            for item in blocks.open_questions[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.constraints:
            lines.append("Previous Constraints (may no longer apply):")
            for item in blocks.constraints[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        if blocks.next_steps:
            lines.append("Previously Planned Steps (may be completed or outdated):")
            for item in blocks.next_steps[-5:]:  # Last 5 items
                truncated_item = truncate_item(str(item))
                lines.append(f"  - {truncated_item}")
        
        return "\n".join(lines) if lines else "XXXX"
    
    xǁPromptBuilderǁ_format_summary__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPromptBuilderǁ_format_summary__mutmut_1': xǁPromptBuilderǁ_format_summary__mutmut_1, 
        'xǁPromptBuilderǁ_format_summary__mutmut_2': xǁPromptBuilderǁ_format_summary__mutmut_2, 
        'xǁPromptBuilderǁ_format_summary__mutmut_3': xǁPromptBuilderǁ_format_summary__mutmut_3, 
        'xǁPromptBuilderǁ_format_summary__mutmut_4': xǁPromptBuilderǁ_format_summary__mutmut_4, 
        'xǁPromptBuilderǁ_format_summary__mutmut_5': xǁPromptBuilderǁ_format_summary__mutmut_5, 
        'xǁPromptBuilderǁ_format_summary__mutmut_6': xǁPromptBuilderǁ_format_summary__mutmut_6, 
        'xǁPromptBuilderǁ_format_summary__mutmut_7': xǁPromptBuilderǁ_format_summary__mutmut_7, 
        'xǁPromptBuilderǁ_format_summary__mutmut_8': xǁPromptBuilderǁ_format_summary__mutmut_8, 
        'xǁPromptBuilderǁ_format_summary__mutmut_9': xǁPromptBuilderǁ_format_summary__mutmut_9, 
        'xǁPromptBuilderǁ_format_summary__mutmut_10': xǁPromptBuilderǁ_format_summary__mutmut_10, 
        'xǁPromptBuilderǁ_format_summary__mutmut_11': xǁPromptBuilderǁ_format_summary__mutmut_11, 
        'xǁPromptBuilderǁ_format_summary__mutmut_12': xǁPromptBuilderǁ_format_summary__mutmut_12, 
        'xǁPromptBuilderǁ_format_summary__mutmut_13': xǁPromptBuilderǁ_format_summary__mutmut_13, 
        'xǁPromptBuilderǁ_format_summary__mutmut_14': xǁPromptBuilderǁ_format_summary__mutmut_14, 
        'xǁPromptBuilderǁ_format_summary__mutmut_15': xǁPromptBuilderǁ_format_summary__mutmut_15, 
        'xǁPromptBuilderǁ_format_summary__mutmut_16': xǁPromptBuilderǁ_format_summary__mutmut_16, 
        'xǁPromptBuilderǁ_format_summary__mutmut_17': xǁPromptBuilderǁ_format_summary__mutmut_17, 
        'xǁPromptBuilderǁ_format_summary__mutmut_18': xǁPromptBuilderǁ_format_summary__mutmut_18, 
        'xǁPromptBuilderǁ_format_summary__mutmut_19': xǁPromptBuilderǁ_format_summary__mutmut_19, 
        'xǁPromptBuilderǁ_format_summary__mutmut_20': xǁPromptBuilderǁ_format_summary__mutmut_20, 
        'xǁPromptBuilderǁ_format_summary__mutmut_21': xǁPromptBuilderǁ_format_summary__mutmut_21, 
        'xǁPromptBuilderǁ_format_summary__mutmut_22': xǁPromptBuilderǁ_format_summary__mutmut_22, 
        'xǁPromptBuilderǁ_format_summary__mutmut_23': xǁPromptBuilderǁ_format_summary__mutmut_23, 
        'xǁPromptBuilderǁ_format_summary__mutmut_24': xǁPromptBuilderǁ_format_summary__mutmut_24, 
        'xǁPromptBuilderǁ_format_summary__mutmut_25': xǁPromptBuilderǁ_format_summary__mutmut_25, 
        'xǁPromptBuilderǁ_format_summary__mutmut_26': xǁPromptBuilderǁ_format_summary__mutmut_26, 
        'xǁPromptBuilderǁ_format_summary__mutmut_27': xǁPromptBuilderǁ_format_summary__mutmut_27, 
        'xǁPromptBuilderǁ_format_summary__mutmut_28': xǁPromptBuilderǁ_format_summary__mutmut_28, 
        'xǁPromptBuilderǁ_format_summary__mutmut_29': xǁPromptBuilderǁ_format_summary__mutmut_29, 
        'xǁPromptBuilderǁ_format_summary__mutmut_30': xǁPromptBuilderǁ_format_summary__mutmut_30, 
        'xǁPromptBuilderǁ_format_summary__mutmut_31': xǁPromptBuilderǁ_format_summary__mutmut_31, 
        'xǁPromptBuilderǁ_format_summary__mutmut_32': xǁPromptBuilderǁ_format_summary__mutmut_32, 
        'xǁPromptBuilderǁ_format_summary__mutmut_33': xǁPromptBuilderǁ_format_summary__mutmut_33, 
        'xǁPromptBuilderǁ_format_summary__mutmut_34': xǁPromptBuilderǁ_format_summary__mutmut_34, 
        'xǁPromptBuilderǁ_format_summary__mutmut_35': xǁPromptBuilderǁ_format_summary__mutmut_35, 
        'xǁPromptBuilderǁ_format_summary__mutmut_36': xǁPromptBuilderǁ_format_summary__mutmut_36, 
        'xǁPromptBuilderǁ_format_summary__mutmut_37': xǁPromptBuilderǁ_format_summary__mutmut_37, 
        'xǁPromptBuilderǁ_format_summary__mutmut_38': xǁPromptBuilderǁ_format_summary__mutmut_38, 
        'xǁPromptBuilderǁ_format_summary__mutmut_39': xǁPromptBuilderǁ_format_summary__mutmut_39, 
        'xǁPromptBuilderǁ_format_summary__mutmut_40': xǁPromptBuilderǁ_format_summary__mutmut_40, 
        'xǁPromptBuilderǁ_format_summary__mutmut_41': xǁPromptBuilderǁ_format_summary__mutmut_41, 
        'xǁPromptBuilderǁ_format_summary__mutmut_42': xǁPromptBuilderǁ_format_summary__mutmut_42, 
        'xǁPromptBuilderǁ_format_summary__mutmut_43': xǁPromptBuilderǁ_format_summary__mutmut_43, 
        'xǁPromptBuilderǁ_format_summary__mutmut_44': xǁPromptBuilderǁ_format_summary__mutmut_44, 
        'xǁPromptBuilderǁ_format_summary__mutmut_45': xǁPromptBuilderǁ_format_summary__mutmut_45, 
        'xǁPromptBuilderǁ_format_summary__mutmut_46': xǁPromptBuilderǁ_format_summary__mutmut_46, 
        'xǁPromptBuilderǁ_format_summary__mutmut_47': xǁPromptBuilderǁ_format_summary__mutmut_47, 
        'xǁPromptBuilderǁ_format_summary__mutmut_48': xǁPromptBuilderǁ_format_summary__mutmut_48, 
        'xǁPromptBuilderǁ_format_summary__mutmut_49': xǁPromptBuilderǁ_format_summary__mutmut_49, 
        'xǁPromptBuilderǁ_format_summary__mutmut_50': xǁPromptBuilderǁ_format_summary__mutmut_50, 
        'xǁPromptBuilderǁ_format_summary__mutmut_51': xǁPromptBuilderǁ_format_summary__mutmut_51, 
        'xǁPromptBuilderǁ_format_summary__mutmut_52': xǁPromptBuilderǁ_format_summary__mutmut_52, 
        'xǁPromptBuilderǁ_format_summary__mutmut_53': xǁPromptBuilderǁ_format_summary__mutmut_53, 
        'xǁPromptBuilderǁ_format_summary__mutmut_54': xǁPromptBuilderǁ_format_summary__mutmut_54, 
        'xǁPromptBuilderǁ_format_summary__mutmut_55': xǁPromptBuilderǁ_format_summary__mutmut_55, 
        'xǁPromptBuilderǁ_format_summary__mutmut_56': xǁPromptBuilderǁ_format_summary__mutmut_56, 
        'xǁPromptBuilderǁ_format_summary__mutmut_57': xǁPromptBuilderǁ_format_summary__mutmut_57, 
        'xǁPromptBuilderǁ_format_summary__mutmut_58': xǁPromptBuilderǁ_format_summary__mutmut_58, 
        'xǁPromptBuilderǁ_format_summary__mutmut_59': xǁPromptBuilderǁ_format_summary__mutmut_59, 
        'xǁPromptBuilderǁ_format_summary__mutmut_60': xǁPromptBuilderǁ_format_summary__mutmut_60, 
        'xǁPromptBuilderǁ_format_summary__mutmut_61': xǁPromptBuilderǁ_format_summary__mutmut_61, 
        'xǁPromptBuilderǁ_format_summary__mutmut_62': xǁPromptBuilderǁ_format_summary__mutmut_62, 
        'xǁPromptBuilderǁ_format_summary__mutmut_63': xǁPromptBuilderǁ_format_summary__mutmut_63, 
        'xǁPromptBuilderǁ_format_summary__mutmut_64': xǁPromptBuilderǁ_format_summary__mutmut_64, 
        'xǁPromptBuilderǁ_format_summary__mutmut_65': xǁPromptBuilderǁ_format_summary__mutmut_65, 
        'xǁPromptBuilderǁ_format_summary__mutmut_66': xǁPromptBuilderǁ_format_summary__mutmut_66, 
        'xǁPromptBuilderǁ_format_summary__mutmut_67': xǁPromptBuilderǁ_format_summary__mutmut_67
    }
    
    def _format_summary(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPromptBuilderǁ_format_summary__mutmut_orig"), object.__getattribute__(self, "xǁPromptBuilderǁ_format_summary__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _format_summary.__signature__ = _mutmut_signature(xǁPromptBuilderǁ_format_summary__mutmut_orig)
    xǁPromptBuilderǁ_format_summary__mutmut_orig.__name__ = 'xǁPromptBuilderǁ_format_summary'
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_orig(self, project_state: ProjectState) -> str:
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
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_1(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = None
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_2(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(None)
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_3(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(None)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_4(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {'XX, XX'.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_5(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(None)
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_6(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(None)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_7(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {'XX, XX'.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_8(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append(None)
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_9(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("XXKnown Issues:XX")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_10(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("known issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_11(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("KNOWN ISSUES:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_12(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[+3:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_13(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-4:]:  # Last 3 issues
                lines.append(f"  - {issue}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_14(self, project_state: ProjectState) -> str:
        """Format project state for prompt."""
        lines = []
        
        if project_state.repo_paths:
            lines.append(f"Repository Paths: {', '.join(project_state.repo_paths)}")
        
        if project_state.enabled_modules:
            lines.append(f"Enabled Modules: {', '.join(project_state.enabled_modules)}")
        
        if project_state.known_issues:
            lines.append("Known Issues:")
            for issue in project_state.known_issues[-3:]:  # Last 3 issues
                lines.append(None)
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_15(self, project_state: ProjectState) -> str:
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
        
        return "\n".join(None) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_16(self, project_state: ProjectState) -> str:
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
        
        return "XX\nXX".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_project_state__mutmut_17(self, project_state: ProjectState) -> str:
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
        
        return "\n".join(lines) if lines else "XXXX"
    
    xǁPromptBuilderǁ_format_project_state__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPromptBuilderǁ_format_project_state__mutmut_1': xǁPromptBuilderǁ_format_project_state__mutmut_1, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_2': xǁPromptBuilderǁ_format_project_state__mutmut_2, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_3': xǁPromptBuilderǁ_format_project_state__mutmut_3, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_4': xǁPromptBuilderǁ_format_project_state__mutmut_4, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_5': xǁPromptBuilderǁ_format_project_state__mutmut_5, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_6': xǁPromptBuilderǁ_format_project_state__mutmut_6, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_7': xǁPromptBuilderǁ_format_project_state__mutmut_7, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_8': xǁPromptBuilderǁ_format_project_state__mutmut_8, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_9': xǁPromptBuilderǁ_format_project_state__mutmut_9, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_10': xǁPromptBuilderǁ_format_project_state__mutmut_10, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_11': xǁPromptBuilderǁ_format_project_state__mutmut_11, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_12': xǁPromptBuilderǁ_format_project_state__mutmut_12, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_13': xǁPromptBuilderǁ_format_project_state__mutmut_13, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_14': xǁPromptBuilderǁ_format_project_state__mutmut_14, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_15': xǁPromptBuilderǁ_format_project_state__mutmut_15, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_16': xǁPromptBuilderǁ_format_project_state__mutmut_16, 
        'xǁPromptBuilderǁ_format_project_state__mutmut_17': xǁPromptBuilderǁ_format_project_state__mutmut_17
    }
    
    def _format_project_state(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPromptBuilderǁ_format_project_state__mutmut_orig"), object.__getattribute__(self, "xǁPromptBuilderǁ_format_project_state__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _format_project_state.__signature__ = _mutmut_signature(xǁPromptBuilderǁ_format_project_state__mutmut_orig)
    xǁPromptBuilderǁ_format_project_state__mutmut_orig.__name__ = 'xǁPromptBuilderǁ_format_project_state'
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_orig(
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
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_1(
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
        non_system = None
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_2(
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
        non_system = [m for m in messages if m.get(None) != "system"]
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_3(
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
        non_system = [m for m in messages if m.get("XXroleXX") != "system"]
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_4(
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
        non_system = [m for m in messages if m.get("ROLE") != "system"]
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_5(
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
        non_system = [m for m in messages if m.get("role") == "system"]
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_6(
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
        non_system = [m for m in messages if m.get("role") != "XXsystemXX"]
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_7(
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
        non_system = [m for m in messages if m.get("role") != "SYSTEM"]
        
        # Get last count*2 messages (each turn = user + assistant)
        # But make sure we don't go past the beginning
        start_idx = max(0, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_8(
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
        start_idx = None
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_9(
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
        start_idx = max(None, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_10(
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
        start_idx = max(0, None)
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_11(
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
        start_idx = max(len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_12(
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
        start_idx = max(0, )
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_13(
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
        start_idx = max(1, len(non_system) - (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_14(
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
        start_idx = max(0, len(non_system) + (count * 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_15(
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
        start_idx = max(0, len(non_system) - (count / 2))
        return non_system[start_idx:]
    
    def xǁPromptBuilderǁ_get_last_turns__mutmut_16(
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
        start_idx = max(0, len(non_system) - (count * 3))
        return non_system[start_idx:]
    
    xǁPromptBuilderǁ_get_last_turns__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPromptBuilderǁ_get_last_turns__mutmut_1': xǁPromptBuilderǁ_get_last_turns__mutmut_1, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_2': xǁPromptBuilderǁ_get_last_turns__mutmut_2, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_3': xǁPromptBuilderǁ_get_last_turns__mutmut_3, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_4': xǁPromptBuilderǁ_get_last_turns__mutmut_4, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_5': xǁPromptBuilderǁ_get_last_turns__mutmut_5, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_6': xǁPromptBuilderǁ_get_last_turns__mutmut_6, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_7': xǁPromptBuilderǁ_get_last_turns__mutmut_7, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_8': xǁPromptBuilderǁ_get_last_turns__mutmut_8, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_9': xǁPromptBuilderǁ_get_last_turns__mutmut_9, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_10': xǁPromptBuilderǁ_get_last_turns__mutmut_10, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_11': xǁPromptBuilderǁ_get_last_turns__mutmut_11, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_12': xǁPromptBuilderǁ_get_last_turns__mutmut_12, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_13': xǁPromptBuilderǁ_get_last_turns__mutmut_13, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_14': xǁPromptBuilderǁ_get_last_turns__mutmut_14, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_15': xǁPromptBuilderǁ_get_last_turns__mutmut_15, 
        'xǁPromptBuilderǁ_get_last_turns__mutmut_16': xǁPromptBuilderǁ_get_last_turns__mutmut_16
    }
    
    def _get_last_turns(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPromptBuilderǁ_get_last_turns__mutmut_orig"), object.__getattribute__(self, "xǁPromptBuilderǁ_get_last_turns__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_last_turns.__signature__ = _mutmut_signature(xǁPromptBuilderǁ_get_last_turns__mutmut_orig)
    xǁPromptBuilderǁ_get_last_turns__mutmut_orig.__name__ = 'xǁPromptBuilderǁ_get_last_turns'
    
    def xǁPromptBuilderǁ_format_turns__mutmut_orig(self, turns: List[Dict[str, Any]]) -> str:
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_1(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = None
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_2(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = None
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_3(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get(None, "unknown")
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_4(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", None)
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_5(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("unknown")
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_6(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", )
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_7(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("XXroleXX", "unknown")
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_8(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("ROLE", "unknown")
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_9(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "XXunknownXX")
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_10(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "UNKNOWN")
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
    
    def xǁPromptBuilderǁ_format_turns__mutmut_11(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = None
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_12(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get(None, "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_13(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", None)
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_14(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_15(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", )
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_16(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("XXcontentXX", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_17(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("CONTENT", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_18(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "XXXX")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_19(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role != "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_20(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "XXuserXX":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_21(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "USER":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_22(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(None)
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_23(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role != "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_24(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "XXassistantXX":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_25(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "ASSISTANT":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_26(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(None)
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_27(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role != "tool":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_28(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "XXtoolXX":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_29(self, turns: List[Dict[str, Any]]) -> str:
        """Format turns for prompt."""
        lines = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "TOOL":
                tool_name = msg.get("name", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_30(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = None
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_31(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get(None, "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_32(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get("name", None)
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_33(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get("unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_34(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get("name", )
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_35(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get("XXnameXX", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_36(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get("NAME", "unknown")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_37(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get("name", "XXunknownXX")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_38(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_name = msg.get("name", "UNKNOWN")
                tool_content = content[:200]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_39(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_content = None  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_40(self, turns: List[Dict[str, Any]]) -> str:
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
                tool_content = content[:201]  # Truncate long tool results
                lines.append(f"Tool {tool_name}: {tool_content}")
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_41(self, turns: List[Dict[str, Any]]) -> str:
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
                lines.append(None)
        
        return "\n".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_42(self, turns: List[Dict[str, Any]]) -> str:
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
        
        return "\n".join(None) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_43(self, turns: List[Dict[str, Any]]) -> str:
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
        
        return "XX\nXX".join(lines) if lines else ""
    
    def xǁPromptBuilderǁ_format_turns__mutmut_44(self, turns: List[Dict[str, Any]]) -> str:
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
        
        return "\n".join(lines) if lines else "XXXX"
    
    xǁPromptBuilderǁ_format_turns__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPromptBuilderǁ_format_turns__mutmut_1': xǁPromptBuilderǁ_format_turns__mutmut_1, 
        'xǁPromptBuilderǁ_format_turns__mutmut_2': xǁPromptBuilderǁ_format_turns__mutmut_2, 
        'xǁPromptBuilderǁ_format_turns__mutmut_3': xǁPromptBuilderǁ_format_turns__mutmut_3, 
        'xǁPromptBuilderǁ_format_turns__mutmut_4': xǁPromptBuilderǁ_format_turns__mutmut_4, 
        'xǁPromptBuilderǁ_format_turns__mutmut_5': xǁPromptBuilderǁ_format_turns__mutmut_5, 
        'xǁPromptBuilderǁ_format_turns__mutmut_6': xǁPromptBuilderǁ_format_turns__mutmut_6, 
        'xǁPromptBuilderǁ_format_turns__mutmut_7': xǁPromptBuilderǁ_format_turns__mutmut_7, 
        'xǁPromptBuilderǁ_format_turns__mutmut_8': xǁPromptBuilderǁ_format_turns__mutmut_8, 
        'xǁPromptBuilderǁ_format_turns__mutmut_9': xǁPromptBuilderǁ_format_turns__mutmut_9, 
        'xǁPromptBuilderǁ_format_turns__mutmut_10': xǁPromptBuilderǁ_format_turns__mutmut_10, 
        'xǁPromptBuilderǁ_format_turns__mutmut_11': xǁPromptBuilderǁ_format_turns__mutmut_11, 
        'xǁPromptBuilderǁ_format_turns__mutmut_12': xǁPromptBuilderǁ_format_turns__mutmut_12, 
        'xǁPromptBuilderǁ_format_turns__mutmut_13': xǁPromptBuilderǁ_format_turns__mutmut_13, 
        'xǁPromptBuilderǁ_format_turns__mutmut_14': xǁPromptBuilderǁ_format_turns__mutmut_14, 
        'xǁPromptBuilderǁ_format_turns__mutmut_15': xǁPromptBuilderǁ_format_turns__mutmut_15, 
        'xǁPromptBuilderǁ_format_turns__mutmut_16': xǁPromptBuilderǁ_format_turns__mutmut_16, 
        'xǁPromptBuilderǁ_format_turns__mutmut_17': xǁPromptBuilderǁ_format_turns__mutmut_17, 
        'xǁPromptBuilderǁ_format_turns__mutmut_18': xǁPromptBuilderǁ_format_turns__mutmut_18, 
        'xǁPromptBuilderǁ_format_turns__mutmut_19': xǁPromptBuilderǁ_format_turns__mutmut_19, 
        'xǁPromptBuilderǁ_format_turns__mutmut_20': xǁPromptBuilderǁ_format_turns__mutmut_20, 
        'xǁPromptBuilderǁ_format_turns__mutmut_21': xǁPromptBuilderǁ_format_turns__mutmut_21, 
        'xǁPromptBuilderǁ_format_turns__mutmut_22': xǁPromptBuilderǁ_format_turns__mutmut_22, 
        'xǁPromptBuilderǁ_format_turns__mutmut_23': xǁPromptBuilderǁ_format_turns__mutmut_23, 
        'xǁPromptBuilderǁ_format_turns__mutmut_24': xǁPromptBuilderǁ_format_turns__mutmut_24, 
        'xǁPromptBuilderǁ_format_turns__mutmut_25': xǁPromptBuilderǁ_format_turns__mutmut_25, 
        'xǁPromptBuilderǁ_format_turns__mutmut_26': xǁPromptBuilderǁ_format_turns__mutmut_26, 
        'xǁPromptBuilderǁ_format_turns__mutmut_27': xǁPromptBuilderǁ_format_turns__mutmut_27, 
        'xǁPromptBuilderǁ_format_turns__mutmut_28': xǁPromptBuilderǁ_format_turns__mutmut_28, 
        'xǁPromptBuilderǁ_format_turns__mutmut_29': xǁPromptBuilderǁ_format_turns__mutmut_29, 
        'xǁPromptBuilderǁ_format_turns__mutmut_30': xǁPromptBuilderǁ_format_turns__mutmut_30, 
        'xǁPromptBuilderǁ_format_turns__mutmut_31': xǁPromptBuilderǁ_format_turns__mutmut_31, 
        'xǁPromptBuilderǁ_format_turns__mutmut_32': xǁPromptBuilderǁ_format_turns__mutmut_32, 
        'xǁPromptBuilderǁ_format_turns__mutmut_33': xǁPromptBuilderǁ_format_turns__mutmut_33, 
        'xǁPromptBuilderǁ_format_turns__mutmut_34': xǁPromptBuilderǁ_format_turns__mutmut_34, 
        'xǁPromptBuilderǁ_format_turns__mutmut_35': xǁPromptBuilderǁ_format_turns__mutmut_35, 
        'xǁPromptBuilderǁ_format_turns__mutmut_36': xǁPromptBuilderǁ_format_turns__mutmut_36, 
        'xǁPromptBuilderǁ_format_turns__mutmut_37': xǁPromptBuilderǁ_format_turns__mutmut_37, 
        'xǁPromptBuilderǁ_format_turns__mutmut_38': xǁPromptBuilderǁ_format_turns__mutmut_38, 
        'xǁPromptBuilderǁ_format_turns__mutmut_39': xǁPromptBuilderǁ_format_turns__mutmut_39, 
        'xǁPromptBuilderǁ_format_turns__mutmut_40': xǁPromptBuilderǁ_format_turns__mutmut_40, 
        'xǁPromptBuilderǁ_format_turns__mutmut_41': xǁPromptBuilderǁ_format_turns__mutmut_41, 
        'xǁPromptBuilderǁ_format_turns__mutmut_42': xǁPromptBuilderǁ_format_turns__mutmut_42, 
        'xǁPromptBuilderǁ_format_turns__mutmut_43': xǁPromptBuilderǁ_format_turns__mutmut_43, 
        'xǁPromptBuilderǁ_format_turns__mutmut_44': xǁPromptBuilderǁ_format_turns__mutmut_44
    }
    
    def _format_turns(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPromptBuilderǁ_format_turns__mutmut_orig"), object.__getattribute__(self, "xǁPromptBuilderǁ_format_turns__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _format_turns.__signature__ = _mutmut_signature(xǁPromptBuilderǁ_format_turns__mutmut_orig)
    xǁPromptBuilderǁ_format_turns__mutmut_orig.__name__ = 'xǁPromptBuilderǁ_format_turns'

