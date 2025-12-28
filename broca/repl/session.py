from __future__ import annotations

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
import uuid
import time
import sys
import re
from datetime import datetime, timezone
from ..llm import create_llm_client, LLMClient
from .response_guard import ensure_non_empty
from .ansi_repair import repair_ansi_codes
from ..summarization.token_estimator import truncate_tool_result, estimate_messages_tokens

# Try to import termios for terminal control (Unix only)
try:
    import termios
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False

if TYPE_CHECKING:
    from ..storage import ConversationStorage
    from ..tools.registry import ToolRegistry
    from ..internal_sensing.framework import InternalSensingFramework
    from ..world_state.aggregator import WorldStateAggregator
    from ..world_state.formatter import WorldStateFormatter
    from ..summarization.event_logger import EventLogger
    from ..summarization.manager import SummarizationManager

# Import response analyzer for instrumentation
try:
    from ..internal_sensing.response_analyzer import ResponseAnalyzer
except ImportError:
    ResponseAnalyzer = None  # type: ignore

logger = logging.getLogger(__name__)


class ConversationSession:
    """
    Maintains chat history and exposes a simple .send(user_text) → assistant_text interface.

    Logging responsibilities:
    - Track and log current context length (messages, characters).
    - Log each turn with summary of both prompt and reply.

    Storage responsibilities:
    - Optionally persist conversation history to storage backend.
    - Auto-save after each message exchange if storage is provided.
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        llm: Optional["LLMClient"] = None,
        storage: Optional["ConversationStorage"] = None,
        session_id: Optional[str] = None,
        tool_registry: Optional["ToolRegistry"] = None,
        internal_sensing_framework: Optional["InternalSensingFramework"] = None,
        world_state_aggregator: Optional["WorldStateAggregator"] = None,
        base_system_prompt: Optional[str] = None,
        color_manager: Optional[Any] = None,
    ) -> None:
        # If an LLM client is provided, use it directly.
        # Otherwise, if a world_state_aggregator is available, wrap the
        # underlying client with a world-state-aware caching layer.
        if llm is not None:
            self.llm = llm
        else:
            if world_state_aggregator is not None:
                from ..llm import create_cached_llm_client
                self.llm = create_cached_llm_client(
                    scope="broca:repl_interactive",
                    world_state_aggregator=world_state_aggregator,
                )
            else:
                from ..llm import create_llm_client
                self.llm = create_llm_client()
        self.messages: List[Dict[str, str]] = []
        self.storage = storage
        self.tool_registry = tool_registry
        self.internal_sensing_framework = internal_sensing_framework
        self.world_state_aggregator = world_state_aggregator
        self.session_id = session_id or str(uuid.uuid4())
        self.system_prompt = system_prompt

        # World-state hash tracking for system prompt / caching
        self._last_world_state_hash: Optional[str] = None
        self._last_world_state_raw: Optional[dict] = None

        # Get base system prompt from parameter, system_prompt, or config
        # Track whether base_system_prompt was explicitly provided
        # Store initial size to detect unbounded growth
        if base_system_prompt is not None:
            self._base_system_prompt_internal = base_system_prompt
            self._base_system_prompt_explicit = True
        elif system_prompt:
            # If system_prompt is provided but base_system_prompt is not,
            # use system_prompt as the base (for backward compatibility)
            self._base_system_prompt_internal = system_prompt
            self._base_system_prompt_explicit = True
        else:
            # Fall back to config if not provided
            from ..config import config

            self._base_system_prompt_internal = config.storage.base_system_prompt
            self._base_system_prompt_explicit = False
        
        # Store initial base prompt size to detect unbounded growth
        self._initial_base_prompt_size = len(self._base_system_prompt_internal) if self._base_system_prompt_internal else 0
        self._base_prompt_initialized = True

        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self._max_tool_iterations = 100
        
        # Initialize summarization components if enabled (for manual /summarize command only)
        self._event_logger = None
        self._summarization_manager = None
        from ..config import config
        if config.summarization.enabled:
            try:
                from ..summarization.event_logger import EventLogger
                from ..summarization.storage import SummaryStorage
                from ..summarization.manager import SummarizationManager
                
                event_log_dir = config.summarization.event_log_path
                summary_path = config.summarization.summary_path
                
                self._event_logger = EventLogger(log_dir=event_log_dir)
                summary_storage = SummaryStorage(summary_path=summary_path)
                self._summarization_manager = SummarizationManager(
                    event_logger=self._event_logger,
                    summary_storage=summary_storage,
                    trigger_turns=config.summarization.trigger_turns,
                    trigger_token_threshold=config.summarization.trigger_token_threshold
                )
                logger.debug("Summarization enabled for session (manual /summarize only)")
            except Exception as e:
                logger.warning(f"Failed to initialize summarization: {e}", exc_info=True)
        
        # Track turns for summarization triggers (disabled for automatic, kept for manual)
        self._turns_since_last_summary = 0
        
        # Initialize context graph for intelligent context management
        self._context_graph = None
        if config.context.enabled:
            try:
                from ..context import ContextGraph
                self._context_graph = ContextGraph(
                    min_turns_retained=config.context.min_turns_retained,
                    orphan_threshold_turns=config.context.orphan_threshold_turns,
                    main_thread_boost=config.context.main_thread_boost,
                )
                logger.debug("Context graph enabled for session")
            except Exception as e:
                logger.warning(f"Failed to initialize context graph: {e}", exc_info=True)

        # Initialize formatter for world state
        if world_state_aggregator:
            from ..world_state.formatter import WorldStateFormatter

            self._world_state_formatter = WorldStateFormatter()
        else:
            self._world_state_formatter = None

        # Initialize tool status display for visual feedback
        try:
            from .tool_status import ToolStatusDisplay
            self._tool_status_display = ToolStatusDisplay(color_manager=color_manager)
        except Exception as e:
            logger.debug(f"Failed to initialize tool status display: {e}", exc_info=True)
            self._tool_status_display = None

        # Store color manager for colorizing output
        self._color_manager = color_manager

        # Update system prompt with world state immediately if aggregator is available
        # This ensures world state is populated even before first user message
        # Note: We don't manually add system_prompt here because _update_system_prompt() will
        # create the system message from base_system_prompt + world state + summary.
        # This prevents duplicate system messages if _update_system_prompt() is called.
        if self.world_state_aggregator and self._world_state_formatter:
            self._update_system_prompt()
        elif system_prompt and not self.world_state_aggregator:
            # Only add system_prompt directly if world_state_aggregator is not available
            # (in which case _update_system_prompt() won't run)
            # Add tool calling instructions to ensure automatic continuation behavior
            tool_calling_instructions = """## TOOL CALLING BEHAVIOR

When you need to use tools to complete a task:
- You can provide brief commentary alongside tool calls (e.g., "Let me check that file..." or "I'll examine the code...")
- After tool calls complete and results are returned, AUTOMATICALLY continue - do not wait for user input
- Review tool results and either:
  * Make additional tool calls if more information is needed
  * Provide your final comprehensive response to the user
- Continue this loop automatically until you have a complete answer to provide
- Only provide a final text response (with no tool calls) when you're ready to answer the user's question
- The system will automatically continue after tool results are returned - you don't need to wait for explicit "proceed" or "continue" prompts"""
            
            combined_prompt = system_prompt
            if tool_calling_instructions not in system_prompt:
                combined_prompt = f"{system_prompt}\n\n{tool_calling_instructions}"
            self.messages.append({"role": "system", "content": combined_prompt})

        # Check if a system message actually exists in messages after initialization
        # This correctly reflects whether a system prompt is present regardless of
        # how it was created (via parameter or via _update_system_prompt)
        system_prompt_present = any(msg.get("role") == "system" for msg in self.messages)

        logger.info(
            "Conversation session started",
            extra={
                "event": "session_start",
                "system_prompt_present": system_prompt_present,
                "session_id": self.session_id,
                "storage_enabled": storage is not None,
                "tools_enabled": tool_registry is not None,
                "internal_sensing_enabled": internal_sensing_framework is not None,
                "world_state_enabled": world_state_aggregator is not None,
            },
        )
    
    @classmethod
    def from_storage(
        cls,
        session_id: str,
        storage: "ConversationStorage",
        tool_registry: Optional["ToolRegistry"] = None,
        internal_sensing_framework: Optional["InternalSensingFramework"] = None,
        world_state_aggregator: Optional["WorldStateAggregator"] = None,
        base_system_prompt: Optional[str] = None,
        color_manager: Optional[Any] = None,
    ) -> "ConversationSession":
        """Rehydrate a ConversationSession from stored conversation data.

        Loads messages and metadata from the given storage backend and constructs
        a ConversationSession instance bound to that session_id.

        If no stored conversation exists, this behaves like creating a fresh
        session with the provided session_id.
        """
        data = storage.load_conversation(session_id)

        # Create a bare session with explicit session_id and dependencies
        session = cls(
            system_prompt=None,
            llm=None,
            storage=storage,
            session_id=session_id,
            tool_registry=tool_registry,
            internal_sensing_framework=internal_sensing_framework,
            world_state_aggregator=world_state_aggregator,
            base_system_prompt=base_system_prompt,
            color_manager=color_manager,
        )

        if not data:
            return session

        messages = data.get("messages", [])
        metadata = data.get("metadata", {})

        # Validate loaded messages for contamination before processing
        # This is critical - we need to detect multiple system messages before they contaminate the session
        system_messages_in_load = [m for m in messages if m.get("role") == "system"]
        if len(system_messages_in_load) > 1:
            logger.warning(
                f"Loaded conversation has {len(system_messages_in_load)} system messages in from_storage(). "
                "This indicates contamination. All will be removed and rebuilt.",
                extra={
                    "event": "multiple_system_messages_in_from_storage",
                    "count": len(system_messages_in_load),
                }
            )

        # Restore messages but filter out ALL system messages - they will be rebuilt correctly by _update_system_prompt()
        # This prevents contamination from old system messages that may include world state/summary
        # CRITICAL: Filter ALL system messages, not just the first one
        session.messages = [m for m in messages if m.get("role") != "system"]
        
        # Validate that no system messages remain after filtering
        remaining_system = [m for m in session.messages if m.get("role") == "system"]
        if remaining_system:
            logger.error(
                f"CRITICAL: System messages still present after filtering in from_storage(): {len(remaining_system)}. "
                "This is a bug in the filtering logic.",
                extra={
                    "event": "system_messages_remain_after_from_storage_filtering",
                    "count": len(remaining_system),
                }
            )
            # Force remove any remaining system messages
            session.messages = [m for m in session.messages if m.get("role") != "system"]
        
        session.created_at = metadata.get("created_at", session.created_at)
        session.updated_at = metadata.get("updated_at", session.updated_at)

        # Extract base system prompt from metadata ONLY (never from system message content)
        # The system message content is contaminated with world state/summary and should not be used
        stored_base_prompt = metadata.get("system_prompt", "")
        
        # Clean contaminated base prompt if it contains JSON/world state
        if stored_base_prompt:
            cleaned_prompt = cls._clean_base_prompt(stored_base_prompt)
            if cleaned_prompt != stored_base_prompt:
                logger.warning(
                    "Cleaned contaminated base prompt from storage",
                    extra={
                        "event": "base_prompt_cleaned",
                        "original_length": len(stored_base_prompt),
                        "cleaned_length": len(cleaned_prompt),
                    }
                )
            stored_base_prompt = cleaned_prompt
        
        if stored_base_prompt and base_system_prompt is None:
            session.base_system_prompt = stored_base_prompt
        elif base_system_prompt is not None:
            # Use explicitly provided base prompt (also clean it)
            cleaned_provided = cls._clean_base_prompt(base_system_prompt)
            session.base_system_prompt = cleaned_provided

        # Validate that base prompt hasn't been contaminated
        if session.base_system_prompt:
            base_prompt = session.base_system_prompt
            if "{" in base_prompt and "\"timestamp\"" in base_prompt:
                logger.warning(
                    "Base system prompt appears to contain JSON (world state contamination detected). "
                    "This may cause unbounded growth.",
                    extra={
                        "event": "base_prompt_contamination_detected",
                        "base_prompt_size": len(base_prompt),
                        "base_prompt_preview": base_prompt[:200],
                    }
                )
            if "## Session Summary" in base_prompt or "Historical Context" in base_prompt:
                logger.warning(
                    "Base system prompt appears to contain summary content (contamination detected). "
                    "This may cause unbounded growth.",
                    extra={
                        "event": "base_prompt_summary_contamination_detected",
                        "base_prompt_size": len(base_prompt),
                        "base_prompt_preview": base_prompt[:200],
                    }
                )

        # Validate system message state before rebuilding
        # At this point, session.messages should have no system messages
        system_messages_before_rebuild = [m for m in session.messages if m.get("role") == "system"]
        if system_messages_before_rebuild:
            logger.error(
                f"CRITICAL: System messages found before rebuild in from_storage(): {len(system_messages_before_rebuild)}. "
                "Removing them before rebuilding.",
                extra={
                    "event": "system_messages_before_rebuild_in_from_storage",
                    "count": len(system_messages_before_rebuild),
                }
            )
            session.messages = [m for m in session.messages if m.get("role") != "system"]

        # If we have a world state aggregator, rebuild the system prompt correctly
        if session.world_state_aggregator and session._world_state_formatter:
            session._update_system_prompt()
        
        # Final validation after rebuild to ensure clean state
        session._ensure_single_system_message()
        
        # Rebuild context graph from loaded messages if enabled
        if session._context_graph:
            try:
                from ..config import config
                if config.context.enabled:
                    # Rebuild graph from existing messages
                    parent_id = None
                    for msg in session.messages:
                        if "message_id" not in msg:
                            msg["message_id"] = str(uuid.uuid4())
                        session._context_graph.add_message(
                            msg,
                            parent_id=parent_id,
                        )
                        parent_id = msg.get("message_id")
                    logger.debug(f"Rebuilt context graph from {len(session.messages)} loaded messages")
            except Exception as e:
                logger.warning(f"Failed to rebuild context graph from storage: {e}", exc_info=True)

        return session

    @property
    def base_system_prompt(self) -> Optional[str]:
        """
        Get the base system prompt (immutable after initialization).
        
        Returns:
            Base system prompt string or None
        """
        return getattr(self, '_base_system_prompt_internal', None)
    
    @base_system_prompt.setter
    def base_system_prompt(self, value: Optional[str]) -> None:
        """
        Set the base system prompt with immutability enforcement.
        
        Only allows modification during initialization. After initialization,
        modifications are logged as errors and prevented.
        """
        # Allow setting during initialization (before _base_prompt_initialized is set)
        if not hasattr(self, '_base_prompt_initialized') or not self._base_prompt_initialized:
            self._base_system_prompt_internal = value
            return
        
        # After initialization, prevent modification
        old_value = getattr(self, '_base_system_prompt_internal', None)
        if value != old_value:
            logger.error(
                f"Attempted to modify base_system_prompt after initialization! "
                f"This is not allowed and may cause unbounded growth. "
                f"Old size: {len(old_value) if old_value else 0}, "
                f"New size: {len(value) if value else 0}",
                extra={
                    "event": "base_prompt_modification_attempted",
                    "old_size": len(old_value) if old_value else 0,
                    "new_size": len(value) if value else 0,
                    "old_preview": old_value[:200] if old_value else None,
                    "new_preview": value[:200] if value else None,
                }
            )
            # Don't modify - keep the original value
            # This prevents contamination from propagating
    
    @property
    def tool_status_display(self):
        """
        Get the tool status display instance.
        
        Returns:
            ToolStatusDisplay instance or None if not available
        """
        return self._tool_status_display

    # ---------- Public API ----------

    def _ensure_response_non_empty(self, content: Optional[str]) -> str:
        """
        Helper method to ensure a response is never empty.
        
        Wraps ensure_non_empty() with proper trace_id handling.
        
        Args:
            content: The response content to check (may be None or empty string)
            
        Returns:
            Non-empty string (either original content or fallback message)
        """
        trace_id = getattr(self, "_current_response_id", None) or None
        return ensure_non_empty(content, trace_id=trace_id)

    def send(self, user_text: str, stream: bool = None) -> str:
        """
        Append a user message, call the LLM, handle tool calls if needed, and return final reply.

        Args:
            user_text: User's message
            stream: If True, streams the final response (after tool calls are resolved).
                   If None, uses config.llm.streaming_enabled. Default: None.

        Returns the assistant's final reply text after all tool calls are resolved.
        """
        self._log_context_before_turn(user_text=user_text)

        # Clear reasoning_content when starting a new user turn (prevents 400 errors)
        # For deepseek-reasoner, reasoning_content should only be used within a single turn
        if not hasattr(self, '_current_reasoning_content'):
            self._current_reasoning_content = None
        else:
            self._current_reasoning_content = None
        
        # Initialize thought_signature for Gemini 3 (persists across turns to maintain reasoning context)
        if not hasattr(self, '_current_thought_signature'):
            self._current_thought_signature = None

        # Log user message event
        user_event_id = None
        if self._event_logger:
            try:
                user_event_id = self._event_logger.log_user_message(self.session_id, user_text)
            except Exception as e:
                logger.warning(f"Failed to log user message event: {e}", exc_info=True)

        user_message = {"role": "user", "content": user_text}
        if user_event_id:
            user_message["event_ids"] = [user_event_id]
        
        # Add user message to context graph
        if self._context_graph:
            try:
                # Find parent (last message in graph)
                parent_id = None
                if self._context_graph._message_order:
                    parent_id = self._context_graph._message_order[-1]
                
                # Add message_id if not present
                if "message_id" not in user_message:
                    user_message["message_id"] = user_event_id or str(uuid.uuid4())
                
                self._context_graph.add_message(
                    user_message,
                    parent_id=parent_id,
                )
            except Exception as e:
                logger.warning(f"Failed to add user message to context graph: {e}", exc_info=True)
        
        self.messages.append(user_message)
        # Start a new tool-policy turn (for per-turn rate limits)
        if self.tool_registry and hasattr(self.tool_registry, "start_turn"):
            try:
                user_turns = sum(1 for m in self.messages if m.get("role") == "user")
                self.tool_registry.start_turn(user_turns)
            except Exception:
                pass

        # On-demand summarization command (no auto windowing)
        if user_text.strip().startswith("/summarize"):
            summary = self._summarize_history()
            summary = self._ensure_response_non_empty(summary)
            self.messages.append({"role": "assistant", "content": summary})
            self.updated_at = datetime.now(timezone.utc).isoformat()
            self._log_context_after_turn(assistant_text=summary, raw_response={})
            self._save_conversation()
            return summary

        # Instrumentation: Record attention and start latency timer
        if self.internal_sensing_framework and ResponseAnalyzer:
            try:
                # Extract topics from user input and context
                topics = ResponseAnalyzer.extract_topics(user_text, self.messages[-5:])
                for topic, level in topics.items():
                    self.internal_sensing_framework.interoception.cognition.record_attention(
                        topic, level
                    )

                # Start latency timer - store response_id for later use
                response_id = f"response_{len(self.messages)}"
                self._current_response_id = response_id  # Store it
                self.internal_sensing_framework.interoception.physiology._record_operation_start(
                    response_id
                )

                # Compute valence from conversation history BEFORE updating system prompt
                # This ensures valence is available when world state is sampled
                self.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                    self.messages
                )
                # Force a fresh sample to ensure updated valence is included in cached state
                # Reset last sample time to bypass rate limiting
                self.internal_sensing_framework._last_sample_time = 0.0
                self.internal_sensing_framework.sample_internal_state()
            except Exception as e:
                logger.debug(f"Error in pre-LLM instrumentation: {e}", exc_info=True)

        # Prepare tools for LLM if registry is available
        tools = None
        if self.tool_registry:
            tools = self.tool_registry.to_openai_format()
            tool_names = [tool["function"]["name"] for tool in tools]
            logger.info(
                f"Prepared {len(tools)} tools for LLM",
                extra={
                    "event": "tools_prepared",
                    "tool_count": len(tools),
                    "available_tools": tool_names,
                },
            )

        # Determine if streaming should be used (default from config if not specified)
        if stream is None:
            from ..config import config
            stream = config.llm.streaming_enabled
        
        # Track if we've had tool calls in this turn (affects streaming decision)
        had_tool_calls = False
        
        # Track reasoning_content for deepseek-reasoner model (cleared at start of turn)
        # Initialize if not already set (should be None at start of turn)
        if not hasattr(self, '_current_reasoning_content'):
            self._current_reasoning_content = None
        
        # Check if we're using reasoner model
        is_reasoner = hasattr(self.llm, 'is_reasoner_model') and self.llm.is_reasoner_model()
        
        # Check if we're using Gemini client (for thought_signature support)
        is_gemini = self._is_gemini_client()
        
        # Handle tool calls iteratively (may require multiple LLM calls)
        iterations = 0
        response = None
        # Track last warning iteration to prevent duplicate warnings at the same threshold
        last_warning_iteration = 0
        while iterations < self._max_tool_iterations:
            iterations += 1

            # Update system prompt with current world state before each LLM call
            self._update_system_prompt()
            
            # Check for loop conditions and inject warnings if needed
            # Do this before getting messages for LLM so warnings are included
            warning_thresholds = [10, 20, 30, 50, 75, 90]
            should_warn = False
            warning_message = None
            loop_info = None
            
            # Check if we've reached a warning threshold (and haven't warned at this threshold yet)
            for threshold in warning_thresholds:
                if iterations >= threshold and last_warning_iteration < threshold:
                    should_warn = True
                    last_warning_iteration = threshold
                    
                    # Detect loops
                    loop_info = self._detect_tool_call_loop(iterations)
                    
                    # Generate warning message based on severity
                    if iterations >= 75:
                        severity = "CRITICAL"
                        urgency = "MUST"
                    elif iterations >= 50:
                        severity = "CRITICAL"
                        urgency = "MUST"
                    elif iterations >= 30:
                        severity = "HIGH"
                        urgency = "should"
                    else:
                        severity = "MEDIUM"
                        urgency = "should"
                    
                    if loop_info:
                        # Loop detected - include loop information in warning
                        tool_name = loop_info["tool_name"]
                        repeat_count = loop_info["repeat_count"]
                        pattern = loop_info["pattern_description"]
                        warning_message = (
                            f"[SYSTEM DIRECTIVE - {severity} WARNING] You are on iteration {iterations}. "
                            f"A loop has been detected: {pattern}. You {urgency} break out of this loop. "
                            "Review the tool results you've received and either:\n"
                            "- Make different tool calls if you need different information\n"
                            "- Provide your final comprehensive response to the user if you have enough information\n"
                            "Do not continue making the same tool calls repeatedly. The system automatically continues "
                            "after tool results - you should review results and respond accordingly."
                        )
                    else:
                        # High iteration count but no clear loop pattern detected
                        if iterations >= 50:
                            warning_message = (
                                f"[SYSTEM DIRECTIVE - {severity} WARNING] Very high iteration count ({iterations}). "
                                f"You {urgency} provide a final response to the user. Review all tool results you've received "
                                "and provide a comprehensive answer. The system automatically continues after tool results - "
                                "you should respond with your final answer, not wait for user input."
                            )
                        elif iterations >= 30:
                            warning_message = (
                                f"[SYSTEM DIRECTIVE - {severity} WARNING] High iteration count ({iterations}). "
                                "You may be stuck in a loop. Review tool results and either make different tool calls "
                                "if needed, or provide your final response. The system automatically continues - "
                                "you should respond based on tool results, not wait for user prompts."
                            )
                        else:
                            warning_message = (
                                f"[SYSTEM DIRECTIVE - {severity} WARNING] You're on iteration {iterations}. "
                                "Consider if your current approach is working. If you're making progress with tool calls, continue. "
                                "If you have enough information from tool results, provide your final response. "
                                "Remember: the system automatically continues after tool results - review them and respond accordingly."
                            )
                    
                    break  # Only warn at one threshold per iteration
            
            # Inject warning if needed
            if should_warn and warning_message:
                logger.warning(
                    f"Injecting iteration warning at iteration {iterations}",
                    extra={
                        "event": "iteration_warning_injected",
                        "iteration": iterations,
                        "threshold": last_warning_iteration,
                        "loop_detected": loop_info is not None,
                    }
                )
                # Inject as user message (same pattern as critic rejection handling)
                # This prevents system message accumulation issues
                self.messages.append({
                    "role": "user",
                    "content": warning_message,
                })

            # Track if we used streaming (for later use)
            used_streaming = False
            assistant_text = None  # Will be set during streaming or extracted later
            
            try:
                # Determine if we should use streaming
                # We can always stream if streaming is enabled and the LLM supports it
                # Even with tools, we can stream - we'll check for tool calls after the stream completes
                # Streaming with tools: The API will still stream content, and tool calls can be detected from finish_reason
                # Determine whether this particular LLM call should include tools.
                # Enable streaming if available - the code handles tool_calls detection
                # from streaming responses (see lines 291-300 below for fallback logic).
                tools_for_call = tools
                can_stream = stream and hasattr(self.llm, "chat_stream")
                use_streaming = can_stream
                
                # Log streaming decision for debugging
                if stream and not hasattr(self.llm, "chat_stream"):
                    logger.debug(f"Streaming requested but LLM client doesn't support chat_stream method")
                elif stream and can_stream:
                    logger.debug(f"Streaming enabled for this LLM call (iteration {iterations})")
                elif not stream:
                    logger.debug(f"Streaming disabled (stream={stream})")
                
                if use_streaming:
                    # Streaming mode - try streaming first
                    assistant_text = ""
                    prompt_printed = False  # Track if we've printed the prompt yet
                    
                    # Get streaming delay from config
                    from ..config import config
                    streaming_delay = config.llm.streaming_delay
                    
                    # Try to flush any pending input before streaming starts
                    # This prevents interference from any characters already typed
                    try:
                        import select
                        if HAS_TERMIOS and sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
                            # Discard any pending input
                            termios.tcflush(sys.stdin, termios.TCIFLUSH)
                    except (ImportError, termios.error, OSError, AttributeError):
                        # If select or termios flush not available, just continue
                        # This is a best-effort attempt to prevent input interference
                        pass
                    
                    try:
                        # Stream the response - works even with tools available
                        # If tools are used, the stream will yield empty/minimal content, and we'll detect tool_calls after
                        messages_for_llm = self._get_messages_for_llm()
                        messages_for_llm = self._validate_message_size(messages_for_llm)
                        
                        # Validate message ordering before sending to API (Gemini-specific if using Gemini)
                        is_valid, error = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                        if not is_valid:
                            logger.warning(
                                f"Invalid message ordering detected before streaming LLM call: {error}. "
                                "Attempting to fix by removing orphaned tool messages."
                            )
                            messages_for_llm = self._fix_tool_message_ordering(messages_for_llm)
                            # Apply Gemini-specific fix if needed
                            if is_gemini:
                                messages_for_llm = self._fix_gemini_tool_call_ordering(messages_for_llm)
                            # Re-validate after fixing
                            is_valid_after, error_after = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                            if not is_valid_after:
                                logger.error(
                                    f"Message ordering still invalid after fix: {error_after}. "
                                    "Proceeding anyway, but API call may fail."
                                )
                        else:
                            # Even if validation passes, apply fix as safety measure
                            # This ensures orphaned tool messages are removed even if validation misses them
                            original_count = len(messages_for_llm)
                            messages_for_llm = self._fix_tool_message_ordering(messages_for_llm)
                            if len(messages_for_llm) < original_count:
                                logger.info(
                                    f"Fix removed {original_count - len(messages_for_llm)} orphaned tool message(s) "
                                    "even though validation passed (safety measure)"
                                )
                        
                        # Log message structure before API call (for debugging)
                        if is_gemini:
                            msg_structure = [
                                f"{i}:{msg.get('role', 'unknown')}" + 
                                (f"[tool_calls={len(msg.get('tool_calls', []))}]" if msg.get('tool_calls') else "") +
                                (f"[tool_call_id={msg.get('tool_call_id', '')[:15]}]" if msg.get('tool_call_id') else "")
                                for i, msg in enumerate(messages_for_llm[:15])
                            ]
                            logger.info(
                                "Sending messages to Gemini API (streaming)",
                                extra={
                                    "event": "gemini_api_call_pre",
                                    "iteration": iterations,
                                    "messages_count": len(messages_for_llm),
                                    "message_structure": " -> ".join(msg_structure) + ("..." if len(messages_for_llm) > 15 else ""),
                                    "validation_passed": is_valid,
                                }
                            )
                        
                        logger.debug(f"Starting streaming request (iteration {iterations}, has_tools={bool(tools)})")
                        
                        if tools:
                            stream_gen = self.llm.chat_stream(
                                messages_for_llm, 
                                tools=tools,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None,
                                thought_signature=self._current_thought_signature if is_gemini else None
                            )
                        else:
                            stream_gen = self.llm.chat_stream(
                                messages_for_llm,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None,
                                thought_signature=self._current_thought_signature if is_gemini else None
                            )
                        
                        # Collect streaming chunks and print them immediately as they arrive
                        chunk_count = 0
                        for chunk in stream_gen:
                            chunk_count += 1
                            
                            # Repair broken ANSI escape sequences in chunk before accumulating and printing
                            chunk = repair_ansi_codes(chunk)
                            assistant_text += chunk
                            
                            # Print prompt on first chunk only
                            if not prompt_printed:
                                prompt = "BrocaOS> "
                                if self._color_manager:
                                    prompt = self._color_manager.colorize(prompt, "brocaos_prompt")
                                print(prompt, end="", flush=True)
                                prompt_printed = True
                            
                            # Colorize response text chunks
                            if self._color_manager:
                                colored_chunk = self._color_manager.colorize(chunk, "response_text")
                                print(colored_chunk, end="", flush=True)
                            else:
                                print(chunk, end="", flush=True)
                            
                            # Apply delay between chunks if configured
                            if streaming_delay > 0:
                                time.sleep(streaming_delay)
                        
                        logger.debug(f"Streaming completed: {chunk_count} chunks received, prompt_printed={prompt_printed}")
                        
                        # Only print newline if we actually printed content
                        if prompt_printed:
                            print("", flush=True)  # New line after streaming
                        # If streaming produced no visible content (no chunks or only whitespace),
                        # we need to extract from response dict or fall back to non-streaming
                        if chunk_count == 0 or (isinstance(assistant_text, str) and assistant_text.strip() == ""):
                            # No chunks received - try to extract from response dict if available
                            # Otherwise, we'll fall back to non-streaming below
                            assistant_text = None
                            # Mark that streaming didn't actually produce content
                            used_streaming = False
                        else:
                            used_streaming = True
                        
                        # If no chunks were received, log a warning
                        if chunk_count == 0 and tools:
                            logger.debug("Streaming completed but no content chunks received (possible tool calls)")
                        
                        # Build response dict for compatibility with existing code
                        # Note: If tool calls were made, assistant_text will be empty/minimal
                        # We'll detect tool_calls from a separate check after streaming
                        response = {
                            "choices": [{
                                "message": {
                                    "content": assistant_text if assistant_text else None,
                                    "role": "assistant"
                                }
                            }]
                        }
                        
                        # If we streamed but got no/minimal content and tools are available,
                        # make a non-streaming call to get tool_calls properly
                        # This handles the case where LLM chose to use tools instead of responding
                        if tools and (not assistant_text or len(assistant_text.strip()) < 10):
                            logger.debug("Streamed response had minimal content with tools available, checking for tool_calls")
                            # Make a non-streaming call to check for tool_calls
                            messages_for_llm = self._get_messages_for_llm()
                            messages_for_llm = self._validate_message_size(messages_for_llm)
                            
                            # Validate message ordering before sending to API (Gemini-specific if using Gemini)
                            is_valid, error = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                            if not is_valid:
                                logger.warning(
                                    f"Invalid message ordering detected before tool_calls check: {error}. "
                                    "Attempting to fix by removing orphaned tool messages."
                                )
                                messages_for_llm = self._fix_tool_message_ordering(messages_for_llm)
                                # Apply Gemini-specific fix if needed
                                if is_gemini:
                                    messages_for_llm = self._fix_gemini_tool_call_ordering(messages_for_llm)
                                # Re-validate after fixing
                                is_valid_after, error_after = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                                if not is_valid_after:
                                    logger.error(
                                        f"Message ordering still invalid after fix: {error_after}. "
                                        "Proceeding anyway, but API call may fail."
                                    )
                            
                            # Log message structure before API call (for debugging)
                            if is_gemini:
                                msg_structure = [
                                    f"{i}:{msg.get('role', 'unknown')}" + 
                                    (f"[tool_calls={len(msg.get('tool_calls', []))}]" if msg.get('tool_calls') else "") +
                                    (f"[tool_call_id={msg.get('tool_call_id', '')[:15]}]" if msg.get('tool_call_id') else "")
                                    for i, msg in enumerate(messages_for_llm[:15])
                                ]
                                logger.info(
                                    "Sending messages to Gemini API (tool_calls check)",
                                    extra={
                                        "event": "gemini_api_call_pre",
                                        "iteration": iterations,
                                        "messages_count": len(messages_for_llm),
                                        "message_structure": " -> ".join(msg_structure) + ("..." if len(messages_for_llm) > 15 else ""),
                                        "validation_passed": is_valid,
                                    }
                                )
                            
                            non_stream_response = self.llm.chat(
                                messages_for_llm, 
                                tools=tools,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None,
                                thought_signature=self._current_thought_signature if is_gemini else None
                            )
                            tool_calls_from_response = self.llm.extract_tool_calls(non_stream_response)
                            if tool_calls_from_response:
                                # Update response with tool_calls
                                response["choices"][0]["message"]["tool_calls"] = tool_calls_from_response
                                response["choices"][0]["message"]["content"] = None  # No content when tool_calls exist
                                assistant_text = None  # Clear assistant_text since we have tool_calls
                    except Exception as e:
                        # Fall back to non-streaming on error
                        logger.warning(
                            f"Streaming failed, falling back to non-streaming: {e}",
                            exc_info=True,
                            extra={
                                "event": "streaming_failed",
                                "iteration": iterations,
                                "error_type": type(e).__name__,
                                "error_message": str(e)
                            }
                        )
                        assistant_text = None  # Reset so it gets extracted from response
                        used_streaming = False  # Mark that we're not using streaming anymore
                        messages_for_llm = self._get_messages_for_llm()
                        messages_for_llm = self._validate_message_size(messages_for_llm)
                        
                        # Validate message ordering before sending to API
                        is_valid, error = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                        if not is_valid:
                            logger.warning(
                                f"Invalid message ordering detected before LLM call: {error}. "
                                "Attempting to fix by removing orphaned tool messages."
                            )
                            messages_for_llm = self._fix_tool_message_ordering(messages_for_llm)
                            # Apply Gemini-specific fix if needed
                            if is_gemini:
                                messages_for_llm = self._fix_gemini_tool_call_ordering(messages_for_llm)
                            # Re-validate after fixing
                            is_valid_after, error_after = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                            if not is_valid_after:
                                logger.error(
                                    f"Message ordering still invalid after fix: {error_after}. "
                                    "Proceeding anyway, but API call may fail."
                                )
                        
                        # Log message structure before API call (for debugging)
                        if is_gemini:
                            msg_structure = [
                                f"{i}:{msg.get('role', 'unknown')}" + 
                                (f"[tool_calls={len(msg.get('tool_calls', []))}]" if msg.get('tool_calls') else "") +
                                (f"[tool_call_id={msg.get('tool_call_id', '')[:15]}]" if msg.get('tool_call_id') else "")
                                for i, msg in enumerate(messages_for_llm[:15])
                            ]
                            logger.info(
                                "Sending messages to Gemini API (fallback non-streaming)",
                                extra={
                                    "event": "gemini_api_call_pre",
                                    "iteration": iterations,
                                    "messages_count": len(messages_for_llm),
                                    "message_structure": " -> ".join(msg_structure) + ("..." if len(messages_for_llm) > 15 else ""),
                                    "validation_passed": is_valid,
                                }
                            )
                        
                        if tools:
                            response = self.llm.chat(
                                messages_for_llm, 
                                tools=tools,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None,
                                thought_signature=self._current_thought_signature if is_gemini else None
                            )
                        else:
                            response = self.llm.chat(
                                messages_for_llm,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None,
                                thought_signature=self._current_thought_signature if is_gemini else None
                            )
                    finally:
                        # No terminal settings to restore since we only flushed input
                        pass
                else:
                    # Non-streaming mode (when streaming disabled)
                    messages_for_llm = self._get_messages_for_llm()
                    messages_for_llm = self._validate_message_size(messages_for_llm)
                    
                    # Validate message ordering before sending to API
                    is_valid, error = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                    if not is_valid:
                        logger.warning(
                            f"Invalid message ordering detected before LLM call: {error}. "
                            "Attempting to fix by removing orphaned tool messages."
                        )
                        messages_for_llm = self._fix_tool_message_ordering(messages_for_llm)
                        # Apply Gemini-specific fix if needed
                        if is_gemini:
                            messages_for_llm = self._fix_gemini_tool_call_ordering(messages_for_llm)
                        # Re-validate after fixing
                        is_valid_after, error_after = self._validate_message_ordering(messages_for_llm, check_gemini_ordering=is_gemini)
                        if not is_valid_after:
                            logger.error(
                                f"Message ordering still invalid after fix: {error_after}. "
                                "Proceeding anyway, but API call may fail."
                            )
                    
                    # Log message structure before API call (for debugging)
                    if is_gemini:
                        msg_structure = [
                            f"{i}:{msg.get('role', 'unknown')}" + 
                            (f"[tool_calls={len(msg.get('tool_calls', []))}]" if msg.get('tool_calls') else "") +
                            (f"[tool_call_id={msg.get('tool_call_id', '')[:15]}]" if msg.get('tool_call_id') else "")
                            for i, msg in enumerate(messages_for_llm[:15])
                        ]
                        logger.info(
                            "Sending messages to Gemini API (non-streaming)",
                            extra={
                                "event": "gemini_api_call_pre",
                                "iteration": iterations,
                                "messages_count": len(messages_for_llm),
                                "message_structure": " -> ".join(msg_structure) + ("..." if len(messages_for_llm) > 15 else ""),
                                "validation_passed": is_valid,
                            }
                        )
                    
                    if tools:
                        response = self.llm.chat(
                            messages_for_llm, 
                            tools=tools,
                            reasoning_content=self._current_reasoning_content if is_reasoner else None,
                            thought_signature=self._current_thought_signature if is_gemini else None
                        )
                    else:
                        response = self.llm.chat(
                            messages_for_llm,
                            reasoning_content=self._current_reasoning_content if is_reasoner else None,
                            thought_signature=self._current_thought_signature if is_gemini else None
                        )
            except TimeoutError as e:
                logger.error(f"LLM request timed out: {e}", exc_info=True)
                error_message = (
                    "I apologize, but the API request timed out. This can happen with "
                    "large conversations or when the API is slow. You may want to try "
                    "using /reset to clear the conversation history, or try again."
                )
                trace = getattr(self, "_current_response_id", None) or str(__import__('uuid').uuid4())
                error_with_trace = f"{error_message} TraceID: {trace}"
                error_with_trace = self._ensure_response_non_empty(error_with_trace)
                self.messages.append({"role": "assistant", "content": error_with_trace})
                self.updated_at = datetime.now(timezone.utc).isoformat()
                # Log conversation turn completion even on error
                self._log_context_after_turn(
                    assistant_text=error_with_trace, raw_response={}
                )
                self._save_conversation()
                return error_with_trace
            except ConnectionError as e:
                logger.error(f"Network error during LLM request: {e}", exc_info=True)
                error_message = (
                    "I apologize, but there was a network error connecting to the API. "
                    "Please check your internet connection and try again."
                )
                trace = getattr(self, "_current_response_id", None) or str(__import__('uuid').uuid4())
                error_with_trace = f"{error_message} TraceID: {trace}"
                error_with_trace = self._ensure_response_non_empty(error_with_trace)
                self.messages.append({"role": "assistant", "content": error_with_trace})
                self.updated_at = datetime.now(timezone.utc).isoformat()
                # Log conversation turn completion even on error
                self._log_context_after_turn(
                    assistant_text=error_with_trace, raw_response={}
                )
                self._save_conversation()
                return error_with_trace
            except Exception as e:
                logger.error(f"Unexpected error during LLM request: {e}", exc_info=True)
                error_message = (
                    f"I apologize, but an unexpected error occurred: {str(e)}. "
                    "Please try again or use /reset to clear the conversation."
                )
                trace = getattr(self, "_current_response_id", None) or str(__import__('uuid').uuid4())
                error_with_trace = f"{error_message} TraceID: {trace}"
                error_with_trace = self._ensure_response_non_empty(error_with_trace)
                self.messages.append({"role": "assistant", "content": error_with_trace})
                self.updated_at = datetime.now(timezone.utc).isoformat()
                # Log conversation turn completion even on error
                self._log_context_after_turn(
                    assistant_text=error_with_trace, raw_response={}
                )
                self._save_conversation()
                return error_with_trace

            # Extract tool calls if any (needed for logging below)
            extract_tool_calls = getattr(self.llm, 'extract_tool_calls', lambda resp: [])
            tool_calls = extract_tool_calls(response) or []

            # Extract reasoning_content for reasoner model (if present)
            # Always try to extract, even if None (for logging purposes)
            if is_reasoner and hasattr(self.llm, 'extract_reasoning_content'):
                extracted_reasoning = self.llm.extract_reasoning_content(response)
                if extracted_reasoning:
                    self._current_reasoning_content = extracted_reasoning
                    # Only call len() if it's actually a string/sequence, not a Mock
                    try:
                        reasoning_length = len(extracted_reasoning)
                    except TypeError:
                        # Mock objects or other non-sequence types
                        reasoning_length = 0
                    logger.info(
                        "Extracted reasoning_content from reasoner response",
                        extra={
                            "event": "reasoning_content_extracted",
                            "iteration": iterations,
                            "reasoning_length": reasoning_length,
                            "has_tool_calls": bool(tool_calls),
                        }
                    )
                else:
                    # No reasoning_content in response - this is OK for first request
                    # But we'll need to ensure assistant messages with tool_calls have the field
                    logger.debug(
                        "No reasoning_content in reasoner response",
                        extra={
                            "event": "no_reasoning_content_in_response",
                            "iteration": iterations,
                            "has_tool_calls": bool(tool_calls),
                        }
                    )
                    # Initialize to empty string if we have tool_calls (field must exist)
                    if tool_calls and not hasattr(self, '_current_reasoning_content'):
                        self._current_reasoning_content = ""
            
            # Extract thought_signature for Gemini 3 (if present)
            # Thought signature persists across turns to maintain reasoning context
            if is_gemini and hasattr(self.llm, 'extract_thought_signature'):
                extracted_sig = self.llm.extract_thought_signature(response)
                if extracted_sig:
                    self._current_thought_signature = extracted_sig
                    logger.info(
                        "Extracted thought_signature from Gemini response",
                        extra={
                            "event": "thought_signature_extracted",
                            "iteration": iterations,
                            "has_tool_calls": bool(tool_calls),
                        }
                    )
                else:
                    logger.debug(
                        "No thought_signature in Gemini response",
                        extra={
                            "event": "no_thought_signature_in_response",
                            "iteration": iterations,
                            "has_tool_calls": bool(tool_calls),
                        }
                    )

            # Instrumentation: Track processing depth from tool calls
            if self.internal_sensing_framework and tool_calls:
                try:
                    processing_depth = len(tool_calls) + iterations - 1
                    self.internal_sensing_framework.interoception.cognition.record_processing_depth(
                        f"turn_{iterations}", processing_depth
                    )
                except Exception as e:
                    logger.debug(f"Error tracking processing depth: {e}", exc_info=True)

            # If we didn't stream and got a non-streaming response, extract assistant text
            if not used_streaming and assistant_text is None:
                assistant_text = self.llm.extract_assistant_content(response) or None
                # Normalize empty string to None so guard can catch it
                if assistant_text == "":
                    assistant_text = None
                # Repair broken ANSI escape sequences in extracted text
                if assistant_text:
                    assistant_text = repair_ansi_codes(assistant_text)

            if tool_calls and self.tool_registry:
                # Mark that we've had tool calls
                had_tool_calls = True
                
                # Log tool calls detected
                tool_names = [
                    tc.get("function", {}).get("name", "unknown") for tc in tool_calls
                ]
                logger.info(
                    f"Tool calls detected in LLM response (iteration {iterations})",
                    extra={
                        "event": "tool_calls_detected",
                        "tool_calls_count": len(tool_calls),
                        "tool_names": tool_names,
                        "iteration": iterations,
                    },
                )
                # Handle tool calls
                self._handle_tool_calls(response, tool_calls)

                # Note: We don't enforce critic iteration immediately after tool calls.
                # This allows the LLM to use other tools (terminal, web_search, etc.) to
                # gather information before calling the critic again.
                # Enforcement only happens when the LLM attempts a final response.

                # Log that we're continuing with reasoning_content
                if is_reasoner and self._current_reasoning_content:
                    # Safely get reasoning content length, handling Mock objects
                    try:
                        reasoning_length = len(self._current_reasoning_content) if isinstance(self._current_reasoning_content, (str, bytes, list, tuple)) else 0
                    except (TypeError, AttributeError):
                        reasoning_length = 0
                    logger.info(
                        f"Continuing tool iteration {iterations + 1} with reasoning_content",
                        extra={
                            "event": "tool_iteration_continue",
                            "current_iteration": iterations,
                            "next_iteration": iterations + 1,
                            "reasoning_content_length": reasoning_length,
                            "messages_count": len(self.messages),
                        }
                    )

                # Verify tool results were added to messages before continuing
                # This ensures the next LLM call receives complete context
                # Count tool results that were just added (should match number of tool calls)
                tool_results_count = sum(1 for msg in self.messages if msg.get("role") == "tool")
                logger.debug(
                    f"Continuing after tool calls: {len(tool_calls)} tool calls made, {tool_results_count} total tool results in messages",
                    extra={
                        "event": "auto_continuation_after_tools",
                        "iteration": iterations,
                        "tool_calls_count": len(tool_calls),
                        "tool_results_count": tool_results_count,
                        "messages_count": len(self.messages),
                    }
                )
                
                # Continue loop to get LLM response with tool results
                # The reasoning_content extracted above will be passed in the next iteration
                # The LLM will automatically receive tool results and should continue without waiting for user input
                continue
            else:
                # No tool calls - extract final response
                logger.info(f"NO TOOL CALLS: Reached final response path (iteration {iterations}), will run post-processing")
                if iterations > 1:
                    logger.info(
                        f"Final LLM response after {iterations} tool iteration(s)",
                        extra={
                            "event": "final_response_after_tools",
                            "iterations": iterations,
                        },
                    )

                # Extract assistant text - if we used streaming, it's already in assistant_text
                # But make sure we have it even if streaming was used (fallback)
                if assistant_text is None:
                    logger.debug(f"Extracting assistant text from response (used_streaming={used_streaming})")
                    assistant_text = self.llm.extract_assistant_content(response) or None
                    logger.debug(f"Extracted assistant_text length: {len(assistant_text) if assistant_text else 0}")
                    # Normalize empty string to None so guard can catch it
                    if assistant_text == "":
                        assistant_text = None
                        logger.debug("Normalized empty string to None for assistant_text")
                    # Repair broken ANSI escape sequences in extracted text
                    if assistant_text:
                        assistant_text = repair_ansi_codes(assistant_text)
                else:
                    logger.debug(f"Using existing assistant_text (length={len(assistant_text) if assistant_text else 0}, used_streaming={used_streaming})")
                
                # Ensure response is always printed
                if used_streaming:
                    # If we streamed, content was already printed chunk by chunk (if any)
                    # The prompt was only printed if chunks were received, and newline only if prompt was printed
                    # If no chunks were received, nothing was printed (no empty prompt line)
                    # Empty responses are handled by response guard which injects a fallback
                    pass  # Streaming output handling is complete
                else:
                    # Non-streaming: print with prompt only if we have content
                    # Response guard ensures assistant_text is never None/empty, but check anyway
                    if assistant_text:
                        prompt = "BrocaOS> "
                        if self._color_manager:
                            prompt = self._color_manager.colorize(prompt, "brocaos_prompt")
                        
                        # Colorize response text
                        if self._color_manager:
                            colored_text = self._color_manager.colorize(assistant_text, "response_text")
                            print(f"{prompt}{colored_text}\n", end="", flush=True)
                        else:
                            print(f"{prompt}{assistant_text}\n", end="", flush=True)
                    # If assistant_text is None/empty, response guard should have injected fallback
                    # but if it didn't for some reason, don't print empty prompt line

                # Log assistant message event
                assistant_event_id = None
                if self._event_logger:
                    try:
                        assistant_event_id = self._event_logger.log_assistant_message(self.session_id, assistant_text)
                    except Exception as e:
                        logger.warning(f"Failed to log assistant message event: {e}", exc_info=True)

                # Add message to conversation history immediately
                assistant_message = {"role": "assistant", "content": assistant_text}
                if assistant_event_id:
                    assistant_message["event_ids"] = [assistant_event_id]
                self.messages.append(assistant_message)
                self.updated_at = datetime.now(timezone.utc).isoformat()
                
                # Measure cognitive dissonance if available
                if self.world_state_aggregator and hasattr(self.world_state_aggregator, 'reasoning_tool'):
                    reasoning_tool = self.world_state_aggregator.reasoning_tool
                    if reasoning_tool and hasattr(reasoning_tool, 'cognitive_dissonance_monitor'):
                        cognitive_dissonance_monitor = reasoning_tool.cognitive_dissonance_monitor
                        if cognitive_dissonance_monitor:
                            try:
                                # Extract tool usage from messages
                                tool_usage = []
                                for msg in self.messages[-20:]:  # Check last 20 messages
                                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                                        tool_usage.extend(msg.get("tool_calls", []))
                                
                                # Measure dissonance
                                conversation_context = [
                                    {"role": m.get("role"), "content": m.get("content", "")[:200]}
                                    for m in self.messages[-5:]
                                ]
                                
                                cognitive_dissonance_monitor.measure_dissonance(
                                    response=assistant_text,
                                    conversation_context=conversation_context,
                                    tool_usage=tool_usage if tool_usage else None
                                )
                            except Exception as e:
                                logger.debug(f"Error measuring cognitive dissonance: {e}", exc_info=True)
                
                # Update context graph with new message
                if self._context_graph:
                    try:
                        # Add assistant message to graph
                        # Find parent (last user message or last assistant message)
                        parent_id = None
                        if len(self.messages) > 1:
                            # Look backwards for the most recent message
                            for i in range(len(self.messages) - 2, -1, -1):
                                prev_msg = self.messages[i]
                                if prev_msg.get("role") in ["user", "assistant"]:
                                    # Try to find message_id in previous message
                                    parent_id = prev_msg.get("message_id")
                                    if not parent_id and i < len(self._context_graph._message_order):
                                        # Use message order as fallback
                                        parent_id = self._context_graph._message_order[i] if i < len(self._context_graph._message_order) else None
                                    break
                        
                        # Add message with message_id if available
                        msg_with_id = assistant_message.copy()
                        if "message_id" not in msg_with_id:
                            msg_with_id["message_id"] = assistant_event_id or str(uuid.uuid4())
                        
                        self._context_graph.add_message(
                            msg_with_id,
                            parent_id=parent_id,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update context graph: {e}", exc_info=True)
                
                # Automatic summarization is disabled - only manual /summarize command works
                # Increment turn counter for manual summarization tracking only
                self._turns_since_last_summary += 1

                # Persist immediately so callers (and tests) can observe saved state
                try:
                    self._save_conversation()
                except Exception:
                    pass

                # Do post-processing (instrumentation and logging)
                # Run synchronously for ALL responses to ensure metrics are recorded before function returns.
                # This ensures metrics are available when world state is aggregated in the next turn.
                # Note: Streaming output has already been displayed, so this won't block user-facing output.
                logger.info(f"POST-PROCESSING: Starting instrumentation (has_framework={self.internal_sensing_framework is not None}, has_analyzer={ResponseAnalyzer is not None}, has_assistant_text={assistant_text is not None and len(str(assistant_text)) if assistant_text else 0})")
                # CRITICAL: Always record SOMETHING to show system is active, even if values are neutral
                # This ensures the moving average history is populated and values are not stuck at defaults
                # CRITICAL: This block MUST run to update the system prompt with latest values
                try:
                    # Instrumentation: Record metrics from response
                    # Record metrics even when assistant_text is empty (e.g., tool-only responses)
                    # This ensures metrics update from defaults even when only tool calls occur
                    if not self.internal_sensing_framework:
                        logger.error("CRITICAL: internal_sensing_framework is None, skipping instrumentation - THIS IS WHY VALUES ARE STUCK AT DEFAULTS")
                    elif not ResponseAnalyzer:
                        logger.error("CRITICAL: ResponseAnalyzer is None, skipping instrumentation - THIS IS WHY VALUES ARE STUCK AT DEFAULTS")
                    else:
                        # Both are available, proceed with instrumentation
                        logger.info(f"INSTRUMENTATION: Starting recording (assistant_text length: {len(assistant_text) if assistant_text else 0})")
                        try:
                            # Use the stored response_id instead of recalculating
                            response_id = getattr(
                                self,
                                "_current_response_id",
                                f"response_{len(self.messages)}",
                            )

                            logger.info(f"INSTRUMENTATION: Recording metrics for response_id={response_id}, has_assistant_text={bool(assistant_text)}, assistant_text_length={len(assistant_text) if assistant_text else 0}")

                            # Record latency
                            latency = self.internal_sensing_framework.interoception.physiology._record_operation_end(
                                response_id
                            )
                            if latency is not None and latency > 0:
                                normalized_latency = self.internal_sensing_framework.interoception.physiology._normalize_latency(
                                    latency
                                )
                                if normalized_latency is not None:
                                    self.internal_sensing_framework.interoception.physiology.metrics[
                                        "processing_latency"
                                    ] = normalized_latency

                            # Only analyze text-based metrics if assistant_text is available
                            confidence = None
                            uncertainty = None
                            if assistant_text:
                                # Estimate confidence from response
                                confidence = ResponseAnalyzer.estimate_confidence(
                                    assistant_text
                                )
                                if confidence is not None:
                                    history_len_before = len(self.internal_sensing_framework.interoception.cognition._confidence_history)
                                    logger.info(f"RECORDING CONFIDENCE: {confidence:.3f} for response_id={response_id} (text_length={len(assistant_text)}, history_len_before={history_len_before})")
                                    self.internal_sensing_framework.interoception.cognition.record_confidence(
                                        response_id, confidence
                                    )
                                    # Verify it was recorded
                                    state_after = self.internal_sensing_framework.interoception.cognition.sample_cognitive_state()
                                    history_len_after = len(self.internal_sensing_framework.interoception.cognition._confidence_history)
                                    logger.info(f"CONFIDENCE AFTER RECORDING: {state_after['confidence_level']:.3f} (history_len: {history_len_before} -> {history_len_after}, moving_avg)")
                                    # Save state after recording
                                    try:
                                        self.internal_sensing_framework.save_state()
                                    except Exception as e:
                                        logger.warning(f"Failed to save state after confidence recording: {e}", exc_info=True)
                                else:
                                    # Use neutral confidence for tool-only responses
                                    logger.warning(f"No confidence computed from text, using neutral 0.5 for response_id={response_id}")
                                    self.internal_sensing_framework.interoception.cognition.record_confidence(
                                        response_id, 0.5
                                    )
                                    confidence = 0.5

                                # Detect uncertainty
                                uncertainty = ResponseAnalyzer.detect_uncertainty(
                                    assistant_text
                                )
                                if uncertainty is not None:
                                    history_len_before = len(self.internal_sensing_framework.interoception.cognition._uncertainty_history)
                                    logger.info(f"RECORDING UNCERTAINTY: {uncertainty:.3f} for response_id={response_id} (history_len_before={history_len_before})")
                                    self.internal_sensing_framework.interoception.cognition.record_uncertainty(
                                        response_id, uncertainty
                                    )
                                    # Verify it was recorded
                                    state_after = self.internal_sensing_framework.interoception.cognition.sample_cognitive_state()
                                    history_len_after = len(self.internal_sensing_framework.interoception.cognition._uncertainty_history)
                                    logger.info(f"UNCERTAINTY AFTER RECORDING: {state_after['uncertainty_tracking']:.3f} (history_len: {history_len_before} -> {history_len_after}, moving_avg)")
                                    # Save state after recording
                                    try:
                                        self.internal_sensing_framework.save_state()
                                    except Exception as e:
                                        logger.warning(f"Failed to save state after uncertainty recording: {e}", exc_info=True)
                            else:
                                # Tool-only response: use neutral/default values but still record
                                logger.info(f"Tool-only response detected (no assistant_text), recording neutral metrics for response_id={response_id}")
                                self.internal_sensing_framework.interoception.cognition.record_confidence(
                                    response_id, 0.5  # Neutral confidence for tool-only responses
                                )
                                confidence = 0.5
                                # Still record uncertainty as 0.0 to show system is active
                                self.internal_sensing_framework.interoception.cognition.record_uncertainty(
                                    response_id, 0.0
                                )
                                uncertainty = 0.0
                                logger.info(f"Recorded neutral values: confidence=0.5, uncertainty=0.0 for tool-only response")

                            # Analyze internal thoughts if available
                            reasoning_content = getattr(self, '_current_reasoning_content', None)
                            if reasoning_content and isinstance(reasoning_content, str):
                                thought_metrics = ResponseAnalyzer.analyze_thoughts(reasoning_content)
                                # Update uncertainty with thought-based analysis
                                if thought_metrics['uncertainty'] > (uncertainty or 0.0):
                                    uncertainty = thought_metrics['uncertainty']
                                    self.internal_sensing_framework.interoception.cognition.record_uncertainty(
                                        f'thought_{response_id}', uncertainty
                                    )
                                
                                # Record processing depth from thoughts
                                if thought_metrics['depth'] > 0:
                                    self.internal_sensing_framework.interoception.cognition.record_processing_depth(
                                        f'thought_{response_id}', int(thought_metrics['depth'] * 10)
                                    )

                            # Compute valence and arousal only if assistant_text is available
                            # For tool-only responses, skip text-based affective analysis
                            if assistant_text:
                                # Compute valence and arousal
                                # Use conversation history for valence (excluding system prompts)
                                # Include current assistant response in history
                                self._ensure_single_system_message()
                                
                                conversation_messages = self.messages + [
                                    {"role": "assistant", "content": assistant_text}
                                ]
                                
                                # Validate the concatenated list doesn't have multiple system messages
                                system_count = sum(1 for m in conversation_messages if m.get("role") == "system")
                                if system_count > 1:
                                    logger.warning(
                                        f"conversation_messages contains {system_count} system messages. "
                                        "Filtering to single system message.",
                                        extra={
                                            "event": "multiple_system_messages_filtered",
                                            "count": system_count,
                                        }
                                    )
                                    # Filter to keep only first system message
                                    system_msgs = [m for m in conversation_messages if m.get("role") == "system"]
                                    non_system_msgs = [m for m in conversation_messages if m.get("role") != "system"]
                                    if system_msgs:
                                        conversation_messages = [system_msgs[0]] + non_system_msgs
                                    else:
                                        conversation_messages = non_system_msgs
                                
                                logger.info(f"Computing valence from {len(conversation_messages)} conversation messages")
                                valence_before = self.internal_sensing_framework.interoception.affect.affective_states.get("valence", 0.0)
                                history_len_before = len(self.internal_sensing_framework.interoception.affect._valence_history)
                                self.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                                    conversation_messages
                                )
                                valence_after = self.internal_sensing_framework.interoception.affect.affective_states.get("valence", 0.0)
                                history_len_after = len(self.internal_sensing_framework.interoception.affect._valence_history)
                                logger.info(f"VALENCE: {valence_before:.3f} -> {valence_after:.3f} (history_len: {history_len_before} -> {history_len_after}, moving_avg)")
                                # Save state after recording
                                try:
                                    self.internal_sensing_framework.save_state()
                                except Exception as e:
                                    logger.warning(f"Failed to save state after valence recording: {e}", exc_info=True)

                                arousal = ResponseAnalyzer.compute_arousal(assistant_text)
                                if arousal is not None:
                                    arousal_before = self.internal_sensing_framework.interoception.affect.affective_states.get("arousal", 0.5)
                                    history_len_before = len(self.internal_sensing_framework.interoception.affect._arousal_history)
                                    logger.info(f"RECORDING AROUSAL: {arousal:.3f} for response_id={response_id} (history_len_before={history_len_before})")
                                    self.internal_sensing_framework.interoception.affect.compute_arousal(
                                        arousal
                                    )
                                    arousal_after = self.internal_sensing_framework.interoception.affect.affective_states.get("arousal", 0.5)
                                    history_len_after = len(self.internal_sensing_framework.interoception.affect._arousal_history)
                                    logger.info(f"AROUSAL: {arousal_before:.3f} -> {arousal_after:.3f} (history_len: {history_len_before} -> {history_len_after}, moving_avg)")
                                    # Save state after recording
                                    try:
                                        self.internal_sensing_framework.save_state()
                                    except Exception as e:
                                        logger.warning(f"Failed to save state after arousal recording: {e}", exc_info=True)
                            else:
                                # Tool-only response: compute valence from existing conversation history (without current response)
                                logger.debug("Tool-only response: computing valence from existing conversation history")
                                self._ensure_single_system_message()
                                # Use existing messages (already includes tool results)
                                conversation_messages = [m for m in self.messages if m.get("role") in ("user", "assistant")]
                                if conversation_messages:
                                    self.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                                        conversation_messages
                                    )
                                # Use neutral arousal for tool-only responses
                                self.internal_sensing_framework.interoception.affect.compute_arousal(0.5)

                            # Update affective states from cognitive
                            # This must happen AFTER cognitive metrics are updated above
                            logger.debug("Updating affective states from cognitive metrics")
                            self.internal_sensing_framework.interoception.affect.update_from_cognitive(
                                self.internal_sensing_framework.interoception.cognition
                            )
                            # Save state after updating affective states from cognitive
                            try:
                                self.internal_sensing_framework.save_state()
                            except Exception as e:
                                logger.warning(f"Failed to save state after affective update: {e}", exc_info=True)

                            # Record reasoning step
                            self.internal_sensing_framework.interoception.cognition.record_reasoning_step(
                                f"step_{response_id}",
                                {
                                    "premise": user_text[:100] if self.messages else "",
                                    "conclusion": assistant_text[:100] if assistant_text else "[tool-only response]",
                                    "confidence": confidence,
                                },
                            )

                            # Sample internal state after ALL recording is complete
                            # Force a fresh sample to ensure updated metrics are included
                            logger.debug("Sampling internal state after metrics recording (forced)")
                            fresh_state = self.internal_sensing_framework.sample_internal_state(force=True)
                            # Save state after sampling (ensures latest moving averages are persisted)
                            try:
                                self.internal_sensing_framework.save_state()
                            except Exception as e:
                                logger.warning(f"Failed to save state after sampling: {e}", exc_info=True)
                            logger.debug(
                                f"Fresh state sampled: confidence={fresh_state.get('cognitive', {}).get('confidence_level', 'N/A'):.3f}, "
                                f"uncertainty={fresh_state.get('cognitive', {}).get('uncertainty_tracking', 'N/A'):.3f}, "
                                f"valence={fresh_state.get('affective', {}).get('valence', 'N/A'):.3f}, "
                                f"arousal={fresh_state.get('affective', {}).get('arousal', 'N/A'):.3f}"
                            )
                            
                            # CRITICAL: Update system prompt AFTER recording to ensure world state reflects new values
                            # This ensures the next LLM call sees the updated internal sensing values
                            # Force update even if hash hasn't changed (values might be same but we want to ensure persistence)
                            if self.world_state_aggregator and self._world_state_formatter:
                                logger.info("Updating system prompt after internal sensing update to reflect new values")
                                # Temporarily reset hash to force update (ensures system message is updated even if values are same)
                                old_hash = self._last_world_state_hash
                                self._last_world_state_hash = None
                                self._update_system_prompt()
                                # Hash will be set by _update_system_prompt() to new value
                                
                                # CRITICAL: Re-save conversation with updated world state
                                # This ensures saved conversations show the latest internal sensing values, not defaults
                                try:
                                    self._save_conversation()
                                    logger.info("Re-saved conversation with updated world state after recording")
                                except Exception as save_error:
                                    logger.warning(f"Failed to re-save conversation after recording: {save_error}", exc_info=True)

                        except Exception as e:
                                logger.error(
                                    f"CRITICAL: Error in response instrumentation: {e}", exc_info=True
                                )
                                # Even on error, try to record at least neutral values to show system is active
                                try:
                                    response_id = getattr(self, "_current_response_id", f"response_{len(self.messages)}")
                                    logger.info(f"Recording fallback neutral values after instrumentation error")
                                    self.internal_sensing_framework.interoception.cognition.record_confidence(response_id, 0.5)
                                    if assistant_text:
                                        self.internal_sensing_framework.interoception.affect.compute_arousal(0.5)
                                except Exception as fallback_error:
                                    logger.error(f"Even fallback recording failed: {fallback_error}", exc_info=True)

                    # Log context after turn
                    self._log_context_after_turn(
                        assistant_text=assistant_text, raw_response=response
                    )
                    
                    # CRITICAL: Re-save conversation AFTER all instrumentation is complete
                    # This ensures saved conversations include the latest world state with updated internal sensing values
                    # The initial save at line 1216 happens before instrumentation, so we need to save again here
                    try:
                        self._save_conversation()
                        logger.debug("Re-saved conversation after instrumentation with updated world state")
                    except Exception as save_error:
                        logger.warning(f"Failed to re-save conversation after instrumentation: {save_error}", exc_info=True)

                    # Auto-save skipped here to avoid background writes after test teardown
                except Exception as e:
                    logger.error(
                        f"CRITICAL: Error in post-processing block: {e}", exc_info=True
                    )
                    logger.warning(
                        f"Error in post-processing: {e}", exc_info=True
                    )

                # --- response-guard: ensure the assistant never returns an empty string ---
                try:
                    assistant_msg = next((m for m in reversed(self.messages) if m.get("role") == "assistant"), None)
                    trace_id = getattr(self, "_current_response_id", None) or None
                    # Normalize whitespace-only content to None to ensure the
                    # response_guard will inject a fallback. This covers cases
                    # where some code paths set empty-string replies explicitly.
                    if assistant_msg is None:
                        final_reply = ensure_non_empty(None, trace_id=trace_id)
                        self.messages.append({"role": "assistant", "content": final_reply})
                    else:
                        content = assistant_msg.get("content", "")
                        if isinstance(content, str) and content.strip() == "":
                            content = None
                        final_reply = ensure_non_empty(content, trace_id=trace_id)
                        if final_reply != (assistant_msg.get("content", None)):
                            assistant_msg["content"] = final_reply
                            logger.info("Injected fallback assistant reply due to empty content (TraceID=%s)", trace_id)
                except Exception as _e:
                    import uuid
                    trace = getattr(self, "_current_response_id", None) or str(uuid.uuid4())
                    fallback = ensure_non_empty(None, trace_id=trace)
                    self.messages.append({"role": "assistant", "content": fallback})
                    final_reply = fallback

                return final_reply

        # Max iterations reached
        logger.warning(
            f"Reached max tool iterations ({self._max_tool_iterations})",
            extra={
                "event": "max_tool_iterations_reached",
                "max_iterations": self._max_tool_iterations,
                "iteration": iterations,
            },
        )
        if response:
            assistant_text = (
                self.llm.extract_assistant_content(response)
                or "I apologize, but I encountered an issue processing your request."
            )
        else:
            assistant_text = (
                "I apologize, but I encountered an issue processing your request."
            )
        
        # Normalize empty string to None so guard can catch it
        if assistant_text == "" or (isinstance(assistant_text, str) and assistant_text.strip() == ""):
            assistant_text = None
        
        # Apply response guard to ensure non-empty
        assistant_text = self._ensure_response_non_empty(assistant_text)

        self.messages.append({"role": "assistant", "content": assistant_text})
        self.updated_at = datetime.now(timezone.utc).isoformat()
        # Log conversation turn completion even on max iterations
        if response:
            self._log_context_after_turn(
                assistant_text=assistant_text, raw_response=response
            )
        else:
            # Create a minimal response dict for logging
            self._log_context_after_turn(assistant_text=assistant_text, raw_response={})
        
        # CRITICAL: Run post-processing even on max iterations path
        # This ensures metrics are recorded and system prompt is updated
        logger.info(f"MAX ITERATIONS PATH: Running post-processing (has_framework={self.internal_sensing_framework is not None}, has_analyzer={ResponseAnalyzer is not None})")
        try:
            # Reuse the same post-processing logic from the normal path
            if self.internal_sensing_framework and ResponseAnalyzer:
                response_id = getattr(self, "_current_response_id", f"response_{len(self.messages)}")
                logger.info(f"MAX ITERATIONS: Recording metrics for response_id={response_id}")
                
                # Record at least neutral values to show system is active
                self.internal_sensing_framework.interoception.cognition.record_confidence(response_id, 0.5)
                self.internal_sensing_framework.interoception.cognition.record_uncertainty(response_id, 0.0)
                if assistant_text:
                    self.internal_sensing_framework.interoception.affect.compute_arousal(0.5)
                
                # Force fresh sample and update system prompt
                self.internal_sensing_framework.sample_internal_state(force=True)
                # Save state after sampling
                try:
                    self.internal_sensing_framework.save_state()
                except Exception as e:
                    logger.warning(f"Failed to save state after sampling: {e}", exc_info=True)
                if self.world_state_aggregator and self._world_state_formatter:
                    logger.info("MAX ITERATIONS: Updating system prompt after recording")
                    self._last_world_state_hash = None  # Force update
                    self._update_system_prompt()
        except Exception as e:
            logger.error(f"Error in max iterations post-processing: {e}", exc_info=True)
        
        self._save_conversation()
        return assistant_text

    def _is_gemini_client(self) -> bool:
        """
        Check if the LLM client is a GeminiClient, handling both direct and wrapped clients.
        
        When world_state_aggregator is available, the LLM is wrapped in CachedLLMClient.
        This method checks both the direct client and the underlying client if wrapped.
        
        Returns:
            True if the LLM (or its underlying client) is a GeminiClient, False otherwise
        """
        from ..llm.gemini_client import GeminiClient
        from ..llm.cached_client import CachedLLMClient
        
        # Check if it's a direct GeminiClient
        if isinstance(self.llm, GeminiClient):
            return True
        
        # Check if it's a CachedLLMClient wrapping a GeminiClient
        if isinstance(self.llm, CachedLLMClient):
            underlying = getattr(self.llm, '_underlying', None)
            if underlying is not None and isinstance(underlying, GeminiClient):
                return True
        
        return False
    
    def _summarize_history(self, max_tokens: int = 250) -> str:
        """Summarize recent conversation history (opt-in, read-only)."""
        try:
            convo_preview = []
            for m in self.messages[-20:]:
                role = m.get("role", "")
                if role not in ("user", "assistant"):
                    continue
                content = (m.get("content") or "")[:800]
                convo_preview.append(f"{role}: {content}")
            prompt = (
                "Summarize the conversation so far. Keep it concise (<= "
                f"{max_tokens} tokens). Capture key goals, decisions, constraints, and open items."
            )
            messages = [
                {
                    "role": "system",
                    "content": "You are a concise conversation summarizer.",
                },
                {"role": "user", "content": prompt + "\n\n" + "\n".join(convo_preview)},
            ]
            # Validate message size before sending (use a higher limit for summarization)
            messages = self._validate_message_size(messages, max_tokens=50000)
            resp = self.llm.chat(messages)
            return self.llm.extract_assistant_content(resp) or "Summary generated."
        except Exception:
            return "Summary unavailable due to an internal error."
    
    def _calculate_buffer_turns(self) -> int:
        """
        Calculate the number of turns to keep based on gradual pruning configuration.
        
        Returns:
            Number of turns to keep in the buffer
        """
        from ..config import config
        
        # If gradual pruning is disabled, use the standard last_turns_count
        if not config.summarization.gradual_pruning_enabled:
            last_turns_count = config.summarization.last_turns_count
            if not isinstance(last_turns_count, int):
                return 3  # Default
            return last_turns_count
        
        # Get the current summary to check cycle count
        try:
            if self._summarization_manager:
                summary = self._summarization_manager.summary_storage.load_session_summary(self.session_id)
                if summary:
                    cycle_count = summary.header.summarization_cycle_count
                else:
                    # No summary yet, first summarization will have cycle_count = 0
                    cycle_count = 0
            else:
                cycle_count = 0
        except Exception as e:
            logger.debug(f"Error loading summary for buffer calculation: {e}")
            cycle_count = 0
        
        # Calculate buffer size using gradual reduction formula
        initial_buffer = config.summarization.initial_buffer_turns
        min_buffer = config.summarization.min_buffer_turns
        reduction_rate = config.summarization.buffer_reduction_rate
        
        if not isinstance(initial_buffer, int):
            initial_buffer = 10
        if not isinstance(min_buffer, int):
            min_buffer = 3
        if not isinstance(reduction_rate, int):
            reduction_rate = 2
        
        # Formula: buffer_size = max(min_buffer, initial_buffer - (cycle_count * reduction_rate))
        buffer_size = max(min_buffer, initial_buffer - (cycle_count * reduction_rate))
        
        logger.debug(
            f"Calculated buffer size: {buffer_size} turns "
            f"(cycle_count={cycle_count}, initial={initial_buffer}, min={min_buffer}, reduction={reduction_rate})"
        )
        
        return buffer_size
    
    def _prune_summarized_messages(self, last_summarized_event_id: str) -> int:
        """
        Remove messages that correspond to summarized events, keeping only system message and last K turns.
        
        After summarization, this method collapses the context by removing all messages that were
        summarized, leaving only:
        - System message (always preserved)
        - Last K turns that occurred after the last summarized event (using gradual pruning if enabled)
        
        Args:
            last_summarized_event_id: The event ID of the last event that was summarized
            
        Returns:
            Number of messages removed
        """
        if not self._event_logger or not last_summarized_event_id:
            logger.debug("Cannot prune messages: event logger not available or no last_summarized_event_id")
            return 0
        
        try:
            from ..config import config
            
            # Get all events up to and including the last summarized event
            all_events = self._event_logger.get_events(self.session_id)
            summarized_event_ids = set()
            
            # Find the index of the last summarized event
            last_summarized_index = -1
            for i, event in enumerate(all_events):
                if event.get("event_id") == last_summarized_event_id:
                    last_summarized_index = i
                    break
            
            if last_summarized_index == -1:
                logger.warning(f"Could not find event {last_summarized_event_id} in event log")
                return 0
            
            # Collect all event IDs that were summarized (up to and including last_summarized_event_id)
            for i in range(last_summarized_index + 1):
                event_id = all_events[i].get("event_id")
                if event_id:
                    summarized_event_ids.add(event_id)
            
            # Calculate buffer size using gradual pruning if enabled
            last_turns_count = self._calculate_buffer_turns()
            
            # Get events after the last summarized event to determine which messages to keep
            events_after_summary = all_events[last_summarized_index + 1:]
            keep_event_ids = set()
            for event in events_after_summary:
                event_id = event.get("event_id")
                if event_id:
                    keep_event_ids.add(event_id)
            
            # Separate system message from other messages
            system_message = None
            other_messages = []
            for msg in self.messages:
                if msg.get("role") == "system":
                    system_message = msg
                else:
                    other_messages.append(msg)
            
            # Filter messages: remove those with summarized event IDs, but keep those with event IDs after summary
            # Also handle messages without event IDs (backward compatibility - skip pruning for them)
            pruned_messages = []
            removed_count = 0
            
            # Keep system message
            if system_message:
                pruned_messages.append(system_message)
            
            # Process other messages
            for msg in other_messages:
                msg_event_ids = msg.get("event_ids", [])
                
                # If message has no event IDs, keep it (backward compatibility)
                if not msg_event_ids:
                    pruned_messages.append(msg)
                    continue
                
                # Check if any event ID in this message was summarized
                has_summarized_event = any(eid in summarized_event_ids for eid in msg_event_ids)
                
                # Check if any event ID in this message should be kept (occurred after summary)
                has_keep_event = any(eid in keep_event_ids for eid in msg_event_ids)
                
                if has_summarized_event and not has_keep_event:
                    # This message was summarized and has no events after summary - remove it
                    removed_count += 1
                else:
                    # Keep this message (either not summarized, or has events after summary)
                    pruned_messages.append(msg)
            
            # Now ensure we keep at least last K turns (using gradual buffer calculation)
            # Count turns from the end (non-system messages)
            non_system_pruned = [m for m in pruned_messages if m.get("role") != "system"]
            
            # Calculate minimum messages to keep based on buffer size
            # Each turn is typically 2 messages (user + assistant), but can be more with tool calls
            min_messages_to_keep = last_turns_count * 2
            
            # If we removed too many, we need to keep more recent messages even if they have summarized events
            # This ensures continuity - prioritize recency
            if len(non_system_pruned) < min_messages_to_keep:
                # We need to keep more messages - restore some from the end even if they were summarized
                # This is a safety mechanism to ensure we always have some context
                logger.debug(
                    f"Only {len(non_system_pruned)} non-system messages remain after pruning, "
                    f"keeping last {min_messages_to_keep} messages for continuity (buffer size: {last_turns_count} turns)"
                )
                # Rebuild with system message + last K*2 messages
                if system_message:
                    pruned_messages = [system_message]
                else:
                    pruned_messages = []
                pruned_messages.extend(other_messages[-min_messages_to_keep:])
                # Recalculate removed count
                removed_count = len(self.messages) - len(pruned_messages)
            
            # Update messages
            self.messages = pruned_messages
            
            # Validate system message count after pruning to prevent accumulation
            self._ensure_single_system_message()
            
            logger.info(
                f"Pruned {removed_count} messages after summarization (kept {len(pruned_messages)} messages)",
                extra={
                    "event": "messages_pruned_after_summarization",
                    "removed_count": removed_count,
                    "kept_count": len(pruned_messages),
                    "last_summarized_event_id": last_summarized_event_id,
                }
            )
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error pruning summarized messages: {e}", exc_info=True)
            return 0

    # ---------- Internal logging helpers ----------

    def _get_reasoning_length(self) -> int:
        """Get the length of current reasoning content, safely handling Mock objects."""
        if not hasattr(self, '_current_reasoning_content'):
            return 0
        try:
            reasoning = self._current_reasoning_content
            if isinstance(reasoning, (str, bytes, list, tuple)):
                return len(reasoning)
            return 0
        except (TypeError, AttributeError):
            return 0

    def _current_context_stats(self) -> Dict[str, Any]:
        """
        Simple approximations; later you can add token counting if needed.
        """
        total_chars = sum(len(m.get("content") or "") for m in self.messages)
        user_msgs = sum(1 for m in self.messages if m.get("role") == "user")
        assistant_msgs = sum(1 for m in self.messages if m.get("role") == "assistant")
        system_msgs = sum(1 for m in self.messages if m.get("role") == "system")
        return {
            "messages_total": len(self.messages),
            "messages_user": user_msgs,
            "messages_assistant": assistant_msgs,
            "messages_system": system_msgs,
            "total_chars": total_chars,
        }

    def _log_context_before_turn(self, user_text: str) -> None:
        stats = self._current_context_stats()
        logger.info(
            "Sending user message",
            extra={
                "event": "turn_before",
                "context_stats": stats,
                "user_preview": user_text[:200]
                + ("..." if len(user_text) > 200 else ""),
            },
        )

    def _log_context_after_turn(
        self, assistant_text: str, raw_response: Dict[str, Any]
    ) -> None:
        stats = self._current_context_stats()
        # Ensure usage is a dict, not a Mock object
        usage = raw_response.get("usage", {}) if isinstance(raw_response, dict) else {}
        if not isinstance(usage, dict):
            usage = {}
        logger.info(
            "Received assistant message",
            extra={
                "event": "turn_after",
                "context_stats": stats,
                "assistant_preview": (assistant_text[:200] if assistant_text else None)
                + ("..." if assistant_text and len(assistant_text) > 200 else ""),
                "usage": usage,
            },
        )

    def _get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get messages to send to LLM using intelligent context graph pruning.
        
        When context graph is enabled, uses tree-based pruning that:
        - Preserves main conversation thread
        - Retains relevant branches as long as possible
        - Automatically removes orphaned branches
        - Stays within token limits
        
        When context graph is disabled, falls back to token-aware filtering.
        
        Note: This method applies intelligent pruning, but _validate_message_size()
        is always called afterward as a failsafe to ensure we never exceed token limits.
        
        Returns:
            Filtered message list for LLM calls (with tool results truncated if needed)
        """
        from ..config import config
        
        # Check if we're using Gemini client (for Gemini-specific ordering fixes)
        is_gemini = self._is_gemini_client()
        
        # Validate system message count before filtering
        self._ensure_single_system_message()
        
        max_context_tokens = config.llm.max_context_tokens
        if not isinstance(max_context_tokens, int):
            max_context_tokens = 100000  # Default value
        
        # Use context graph if enabled
        if self._context_graph and config.context.enabled:
            try:
                # Ensure all messages are in the graph
                # (in case graph wasn't updated for some messages)
                for msg in self.messages:
                    if "message_id" not in msg:
                        msg["message_id"] = str(uuid.uuid4())
                    # Check if message is already in graph
                    msg_id = msg.get("message_id")
                    if msg_id not in self._context_graph.nodes:
                        # Find parent (previous message)
                        parent_id = None
                        if self._context_graph._message_order:
                            parent_id = self._context_graph._message_order[-1]
                        self._context_graph.add_message(msg, parent_id=parent_id)
                
                # Get messages from context graph with intelligent pruning
                filtered_messages = self._context_graph.get_messages_for_llm(
                    max_tokens=max_context_tokens,
                    safety_margin=config.context.safety_margin,
                )
                
                # Ensure system message is first if it exists
                system_message = None
                non_system_messages = []
                for msg in filtered_messages:
                    if msg.get("role") == "system":
                        system_message = msg
                    else:
                        non_system_messages.append(msg)
                
                # Reconstruct with system message first
                if system_message:
                    filtered_messages = [system_message] + non_system_messages
                else:
                    filtered_messages = non_system_messages
                
                # Truncate tool results as safety measure
                filtered_messages = self._truncate_tool_results_in_messages(
                    filtered_messages, config.summarization.max_tool_result_size
                )
                
                # Apply Gemini-specific fix if needed
                if is_gemini:
                    filtered_messages = self._fix_gemini_tool_call_ordering(filtered_messages)
                
                logger.debug(
                    f"Context graph filtered messages: {len(filtered_messages)} messages "
                    f"(from {len(self.messages)} total)"
                )
                return filtered_messages
                
            except Exception as e:
                logger.warning(f"Error using context graph, falling back to token filtering: {e}", exc_info=True)
                # Fall through to token-aware filtering
        
        # Fallback: token-aware filtering (no context graph or error occurred)
        filtered = self._apply_token_aware_filtering(self.messages, max_context_tokens)
        # Apply Gemini-specific fix if needed
        if is_gemini:
            filtered = self._fix_gemini_tool_call_ordering(filtered)
        return filtered
    
    def _apply_token_aware_filtering(
        self, messages: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Apply token-aware filtering to messages, truncating tool results and removing messages if needed.
        
        Args:
            messages: List of messages to filter
            max_tokens: Maximum token limit
            
        Returns:
            Filtered messages with tool results truncated and messages removed if needed to stay under limit
        """
        from ..config import config
        
        # Validate system message count in the messages list before filtering
        # If messages is self.messages, validate directly; otherwise check the list
        if messages is self.messages:
            self._ensure_single_system_message()
        else:
            # Check for multiple system messages in the provided list
            system_messages = [i for i, msg in enumerate(messages) if msg.get("role") == "system"]
            if len(system_messages) > 1:
                logger.warning(
                    f"Found {len(system_messages)} system messages in filtering list. "
                    "Keeping only the first.",
                    extra={
                        "event": "multiple_system_messages_in_filtering",
                        "count": len(system_messages),
                    }
                )
                # Keep only the first system message
                first_system_msg = messages[system_messages[0]]
                # Remove all system messages
                for idx in reversed(system_messages):
                    messages.pop(idx)
                # Insert at index 0
                messages.insert(0, first_system_msg)
        
        # Check if we're using Gemini client (for Gemini-specific ordering fixes)
        is_gemini = self._is_gemini_client()
        
        # Fix tool message ordering first (remove orphaned tool messages)
        messages = self._fix_tool_message_ordering(messages)
        
        # Apply Gemini-specific fix proactively if using Gemini
        if is_gemini:
            messages = self._fix_gemini_tool_call_ordering(messages)
        
        # Apply safety margin (5%) to account for token estimation inaccuracy
        effective_max_tokens = int(max_tokens * 0.95)
        
        # Truncate tool results first (this is the least destructive operation)
        messages = self._truncate_tool_results_in_messages(
            messages, config.summarization.max_tool_result_size
        )
        
        # Re-apply Gemini fix after truncation (defensive)
        if is_gemini:
            messages = self._fix_gemini_tool_call_ordering(messages)
        
        # Estimate tokens after tool result truncation
        estimated_tokens = estimate_messages_tokens(messages)
        
        # If under limit after tool result truncation, we're done
        if estimated_tokens <= effective_max_tokens:
            return messages
        
        # Still over limit - need to remove messages
        # Separate system message from conversation messages
        system_message = None
        conversation_messages = []
        
        if messages and messages[0].get("role") == "system":
            system_message = messages[0]
            conversation_messages = messages[1:]
        else:
            conversation_messages = messages
        
        # If we only have system message or no conversation messages, return as-is
        if not conversation_messages:
            if estimated_tokens > max_tokens:
                logger.warning(
                    f"Messages exceed token limit ({estimated_tokens} > {max_tokens}) "
                    "but cannot remove more messages"
                )
            return messages if system_message is None else [system_message]
        
        # Validate conversation_messages before copying to prevent contamination
        self._validate_message_list_for_system_messages(conversation_messages)
        
        # Iteratively remove oldest non-system messages until under limit
        filtered_messages = conversation_messages.copy()
        
        # Validate filtered_messages after copy
        self._validate_message_list_for_system_messages(filtered_messages)
        
        while filtered_messages and estimated_tokens > effective_max_tokens:
            # Remove oldest message (first in list)
            removed = filtered_messages.pop(0)
            logger.debug(
                f"Removing message to reduce token count: role={removed.get('role')}, "
                f"estimated_tokens={estimated_tokens} > {effective_max_tokens}"
            )
            
            # Reconstruct full message list with system message (if present)
            if system_message:
                current_messages = [system_message] + filtered_messages
                # Validate concatenated list
                self._validate_message_list_for_system_messages(current_messages)
            else:
                current_messages = filtered_messages
            
            # Re-estimate after removal
            estimated_tokens = estimate_messages_tokens(current_messages)
            
            # Stop if we only have system message + last message remaining (minimum)
            if len(filtered_messages) <= 1:
                break
        
        # Reconstruct final message list
        if system_message:
            result = [system_message] + filtered_messages
            # Validate concatenated result
            self._validate_message_list_for_system_messages(result)
        else:
            result = filtered_messages
            # Validate result
            self._validate_message_list_for_system_messages(result)
        
        # Final check - if still over limit, log warning but return anyway
        final_estimated_tokens = estimate_messages_tokens(result)
        if final_estimated_tokens > max_tokens:
            logger.warning(
                f"Messages still exceed token limit after filtering "
                f"({final_estimated_tokens} > {max_tokens}). "
                f"Effective limit was {effective_max_tokens}. "
                "This may cause API errors."
            )
        else:
            logger.debug(
                f"Token filtering complete: {final_estimated_tokens} <= {max_tokens} "
                f"(removed {len(conversation_messages) - len(filtered_messages)} messages)"
            )
        
        return result
    
    def _fix_tool_message_ordering(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fix tool message ordering by removing orphaned tool messages.
        
        Removes tool messages that don't have a preceding assistant message
        with matching tool_calls. This ensures messages are valid for OpenAI API.
        
        Args:
            messages: List of messages (may contain orphaned tool messages)
            
        Returns:
            List of messages with orphaned tool messages removed
        """
        if not messages:
            return messages
        
        fixed_messages = []
        # Track tool_call_ids from assistant messages with tool_calls
        valid_tool_call_ids = set()
        # Track the last assistant message index with tool_calls
        last_assistant_with_tool_calls_idx = -1
        
        for i, msg in enumerate(messages):
            role = msg.get("role")
            
            # System messages are always included
            if role == "system":
                fixed_messages.append(msg)
                continue
            
            # Handle assistant messages
            if role == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls and isinstance(tool_calls, list):
                    # Extract tool_call_ids
                    current_tool_call_ids = set()
                    for tool_call in tool_calls:
                        if isinstance(tool_call, dict):
                            tool_call_id = tool_call.get("id")
                            if isinstance(tool_call_id, str):
                                current_tool_call_ids.add(tool_call_id)
                    
                    # Update tracking
                    valid_tool_call_ids = current_tool_call_ids
                    last_assistant_with_tool_calls_idx = len(fixed_messages)
                    fixed_messages.append(msg)
                else:
                    # Assistant without tool_calls - reset tracking
                    valid_tool_call_ids.clear()
                    last_assistant_with_tool_calls_idx = -1
                    fixed_messages.append(msg)
            
            # Handle tool messages
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id")
                # CRITICAL: Check if there's a valid preceding assistant message with this tool_call_id
                has_valid_predecessor = False
                if last_assistant_with_tool_calls_idx >= 0:
                    # Check if tool_call_id is in the valid set
                    if isinstance(tool_call_id, str) and tool_call_id in valid_tool_call_ids:
                        has_valid_predecessor = True
                    else:
                        # Also check if it's in any preceding assistant message (not just the most recent)
                        for j in range(len(fixed_messages) - 1, -1, -1):
                            prev_msg = fixed_messages[j]
                            if prev_msg.get("role") == "assistant":
                                prev_tool_calls = prev_msg.get("tool_calls")
                                if prev_tool_calls and isinstance(prev_tool_calls, list):
                                    prev_tool_call_ids = {
                                        tc.get("id") for tc in prev_tool_calls
                                        if isinstance(tc, dict) and isinstance(tc.get("id"), str)
                                    }
                                    if tool_call_id in prev_tool_call_ids:
                                        has_valid_predecessor = True
                                        break
                                # If assistant doesn't have tool_calls, stop looking
                                break
                            elif prev_msg.get("role") == "user":
                                # User message resets context
                                break
                
                if has_valid_predecessor:
                    # Valid tool message - has matching tool_call_id
                    fixed_messages.append(msg)
                else:
                    # Orphaned tool message - remove it
                    logger.warning(
                        f"Removing orphaned tool message with tool_call_id '{tool_call_id}' "
                        f"(no preceding assistant message with matching tool_calls)"
                    )
            
            # User messages are always included
            elif role == "user":
                # User messages reset the tool call context
                valid_tool_call_ids.clear()
                last_assistant_with_tool_calls_idx = -1
                fixed_messages.append(msg)
            else:
                # Unknown role - include it (might be custom roles)
                fixed_messages.append(msg)
        
        return fixed_messages
    
    def _find_most_recent_content_message(
        self, messages: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the most recent user or assistant message with content.
        
        Searches backwards through messages to find the most recent message that
        can serve as content for an API call. Prefers user messages, falls back
        to assistant messages with actual content (not just tool_calls).
        
        Args:
            messages: List of message dictionaries to search
            
        Returns:
            Most recent valid content message, or None if none found
        """
        # Search backwards to find the most recent valid content message
        for msg in reversed(messages):
            role = msg.get("role")
            
            # Skip system messages
            if role == "system":
                continue
            
            # User messages are always valid content
            if role == "user":
                content = msg.get("content")
                if content is not None and content != "":
                    return msg
            
            # Assistant messages are valid if they have content (not just tool_calls)
            if role == "assistant":
                content = msg.get("content")
                # Assistant message is valid if it has non-empty content
                # (tool_calls alone are not sufficient for API calls)
                if content is not None and content != "":
                    return msg
        
        return None
    
    def _find_minimal_preserved_context(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find minimal context to preserve when Gemini fix removes everything.
        
        Preserves:
        1. The most recent user message (the original query)
        2. The last complete tool call sequence (assistant with tool_calls + its tool results)
        
        This ensures the model has context about what it was trying to do, even if
        message ordering is invalid.
        
        Args:
            messages: List of message dictionaries to search
            
        Returns:
            List of messages to preserve (most recent user + last tool call sequence)
        """
        preserved = []
        
        # Find the most recent user message
        most_recent_user = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content")
                if content is not None and content != "":
                    most_recent_user = msg
                    break
        
        if most_recent_user:
            preserved.append(most_recent_user)
        
        # Find the last complete tool call sequence
        # Look for: assistant message with tool_calls, followed by its tool results
        last_assistant_with_tool_calls = None
        last_tool_call_ids = set()
        
        # Search backwards for the last assistant message with tool_calls
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls and isinstance(tool_calls, list):
                    # Extract tool_call_ids
                    for tool_call in tool_calls:
                        if isinstance(tool_call, dict):
                            tool_call_id = tool_call.get("id")
                            if isinstance(tool_call_id, str):
                                last_tool_call_ids.add(tool_call_id)
                    last_assistant_with_tool_calls = (i, msg)
                    break
        
        if last_assistant_with_tool_calls:
            assistant_idx, assistant_msg = last_assistant_with_tool_calls
            preserved.append(assistant_msg)
            
            # Find tool messages that correspond to this assistant's tool_calls
            # Look forward from the assistant message
            for i in range(assistant_idx + 1, len(messages)):
                msg = messages[i]
                if msg.get("role") == "tool":
                    tool_call_id = msg.get("tool_call_id")
                    if isinstance(tool_call_id, str) and tool_call_id in last_tool_call_ids:
                        preserved.append(msg)
                elif msg.get("role") == "user":
                    # User message breaks the sequence
                    break
        
        return preserved
    
    def _detect_tool_call_loop(self, iterations: int) -> Optional[Dict[str, Any]]:
        """
        Detect if the model is stuck in a loop making repeated tool calls.
        
        Analyzes recent tool calls in the current turn to detect patterns where
        the same tool is called with identical or similar arguments repeatedly.
        Only triggers when actual repetition occurs (same tool + same/similar arguments),
        not just when the same tool is used with different arguments.
        
        Args:
            iterations: Current iteration count
            
        Returns:
            Dictionary with loop detection info if loop detected, None otherwise.
            Contains: tool_name, repeat_count, pattern_description
        """
        if not self.messages:
            return None
        
        # Find the start of the current turn (last user message)
        last_user_idx = -1
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i].get("role") == "user":
                last_user_idx = i
                break
        
        if last_user_idx == -1:
            return None
        
        # Collect tool calls from current turn
        recent_tool_calls = []
        for i in range(last_user_idx + 1, len(self.messages)):
            msg = self.messages[i]
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls and isinstance(tool_calls, list):
                    for tool_call in tool_calls:
                        if isinstance(tool_call, dict):
                            func = tool_call.get("function", {})
                            tool_name = func.get("name", "unknown")
                            arguments_str = func.get("arguments", "{}")
                            # Try to parse arguments for comparison
                            try:
                                import json
                                arguments = json.loads(arguments_str) if arguments_str else {}
                            except (json.JSONDecodeError, TypeError):
                                arguments = {}
                            recent_tool_calls.append({
                                "tool_name": tool_name,
                                "arguments": arguments,
                                "arguments_str": arguments_str,
                            })
        
        if len(recent_tool_calls) < 2:
            # Need at least 2 tool calls to detect a loop
            return None
        
        # Check for patterns: look at last 5 tool calls
        last_n = min(5, len(recent_tool_calls))
        last_tool_calls = recent_tool_calls[-last_n:]
        
        # Pattern: Same tool + same/similar arguments repeated 2+ times
        # Only trigger loop detection when the same tool is called with identical or similar arguments
        # This prevents false positives when different commands are executed with the same tool
        for i in range(len(last_tool_calls) - 1):
            tc1 = last_tool_calls[i]
            for j in range(i + 1, len(last_tool_calls)):
                tc2 = last_tool_calls[j]
                if tc1["tool_name"] == tc2["tool_name"]:
                    # Check if arguments are similar
                    if self._tool_arguments_similar(tc1["arguments"], tc2["arguments"], tc1["tool_name"]):
                        # Found duplicate - check if there are more
                        duplicate_count = 2
                        for k in range(j + 1, len(last_tool_calls)):
                            tc3 = last_tool_calls[k]
                            if tc3["tool_name"] == tc1["tool_name"]:
                                if self._tool_arguments_similar(tc1["arguments"], tc3["arguments"], tc1["tool_name"]):
                                    duplicate_count += 1
                        
                        if duplicate_count >= 2:
                            return {
                                "tool_name": tc1["tool_name"],
                                "repeat_count": duplicate_count,
                                "pattern_description": f"Tool '{tc1['tool_name']}' with similar arguments called {duplicate_count} times",
                                "pattern_type": "repeated_tool_args",
                            }
        
        return None
    
    def _tool_arguments_similar(
        self, args1: Dict[str, Any], args2: Dict[str, Any], tool_name: str
    ) -> bool:
        """
        Check if two tool argument dictionaries are similar.
        
        For terminal tool, normalizes commands to detect similar patterns.
        For other tools, does exact comparison.
        
        Args:
            args1: First arguments dict
            args2: Second arguments dict
            tool_name: Name of the tool
            
        Returns:
            True if arguments are similar, False otherwise
        """
        if tool_name == "terminal":
            # For terminal, compare command strings (normalize whitespace and paths)
            cmd1 = args1.get("command", "")
            cmd2 = args2.get("command", "")
            if not cmd1 or not cmd2:
                return cmd1 == cmd2
            
            # Normalize: strip whitespace, convert to lowercase for comparison
            cmd1_normalized = " ".join(cmd1.strip().lower().split())
            cmd2_normalized = " ".join(cmd2.strip().lower().split())
            
            # For exact matches (like "ls -R" repeated)
            if cmd1_normalized == cmd2_normalized:
                return True
            
            # For similar patterns (like commands with same structure but different paths)
            # Extract base command (first word)
            cmd1_base = cmd1_normalized.split()[0] if cmd1_normalized else ""
            cmd2_base = cmd2_normalized.split()[0] if cmd2_normalized else ""
            if cmd1_base == cmd2_base and cmd1_base:
                # Same base command - check if they're very similar (same flags, etc.)
                # Simple heuristic: if the normalized commands share significant similarity
                if len(cmd1_normalized) > 10 and len(cmd2_normalized) > 10:
                    # For longer commands, check if they share the same structure
                    # (same first few words, same flags)
                    words1 = cmd1_normalized.split()[:3]  # First 3 words
                    words2 = cmd2_normalized.split()[:3]
                    if words1 == words2:
                        return True
        
        # For other tools, do exact comparison
        return args1 == args2
    
    def _fix_gemini_tool_call_ordering_single_pass(
        self, messages: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Single pass of Gemini tool call ordering fix.
        
        Performs one iteration of removing invalid assistant messages with tool_calls
        and their orphaned tool messages.
        
        Args:
            messages: List of messages to fix
            
        Returns:
            Tuple of (fixed_messages, removed_count)
        """
        if not messages:
            return messages, 0
        
        fixed_messages = []
        # Track tool_call_ids from assistant messages with tool_calls that we keep
        valid_tool_call_ids = set()
        removed_count = 0
        
        # Track the last non-system message we've added to fixed_messages
        # This helps us detect if we're starting with an invalid assistant message
        last_non_system_in_fixed = None
        
        for i, msg in enumerate(messages):
            role = msg.get("role")
            
            # System messages are always included
            if role == "system":
                fixed_messages.append(msg)
                continue
            
            # Handle assistant messages
            if role == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls and isinstance(tool_calls, list):
                    # Check if this assistant message with tool_calls has a valid predecessor
                    # Must check in fixed_messages (not original) to handle cascading invalidations
                    found_valid_predecessor = False
                    predecessor_role = None
                    
                    # Check the last non-system message in fixed_messages
                    if last_non_system_in_fixed in ("user", "tool"):
                        found_valid_predecessor = True
                        predecessor_role = last_non_system_in_fixed
                    elif last_non_system_in_fixed is None:
                        # This is the first non-system message and it's an assistant with tool_calls
                        # This is invalid - must start with user message
                        found_valid_predecessor = False
                        predecessor_role = "none (first message)"
                    else:
                        # Predecessor is assistant - invalid
                        found_valid_predecessor = False
                        predecessor_role = last_non_system_in_fixed
                    
                    if found_valid_predecessor:
                        # Valid - keep this assistant message and track its tool_call_ids
                        current_tool_call_ids = set()
                        for tool_call in tool_calls:
                            if isinstance(tool_call, dict):
                                tool_call_id = tool_call.get("id")
                                if isinstance(tool_call_id, str):
                                    current_tool_call_ids.add(tool_call_id)
                        valid_tool_call_ids = current_tool_call_ids
                        fixed_messages.append(msg)
                        last_non_system_in_fixed = "assistant"
                        logger.debug(
                            f"Keeping valid assistant message with tool_calls at index {i} "
                            f"(predecessor: {predecessor_role})"
                        )
                    else:
                        # Invalid - skip this assistant message and clear tool_call_ids
                        # We'll also skip any tool messages that follow
                        removed_count += 1
                        tool_names = [
                            tc.get("function", {}).get("name", "unknown")
                            for tc in tool_calls if isinstance(tc, dict)
                        ]
                        valid_tool_call_ids.clear()
                        logger.debug(
                            f"Removing invalid assistant message with tool_calls at index {i} "
                            f"(predecessor: {predecessor_role}). Tool names: {tool_names}"
                        )
                else:
                    # Assistant without tool_calls - always keep, reset tracking
                    valid_tool_call_ids.clear()
                    fixed_messages.append(msg)
                    last_non_system_in_fixed = "assistant"
            
            # Handle tool messages
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id")
                if isinstance(tool_call_id, str) and tool_call_id in valid_tool_call_ids:
                    # Valid tool message - has matching tool_call_id from a kept assistant message
                    fixed_messages.append(msg)
                    last_non_system_in_fixed = "tool"
                else:
                    # Orphaned tool message - remove it
                    removed_count += 1
                    logger.debug(
                        f"Removing orphaned tool message with tool_call_id '{tool_call_id}' "
                        f"(no valid preceding assistant message with matching tool_calls)"
                    )
            
            # User messages are always included
            elif role == "user":
                # User messages reset the tool call context
                valid_tool_call_ids.clear()
                fixed_messages.append(msg)
                last_non_system_in_fixed = "user"
            else:
                # Unknown role - include it (might be custom roles)
                fixed_messages.append(msg)
                last_non_system_in_fixed = role
        
        return fixed_messages, removed_count
    
    def _fix_gemini_tool_call_ordering(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fix Gemini-specific tool call ordering by removing invalid assistant messages.
        
        Gemini API requires that assistant messages with tool_calls must come
        immediately after either a user message or a tool message. This function
        iteratively removes assistant messages with tool_calls that violate this requirement,
        along with their associated tool messages, until no more invalid messages remain.
        
        Uses iterative approach to handle cascading invalidations that occur when
        removing messages makes subsequent messages invalid.
        
        Args:
            messages: List of messages (may contain invalid assistant messages with tool_calls)
            
        Returns:
            List of messages with invalid assistant messages and their tool messages removed
        """
        if not messages:
            return messages
        
        # Log message structure before fixing
        msg_summary = [
            f"{i}:{msg.get('role', 'unknown')}" + 
            (f"[tool_calls={len(msg.get('tool_calls', []))}]" if msg.get('tool_calls') else "") +
            (f"[tool_call_id={msg.get('tool_call_id', '')[:20]}]" if msg.get('tool_call_id') else "")
            for i, msg in enumerate(messages)
        ]
        logger.info(
            "Applying Gemini tool call ordering fix",
            extra={
                "event": "gemini_fix_applied",
                "messages_before": len(messages),
                "message_structure": " -> ".join(msg_summary[:10]) + ("..." if len(msg_summary) > 10 else ""),
            }
        )
        
        MAX_ITERATIONS = 10
        current_messages = messages
        total_removed = 0
        iteration = 0
        
        # Iteratively fix until no more messages are removed
        for iteration in range(MAX_ITERATIONS):
            fixed_messages, removed_count = self._fix_gemini_tool_call_ordering_single_pass(current_messages)
            total_removed += removed_count
            
            if removed_count == 0:
                # No more invalid messages found - we're done
                break
            
            # Messages were removed, so we need another pass to check if this created new invalidations
            current_messages = fixed_messages
            
            if iteration < MAX_ITERATIONS - 1:
                logger.debug(
                    f"Gemini fix pass {iteration + 1}: removed {removed_count} message(s), "
                    f"continuing with {len(fixed_messages)} remaining messages"
                )
        
        if iteration >= MAX_ITERATIONS - 1 and removed_count > 0:
            logger.warning(
                f"Gemini fix reached max iterations ({MAX_ITERATIONS}), "
                f"may still have invalid messages"
            )
        
        # Log final results
        if total_removed > 0:
            msg_summary_after = [
                f"{i}:{msg.get('role', 'unknown')}" + 
                (f"[tool_calls={len(msg.get('tool_calls', []))}]" if msg.get('tool_calls') else "") +
                (f"[tool_call_id={msg.get('tool_call_id', '')[:20]}]" if msg.get('tool_call_id') else "")
                for i, msg in enumerate(current_messages)
            ]
            logger.info(
                f"Gemini fix completed after {iteration + 1} pass(es): removed {total_removed} invalid message(s) total",
                extra={
                    "event": "gemini_fix_completed",
                    "messages_before": len(messages),
                    "messages_after": len(current_messages),
                    "removed_count": total_removed,
                    "iterations": iteration + 1,
                    "message_structure_after": " -> ".join(msg_summary_after[:10]) + ("..." if len(msg_summary_after) > 10 else ""),
                }
            )
        
        # Defensive validation check
        is_valid, error = self._validate_message_ordering(current_messages, check_gemini_ordering=True)
        if not is_valid:
            logger.warning(
                f"Message ordering still invalid after fix: {error}. "
                "Proceeding anyway, but API call may fail."
            )
        
        # Guard: Ensure at least one non-system message remains after the fix
        # The Gemini API requires at least one content message (user or assistant with content)
        non_system_messages = [msg for msg in current_messages if msg.get("role") != "system"]
        if not non_system_messages:
            # All non-system messages were removed - try to preserve meaningful context
            # by keeping the most recent user message and last tool call sequence
            preserved_context = self._find_minimal_preserved_context(messages)
            if preserved_context:
                logger.warning(
                    f"Gemini fix removed all non-system messages. Preserving minimal context "
                    f"({len(preserved_context)} message(s): most recent user + last tool call sequence) "
                    "to ensure API call has meaningful context.",
                    extra={
                        "event": "gemini_fix_guard_triggered",
                        "preserved_message_count": len(preserved_context),
                        "preserved_roles": [msg.get("role") for msg in preserved_context],
                        "messages_before_fix": len(messages),
                        "messages_after_fix_before_guard": len(current_messages),
                    }
                )
                # Add the preserved context after system messages
                system_messages = [msg for msg in current_messages if msg.get("role") == "system"]
                # Ensure only one system message before concatenation
                if len(system_messages) > 1:
                    logger.warning(
                        f"Found {len(system_messages)} system messages in Gemini fix. "
                        "Keeping only the first.",
                        extra={
                            "event": "multiple_system_messages_in_gemini_fix",
                            "count": len(system_messages),
                        }
                    )
                    system_messages = [system_messages[0]]
                current_messages = system_messages + preserved_context
                # Validate concatenated result
                self._validate_message_list_for_system_messages(current_messages)
            else:
                # Fallback to finding just the most recent content message
                fallback_message = self._find_most_recent_content_message(messages)
                if fallback_message:
                    logger.warning(
                        "Gemini fix removed all non-system messages. Preserving most recent content message "
                        f"({fallback_message.get('role')}) to ensure API call can succeed.",
                        extra={
                            "event": "gemini_fix_guard_triggered_fallback",
                            "fallback_role": fallback_message.get("role"),
                            "fallback_has_content": bool(fallback_message.get("content")),
                            "messages_before_fix": len(messages),
                            "messages_after_fix_before_guard": len(current_messages),
                        }
                    )
                    system_messages = [msg for msg in current_messages if msg.get("role") == "system"]
                    if len(system_messages) > 1:
                        system_messages = [system_messages[0]]
                    current_messages = system_messages + [fallback_message]
                    self._validate_message_list_for_system_messages(current_messages)
                else:
                    # Last resort - inject a default user message to prevent API error
                    logger.warning(
                        "Gemini fix removed all non-system messages and no valid content message found. "
                        "Injecting default user message to prevent API error.",
                        extra={
                            "event": "gemini_fix_injecting_default_message",
                            "messages_before_fix": len(messages),
                            "messages_after_fix": len(current_messages),
                        }
                    )
                    system_messages = [msg for msg in current_messages if msg.get("role") == "system"]
                    if len(system_messages) > 1:
                        logger.warning(
                            f"Found {len(system_messages)} system messages in Gemini fix fallback. "
                            "Keeping only the first.",
                            extra={
                                "event": "multiple_system_messages_in_gemini_fix_fallback",
                                "count": len(system_messages),
                            }
                        )
                        system_messages = [system_messages[0]]
                    default_message = {"role": "user", "content": "Please continue the conversation."}
                    current_messages = system_messages + [default_message]
                    # Validate concatenated result
                    self._validate_message_list_for_system_messages(current_messages)
        
        return current_messages
    
    def _truncate_tool_results_in_messages(
        self, messages: List[Dict[str, Any]], max_tool_result_size: int
    ) -> List[Dict[str, Any]]:
        """
        Truncate tool result content in messages if they exceed size limit.
        
        Args:
            messages: List of messages
            max_tool_result_size: Maximum size for tool result content
            
        Returns:
            List of messages with tool results truncated
        """
        truncated = []
        for msg in messages:
            if msg.get("role") == "tool":
                truncated_msg = truncate_tool_result(msg, max_tool_result_size)
                truncated.append(truncated_msg)
            else:
                truncated.append(msg)
        return truncated
    
    def _validate_message_size(
        self, messages: List[Dict[str, Any]], max_tokens: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Validate and truncate messages to ensure they're under token limit.
        
        Pre-flight check before sending to LLM API. Estimates tokens and truncates
        tool results if needed. Logs warnings when truncation occurs.
        
        Args:
            messages: List of messages to validate
            max_tokens: Maximum token limit (defaults to config.llm.max_context_tokens)
            
        Returns:
            Validated messages with tool results truncated if needed
        """
        from ..config import config
        
        if max_tokens is None:
            max_tokens = config.llm.max_context_tokens
        
        # Estimate tokens
        estimated_tokens = estimate_messages_tokens(messages)
        
        # If under limit, just truncate tool results as safety measure
        if estimated_tokens <= max_tokens:
            truncated = self._truncate_tool_results_in_messages(
                messages, config.summarization.max_tool_result_size
            )
            return truncated
        
        # Over limit - truncate tool results
        logger.warning(
            f"Messages exceed token limit ({estimated_tokens} > {max_tokens}), "
            f"truncating tool results"
        )
        
        truncated = self._truncate_tool_results_in_messages(
            messages, config.summarization.max_tool_result_size
        )
        
        # Re-estimate after truncation
        estimated_after = estimate_messages_tokens(truncated)
        
        if estimated_after > max_tokens:
            logger.warning(
                f"Messages still exceed token limit after truncation "
                f"({estimated_after} > {max_tokens}). Applying aggressive token filtering as failsafe."
            )
            # Apply aggressive token-aware filtering as failsafe
            # This will remove messages if needed to stay under limit
            truncated = self._apply_token_aware_filtering(truncated, max_tokens)
            final_estimated = estimate_messages_tokens(truncated)
            logger.info(
                f"Failsafe filtering complete: {estimated_tokens} -> {final_estimated} tokens "
                f"(limit: {max_tokens})"
            )
        else:
            logger.info(
                f"Messages truncated successfully: {estimated_tokens} -> {estimated_after} tokens"
            )
        
        return truncated

    def _validate_message_ordering(self, messages: List[Dict[str, Any]], check_gemini_ordering: bool = False) -> tuple[bool, Optional[str]]:
        """
        Validate that message ordering follows API requirements.
        
        OpenAI API requires that tool messages must follow an assistant message
        with tool_calls. This function validates that requirement.
        
        Gemini API has stricter requirements: assistant messages with tool_calls
        must come immediately after either a user message or a tool message.
        
        Args:
            messages: List of message dictionaries to validate
            check_gemini_ordering: If True, also validate Gemini-specific ordering requirements
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if messages are valid, False otherwise
            - error_message: None if valid, error description if invalid
        """
        if not messages:
            return True, None
        
        # Track which tool_call_ids we've seen in assistant messages
        seen_tool_call_ids = set()
        
        # Track the last assistant message with tool_calls
        last_assistant_with_tool_calls = None
        
        for i, msg in enumerate(messages):
            role = msg.get("role")
            
            # Skip system messages (they don't affect tool message ordering)
            if role == "system":
                continue
            
            # Handle assistant messages
            if role == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    # Validate tool_calls structure
                    if not isinstance(tool_calls, list):
                        return False, f"Message {i}: tool_calls must be a list, got {type(tool_calls)}"
                    
                    # Gemini-specific validation: assistant messages with tool_calls must
                    # come immediately after a user message or a tool message
                    if check_gemini_ordering:
                        # Find the immediately preceding non-system message
                        found_valid_predecessor = False
                        predecessor_index = -1
                        predecessor_role = None
                        for j in range(i - 1, -1, -1):
                            prev_msg = messages[j]
                            prev_role = prev_msg.get("role")
                            if prev_role == "system":
                                continue
                            # Valid predecessor: user or tool message
                            if prev_role in ("user", "tool"):
                                found_valid_predecessor = True
                                predecessor_index = j
                                predecessor_role = prev_role
                                break
                            # If we hit an assistant message (with or without tool_calls), it's invalid
                            elif prev_role == "assistant":
                                found_valid_predecessor = False
                                predecessor_index = j
                                predecessor_role = prev_role
                                break
                        
                        if not found_valid_predecessor:
                            tool_names = [
                                tc.get("function", {}).get("name", "unknown")
                                for tc in tool_calls if isinstance(tc, dict)
                            ]
                            error_msg = (
                                f"Message {i}: Gemini API requires assistant messages with tool_calls "
                                "to come immediately after a user message or a tool message"
                            )
                            logger.warning(
                                error_msg,
                                extra={
                                    "event": "gemini_validation_failed",
                                    "message_index": i,
                                    "predecessor_index": predecessor_index,
                                    "predecessor_role": predecessor_role,
                                    "tool_names": tool_names,
                                    "tool_calls_count": len(tool_calls),
                                }
                            )
                            return False, error_msg
                        else:
                            logger.debug(
                                f"Gemini validation passed for assistant message with tool_calls at index {i} "
                                f"(predecessor: {predecessor_role} at index {predecessor_index})",
                                extra={
                                    "event": "gemini_validation_passed",
                                    "message_index": i,
                                    "predecessor_index": predecessor_index,
                                    "predecessor_role": predecessor_role,
                                }
                            )
                    
                    # Extract tool_call_ids from this assistant message
                    current_tool_call_ids = set()
                    for tool_call in tool_calls:
                        if not isinstance(tool_call, dict):
                            return False, f"Message {i}: tool_calls must contain dictionaries"
                        
                        tool_call_id = tool_call.get("id")
                        if tool_call_id is None:
                            return False, f"Message {i}: tool_call missing 'id' field"
                        
                        if not isinstance(tool_call_id, str):
                            return False, f"Message {i}: tool_call 'id' must be a string, got {type(tool_call_id)}"
                        
                        current_tool_call_ids.add(tool_call_id)
                    
                    # Update tracking
                    seen_tool_call_ids.update(current_tool_call_ids)
                    last_assistant_with_tool_calls = i
                else:
                    # Assistant without tool_calls - reset tracking
                    last_assistant_with_tool_calls = None
                    seen_tool_call_ids.clear()
            
            # Handle tool messages
            elif role == "tool":
                # Tool message must have a tool_call_id
                tool_call_id = msg.get("tool_call_id")
                
                # CRITICAL: Tool message must follow an assistant message with tool_calls
                # Check if there's a preceding assistant message with tool_calls
                has_preceding_assistant = False
                for j in range(i - 1, -1, -1):
                    prev_msg = messages[j]
                    if prev_msg.get("role") == "system":
                        continue
                    if prev_msg.get("role") == "assistant":
                        prev_tool_calls = prev_msg.get("tool_calls")
                        if prev_tool_calls and isinstance(prev_tool_calls, list):
                            # Check if this tool_call_id is in the preceding assistant's tool_calls
                            prev_tool_call_ids = {
                                tc.get("id") for tc in prev_tool_calls
                                if isinstance(tc, dict) and isinstance(tc.get("id"), str)
                            }
                            if tool_call_id in prev_tool_call_ids:
                                has_preceding_assistant = True
                                break
                        # If assistant doesn't have tool_calls, stop looking
                        break
                    elif prev_msg.get("role") == "user":
                        # User message resets context - no valid preceding assistant
                        break
                
                if not has_preceding_assistant:
                    return False, (
                        f"Message {i}: Tool message with tool_call_id '{tool_call_id}' "
                        "has no preceding assistant message with matching tool_calls. "
                        "Tool messages must immediately follow an assistant message that contains tool_calls with this tool_call_id."
                    )
                if tool_call_id is None:
                    return False, f"Message {i}: tool message missing 'tool_call_id' field"
                
                if not isinstance(tool_call_id, str):
                    return False, f"Message {i}: tool message 'tool_call_id' must be a string, got {type(tool_call_id)}"
                
                # Check if this tool_call_id was seen in a preceding assistant message with tool_calls
                if tool_call_id not in seen_tool_call_ids:
                    # Check if there's an assistant message with tool_calls before this tool message
                    found_preceding_assistant = False
                    for j in range(i - 1, -1, -1):
                        prev_msg = messages[j]
                        if prev_msg.get("role") == "system":
                            continue
                        if prev_msg.get("role") == "assistant":
                            prev_tool_calls = prev_msg.get("tool_calls")
                            if prev_tool_calls and isinstance(prev_tool_calls, list):
                                prev_tool_call_ids = {
                                    tc.get("id") for tc in prev_tool_calls
                                    if isinstance(tc, dict) and isinstance(tc.get("id"), str)
                                }
                                if tool_call_id in prev_tool_call_ids:
                                    found_preceding_assistant = True
                                    break
                            # If assistant doesn't have tool_calls, stop looking
                            break
                        elif prev_msg.get("role") in ("user", "tool"):
                            # Continue looking backwards
                            continue
                    
                    if not found_preceding_assistant:
                        return False, (
                            f"Message {i}: tool message with tool_call_id '{tool_call_id}' "
                            "does not follow an assistant message with matching tool_calls"
                        )
            
            # User messages don't need special validation for tool ordering
            elif role == "user":
                # User messages reset the tool call context
                last_assistant_with_tool_calls = None
                seen_tool_call_ids.clear()
        
        return True, None
    
    def _normalize_world_state_for_hash(self, world_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize world state for stable hashing by removing volatile fields.
        
        Removes timestamp fields and other volatile data that changes frequently
        but doesn't represent meaningful state changes. This ensures hash stability
        when only timestamps change but meaningful content remains the same.
        
        Args:
            world_state: Raw world state dictionary
            
        Returns:
            Normalized world state dictionary suitable for hashing
        """
        def normalize_value(value: Any) -> Any:
            """Recursively normalize values, removing timestamps."""
            if isinstance(value, dict):
                normalized = {}
                for k, v in value.items():
                    # Skip timestamp fields
                    if k in ("timestamp", "last_indexed", "last_scan", "last_updated"):
                        continue
                    normalized[k] = normalize_value(v)
                return normalized
            elif isinstance(value, list):
                return [normalize_value(item) for item in value]
            else:
                return value
        
        normalized = normalize_value(world_state)
        return normalized
    
    def _calculate_stable_world_state_hash(self, world_state: Dict[str, Any]) -> str:
        """
        Calculate stable hash of world state using normalized data and deterministic JSON.
        
        Uses JSON serialization with sorted keys to ensure deterministic output,
        and normalizes the world state to exclude volatile timestamp fields.
        
        Args:
            world_state: World state dictionary
            
        Returns:
            SHA256 hash hex digest
        """
        import hashlib
        import json
        
        normalized = self._normalize_world_state_for_hash(world_state)
        # Use JSON with sorted keys for deterministic serialization
        json_str = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _clean_base_prompt(contaminated_prompt: str) -> str:
        """
        Extract clean base prompt from contaminated storage data.
        
        Removes world state JSON, summary context, and truncation messages
        that may have been incorrectly stored as part of the base prompt.
        
        Args:
            contaminated_prompt: Potentially contaminated base prompt string
            
        Returns:
            Clean base prompt with all JSON/world state/summary content removed
        """
        if not contaminated_prompt:
            return ""
        
        import json
        import re
        
        cleaned = contaminated_prompt
        
        # Remove any JSON objects (world state) - look for { ... } patterns
        # Try to find where JSON starts and remove everything from there
        json_start_patterns = [
            r'\n\s*\{',  # Newline followed by opening brace
            r'\n\n\s*\{',  # Double newline followed by opening brace
            r'^\s*\{',  # Start of string with opening brace
        ]
        
        for pattern in json_start_patterns:
            match = re.search(pattern, cleaned)
            if match:
                # Found JSON start - keep everything before it
                cleaned = cleaned[:match.start()].rstrip()
                break
        
        # Remove summary context markers
        summary_markers = [
            "## Session Summary",
            "Historical Context",
            "Session Summary (Historical Context)",
        ]
        for marker in summary_markers:
            if marker in cleaned:
                # Find where summary starts and remove everything from there
                idx = cleaned.find(marker)
                if idx > 0:
                    # Try to find the section start (## or similar)
                    section_start = cleaned.rfind("\n##", 0, idx)
                    if section_start >= 0:
                        cleaned = cleaned[:section_start].rstrip()
                    else:
                        cleaned = cleaned[:idx].rstrip()
        
        # Remove truncation messages (they shouldn't be in base prompt)
        truncation_messages = [
            "[Base system prompt truncated due to size limit]",
            "[System prompt truncated due to size limit]",
            "[World state omitted due to size limit]",
            "[Summary context truncated due to size limit]",
        ]
        for msg in truncation_messages:
            cleaned = cleaned.replace(msg, "").strip()
        
        # Remove any trailing JSON-like content
        # Look for patterns like "}\n\n{" which indicate multiple JSON objects
        if re.search(r'\}\s*\n\s*\n\s*\{', cleaned):
            # Multiple JSON objects detected - remove all JSON
            # Find the last non-JSON content
            parts = re.split(r'\}\s*\n\s*\n\s*\{', cleaned)
            if parts:
                cleaned = parts[0].rstrip()
                # Remove any trailing brace
                cleaned = re.sub(r'\}\s*$', '', cleaned).rstrip()
        
        # Final cleanup: remove any remaining JSON structure
        # If the cleaned string still looks like it starts with JSON, it's all contaminated
        cleaned_stripped = cleaned.strip()
        if cleaned_stripped.startswith('{') or cleaned_stripped.startswith('['):
            # Entire prompt is JSON - return empty (no valid base prompt)
            logger.warning(
                "Base prompt appears to be entirely JSON/world state - returning empty base prompt",
                extra={
                    "event": "base_prompt_entirely_contaminated",
                    "original_length": len(contaminated_prompt),
                }
            )
            return ""
        
        # Validate that we actually have content left
        if len(cleaned) < len(contaminated_prompt) * 0.1:
            # Less than 10% of original - likely all was contamination
            logger.warning(
                "Base prompt cleaning removed >90% of content - likely all was contamination",
                extra={
                    "event": "base_prompt_mostly_contaminated",
                    "original_length": len(contaminated_prompt),
                    "cleaned_length": len(cleaned),
                }
            )
        
        return cleaned.strip()
    
    def _update_system_prompt(self) -> None:
        """
        Update system prompt with current world state and session summary.

        Aggregates world state from all available sources and updates
        the system message in the conversation. If no system message exists,
        creates one. If world state aggregator is not available, does nothing.

        The system prompt consists of:
        1. Base system prompt (if configured) - user-defined invariants
        2. Session summary context (if summarization enabled) - rolling summary
        3. Formatted world state JSON - dynamic content with consistent structure

        Implements size limits, deduplication, and hash-based change detection
        to prevent unbounded growth and duplicate content.
        """
        if not self.world_state_aggregator or not self._world_state_formatter:
            return

        try:
            from ..config import config
            
            # Runtime monitoring: validate state before update
            self._validate_before_update()
            # Ensure single system message before update (fixes any accumulation issues)
            self._ensure_single_system_message()
            
            # Aggregate current world state
            world_state = self.world_state_aggregator.aggregate()

            # Calculate stable hash of world state to detect changes
            world_state_hash = self._calculate_stable_world_state_hash(world_state)
            
            # Skip update if world state hasn't changed (hash-based change detection)
            if world_state_hash == self._last_world_state_hash:
                logger.debug("World state unchanged, skipping system prompt update")
                return
            
            self._last_world_state_hash = world_state_hash
            self._last_world_state_raw = world_state

            # Format world state for prompt (formatter handles its own size limits)
            formatted_world_state = self._world_state_formatter.format(world_state)

            # Combine base prompt, summary context, and world state
            parts = []
            
            # 1. Base system prompt (only include once, no duplicates)
            # Enforce size limit to prevent unbounded growth
            if self.base_system_prompt:
                base_prompt = self.base_system_prompt.strip()
                if base_prompt:
                    max_base_size = config.storage.max_base_prompt_size
                    base_prompt_size = len(base_prompt)
                    
                    # Validate that base prompt hasn't grown unbounded since initialization
                    if hasattr(self, '_initial_base_prompt_size'):
                        growth_ratio = base_prompt_size / self._initial_base_prompt_size if self._initial_base_prompt_size > 0 else 1.0
                        if growth_ratio > 1.1:  # More than 10% growth
                            logger.warning(
                                f"Base system prompt has grown {growth_ratio:.1f}x since initialization "
                                f"({self._initial_base_prompt_size} -> {base_prompt_size} chars). "
                                "This may indicate unbounded growth. Base prompt should be immutable.",
                                extra={
                                    "event": "base_prompt_growth_detected",
                                    "initial_size": self._initial_base_prompt_size,
                                    "current_size": base_prompt_size,
                                    "growth_ratio": round(growth_ratio, 2),
                                }
                            )
                    
                    if base_prompt_size > max_base_size:
                        # Truncate base prompt intelligently
                        truncated_base = base_prompt[:max_base_size - 50]  # Leave room for truncation message
                        # Try to truncate at a paragraph boundary
                        last_double_newline = truncated_base.rfind("\n\n")
                        if last_double_newline > max_base_size * 0.7:  # Only if we're keeping most of it
                            truncated_base = truncated_base[:last_double_newline]
                        else:
                            # Fallback to single newline
                            last_newline = truncated_base.rfind("\n")
                            if last_newline > max_base_size * 0.8:
                                truncated_base = truncated_base[:last_newline]
                        
                        # Check if truncation message already exists to prevent accumulation
                        truncation_msg = "[Base system prompt truncated due to size limit]"
                        if truncation_msg not in truncated_base:
                            base_prompt = truncated_base + "\n" + truncation_msg
                        else:
                            # Already has truncation message - don't add another
                            base_prompt = truncated_base
                        logger.warning(
                            f"Base system prompt truncated from {base_prompt_size} to {len(base_prompt)} characters "
                            f"(limit: {max_base_size})"
                        )
                    
                    parts.append(base_prompt)
            
            # 1.5. Add tool calling behavior instructions
            # This ensures the LLM understands it should automatically continue after tool results
            tool_calling_instructions = """## TOOL CALLING BEHAVIOR

When you need to use tools to complete a task:
- You can provide brief commentary alongside tool calls (e.g., "Let me check that file..." or "I'll examine the code...")
- After tool calls complete and results are returned, AUTOMATICALLY continue - do not wait for user input
- Review tool results and either:
  * Make additional tool calls if more information is needed
  * Provide your final comprehensive response to the user
- Continue this loop automatically until you have a complete answer to provide
- Only provide a final text response (with no tool calls) when you're ready to answer the user's question
- The system will automatically continue after tool results are returned - you don't need to wait for explicit "proceed" or "continue" prompts"""
            
            parts.append(tool_calling_instructions)
            
            # 2. Add summary context if summarization is enabled
            if self._summarization_manager:
                try:
                    from ..summarization.prompt_builder import PromptBuilder
                    
                    prompt_builder = PromptBuilder(
                        summary_storage=self._summarization_manager.summary_storage,
                        last_turns_count=config.summarization.last_turns_count
                    )
                    # Get summary context (without base system prompt to avoid duplication)
                    summary_context = prompt_builder.build_context(
                        self.session_id,
                        self.messages,
                        system_prompt=None
                    )
                    if summary_context and summary_context.strip():
                        # Deduplicate: check if summary context duplicates base prompt
                        summary_clean = summary_context.strip()
                        if not self.base_system_prompt or not self._is_duplicate_content(
                            summary_clean, self.base_system_prompt
                        ):
                            parts.append(summary_context)
                except Exception as e:
                    logger.debug(f"Failed to add summary context to prompt: {e}", exc_info=True)
            
            # 3. World state JSON
            if formatted_world_state and formatted_world_state.strip():
                parts.append(formatted_world_state)

            # Pre-validate component sizes before combining
            # This prevents unbounded growth by checking totals before combination
            max_size = config.storage.max_system_prompt_size
            component_sizes = [len(part) for part in parts]
            total_size = sum(component_sizes)
            separator_size = len("\n\n") * (len(parts) - 1) if len(parts) > 1 else 0
            estimated_total = total_size + separator_size
            
            # Log component sizes for monitoring
            logger.debug(
                "System prompt component sizes",
                extra={
                    "event": "system_prompt_component_sizes",
                    "base_prompt_size": component_sizes[0] if len(parts) > 0 else 0,
                    "summary_context_size": component_sizes[1] if len(parts) > 1 else 0,
                    "world_state_size": component_sizes[2] if len(parts) > 2 else 0,
                    "total_components": len(parts),
                    "estimated_total_size": estimated_total,
                    "max_size": max_size,
                }
            )
            
            # If estimated total exceeds limit, reduce components intelligently
            # Priority: base prompt > summary context > world state
            if estimated_total > max_size:
                logger.warning(
                    f"System prompt components exceed limit ({estimated_total} > {max_size}), "
                    "reducing component sizes"
                )
                
                # Calculate available space (leave some buffer for separators)
                available_space = max_size - 100  # 100 char buffer for separators and truncation messages
                
                # Strategy: Preserve base prompt, reduce summary and world state proportionally
                if len(parts) >= 1:
                    base_size = component_sizes[0]
                    remaining_space = available_space - base_size
                    
                    if remaining_space < 0:
                        # Base prompt alone exceeds limit - it was already truncated above
                        # Just keep base prompt
                        parts = [parts[0]]
                    elif len(parts) >= 2:
                        # We have summary context and/or world state
                        # Allocate remaining space: 40% to summary, 60% to world state (if both exist)
                        if len(parts) == 3:
                            # Both summary and world state exist
                            summary_target = int(remaining_space * 0.4)
                            world_state_target = remaining_space - summary_target
                            
                            # Truncate summary context if needed
                            if component_sizes[1] > summary_target:
                                summary_part = parts[1]
                                truncated_summary = summary_part[:summary_target - 50]
                                last_section = truncated_summary.rfind("##")
                                if last_section > summary_target * 0.7:
                                    truncated_summary = truncated_summary[:last_section]
                                # Check if truncation message already exists to prevent accumulation
                                truncation_msg = "[Summary context truncated due to size limit]"
                                if truncation_msg not in truncated_summary:
                                    parts[1] = truncated_summary + "\n" + truncation_msg
                                else:
                                    parts[1] = truncated_summary
                                logger.warning(
                                    f"Summary context reduced from {component_sizes[1]} to {len(parts[1])} characters"
                                )
                            
                            # Truncate world state if needed
                            if component_sizes[2] > world_state_target:
                                world_state_part = parts[2]
                                truncated_world_state = world_state_part[:world_state_target - 50]
                                # Try to truncate at JSON boundary
                                last_brace = truncated_world_state.rfind("}")
                                if last_brace > world_state_target * 0.8:
                                    truncated_world_state = truncated_world_state[:last_brace + 1]
                                else:
                                    truncated_world_state = truncated_world_state.rstrip() + '\n}'
                                truncated_world_state += '\n  "_truncated": true\n}'
                                parts[2] = truncated_world_state
                                logger.warning(
                                    f"World state reduced from {component_sizes[2]} to {len(parts[2])} characters"
                                )
                        elif len(parts) == 2:
                            # Only one of summary or world state
                            if component_sizes[1] > remaining_space:
                                part_to_truncate = parts[1]
                                truncated = part_to_truncate[:remaining_space - 50]
                                # Try to truncate at a reasonable boundary
                                last_newline = truncated.rfind("\n")
                                if last_newline > remaining_space * 0.8:
                                    truncated = truncated[:last_newline]
                                # Check if truncation message already exists to prevent accumulation
                                truncation_msg = "[Component truncated due to size limit]"
                                if truncation_msg not in truncated:
                                    parts[1] = truncated + "\n" + truncation_msg
                                else:
                                    parts[1] = truncated
                                logger.warning(
                                    f"Component reduced from {component_sizes[1]} to {len(parts[1])} characters"
                                )

            # Join with double newline if multiple parts exist
            if len(parts) > 1:
                complete_prompt = "\n\n".join(parts)
            elif len(parts) == 1:
                complete_prompt = parts[0]
            else:
                complete_prompt = ""

            # Apply overall size limit and truncation if needed (final safety check)
            original_size = len(complete_prompt)
            if original_size > max_size:
                # Truncate intelligently: preserve base prompt if possible, truncate world state
                if len(parts) > 1:
                    # Check if base prompt alone exceeds limit
                    base_prompt_size = len(parts[0]) if parts else 0
                    if base_prompt_size > max_size:
                        # Base prompt is too large, truncate it directly
                        truncated_base = parts[0][:max_size - 50]  # Leave room for truncation message
                        last_newline = truncated_base.rfind("\n")
                        if last_newline > (max_size - 50) * 0.8:
                            truncated_base = truncated_base[:last_newline]
                        # Check if truncation message already exists to prevent accumulation
                        truncation_msg = "[System prompt truncated due to size limit]"
                        if truncation_msg not in truncated_base:
                            complete_prompt = truncated_base + "\n" + truncation_msg
                        else:
                            complete_prompt = truncated_base
                    else:
                        # Keep base prompt and summary, truncate world state
                        base_and_summary = "\n\n".join(parts[:-1])  # All except world state
                        world_state_part = parts[-1]
                        available_for_world_state = max_size - len(base_and_summary) - 10  # 10 for separator
                        
                        if available_for_world_state > 100:  # Only if we have reasonable space
                            # Truncate world state JSON
                            truncated_world_state = world_state_part[:available_for_world_state]
                            # Try to truncate at a JSON boundary
                            last_brace = truncated_world_state.rfind("}")
                            if last_brace > available_for_world_state * 0.8:
                                truncated_world_state = truncated_world_state[:last_brace + 1]
                            else:
                                truncated_world_state = truncated_world_state.rstrip() + '\n}'
                            truncated_world_state += '\n  "_truncated": true\n}'
                            complete_prompt = base_and_summary + "\n\n" + truncated_world_state
                        else:
                            # Too little space, just keep base and summary
                            complete_prompt = base_and_summary + "\n\n[World state omitted due to size limit]"
                else:
                    # Single part, truncate directly
                    complete_prompt = complete_prompt[:max_size - 50]  # Leave room for message
                    # Try to truncate at a reasonable boundary
                    last_newline = complete_prompt.rfind("\n")
                    if last_newline > (max_size - 50) * 0.8:
                        complete_prompt = complete_prompt[:last_newline]
                    # Check if truncation message already exists to prevent accumulation
                    truncation_msg = "[System prompt truncated due to size limit]"
                    if truncation_msg not in complete_prompt:
                        complete_prompt += "\n" + truncation_msg
                
                logger.warning(
                    f"System prompt truncated from {original_size} to {len(complete_prompt)} characters "
                    f"(limit: {max_size})"
                )

            # Validate: check for duplicate sections within the prompt itself
            self._validate_system_prompt_for_duplicates(complete_prompt)
            
            # Validate: ensure we're not duplicating existing content
            # Check for ANY system messages (there should only be one, but handle multiple)
            existing_system_messages = [i for i, msg in enumerate(self.messages) if msg.get("role") == "system"]
            existing_system_content = None
            if existing_system_messages:
                # Use the first system message's content for comparison
                existing_system_content = self.messages[existing_system_messages[0]].get("content", "")
            
            # Only update if content actually changed (avoid unnecessary updates)
            if existing_system_content != complete_prompt:
                # Remove ALL system messages first (handle multiple system messages bug)
                # This ensures we always REPLACE, never append
                if existing_system_messages:
                    # Remove in reverse order to maintain indices
                    for idx in reversed(existing_system_messages):
                        removed_msg = self.messages.pop(idx)
                        logger.debug(
                            f"Removed system message at index {idx} before replacing",
                            extra={
                                "event": "system_message_removed",
                                "removed_content_length": len(removed_msg.get("content", "")),
                            }
                        )
                    
                    # Log warning if multiple system messages were found
                    if len(existing_system_messages) > 1:
                        logger.warning(
                            f"Found {len(existing_system_messages)} system messages - removed all before replacing. "
                            "This indicates a bug where system messages were being appended instead of replaced.",
                            extra={
                                "event": "multiple_system_messages_detected",
                                "count": len(existing_system_messages),
                            }
                        )
                
                # Insert new system message at the beginning (always at index 0)
                self.messages.insert(0, {"role": "system", "content": complete_prompt})
                
                # Runtime monitoring: validate state after update
                self._validate_after_update(complete_prompt)
                
                # Validate: ensure only ONE system message exists after update
                system_msg_count = sum(1 for msg in self.messages if msg.get("role") == "system")
                if system_msg_count != 1:
                    logger.error(
                        f"CRITICAL: After system prompt update, found {system_msg_count} system messages "
                        f"(expected 1). This is a bug.",
                        extra={
                            "event": "multiple_system_messages_after_update",
                            "count": system_msg_count,
                        }
                    )

                # Log system prompt size for monitoring with detailed component breakdown
                prompt_size = len(complete_prompt)
                size_kb = prompt_size / 1024
                max_size_kb = config.storage.max_system_prompt_size / 1024
                
                # Calculate final component sizes for logging
                final_parts = complete_prompt.split("\n\n")
                final_component_sizes = [len(part) for part in final_parts]
                
                # Build detailed logging context
                log_extra = {
                    "event": "system_prompt_updated",
                    "total_size": prompt_size,
                    "total_size_kb": round(size_kb, 2),
                    "max_size": config.storage.max_system_prompt_size,
                    "max_size_kb": round(max_size_kb, 2),
                    "size_percentage": round(prompt_size / config.storage.max_system_prompt_size * 100, 1),
                    "component_count": len(final_parts),
                }
                
                # Add component sizes if we have them
                if len(final_parts) >= 1:
                    log_extra["base_prompt_size"] = final_component_sizes[0]
                if len(final_parts) >= 2:
                    log_extra["summary_context_size"] = final_component_sizes[1]
                if len(final_parts) >= 3:
                    log_extra["world_state_size"] = final_component_sizes[2]
                
                if prompt_size > config.storage.max_system_prompt_size * 0.9:
                    logger.warning(
                        f"System prompt size is {size_kb:.1f}KB (90% of {max_size_kb:.1f}KB limit) - "
                        f"consider reducing content",
                        extra=log_extra
                    )
                elif prompt_size > config.storage.max_system_prompt_size * 0.7:
                    logger.info(
                        f"System prompt size is {size_kb:.1f}KB ({prompt_size / config.storage.max_system_prompt_size * 100:.0f}% of limit)",
                        extra=log_extra
                    )
                else:
                    logger.debug(
                        f"Updated system prompt with current world state and summary context "
                        f"(size: {prompt_size} chars, {size_kb:.1f}KB)",
                        extra=log_extra
                    )
            else:
                logger.debug("System prompt content unchanged, skipping update")

        except Exception as e:
            logger.warning(
                f"Error updating system prompt with world state: {e}", exc_info=True
            )
            # Continue with existing system prompt on error
    
    def _is_duplicate_content(self, content1: str, content2: str, threshold: float = 0.8) -> bool:
        """
        Check if two content strings are duplicates or highly similar.
        
        Args:
            content1: First content string
            content2: Second content string
            threshold: Similarity threshold (0.0-1.0) for considering content duplicate
            
        Returns:
            True if content is considered duplicate, False otherwise
        """
        if not content1 or not content2:
            return False
        
        # Normalize whitespace
        norm1 = " ".join(content1.split())
        norm2 = " ".join(content2.split())
        
        # Quick check: exact match after normalization
        if norm1 == norm2:
            return True
        
        # Check if one is a substring of the other (with threshold)
        shorter = norm1 if len(norm1) < len(norm2) else norm2
        longer = norm2 if len(norm1) < len(norm2) else norm1
        
        if len(shorter) == 0:
            return False
        
        # If shorter is contained in longer, check overlap ratio
        if shorter in longer:
            overlap_ratio = len(shorter) / len(longer) if len(longer) > 0 else 0
            if overlap_ratio >= threshold:
                return True
            # Also check if shorter represents a significant portion of longer
            # (e.g., "Hello" in "Hello world" with threshold 0.5 should match)
            if len(shorter) / len(longer) >= threshold:
                return True
        
        return False
    
    def _validate_system_prompt_for_duplicates(self, prompt_content: str) -> None:
        """
        Validate system prompt for duplicate sections and log warnings.
        
        Args:
            prompt_content: The system prompt content to validate
        """
        if not prompt_content:
            return
        
        # Split by double newlines (section separators)
        sections = [s.strip() for s in prompt_content.split("\n\n") if s.strip()]
        
        if len(sections) < 2:
            return
        
        # Check for duplicate sections
        seen_sections = []
        duplicates_found = []
        
        for i, section in enumerate(sections):
            # Normalize section for comparison (remove leading markers like "##")
            normalized = " ".join(section.split())
            
            # Check against previously seen sections
            for j, seen in enumerate(seen_sections):
                if self._is_duplicate_content(normalized, seen, threshold=0.7):
                    duplicates_found.append((i, j, section[:100]))  # Store first 100 chars for logging
                    break
            
            seen_sections.append(normalized)
        
        if duplicates_found:
            logger.warning(
                f"Detected {len(duplicates_found)} potential duplicate section(s) in system prompt. "
                f"This may indicate content accumulation. Sections: {duplicates_found[:3]}"
            )
    
    def _validate_before_update(self) -> None:
        """
        Validate system state before updating system prompt.
        
        Checks for issues that could lead to accumulation:
        - Multiple system messages
        - Base prompt growth
        - JSON contamination in base prompt
        """
        # Check for multiple system messages
        system_messages = [i for i, msg in enumerate(self.messages) if msg.get("role") == "system"]
        if len(system_messages) > 1:
            logger.warning(
                f"Found {len(system_messages)} system messages before update (expected 0-1). "
                "This may indicate accumulation bug.",
                extra={
                    "event": "multiple_system_messages_before_update",
                    "count": len(system_messages),
                    "indices": system_messages,
                }
            )
        
        # Check base prompt hasn't grown unexpectedly
        if hasattr(self, '_initial_base_prompt_size') and self.base_system_prompt:
            current_size = len(self.base_system_prompt)
            if self._initial_base_prompt_size > 0:
                growth_ratio = current_size / self._initial_base_prompt_size
                if growth_ratio > 1.1:  # More than 10% growth
                    logger.warning(
                        f"Base prompt has grown {growth_ratio:.1f}x before update "
                        f"({self._initial_base_prompt_size} -> {current_size} chars). "
                        "Base prompt should be immutable.",
                        extra={
                            "event": "base_prompt_growth_before_update",
                            "initial_size": self._initial_base_prompt_size,
                            "current_size": current_size,
                            "growth_ratio": round(growth_ratio, 2),
                        }
                    )
        
        # Check for JSON contamination in base prompt
        if self.base_system_prompt:
            self._validate_base_prompt_clean()
    
    def _validate_after_update(self, prompt_content: str) -> None:
        """
        Validate system state after updating system prompt.
        
        Checks for issues that could indicate accumulation:
        - Multiple system messages
        - Duplicate world state JSON
        - System message not at index 0
        
        Args:
            prompt_content: The system prompt content that was just set
        """
        # Check system message count
        system_messages = [i for i, msg in enumerate(self.messages) if msg.get("role") == "system"]
        if len(system_messages) != 1:
            logger.error(
                f"CRITICAL: After system prompt update, found {len(system_messages)} system messages "
                f"(expected 1). This is a bug.",
                extra={
                    "event": "invalid_system_message_count_after_update",
                    "count": len(system_messages),
                    "indices": system_messages,
                }
            )
        elif system_messages[0] != 0:
            logger.warning(
                f"System message is at index {system_messages[0]} instead of 0. "
                "This may indicate ordering issues.",
                extra={
                    "event": "system_message_wrong_index",
                    "index": system_messages[0],
                }
            )
        
        # Check for duplicate world state JSON in prompt
        if prompt_content:
            # Count JSON objects (look for opening braces followed by timestamp-like keys)
            json_pattern = r'\{\s*"[^"]*"\s*:\s*"[^"]*"\s*,\s*"[^"]*"\s*:\s*"[^"]*"'
            json_matches = len(re.findall(json_pattern, prompt_content))
            if json_matches > 1:
                # Check if they're actually separate JSON objects (not nested)
                # Look for patterns like "}\n\n{" which indicate multiple top-level objects
                if re.search(r'\}\s*\n\s*\n\s*\{', prompt_content):
                    logger.warning(
                        f"Detected {json_matches} potential duplicate JSON objects in system prompt. "
                        "This may indicate world state accumulation.",
                        extra={
                            "event": "duplicate_json_detected_after_update",
                            "json_count": json_matches,
                        }
                    )
    
    def _validate_base_prompt_clean(self) -> None:
        """
        Validate that base prompt is clean (no JSON contamination, no summary markers, etc.).
        
        Logs warnings if contamination is detected.
        """
        if not self.base_system_prompt:
            return
        
        base_prompt = self.base_system_prompt
        contamination_detected = False
        contamination_types = []
        
        # Check for JSON objects (world state contamination)
        if "{" in base_prompt and "\"timestamp\"" in base_prompt:
            contamination_detected = True
            contamination_types.append("JSON/world_state")
        
        # Check for summary markers
        summary_markers = [
            "## Session Summary",
            "Historical Context",
            "Session Summary (Historical Context)",
        ]
        for marker in summary_markers:
            if marker in base_prompt:
                contamination_detected = True
                contamination_types.append("summary_marker")
                break
        
        # Check for multiple truncation messages (indicates accumulation)
        truncation_messages = [
            "[Base system prompt truncated due to size limit]",
            "[System prompt truncated due to size limit]",
        ]
        truncation_count = sum(1 for msg in truncation_messages if msg in base_prompt)
        if truncation_count > 1:
            contamination_detected = True
            contamination_types.append("multiple_truncation_messages")
        
        if contamination_detected:
            logger.error(
                f"Base prompt contamination detected: {', '.join(contamination_types)}. "
                "Base prompt should be clean and immutable. This may cause unbounded growth.",
                extra={
                    "event": "base_prompt_contamination_detected",
                    "contamination_types": contamination_types,
                    "base_prompt_length": len(base_prompt),
                    "base_prompt_preview": base_prompt[:200],
                }
            )
    
    def _ensure_single_system_message(self) -> bool:
        """
        Ensure only one system message exists and it's at index 0.
        
        This is a critical validation method that prevents system message accumulation.
        It should be called at all critical points where system messages might be modified.
        
        Returns:
            True if validation passed (no issues found), False if issues were found and fixed
        """
        system_messages = [i for i, msg in enumerate(self.messages) if msg.get("role") == "system"]
        
        if len(system_messages) == 0:
            # No system message - this is OK if world_state_aggregator will create one
            return True
        
        if len(system_messages) == 1 and system_messages[0] == 0:
            # Perfect: exactly one system message at index 0
            return True
        
        # Issues found - fix them
        if len(system_messages) > 1:
            logger.error(
                f"Found {len(system_messages)} system messages - keeping only the first. "
                "This indicates a bug where system messages were being accumulated.",
                extra={
                    "event": "multiple_system_messages_fixed",
                    "count": len(system_messages),
                    "indices": system_messages,
                }
            )
        elif system_messages[0] != 0:
            logger.warning(
                f"System message is at index {system_messages[0]} instead of 0. "
                "Moving it to index 0.",
                extra={
                    "event": "system_message_wrong_index_fixed",
                    "original_index": system_messages[0],
                }
            )
        
        # Keep only the first system message
        first_system_idx = system_messages[0]
        first_system_msg = self.messages[first_system_idx].copy()  # Copy to avoid reference issues
        
        # Remove all system messages (in reverse order to maintain indices)
        for idx in reversed(system_messages):
            self.messages.pop(idx)
        
        # Insert system message at index 0
        self.messages.insert(0, first_system_msg)
        
        # Validate fix worked
        final_system_messages = [i for i, msg in enumerate(self.messages) if msg.get("role") == "system"]
        if len(final_system_messages) != 1 or final_system_messages[0] != 0:
            logger.error(
                f"CRITICAL: Failed to fix system message issues. "
                f"After fix: {len(final_system_messages)} system messages at indices {final_system_messages}",
                extra={
                    "event": "system_message_fix_failed",
                    "final_count": len(final_system_messages),
                    "final_indices": final_system_messages,
                }
            )
        
        return False  # Issues were found and fixed
    
    def _validate_message_list_for_system_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Validate a message list for system message issues.
        
        This helper method checks if a message list (which may not be self.messages)
        contains multiple system messages, which would indicate contamination.
        
        Args:
            messages: Message list to validate
            
        Returns:
            True if valid (0-1 system messages), False if invalid (multiple system messages)
        """
        system_messages = [i for i, msg in enumerate(messages) if msg.get("role") == "system"]
        
        if len(system_messages) <= 1:
            return True
        
        logger.warning(
            f"Message list contains {len(system_messages)} system messages (expected 0-1). "
            "This indicates contamination or accumulation.",
            extra={
                "event": "multiple_system_messages_in_list",
                "count": len(system_messages),
                "indices": system_messages,
                "list_length": len(messages),
            }
        )
        return False

    # ---------- Tool handling helpers ----------

    def _handle_tool_calls(
        self, response: Dict[str, Any], tool_calls: List[Dict[str, Any]]
    ) -> None:
        """
        Handle tool calls from LLM response.

        Executes tools and adds results to conversation history.

        Args:
            response: Raw LLM response
            tool_calls: List of tool call dictionaries
        """
        if not self.tool_registry:
            logger.warning(
                "Received tool calls but no tool registry available",
                extra={
                    "event": "tool_calls_no_registry",
                    "tool_calls_count": len(tool_calls),
                },
            )
            return

        # Add assistant message with tool calls
        # For deepseek-reasoner, we must include reasoning_content in the assistant message
        # if it was present in the response
        # For Gemini, we must preserve thought_signature in each tool_call
        is_gemini = self._is_gemini_client()
        
        # For Gemini, ensure each tool_call has thought_signature
        # If missing, add the current thought_signature from the response
        if is_gemini and tool_calls:
            current_sig = getattr(self, '_current_thought_signature', None)
            tool_calls_fixed = False
            for tool_call in tool_calls:
                if isinstance(tool_call, dict) and "thought_signature" not in tool_call:
                    if current_sig:
                        tool_call["thought_signature"] = current_sig
                        tool_calls_fixed = True
                        logger.debug(
                            "Added thought_signature to tool_call using current signature",
                            extra={
                                "event": "thought_signature_added_to_tool_call",
                                "tool_call_id": tool_call.get("id", "unknown"),
                                "function_name": tool_call.get("function", {}).get("name", "unknown"),
                            }
                        )
                    else:
                        logger.warning(
                            "Tool call missing thought_signature and no current signature available",
                            extra={
                                "event": "missing_thought_signature_in_tool_call",
                                "tool_call_id": tool_call.get("id", "unknown"),
                                "function_name": tool_call.get("function", {}).get("name", "unknown"),
                            }
                        )
            
            if tool_calls_fixed:
                logger.info(
                    "Fixed missing thought_signature in tool_calls for Gemini",
                    extra={
                        "event": "thought_signature_fixed_in_tool_calls",
                        "total_tool_calls": len(tool_calls),
                    }
                )
        
        # Log thought_signature preservation for Gemini (for debugging)
        if is_gemini:
            thought_sigs_in_tool_calls = sum(1 for tc in tool_calls if tc.get("thought_signature"))
            if thought_sigs_in_tool_calls > 0:
                logger.debug(
                    f"Preserved thought_signature in {thought_sigs_in_tool_calls}/{len(tool_calls)} tool_calls",
                    extra={
                        "event": "thought_signature_in_tool_calls",
                        "total_tool_calls": len(tool_calls),
                        "tool_calls_with_signature": thought_sigs_in_tool_calls,
                    }
                )
            elif len(tool_calls) > 0:
                logger.warning(
                    "No thought_signature found in tool_calls for Gemini - this may cause API errors",
                    extra={
                        "event": "missing_thought_signature_in_tool_calls",
                        "total_tool_calls": len(tool_calls),
                    }
                )
        
        assistant_message = {
            "role": "assistant",
            "content": self.llm.extract_assistant_content(response) or None,
            "tool_calls": tool_calls,
        }
        
        # Include reasoning_content in the assistant message for reasoner model
        # The API requires this field to be present in assistant messages with tool_calls
        # Even if it's empty, the field must exist
        is_reasoner = hasattr(self.llm, 'is_reasoner_model') and self.llm.is_reasoner_model()
        if is_reasoner:
            # Always include reasoning_content field for reasoner model when tool_calls are present
            # Use stored value if available, otherwise use empty string (field must exist)
            reasoning_value = ""
            if hasattr(self, '_current_reasoning_content'):
                if self._current_reasoning_content:
                    reasoning_value = self._current_reasoning_content
            # Always add the field, even if empty (API requirement)
            assistant_message["reasoning_content"] = reasoning_value
            # Only call len() if it's actually a string/sequence, not a Mock
            try:
                reasoning_length = len(reasoning_value) if isinstance(reasoning_value, (str, bytes, list, tuple)) else 0
            except (TypeError, AttributeError):
                reasoning_length = 0
            logger.info(
                "Added reasoning_content to assistant message with tool_calls",
                extra={
                    "event": "reasoning_content_added_to_message",
                    "has_reasoning_content": bool(reasoning_value),
                    "reasoning_length": reasoning_length,
                    "attribute_exists": hasattr(self, '_current_reasoning_content'),
                }
            )
        
        # Initialize event_ids list for tool call events
        assistant_message["event_ids"] = []
        
        self.messages.append(assistant_message)

        # Execute each tool call
        for i, tool_call in enumerate(tool_calls, 1):
            tool_name = tool_call.get("function", {}).get("name", "unknown")
            tool_call_id = tool_call.get("id", "")

            # Extract arguments from tool call for recording
            arguments_str = tool_call.get("function", {}).get("arguments", "{}")
            try:
                import json

                arguments = json.loads(arguments_str) if arguments_str else {}
            except (json.JSONDecodeError, TypeError):
                arguments = {}

            logger.info(
                f"Processing tool call {i}/{len(tool_calls)}: {tool_name}",
                extra={
                    "event": "tool_call_processing",
                    "tool_name": tool_name,
                    "tool_call_id": tool_call_id,
                    "tool_call_index": i,
                    "total_tool_calls": len(tool_calls),
                },
            )

            try:
                # Show visual feedback for tool invocation
                if self._tool_status_display:
                    try:
                        self._tool_status_display.start_tool_call(
                            tool_name=tool_name,
                            arguments=arguments,
                            tool_call_id=tool_call_id
                        )
                    except Exception as e:
                        logger.debug(f"Failed to start tool status display: {e}", exc_info=True)
                
                # Log tool call event
                tool_call_event_id = None
                if self._event_logger:
                    try:
                        tool_call_event_id = self._event_logger.log_tool_call(
                            self.session_id,
                            tool_name,
                            arguments,
                            tool_call_id=tool_call_id
                        )
                        # Store tool call event ID in the assistant message that contains the tool_calls
                        # The assistant_message was just appended, so it's the last message
                        if tool_call_event_id and assistant_message.get("event_ids") is not None:
                            assistant_message["event_ids"].append(tool_call_event_id)
                    except Exception as e:
                        logger.warning(f"Failed to log tool call event: {e}", exc_info=True)
                
                tool_result = self.tool_registry.execute_tool_call(tool_call)
                
                # Determine if tool call was successful
                # Use _success field if available (from raw result), otherwise fall back to content parsing
                tool_success = True
                if isinstance(tool_result, dict):
                    # Prefer explicit success field from raw result
                    if "_success" in tool_result:
                        # Explicitly check the boolean value - don't rely on truthiness
                        tool_success = bool(tool_result["_success"])
                    else:
                        # Fallback: check content for error indicators (legacy behavior)
                        # Only use this if _success field is not available
                        content = tool_result.get("content", "")
                        if isinstance(content, str):
                            content_lower = content.lower()
                            # Only mark as failed if content explicitly indicates error/failure
                            # Skip common false positives like "Error output:" label for successful commands
                            if ("error executing" in content_lower or 
                                ("failed" in content_lower and ("command failed" in content_lower or "execution failed" in content_lower))):
                                tool_success = False
                
                # Complete visual feedback
                if self._tool_status_display:
                    try:
                        self._tool_status_display.complete_tool_call(
                            tool_call_id=tool_call_id,
                            tool_name=tool_name,
                            success=tool_success
                        )
                    except Exception as e:
                        logger.debug(f"Failed to complete tool status display: {e}", exc_info=True)
                
                # Truncate tool result if it exceeds size limit
                from ..config import config
                max_tool_result_size = config.summarization.max_tool_result_size
                tool_result = truncate_tool_result(tool_result, max_tool_result_size)
                
                # Log tool result event before appending (so we can store event ID)
                tool_result_event_id = None
                if self._event_logger:
                    try:
                        # Extract result content (may be a dict or string)
                        result_content = tool_result.get("content", "")
                        if isinstance(result_content, str):
                            # Try to parse as JSON if possible
                            try:
                                import json
                                result_dict = json.loads(result_content)
                            except (json.JSONDecodeError, TypeError):
                                result_dict = {"content": result_content}
                        else:
                            result_dict = result_content if isinstance(result_content, dict) else {"content": str(result_content)}
                        
                        tool_result_event_id = self._event_logger.log_tool_result(
                            self.session_id,
                            tool_name,
                            result_dict,
                            tool_call_id=tool_call_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log tool result event: {e}", exc_info=True)
                
                # Store tool result event ID in the tool result message
                if tool_result_event_id:
                    if "event_ids" not in tool_result:
                        tool_result["event_ids"] = []
                    tool_result["event_ids"].append(tool_result_event_id)
                
                self.messages.append(tool_result)
                
                # Add tool result to context graph
                if self._context_graph:
                    try:
                        # Find parent (the assistant message with tool_calls)
                        parent_id = None
                        for msg in reversed(self.messages[:-1]):  # All messages except the one we just added
                            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                                # Check if this assistant message has the matching tool_call
                                for tc in msg.get("tool_calls", []):
                                    if tc.get("id") == tool_call_id:
                                        parent_id = msg.get("message_id")
                                        if not parent_id and self._context_graph._message_order:
                                            # Find by position
                                            msg_idx = len(self.messages) - 2
                                            if msg_idx < len(self._context_graph._message_order):
                                                parent_id = self._context_graph._message_order[msg_idx]
                                        break
                                if parent_id:
                                    break
                        
                        # Fallback: use last message in graph
                        if not parent_id and self._context_graph._message_order:
                            parent_id = self._context_graph._message_order[-1]
                        
                        # Add message_id if not present
                        if "message_id" not in tool_result:
                            tool_result["message_id"] = tool_result_event_id or str(uuid.uuid4())
                        
                        self._context_graph.add_message(
                            tool_result,
                            parent_id=parent_id,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add tool result to context graph: {e}", exc_info=True)
                
                # Verify tool result was properly added to messages
                # This ensures the next LLM iteration will receive the tool result
                logger.debug(
                    f"Tool result added to messages: {tool_name} (call_id: {tool_call_id})",
                    extra={
                        "event": "tool_result_added",
                        "tool_name": tool_name,
                        "tool_call_id": tool_call_id,
                        "messages_count": len(self.messages),
                        "last_message_role": self.messages[-1].get("role") if self.messages else None,
                    }
                )

                # Instrumentation: Record tool usage and reasoning
                if self.internal_sensing_framework:
                    try:
                        # Record tool usage
                        self.internal_sensing_framework.record_tool_usage(
                            tool_name=tool_name,
                            parameters=arguments,
                            result=tool_result,
                        )

                        # Record reasoning step for tool execution
                        self.internal_sensing_framework.interoception.cognition.record_reasoning_step(
                            f"tool_{tool_call_id}",
                            {
                                "premise": f"Need to use {tool_name}",
                                "conclusion": f"Tool {tool_name} executed",
                                "tool": tool_name,
                                "parameters": arguments,
                            },
                        )

                        # Record reasoning pattern
                        self.internal_sensing_framework.interoception.cognition.record_reasoning_pattern(
                            "tool_usage", tool_name
                        )

                        # Check if tool was successful
                        # Use _success field if available, otherwise parse content
                        if "_success" in tool_result:
                            is_success = tool_result.get("_success", True)
                        else:
                            # Fallback: check content (legacy behavior)
                            tool_success = tool_result.get("content", "").lower()
                            is_success = (
                                "error executing" not in tool_success and 
                                ("failed" not in tool_success or 
                                 ("command failed" not in tool_success and "execution failed" not in tool_success))
                            )

                        # Update affective state based on tool outcome
                        if is_success:
                            self.internal_sensing_framework.interoception.affect.record_satisfaction(
                                f"tool_{tool_call_id}", 0.7
                            )
                        else:
                            self.internal_sensing_framework.interoception.affect.record_frustration(
                                f"tool_{tool_call_id}", 0.5
                            )

                    except Exception as e:
                        logger.warning(
                            f"Error recording tool usage: {e}", exc_info=True
                        )

                logger.info(
                    f"Tool result added to conversation: {tool_name}",
                    extra={
                        "event": "tool_result_added",
                        "tool_name": tool_name,
                        "tool_call_id": tool_call_id,
                        "result_length": len(tool_result.get("content", "")),
                    },
                )
            except Exception as e:
                # Complete visual feedback with error
                if self._tool_status_display:
                    try:
                        self._tool_status_display.complete_tool_call(
                            tool_call_id=tool_call_id,
                            tool_name=tool_name,
                            success=False
                        )
                    except Exception:
                        pass  # Ignore errors in display system
                
                logger.error(
                    f"Error executing tool call: {e}",
                    exc_info=True,
                    extra={
                        "event": "tool_call_execution_error",
                        "tool_name": tool_name,
                        "tool_call_id": tool_call_id,
                        "error": str(e),
                    },
                )
                # Add error message
                error_tool_result = {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": f"Error: {str(e)}",
                }
                self.messages.append(error_tool_result)
                
                # Add error tool result to context graph
                if self._context_graph:
                    try:
                        # Find parent (the assistant message with tool_calls)
                        parent_id = None
                        for msg in reversed(self.messages[:-1]):
                            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                                for tc in msg.get("tool_calls", []):
                                    if tc.get("id") == tool_call_id:
                                        parent_id = msg.get("message_id")
                                        if not parent_id and self._context_graph._message_order:
                                            msg_idx = len(self.messages) - 2
                                            if msg_idx < len(self._context_graph._message_order):
                                                parent_id = self._context_graph._message_order[msg_idx]
                                        break
                                if parent_id:
                                    break
                        
                        if not parent_id and self._context_graph._message_order:
                            parent_id = self._context_graph._message_order[-1]
                        
                        if "message_id" not in error_tool_result:
                            error_tool_result["message_id"] = str(uuid.uuid4())
                        
                        self._context_graph.add_message(
                            error_tool_result,
                            parent_id=parent_id,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add error tool result to context graph: {e}", exc_info=True)

    # ---------- Storage helpers ----------

    def _sanitize_for_json(self, obj: Any) -> Any:
        """
        Recursively sanitize objects to be JSON serializable.
        
        Converts Mock objects and other non-serializable types to strings or removes them.
        """
        from unittest.mock import Mock
        
        if isinstance(obj, Mock):
            # Convert Mock objects to string representation
            return str(obj)
        elif isinstance(obj, dict):
            # Recursively sanitize dictionaries
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            # Recursively sanitize lists and tuples
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            # Basic JSON-serializable types
            return obj
        else:
            # For other types, try to convert to string
            try:
                # Test if it's JSON serializable
                import json
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                # If not serializable, convert to string
                return str(obj)

    def _save_conversation(self) -> None:
        """
        Save conversation to storage if storage backend is available.

        Logs errors but does not raise exceptions to avoid breaking the REPL.

        The system_prompt field in metadata stores the base system prompt
        (user-defined invariants), not the full combined prompt with world state.
        The full prompt is always available in the messages[0]["content"].
        
        CRITICAL: Before saving, ensure system prompt is up-to-date with latest world state.
        This ensures saved conversations include the latest internal sensing values.
        """
        if not self.storage:
            return

        try:
            # CRITICAL: Update system prompt with latest world state BEFORE saving
            # This ensures saved conversations have the latest internal sensing values
            if self.world_state_aggregator and self._world_state_formatter:
                logger.debug("Updating system prompt before save to ensure latest world state")
                self._last_world_state_hash = None  # Force update
                self._update_system_prompt()
            
            # Validate system message count before saving to prevent saving contaminated state
            # This is critical - we don't want to persist multiple system messages
            self._ensure_single_system_message()
            # Use base_system_prompt if it was explicitly set, otherwise use system_prompt
            # If base_system_prompt came from config and system_prompt is None, save empty string
            # to indicate no explicit system prompt was set
            if (
                hasattr(self, "_base_system_prompt_explicit")
                and self._base_system_prompt_explicit
            ):
                # Base prompt was explicitly provided (via parameter or system_prompt)
                saved_system_prompt = self.base_system_prompt or ""
            else:
                # Base prompt came from config - only save if system_prompt was also set
                # This preserves the behavior: if user didn't set system_prompt, save empty
                saved_system_prompt = self.system_prompt or ""
            
            # Validate and clean base prompt before saving to prevent contamination
            if saved_system_prompt:
                # Check for contamination
                original_prompt = saved_system_prompt
                cleaned_prompt = self._clean_base_prompt(saved_system_prompt)
                
                if cleaned_prompt != original_prompt:
                    logger.error(
                        "Base prompt contamination detected before save! Cleaning before saving. "
                        "This indicates a bug where base prompt was modified or contaminated.",
                        extra={
                            "event": "base_prompt_contamination_before_save",
                            "original_length": len(original_prompt),
                            "cleaned_length": len(cleaned_prompt),
                            "original_preview": original_prompt[:200],
                            "cleaned_preview": cleaned_prompt[:200],
                        }
                    )
                    saved_system_prompt = cleaned_prompt
                
                # Additional validation: ensure no JSON, summary markers, or multiple truncation messages
                contamination_detected = False
                contamination_types = []
                
                if "{" in saved_system_prompt and "\"timestamp\"" in saved_system_prompt:
                    contamination_detected = True
                    contamination_types.append("JSON/world_state")
                
                summary_markers = ["## Session Summary", "Historical Context"]
                for marker in summary_markers:
                    if marker in saved_system_prompt:
                        contamination_detected = True
                        contamination_types.append("summary_marker")
                        break
                
                truncation_count = saved_system_prompt.count("[Base system prompt truncated due to size limit]")
                if truncation_count > 1:
                    contamination_detected = True
                    contamination_types.append("multiple_truncation_messages")
                
                if contamination_detected:
                    logger.error(
                        f"Base prompt still contains contamination after cleaning: {', '.join(contamination_types)}. "
                        "This is a critical bug. Saving cleaned version.",
                        extra={
                            "event": "base_prompt_still_contaminated_after_cleaning",
                            "contamination_types": contamination_types,
                        }
                    )
                    # Force clean again
                    saved_system_prompt = self._clean_base_prompt(saved_system_prompt)

            metadata = {
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "system_prompt": saved_system_prompt,
            }

            # Sanitize messages to ensure they're JSON serializable (remove Mock objects, etc.)
            sanitized_messages = self._sanitize_for_json(self.messages)

            self.storage.save_conversation(
                session_id=self.session_id, messages=sanitized_messages, metadata=metadata
            )

            logger.debug(f"Saved conversation {self.session_id} to storage")

        except Exception as e:
            logger.warning(
                f"Failed to save conversation {self.session_id}: {e}", exc_info=True
            )

    @classmethod
    def load_from_storage(
        cls,
        session_id: str,
        storage: "ConversationStorage",
        llm: Optional["LLMClient"] = None,
        world_state_aggregator: Optional["WorldStateAggregator"] = None,
    ) -> Optional["ConversationSession"]:
        """
        Load a conversation session from storage.

        Args:
            session_id: Unique identifier for the conversation session
            storage: Storage backend to load from
            llm: Optional LLM client (uses default if not provided)
            world_state_aggregator: Optional world state aggregator for dynamic prompts

        Returns:
            ConversationSession instance if found, None otherwise
        """
        try:
            result = storage.load_conversation(session_id)
            if not result:
                logger.debug(f"Conversation {session_id} not found in storage")
                return None

            messages = result.get("messages", [])
            metadata = result.get("metadata", {})

            # Extract base system prompt from metadata ONLY (never from system message content)
            # The system message content is contaminated with world state/summary and should not be used
            # Use the saved value, even if empty (don't override with config when loading)
            stored_base_prompt = metadata.get("system_prompt", "")
            
            # Clean contaminated base prompt if it contains JSON/world state
            if stored_base_prompt:
                cleaned_prompt = cls._clean_base_prompt(stored_base_prompt)
                if cleaned_prompt != stored_base_prompt:
                    logger.warning(
                        "Cleaned contaminated base prompt from storage",
                        extra={
                            "event": "base_prompt_cleaned",
                            "original_length": len(stored_base_prompt),
                            "cleaned_length": len(cleaned_prompt),
                        }
                    )
                base_system_prompt = cleaned_prompt
            else:
                base_system_prompt = ""

            # Create session with base system prompt
            # Note: We don't pass system_prompt parameter to avoid double-adding
            # Pass base_system_prompt explicitly (even if empty) to avoid using config
            session = cls(
                system_prompt=None,  # Don't add system prompt here, we'll rebuild it
                llm=llm,
                storage=storage,
                session_id=session_id,
                world_state_aggregator=world_state_aggregator,
                base_system_prompt=base_system_prompt,  # Use saved value, not config
            )

            # Restore messages but remove system message - it will be rebuilt correctly
            # This prevents contamination from old system messages that may include world state/summary
            if messages:
                # Validate loaded messages for contamination before filtering
                system_messages_in_load = [m for m in messages if m.get("role") == "system"]
                if len(system_messages_in_load) > 1:
                    logger.warning(
                        f"Loaded conversation has {len(system_messages_in_load)} system messages. "
                        "This indicates contamination. All will be removed and rebuilt.",
                        extra={
                            "event": "multiple_system_messages_in_loaded_conversation",
                            "count": len(system_messages_in_load),
                        }
                    )
                
                # Filter out all system messages if present
                session.messages = [m for m in messages if m.get("role") != "system"]
                
                # Validate that no system messages remain after filtering
                remaining_system = [m for m in session.messages if m.get("role") == "system"]
                if remaining_system:
                    logger.error(
                        f"CRITICAL: System messages still present after filtering: {len(remaining_system)}. "
                        "This is a bug in the filtering logic.",
                        extra={
                            "event": "system_messages_remain_after_load_filtering",
                            "count": len(remaining_system),
                        }
                    )
                    # Force remove any remaining system messages
                    session.messages = [m for m in session.messages if m.get("role") != "system"]

            # Restore timestamps
            session.created_at = metadata.get("created_at", session.created_at)
            session.updated_at = metadata.get("updated_at", session.updated_at)

            # Restore system_prompt for backward compatibility (legacy code may check this)
            # This is the base prompt, not the full combined prompt
            # If saved value is empty, set to None to indicate no system prompt was set
            session.system_prompt = base_system_prompt if base_system_prompt else None

            # Validate that base prompt hasn't been contaminated
            if base_system_prompt:
                if "{" in base_system_prompt and "\"timestamp\"" in base_system_prompt:
                    logger.warning(
                        "Base system prompt appears to contain JSON (world state contamination detected). "
                        "Using metadata value but this may be incorrect.",
                        extra={
                            "event": "base_prompt_contamination_detected",
                            "base_prompt_preview": base_system_prompt[:200],
                        }
                    )
                if "## Session Summary" in base_system_prompt or "Historical Context" in base_system_prompt:
                    logger.warning(
                        "Base system prompt appears to contain summary content (contamination detected). "
                        "Using metadata value but this may be incorrect.",
                        extra={
                            "event": "base_prompt_summary_contamination_detected",
                            "base_prompt_preview": base_system_prompt[:200],
                        }
                    )

            # If we have a world state aggregator, update the system prompt to refresh world state
            # This ensures the world state is current even after loading and rebuilds from clean base
            if world_state_aggregator and session._world_state_formatter:
                session._update_system_prompt()
            
            # Final validation after rebuild to ensure clean state
            session._ensure_single_system_message()

            logger.info(f"Loaded conversation {session_id} from storage")
            return session

        except Exception as e:
            logger.error(
                f"Failed to load conversation {session_id}: {e}", exc_info=True
            )
            return None
