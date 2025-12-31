from __future__ import annotations

from typing import List, Dict, Any, Optional, Iterator
import logging
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError, APIError

from ..config import config

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Thin wrapper around OpenAI's chat completion API.
    Uses the official OpenAI SDK for consistency and reliability.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.api_key = api_key or config.llm.api_key
        self.base_url = base_url or config.llm.api_base
        self.model = model or config.llm.model
        self.temperature = temperature if temperature is not None else config.llm.temperature
        timeout_value = timeout if timeout is not None else config.llm.timeout

        # Initialize OpenAI client with configuration
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout_value,
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request and return the raw JSON response.
        
        Args:
            messages: List of message dictionaries
            temperature: Optional temperature override
            tools: Optional list of tools in OpenAI function calling format
            reasoning_content: Optional reasoning_content (ignored for OpenAI, kept for Protocol compatibility)
        """
        temp = temperature if temperature is not None else self.temperature

        # Clean messages to remove orphaned tool messages (OpenAI API requirement)
        cleaned_messages = self._clean_messages(messages)

        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": cleaned_messages,
        }
        
        # Some OpenAI models (like o1, o1-preview, o1-mini, gpt-5, gpt-5.2, etc.) only support temperature=1.0 (the default)
        # They reject temperature=0.0 and other values, so we omit the parameter for any value != 1.0 for those models
        # This allows the API to use its default (1.0)
        models_requiring_default_temp = ["o1", "gpt-5"]
        requires_default_temp = any(self.model.startswith(prefix) for prefix in models_requiring_default_temp)
        
        # For models that only support default temperature, omit temperature parameter if temp != 1.0
        # For other models, always include temperature
        if not requires_default_temp or temp == 1.0:
            request_params["temperature"] = temp
        
        if tools:
            request_params["tools"] = tools
        if tool_choice is not None:
            request_params["tool_choice"] = tool_choice

        logger.debug(
            "Sending chat request",
            extra={
                "event": "llm_request",
                "model": self.model,
                "temperature": temp,
                "messages_count": len(cleaned_messages),
                "original_messages_count": len(messages),
                "tools_count": len(tools) if tools else 0,
                "tool_choice_set": tool_choice is not None,
                "last_user_message_preview": self._last_user_preview(cleaned_messages),
            },
        )

        try:
            # Call OpenAI API
            response = self._client.chat.completions.create(**request_params)
            
            # Convert Pydantic model to dict
            data = response.model_dump()

            logger.debug(
                "Received chat response",
                extra={
                    "event": "llm_response",
                    "model": self.model,
                    "usage": data.get("usage", {}),
                    "choices_count": len(data.get("choices", [])),
                },
            )

            return data
            
        except APITimeoutError as e:
            logger.error(
                f"API request timed out",
                exc_info=True
            )
            raise TimeoutError(
                f"API request timed out. "
                "This may happen with large conversations or when the API is slow. "
                "Try reducing conversation history or increasing the timeout."
            ) from e
        except APIConnectionError as e:
            logger.error(
                f"Network error during API request: {e}",
                exc_info=True
            )
            raise ConnectionError(f"Network error: {e}") from e
        except APIError as e:
            logger.error(
                f"API returned error: {e}",
                exc_info=True
            )
            raise  # Re-raise API errors (preserve existing behavior)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream chat completion, yielding text chunks as they arrive.
        
        Args:
            messages: List of message dictionaries
            temperature: Optional temperature override
            tools: Optional list of tools in OpenAI function calling format
            reasoning_content: Optional reasoning_content (ignored for OpenAI, kept for Protocol compatibility)
        
        Yields:
            Text chunks from the streaming response
        
        Note: This should only be used for final responses (no tool calls expected).
        For requests with tools, use chat() instead and handle tool calls first.
        """
        temp = temperature if temperature is not None else self.temperature

        # Clean messages to remove orphaned tool messages (OpenAI API requirement)
        cleaned_messages = self._clean_messages(messages)

        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": cleaned_messages,
            "stream": True,
        }
        
        # Some OpenAI models (like o1, o1-preview, o1-mini, gpt-5, gpt-5.2, etc.) only support temperature=1.0 (the default)
        # They reject temperature=0.0 and other values, so we omit the parameter for any value != 1.0 for those models
        # This allows the API to use its default (1.0)
        models_requiring_default_temp = ["o1", "gpt-5"]
        requires_default_temp = any(self.model.startswith(prefix) for prefix in models_requiring_default_temp)
        
        # For models that only support default temperature, omit temperature parameter if temp != 1.0
        # For other models, always include temperature
        if not requires_default_temp or temp == 1.0:
            request_params["temperature"] = temp
        
        if tools:
            request_params["tools"] = tools

        logger.debug(
            "Sending streaming chat request",
            extra={
                "event": "llm_request_stream",
                "model": self.model,
                "temperature": temp,
                "messages_count": len(messages),
                "tools_count": len(tools) if tools else 0,
                "last_user_message_preview": self._last_user_preview(messages),
            },
        )

        try:
            # Call OpenAI API with streaming
            stream = self._client.chat.completions.create(**request_params)
            
            # Yield text chunks as they arrive
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    # Check if delta has content attribute and it's not None/empty
                    # delta.content can be None for chunks that don't contain text (e.g., tool calls, finish reason)
                    if hasattr(delta, 'content') and delta.content is not None and delta.content:
                        yield delta.content
            
        except APITimeoutError as e:
            logger.error(
                f"API streaming request timed out",
                exc_info=True
            )
            raise TimeoutError(
                f"API request timed out. "
                "This may happen with large conversations or when the API is slow. "
                "Try reducing conversation history or increasing the timeout."
            ) from e
        except APIConnectionError as e:
            logger.error(
                f"Network error during API streaming request: {e}",
                exc_info=True
            )
            raise ConnectionError(f"Network error: {e}") from e
        except APIError as e:
            logger.error(
                f"API returned error during streaming: {e}",
                exc_info=True
            )
            raise  # Re-raise API errors (preserve existing behavior)

    @staticmethod
    def extract_assistant_content(response: Dict[str, Any]) -> str:
        """
        Convenience: pull the assistant's textual content.
        """
        try:
            return response["choices"][0]["message"].get("content", "")
        except (KeyError, IndexError, AttributeError):
            return ""

    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool calls from LLM response.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            List of tool call dictionaries, empty list if no tool calls
        """
        try:
            message = response.get("choices", [{}])[0].get("message", {})
            tool_calls = message.get("tool_calls")
            
            if not tool_calls:
                return []
            
            return tool_calls
            
        except (KeyError, IndexError, AttributeError):
            return []
    
    @staticmethod
    def _clean_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean messages by removing orphaned tool messages.
        
        OpenAI API requires that tool messages must follow an assistant message
        with matching tool_calls. This method filters out tool messages that
        don't have a preceding assistant message with matching tool_calls.
        
        Args:
            messages: List of message dictionaries (may contain orphaned tool messages)
            
        Returns:
            New list of messages with orphaned tool messages removed
        """
        if not messages:
            return messages
        
        cleaned = []
        # Track tool_call_ids from the most recent assistant message with tool_calls
        valid_tool_call_ids = set()
        
        for i, msg in enumerate(messages):
            role = msg.get("role")
            
            # Always include system, user, and assistant messages
            if role in ("system", "user", "assistant"):
                cleaned.append(msg)
                
                # If this is an assistant message with tool_calls, update valid tool_call_ids
                if role == "assistant":
                    tool_calls = msg.get("tool_calls")
                    if tool_calls and isinstance(tool_calls, list):
                        valid_tool_call_ids = {
                            tc.get("id") for tc in tool_calls 
                            if isinstance(tc, dict) and tc.get("id")
                        }
                    else:
                        # Assistant message without tool_calls - clear valid IDs
                        valid_tool_call_ids = set()
            
            # Handle tool messages - only include if they have a valid tool_call_id
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id and tool_call_id in valid_tool_call_ids:
                    cleaned.append(msg)
                    # Remove this tool_call_id from valid set (each tool_call_id should only be responded to once)
                    valid_tool_call_ids.discard(tool_call_id)
                else:
                    logger.warning(
                        f"Removing orphaned tool message at index {i}: tool_call_id={tool_call_id}, "
                        f"valid_ids={valid_tool_call_ids}",
                        extra={
                            "event": "orphaned_tool_message_removed",
                            "message_index": i,
                            "tool_call_id": tool_call_id,
                            "valid_tool_call_ids": list(valid_tool_call_ids),
                        }
                    )
        
        return cleaned

    @staticmethod
    def _last_user_preview(messages: List[Dict[str, str]], max_len: int = 200) -> str:
        """
        Find the last user message and return a truncated preview.
        """
        for msg in reversed(messages):
            if msg.get("role") == "user":
                txt = msg.get("content", "")
                return txt[:max_len] + ("..." if len(txt) > max_len else "")
        return ""
