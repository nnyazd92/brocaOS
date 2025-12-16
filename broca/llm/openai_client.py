from __future__ import annotations

from typing import List, Dict, Any, Optional
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
    ) -> Dict[str, Any]:
        """
        Send a chat completion request and return the raw JSON response.
        
        Args:
            messages: List of message dictionaries
            temperature: Optional temperature override
            tools: Optional list of tools in OpenAI function calling format
        """
        temp = temperature if temperature is not None else self.temperature

        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        
        # Some OpenAI models (like o1, o1-preview, o1-mini, gpt-5, gpt-5.2, etc.) only support temperature=1.0 (the default)
        # They reject temperature=0.0 and other values, so we omit the parameter when temp=0.0 for those models
        # This allows the API to use its default (1.0)
        models_requiring_default_temp = ["o1", "gpt-5"]
        requires_default_temp = any(self.model.startswith(prefix) for prefix in models_requiring_default_temp)
        
        # For models that only support default temperature, omit temperature parameter when temp=0.0
        # For other models, always include temperature
        if not (requires_default_temp and temp == 0.0):
            request_params["temperature"] = temp
        
        if tools:
            request_params["tools"] = tools

        logger.debug(
            "Sending chat request",
            extra={
                "event": "llm_request",
                "model": self.model,
                "temperature": temp,
                "messages_count": len(messages),
                "tools_count": len(tools) if tools else 0,
                "last_user_message_preview": self._last_user_preview(messages),
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
    def _last_user_preview(messages: List[Dict[str, str]], max_len: int = 200) -> str:
        """
        Find the last user message and return a truncated preview.
        """
        for msg in reversed(messages):
            if msg.get("role") == "user":
                txt = msg.get("content", "")
                return txt[:max_len] + ("..." if len(txt) > max_len else "")
        return ""

