from __future__ import annotations

from typing import List, Dict, Any, Optional
import httpx
import logging

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
    ) -> Dict[str, Any]:
        """
        Send a chat completion request and return the raw JSON response.
        
        Args:
            messages: List of message dictionaries
            temperature: Optional temperature override
            tools: Optional list of tools in OpenAI function calling format
        """
        temp = temperature if temperature is not None else self.temperature

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
        }
        
        if tools:
            payload["tools"] = tools

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
            logger.error(
                f"API returned error status: {e.response.status_code}",
                exc_info=True
            )
            raise  # Re-raise HTTP status errors (preserve existing behavior)
        except httpx.RequestError as e:
            logger.error(
                f"Network error during API request: {e}",
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
