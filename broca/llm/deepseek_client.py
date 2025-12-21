from __future__ import annotations

from typing import List, Dict, Any, Optional, Iterator
import httpx
import logging
import json

from ..config import config

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """
    Thin wrapper around DeepSeek's chat completion API.
    Assumes an OpenAI-compatible interface; adjust fields if DeepSeek differs.
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

        # Use httpx.Timeout for granular control (connect timeout vs read timeout)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_value, connect=10.0)  # 10s connect, configurable read
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request and return the raw JSON response.
        
        Args:
            messages: List of message dictionaries
            temperature: Optional temperature override
            tools: Optional list of tools in OpenAI function calling format
            reasoning_content: Optional reasoning_content for deepseek-reasoner model
                              (required when continuing reasoning after tool calls)
        """
        temp = temperature if temperature is not None else self.temperature

        # Clean messages to remove old reasoning_content fields (prevents 400 errors)
        cleaned_messages = self.clean_messages_for_reasoner(messages) if self.is_reasoner_model() else messages
        
        # Debug: Check assistant messages with tool_calls for reasoning_content
        if self.is_reasoner_model():
            for i, msg in enumerate(cleaned_messages):
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    has_reasoning = "reasoning_content" in msg
                    logger.debug(
                        f"Assistant message at index {i} with tool_calls: reasoning_content={'present' if has_reasoning else 'MISSING'}",
                        extra={
                            "event": "assistant_message_check",
                            "index": i,
                            "has_tool_calls": True,
                            "has_reasoning_content": has_reasoning,
                            "reasoning_value": msg.get("reasoning_content", "NOT_PRESENT")[:100] if has_reasoning else None,
                        }
                    )
        
        # Validate message interleaving for reasoner model
        if self.is_reasoner_model():
            if not self.validate_message_interleaving(cleaned_messages):
                logger.warning(
                    "Message interleaving validation failed - consecutive user/assistant messages detected. "
                    "This may cause 400 errors with deepseek-reasoner."
                )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": cleaned_messages,
            "temperature": temp,
        }
        
        if tools:
            payload["tools"] = tools
        
        # Include reasoning_content for reasoner model when provided
        if self.is_reasoner_model() and reasoning_content:
            payload["reasoning_content"] = reasoning_content
            logger.debug(
                "Including reasoning_content in request",
                extra={
                    "event": "reasoning_content_included",
                    "reasoning_length": len(reasoning_content),
                    "messages_count": len(cleaned_messages),
                }
            )

        logger.debug(
            "Sending chat request",
            extra={
                "event": "llm_request",
                "model": self.model,
                "temperature": temp,
                "messages_count": len(messages),
                "tools_count": len(tools) if tools else 0,
                # Truncate to avoid insane logs; you can change this later.
                "last_user_message_preview": self._last_user_preview(messages),
            },
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = self._client.post("/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

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
            
        except httpx.ReadTimeout as e:
            logger.error(
                f"API request timed out after {self._client.timeout.read} seconds",
                exc_info=True
            )
            raise TimeoutError(
                f"API request timed out. The request took longer than {self._client.timeout.read} seconds. "
                "This may happen with large conversations or when the API is slow. "
                "Try reducing conversation history or increasing the timeout."
            ) from e
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                if e.response is not None:
                    error_body = e.response.text
                    error_detail = f" Response body: {error_body[:500]}"
            except Exception:
                pass
            logger.error(
                f"API returned error status: {e.response.status_code}{error_detail}",
                extra={
                    "event": "api_error",
                    "status_code": e.response.status_code if e.response else None,
                    "model": self.model,
                    "is_reasoner": self.is_reasoner_model(),
                },
                exc_info=True
            )
            raise  # Re-raise HTTP status errors (preserve existing behavior)
        except httpx.RequestError as e:
            logger.error(
                f"Network error during API request: {e}",
                exc_info=True
            )
            raise ConnectionError(f"Network error: {e}") from e

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream chat completion, yielding text chunks as they arrive.
        
        Args:
            messages: List of message dictionaries
            temperature: Optional temperature override
            tools: Optional list of tools in OpenAI function calling format
            reasoning_content: Optional reasoning_content for deepseek-reasoner model
                              (required when continuing reasoning after tool calls)
        
        Yields:
            Text chunks from the streaming response
        
        Note: This should only be used for final responses (no tool calls expected).
        For requests with tools, use chat() instead and handle tool calls first.
        """
        temp = temperature if temperature is not None else self.temperature

        # Clean messages to remove old reasoning_content fields (prevents 400 errors)
        cleaned_messages = self.clean_messages_for_reasoner(messages) if self.is_reasoner_model() else messages
        
        # Validate message interleaving for reasoner model
        if self.is_reasoner_model():
            if not self.validate_message_interleaving(cleaned_messages):
                logger.warning(
                    "Message interleaving validation failed - consecutive user/assistant messages detected. "
                    "This may cause 400 errors with deepseek-reasoner."
                )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": cleaned_messages,
            "temperature": temp,
            "stream": True,
        }
        
        if tools:
            payload["tools"] = tools
        
        # Include reasoning_content for reasoner model when provided
        if self.is_reasoner_model() and reasoning_content:
            payload["reasoning_content"] = reasoning_content

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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            # Make streaming request
            with self._client.stream("POST", "/chat/completions", json=payload, headers=headers) as response:
                response.raise_for_status()
                
                # Process streaming response (Server-Sent Events format)
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    # SSE format: "data: {...}" or "data: [DONE]"
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        # Skip [DONE] message
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices and len(choices) > 0:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            # Skip malformed JSON chunks
                            continue
            
        except httpx.ReadTimeout as e:
            logger.error(
                f"API streaming request timed out after {self._client.timeout.read} seconds",
                exc_info=True
            )
            raise TimeoutError(
                f"API request timed out. The request took longer than {self._client.timeout.read} seconds. "
                "This may happen with large conversations or when the API is slow. "
                "Try reducing conversation history or increasing the timeout."
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error(
                f"API returned error status during streaming: {e.response.status_code}",
                exc_info=True
            )
            raise  # Re-raise HTTP status errors (preserve existing behavior)
        except httpx.RequestError as e:
            logger.error(
                f"Network error during API streaming request: {e}",
                exc_info=True
            )
            raise ConnectionError(f"Network error: {e}") from e

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
    
    def is_reasoner_model(self) -> bool:
        """
        Check if the current model is deepseek-reasoner.
        
        Returns:
            True if model is deepseek-reasoner, False otherwise
        """
        return self.model == "deepseek-reasoner"
    
    @staticmethod
    def extract_reasoning_content(response: Dict[str, Any]) -> Optional[str]:
        """
        Extract reasoning_content from DeepSeek reasoner model response.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            reasoning_content string if present, None otherwise
        """
        try:
            message = response.get("choices", [{}])[0].get("message", {})
            reasoning_content = message.get("reasoning_content")
            return reasoning_content
        except (KeyError, IndexError, AttributeError):
            return None
    
    @staticmethod
    def clean_messages_for_reasoner(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean messages by removing reasoning_content fields.
        
        DeepSeek reasoner model requires that reasoning_content from previous
        responses is not included in subsequent requests. However, assistant messages
        with tool_calls MUST retain their reasoning_content field.
        
        This method removes reasoning_content from:
        - Final assistant responses (no tool_calls)
        - But keeps reasoning_content in assistant messages with tool_calls
        
        Args:
            messages: List of message dictionaries (may contain reasoning_content)
            
        Returns:
            New list of messages with reasoning_content removed from final responses only
        """
        cleaned = []
        for msg in messages:
            # Create a copy to avoid mutating the original
            cleaned_msg = msg.copy()
            role = cleaned_msg.get("role")
            
            # Only remove reasoning_content from assistant messages that DON'T have tool_calls
            # Assistant messages with tool_calls MUST keep reasoning_content (API requirement)
            if role == "assistant" and "reasoning_content" in cleaned_msg:
                # Check if this assistant message has tool_calls
                has_tool_calls = "tool_calls" in cleaned_msg and cleaned_msg.get("tool_calls")
                
                # Remove reasoning_content only if it's a final response (no tool_calls)
                if not has_tool_calls:
                    del cleaned_msg["reasoning_content"]
                # If it has tool_calls, keep reasoning_content (required by API)
            elif "reasoning_content" in cleaned_msg:
                # Remove from non-assistant messages (shouldn't have it, but clean it anyway)
                del cleaned_msg["reasoning_content"]
            
            cleaned.append(cleaned_msg)
        return cleaned
    
    @staticmethod
    def validate_message_interleaving(messages: List[Dict[str, Any]]) -> bool:
        """
        Validate that messages are properly interleaved (no consecutive user/assistant messages).
        
        DeepSeek reasoner model does not support consecutive user or assistant messages.
        Messages must alternate between user and assistant (with system/tool messages allowed).
        
        Note: Assistant messages after tool messages are allowed (tool execution is between them).
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            True if messages are properly interleaved, False otherwise
        """
        last_role = None
        last_was_tool = False
        
        for msg in messages:
            role = msg.get("role")
            # Skip system messages (they don't count for interleaving)
            if role == "system":
                continue
            
            # Tool messages reset the last_role tracking (allow assistant after tool)
            if role == "tool":
                last_was_tool = True
                continue
            
            # Check for consecutive user or assistant messages
            # Exception: assistant after tool is allowed
            if role in ("user", "assistant"):
                if last_role == role and not (role == "assistant" and last_was_tool):
                    return False
                last_role = role
                last_was_tool = False
            else:
                # Reset last_role for other message types
                last_role = None
                last_was_tool = False
        
        return True
    
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
