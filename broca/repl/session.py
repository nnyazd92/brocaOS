from __future__ import annotations

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
import uuid
import time
import sys
from datetime import datetime, timezone
from ..llm import create_llm_client, LLMClient

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
    ) -> None:
        self.llm = llm or create_llm_client()
        self.messages: List[Dict[str, str]] = []
        self.storage = storage
        self.tool_registry = tool_registry
        self.internal_sensing_framework = internal_sensing_framework
        self.world_state_aggregator = world_state_aggregator
        self.session_id = session_id or str(uuid.uuid4())
        self.system_prompt = system_prompt

        # Get base system prompt from parameter, system_prompt, or config
        # Track whether base_system_prompt was explicitly provided
        if base_system_prompt is not None:
            self.base_system_prompt = base_system_prompt
            self._base_system_prompt_explicit = True
        elif system_prompt:
            # If system_prompt is provided but base_system_prompt is not,
            # use system_prompt as the base (for backward compatibility)
            self.base_system_prompt = system_prompt
            self._base_system_prompt_explicit = True
        else:
            # Fall back to config if not provided
            from ..config import config

            self.base_system_prompt = config.storage.base_system_prompt
            self._base_system_prompt_explicit = False

        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self._max_tool_iterations = 100
        
        # Initialize summarization components if enabled
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
                logger.debug("Summarization enabled for session")
            except Exception as e:
                logger.warning(f"Failed to initialize summarization: {e}", exc_info=True)
        
        # Track turns for summarization triggers
        self._turns_since_last_summary = 0

        # Initialize formatter for world state
        if world_state_aggregator:
            from ..world_state.formatter import WorldStateFormatter

            self._world_state_formatter = WorldStateFormatter()
        else:
            self._world_state_formatter = None

        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

        # Update system prompt with world state immediately if aggregator is available
        # This ensures world state is populated even before first user message
        if self.world_state_aggregator and self._world_state_formatter:
            self._update_system_prompt()

        logger.info(
            "Conversation session started",
            extra={
                "event": "session_start",
                "system_prompt_present": bool(system_prompt),
                "session_id": self.session_id,
                "storage_enabled": storage is not None,
                "tools_enabled": tool_registry is not None,
                "internal_sensing_enabled": internal_sensing_framework is not None,
                "world_state_enabled": world_state_aggregator is not None,
            },
        )

    # ---------- Public API ----------

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

        # Log user message event
        if self._event_logger:
            try:
                self._event_logger.log_user_message(self.session_id, user_text)
            except Exception as e:
                logger.warning(f"Failed to log user message event: {e}", exc_info=True)

        self.messages.append({"role": "user", "content": user_text})
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
        
        # Handle tool calls iteratively (may require multiple LLM calls)
        iterations = 0
        response = None
        while iterations < self._max_tool_iterations:
            iterations += 1

            # Update system prompt with current world state before each LLM call
            self._update_system_prompt()

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
                
                if use_streaming:
                    # Streaming mode - try streaming first
                    assistant_text = ""
                    print("BrocaOS> ", end="", flush=True)
                    
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
                        if tools:
                            stream_gen = self.llm.chat_stream(
                                self._get_messages_for_llm(), 
                                tools=tools,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None
                            )
                        else:
                            stream_gen = self.llm.chat_stream(
                                self._get_messages_for_llm(),
                                reasoning_content=self._current_reasoning_content if is_reasoner else None
                            )
                        
                        # Collect streaming chunks and print them immediately as they arrive
                        chunk_count = 0
                        for chunk in stream_gen:
                            chunk_count += 1
                            assistant_text += chunk
                            print(chunk, end="", flush=True)
                            
                            # Apply delay between chunks if configured
                            if streaming_delay > 0:
                                time.sleep(streaming_delay)
                        
                        # Always print newline after streaming, even if no chunks were received
                        print("", flush=True)  # New line after streaming
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
                            non_stream_response = self.llm.chat(
                                self._get_messages_for_llm(), 
                                tools=tools,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None
                            )
                            tool_calls_from_response = self.llm.extract_tool_calls(non_stream_response)
                            if tool_calls_from_response:
                                # Update response with tool_calls
                                response["choices"][0]["message"]["tool_calls"] = tool_calls_from_response
                                response["choices"][0]["message"]["content"] = None  # No content when tool_calls exist
                                assistant_text = None  # Clear assistant_text since we have tool_calls
                    except Exception as e:
                        # Fall back to non-streaming on error
                        logger.warning(f"Streaming failed, falling back to non-streaming: {e}", exc_info=True)
                        assistant_text = None  # Reset so it gets extracted from response
                        if tools:
                            response = self.llm.chat(
                                self._get_messages_for_llm(), 
                                tools=tools,
                                reasoning_content=self._current_reasoning_content if is_reasoner else None
                            )
                        else:
                            response = self.llm.chat(
                                self._get_messages_for_llm(),
                                reasoning_content=self._current_reasoning_content if is_reasoner else None
                            )
                    finally:
                        # No terminal settings to restore since we only flushed input
                        pass
                else:
                    # Non-streaming mode (when streaming disabled)
                    if tools:
                        response = self.llm.chat(
                            self._get_messages_for_llm(), 
                            tools=tools,
                            reasoning_content=self._current_reasoning_content if is_reasoner else None
                        )
                    else:
                        response = self.llm.chat(
                            self._get_messages_for_llm(),
                            reasoning_content=self._current_reasoning_content if is_reasoner else None
                        )
            except TimeoutError as e:
                logger.error(f"LLM request timed out: {e}", exc_info=True)
                error_message = (
                    "I apologize, but the API request timed out. This can happen with "
                    "large conversations or when the API is slow. You may want to try "
                    "using /reset to clear the conversation history, or try again."
                )
                self.messages.append({"role": "assistant", "content": error_message})
                self.updated_at = datetime.now(timezone.utc).isoformat()
                # Log conversation turn completion even on error
                self._log_context_after_turn(
                    assistant_text=error_message, raw_response={}
                )
                self._save_conversation()
                return error_message
            except ConnectionError as e:
                logger.error(f"Network error during LLM request: {e}", exc_info=True)
                error_message = (
                    "I apologize, but there was a network error connecting to the API. "
                    "Please check your internet connection and try again."
                )
                self.messages.append({"role": "assistant", "content": error_message})
                self.updated_at = datetime.now(timezone.utc).isoformat()
                # Log conversation turn completion even on error
                self._log_context_after_turn(
                    assistant_text=error_message, raw_response={}
                )
                self._save_conversation()
                return error_message
            except Exception as e:
                logger.error(f"Unexpected error during LLM request: {e}", exc_info=True)
                error_message = (
                    f"I apologize, but an unexpected error occurred: {str(e)}. "
                    "Please try again or use /reset to clear the conversation."
                )
                self.messages.append({"role": "assistant", "content": error_message})
                self.updated_at = datetime.now(timezone.utc).isoformat()
                # Log conversation turn completion even on error
                self._log_context_after_turn(
                    assistant_text=error_message, raw_response={}
                )
                self._save_conversation()
                return error_message

            # Extract tool calls if any (needed for logging below)
            tool_calls = self.llm.extract_tool_calls(response)

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
                assistant_text = self.llm.extract_assistant_content(response) or ""

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

                # Continue loop to get LLM response with tool results
                # The reasoning_content extracted above will be passed in the next iteration
                continue
            else:
                # No tool calls - check if we have a pending critic rejection
                if self._has_pending_critic_rejection():
                    logger.warning(
                        "LLM attempted final response while critic rejection is pending, forcing iteration",
                        extra={
                            "event": "critic_rejection_blocked_final_response",
                            "iteration": iterations,
                        },
                    )
                    # Inject message that allows tool usage but reminds about critic requirement
                    self.messages.append(
                        {
                            "role": "system",
                            "content": (
                                "The critic has rejected your response. You may use tools (terminal, web_search, etc.) "
                                "to gather information, execute code, or improve your response. However, you MUST "
                                "call the critic tool again with your revised response before providing a final "
                                "response to the user. The critic must accept your response before you can respond "
                                "to the user."
                            ),
                        }
                    )
                    # Force another iteration
                    continue

                # No tool calls and no pending critic rejection - extract final response
                if iterations > 1:
                    logger.info(
                        f"Final LLM response after {iterations} tool iteration(s)",
                        extra={
                            "event": "final_response_after_tools",
                            "iterations": iterations,
                        },
                    )

                # Log if critic was involved and accepted
                if self.tool_registry and self.tool_registry.get_tool("critic"):
                    # Check if there was a recent critic acceptance
                    for message in reversed(
                        self.messages[-10:]
                    ):  # Check last 10 messages
                        if (
                            message.get("role") == "tool"
                            and message.get("name") == "critic"
                        ):
                            raw_result = message.get("_raw_result")
                            if (
                                raw_result
                                and isinstance(raw_result, dict)
                                and raw_result.get("accepted", False)
                            ):
                                logger.info(
                                    "Critic acceptance allows final response",
                                    extra={
                                        "event": "critic_acceptance_allows_final_response",
                                        "iteration": iterations,
                                    },
                                )
                            break

                # Extract assistant text - if we used streaming, it's already in assistant_text
                # But make sure we have it even if streaming was used (fallback)
                if assistant_text is None:
                    assistant_text = self.llm.extract_assistant_content(response) or ""
                
                # Ensure response is always printed
                if used_streaming:
                    # If we streamed, content was already printed chunk by chunk
                    # But if assistant_text is empty or None, we still printed "BrocaOS> " so add newline
                    # (The newline is already printed in streaming loop, but ensure it's there)
                    if not assistant_text or not assistant_text.strip():
                        # Empty response after streaming - we already printed "BrocaOS> " but no content
                        # The newline was already printed, so we're done
                        pass
                    # Otherwise streaming already printed everything including newline
                else:
                    # Non-streaming: print with prompt
                    if assistant_text:
                        print(f"BrocaOS> {assistant_text}\n", end="", flush=True)
                    else:
                        print("BrocaOS> \n", end="", flush=True)  # Empty response

                # Log assistant message event
                if self._event_logger:
                    try:
                        self._event_logger.log_assistant_message(self.session_id, assistant_text)
                    except Exception as e:
                        logger.warning(f"Failed to log assistant message event: {e}", exc_info=True)

                # Add message to conversation history immediately
                self.messages.append({"role": "assistant", "content": assistant_text})
                self.updated_at = datetime.now(timezone.utc).isoformat()
                
                # Increment turn counter and trigger summarization if needed
                self._turns_since_last_summary += 1
                if self._summarization_manager:
                    try:
                        self._summarization_manager.maybe_summarize(
                            self.session_id,
                            self.messages,
                            self._turns_since_last_summary
                        )
                        # Reset counter after summarization (even if it didn't trigger)
                        # This prevents rapid re-triggering
                        if self._summarization_manager.should_summarize(
                            self.session_id,
                            self.messages,
                            self._turns_since_last_summary
                        ):
                            self._turns_since_last_summary = 0
                    except Exception as e:
                        logger.warning(f"Failed to trigger summarization: {e}", exc_info=True)

                # Persist immediately so callers (and tests) can observe saved state
                try:
                    self._save_conversation()
                except Exception:
                    pass

                # Return immediately after streaming - do heavy post-processing in background
                # This prevents blocking the user from seeing the response
                try:
                    # Use threading to do post-processing without blocking
                    import threading
                    
                    def do_post_processing():
                        try:
                            # Instrumentation: Record metrics from response
                            if (
                                self.internal_sensing_framework
                                and ResponseAnalyzer
                                and assistant_text
                            ):
                                try:
                                    # Use the stored response_id instead of recalculating
                                    response_id = getattr(
                                        self,
                                        "_current_response_id",
                                        f"response_{len(self.messages)}",
                                    )

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

                                    # Estimate confidence from response
                                    confidence = ResponseAnalyzer.estimate_confidence(
                                        assistant_text
                                    )
                                    if confidence is not None:
                                        self.internal_sensing_framework.interoception.cognition.record_confidence(
                                            response_id, confidence
                                        )

                                    # Detect uncertainty
                                    uncertainty = ResponseAnalyzer.detect_uncertainty(
                                        assistant_text
                                    )
                                    if uncertainty is not None:
                                        self.internal_sensing_framework.interoception.cognition.record_uncertainty(
                                            response_id, uncertainty
                                        )

                                    # Compute valence and arousal
                                    # Use conversation history for valence (excluding system prompts)
                                    # Include current assistant response in history
                                    conversation_messages = self.messages + [
                                        {"role": "assistant", "content": assistant_text}
                                    ]
                                    self.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                                        conversation_messages
                                    )

                                    arousal = ResponseAnalyzer.compute_arousal(assistant_text)
                                    if arousal is not None:
                                        self.internal_sensing_framework.interoception.affect.compute_arousal(
                                            arousal
                                        )

                                    # Update affective states from cognitive
                                    self.internal_sensing_framework.interoception.affect.update_from_cognitive(
                                        self.internal_sensing_framework.interoception.cognition
                                    )

                                    # Record reasoning step
                                    self.internal_sensing_framework.interoception.cognition.record_reasoning_step(
                                        f"step_{response_id}",
                                        {
                                            "premise": user_text[:100] if self.messages else "",
                                            "conclusion": assistant_text[:100],
                                            "confidence": confidence,
                                        },
                                    )

                                    # Sample internal state after recomputing valence
                                    # Force a fresh sample by resetting last sample time to ensure updated valence is included
                                    self.internal_sensing_framework._last_sample_time = 0.0
                                    self.internal_sensing_framework.sample_internal_state()

                                except Exception as e:
                                    logger.warning(
                                        f"Error in response instrumentation: {e}", exc_info=True
                                    )

                            # Log context after turn
                            self._log_context_after_turn(
                                assistant_text=assistant_text, raw_response=response
                            )

                            # Auto-save skipped here to avoid background writes after test teardown
                        except Exception as e:
                            logger.warning(
                                f"Error in post-processing: {e}", exc_info=True
                            )
                    
                    # Start post-processing in background thread
                    thread = threading.Thread(target=do_post_processing, daemon=True)
                    thread.start()
                except Exception as e:
                    # Fallback: do it synchronously if threading fails
                    logger.warning(f"Failed to start background thread, doing post-processing synchronously: {e}", exc_info=True)
                    try:
                        if (
                            self.internal_sensing_framework
                            and ResponseAnalyzer
                            and assistant_text
                        ):
                            # Minimal instrumentation only
                            pass
                        self._log_context_after_turn(
                            assistant_text=assistant_text, raw_response=response
                        )
                        # Skip extra save here to avoid post-teardown writes in tests
                    except Exception as e2:
                        logger.warning(f"Error in fallback post-processing: {e2}", exc_info=True)

                return assistant_text

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
        self._save_conversation()
        return assistant_text

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
            resp = self.llm.chat(messages)
            return self.llm.extract_assistant_content(resp) or "Summary generated."
        except Exception:
            return "Summary unavailable due to an internal error."

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
                "assistant_preview": assistant_text[:200]
                + ("..." if len(assistant_text) > 200 else ""),
                "usage": usage,
            },
        )

    def _get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get messages to send to LLM, filtering to last K turns when summarization is enabled.
        
        When summarization is enabled and a summary exists, returns only:
        - System message (at index 0)
        - Last K turns (user/assistant pairs, where K = config.summarization.last_turns_count)
        
        When summarization is disabled or no summary exists, returns full message history.
        
        Returns:
            Filtered message list for LLM calls
        """
        # If summarization not enabled, return full messages
        if not self._summarization_manager:
            return self.messages
        
        # Check if summary exists for this session
        try:
            summary = self._summarization_manager.summary_storage.load_session_summary(self.session_id)
            if not summary:
                # No summary exists yet, return full messages
                return self.messages
        except Exception as e:
            logger.debug(f"Error checking for summary, using full messages: {e}")
            return self.messages
        
        # Summary exists - filter to system message + last K turns
        from ..config import config
        last_turns_count = config.summarization.last_turns_count
        
        # Get system message (if exists)
        system_message = None
        if self.messages and self.messages[0].get("role") == "system":
            system_message = self.messages[0]
        
        # Get last K turns (non-system messages)
        # Filter out system messages to get conversation turns
        non_system_messages = [m for m in self.messages if m.get("role") != "system"]
        
        # Each turn = user + assistant (and possibly tool calls/results)
        # Get last K turns worth of messages
        # Estimate: each turn is typically 2-4 messages (user, assistant, possibly tool_call, tool_result)
        # To be safe, take last K*2 messages as a conservative estimate for K turns
        turns_to_keep = last_turns_count * 2
        start_idx = max(0, len(non_system_messages) - turns_to_keep)
        last_turns = non_system_messages[start_idx:]
        
        # Reconstruct message list: system message (if exists) + last turns
        filtered_messages = []
        if system_message:
            filtered_messages.append(system_message)
        filtered_messages.extend(last_turns)
        
        logger.debug(
            f"Filtered messages for LLM: {len(filtered_messages)} messages "
            f"(full history: {len(self.messages)} messages, keeping last {last_turns_count} turns)"
        )
        
        return filtered_messages

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
        """
        if not self.world_state_aggregator or not self._world_state_formatter:
            return

        try:
            # Aggregate current world state
            world_state = self.world_state_aggregator.aggregate()

            # Format world state for prompt
            formatted_world_state = self._world_state_formatter.format(world_state)

            # Combine base prompt, summary context, and world state
            parts = []
            if self.base_system_prompt:
                parts.append(self.base_system_prompt)
            
            # Add summary context if summarization is enabled
            if self._summarization_manager:
                try:
                    from ..summarization.prompt_builder import PromptBuilder
                    from ..config import config
                    
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
                        parts.append(summary_context)
                except Exception as e:
                    logger.debug(f"Failed to add summary context to prompt: {e}", exc_info=True)
            
            if formatted_world_state:
                parts.append(formatted_world_state)

            # Join with double newline if multiple parts exist
            if len(parts) > 1:
                complete_prompt = "\n\n".join(parts)
            elif len(parts) == 1:
                complete_prompt = parts[0]
            else:
                complete_prompt = ""

            # Update or create system message
            if self.messages and self.messages[0].get("role") == "system":
                # Update existing system message
                self.messages[0]["content"] = complete_prompt
            else:
                # Create new system message at the beginning
                self.messages.insert(0, {"role": "system", "content": complete_prompt})

            logger.debug("Updated system prompt with current world state and summary context")

        except Exception as e:
            logger.warning(
                f"Error updating system prompt with world state: {e}", exc_info=True
            )
            # Continue with existing system prompt on error

    # ---------- Critic enforcement helpers ----------

    def _has_pending_critic_rejection(self) -> bool:
        """
        Check if there's a pending critic rejection that requires iteration.

        Returns:
            True if:
            - Critic tool exists but has never been called in this turn, OR
            - The last critic tool call resulted in a rejection
            False if the last critic call was accepted
        """
        if not self.tool_registry:
            return False

        # Check if critic tool is registered
        critic_tool = self.tool_registry.get_tool("critic")
        if not critic_tool:
            return False

        # Find the index of the last user message (start of current turn)
        last_user_index = -1
        for i, message in enumerate(self.messages):
            if message.get("role") == "user":
                last_user_index = i

        # Look backwards through messages from the last user message
        # to find critic tool results in the current turn
        critic_called_in_turn = False
        last_critic_result = None

        for i in range(len(self.messages) - 1, last_user_index, -1):
            message = self.messages[i]
            if message.get("role") == "tool" and message.get("name") == "critic":
                critic_called_in_turn = True
                # Check raw result if available
                raw_result = message.get("_raw_result")
                if raw_result and isinstance(raw_result, dict):
                    last_critic_result = raw_result
                    break

                # Fallback: check formatted content for rejection indicators
                content = message.get("content", "")
                if "rejected" in content.lower() or "violat" in content.lower():
                    # Check if it's actually rejected (not just mentioning rejection)
                    if (
                        "accepted" not in content.lower()
                        or "rejected" in content.lower()
                    ):
                        last_critic_result = {"accepted": False}
                        break
                # If we find an accepted critic result
                elif (
                    "accepted" in content.lower() and "rejected" not in content.lower()
                ):
                    last_critic_result = {"accepted": True}
                    break

        # If critic tool exists but was never called in this turn, block final response
        if not critic_called_in_turn:
            return True

        # If critic was called, check if it was accepted
        if last_critic_result:
            accepted = last_critic_result.get("accepted", False)
            return not accepted

        # If we can't determine the result, assume rejection (safer)
        return True

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
                # Log tool call event
                if self._event_logger:
                    try:
                        self._event_logger.log_tool_call(
                            self.session_id,
                            tool_name,
                            arguments,
                            tool_call_id=tool_call_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log tool call event: {e}", exc_info=True)
                
                tool_result = self.tool_registry.execute_tool_call(tool_call)
                self.messages.append(tool_result)
                
                # Log tool result event
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
                        
                        self._event_logger.log_tool_result(
                            self.session_id,
                            tool_name,
                            result_dict,
                            tool_call_id=tool_call_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log tool result event: {e}", exc_info=True)

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
                        tool_success = tool_result.get("content", "").lower()
                        is_success = (
                            "error" not in tool_success and "failed" not in tool_success
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
                self.messages.append(
                    {
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": tool_name,
                        "content": f"Error: {str(e)}",
                    }
                )

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
        """
        if not self.storage:
            return

        try:
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

            # Extract base system prompt from metadata (this is the user-defined base prompt)
            # Use the saved value, even if empty (don't override with config when loading)
            base_system_prompt = metadata.get("system_prompt", "")

            # If messages contain a system message with combined prompt, try to extract base
            # This handles cases where the system message has both base prompt and world state
            if messages and messages[0].get("role") == "system":
                system_content = messages[0].get("content", "")
                # If the content contains both base prompt and JSON (separated by \n\n),
                # and we don't have a base prompt in metadata, try to extract it
                if "\n\n" in system_content and not base_system_prompt:
                    parts = system_content.split("\n\n", 1)
                    potential_base = parts[0].strip()
                    # Only use if it doesn't look like JSON
                    if potential_base and not potential_base.startswith("{"):
                        base_system_prompt = potential_base

            # Create session with base system prompt
            # Note: We don't pass system_prompt parameter to avoid double-adding
            # The messages will be restored below
            # Pass base_system_prompt explicitly (even if empty) to avoid using config
            session = cls(
                system_prompt=None,  # Don't add system prompt here, we'll use messages
                llm=llm,
                storage=storage,
                session_id=session_id,
                world_state_aggregator=world_state_aggregator,
                base_system_prompt=base_system_prompt,  # Use saved value, not config
            )

            # Restore messages directly (they already contain the system message)
            if messages:
                session.messages = messages

            # Restore timestamps
            session.created_at = metadata.get("created_at", session.created_at)
            session.updated_at = metadata.get("updated_at", session.updated_at)

            # Restore system_prompt for backward compatibility (legacy code may check this)
            # This is the base prompt, not the full combined prompt
            # If saved value is empty, set to None to indicate no system prompt was set
            session.system_prompt = base_system_prompt if base_system_prompt else None

            # If we have a world state aggregator, update the system prompt to refresh world state
            # This ensures the world state is current even after loading
            if world_state_aggregator and session._world_state_formatter:
                session._update_system_prompt()

            logger.info(f"Loaded conversation {session_id} from storage")
            return session

        except Exception as e:
            logger.error(
                f"Failed to load conversation {session_id}: {e}", exc_info=True
            )
            return None
