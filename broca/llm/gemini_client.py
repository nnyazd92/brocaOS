from __future__ import annotations

from typing import List, Dict, Any, Optional, Iterator
import logging
import time

import httpx

from ..config import config

logger = logging.getLogger(__name__)

# Check if google-genai SDK is available
try:
    import google.genai as genai
    _HAS_SDK = True
except ImportError:
    _HAS_SDK = False


class GeminiClient:
    """Thin wrapper around Gemini 3 with support for both SDK and REST API.

    Supports Gemini 3 features:
    - thinking_level: "low" (fast) or "high" (deep reasoning) - only supported via SDK (native API)
    - thought_signature: Maintains reasoning context across turns

    Uses google-genai SDK by default (if available), falls back to REST API.
    Note: When using the OpenAI-compatible REST endpoint, Gemini-specific parameters
    like thinking_level are not supported as the endpoint follows OpenAI's API schema.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        thinking_level: Optional[str] = None,
        use_sdk: Optional[bool] = None,
    ) -> None:
        # Defaults come from config.llm but can be overridden.
        self.api_key = api_key or config.llm.api_key
        # For Gemini OpenAI-compatible, base_url is typically something like
        # https://generativelanguage.googleapis.com/v1beta/openai
        self.base_url = base_url or config.llm.api_base
        self.model = model or config.llm.model
        self.temperature = temperature if temperature is not None else config.llm.temperature
        timeout_value = timeout if timeout is not None else config.llm.timeout
        
        # Gemini 3 specific configuration
        self.thinking_level = thinking_level or getattr(config.llm, "thinking_level", "low")
        self.use_sdk = use_sdk if use_sdk is not None else getattr(config.llm, "use_sdk", True)
        
        # Store thought_signature for maintaining reasoning context
        self._thought_signature: Optional[str] = None

        # httpx client for REST API fallback
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_value, connect=10.0),
        )
        
        # Initialize SDK client if available and use_sdk is True
        self._sdk_client: Optional[Any] = None
        if self._should_use_sdk():
            try:
                # Try to initialize SDK - exact API may vary by version
                # This is a best-effort attempt; will fall back to REST if it fails
                if hasattr(genai, "configure"):
                    genai.configure(api_key=self.api_key)
                if hasattr(genai, "Client"):
                    self._sdk_client = genai.Client(api_key=self.api_key)
                elif hasattr(genai, "GenerativeModel"):
                    # Alternative SDK API structure
                    self._sdk_client = genai.GenerativeModel(self.model)
                else:
                    raise AttributeError("SDK API not recognized")
                logger.info("Using google-genai SDK for Gemini 3")
            except Exception as e:
                logger.warning(f"Failed to initialize SDK, falling back to REST API: {e}")
                self.use_sdk = False
                self._sdk_client = None
        else:
            logger.info("Using REST API for Gemini 3")

    def _should_use_sdk(self) -> bool:
        """Determine if SDK should be used."""
        return self.use_sdk and _HAS_SDK

    def _build_generation_config(self) -> Dict[str, Any]:
        """Build generation_config with thinking_level."""
        return {
            "thinking_level": self.thinking_level,
        }
    
    def _should_retry_error(self, error: httpx.HTTPStatusError) -> bool:
        """Determine if an HTTP error should be retried.
        
        Retries on rate limits (429) and server errors (500, 502, 503, 504).
        Does not retry on client errors (4xx except 429) or authentication errors.
        """
        if error.response is None:
            return False
        status_code = error.response.status_code
        # Retry on rate limits and server errors
        return status_code in (429, 500, 502, 503, 504)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a chat completion request and return the raw JSON response.

        Args:
            messages: List of message dictionaries with roles/content.
            temperature: Optional temperature override.
            tools: Optional list of tools in OpenAI function calling format.
            reasoning_content: Unused for Gemini (present for Protocol parity).
            thought_signature: Optional thought_signature to maintain reasoning context.
        """
        # Use parameter if provided, otherwise use stored signature
        sig_to_use = thought_signature if thought_signature is not None else self._thought_signature
        
        if self._should_use_sdk() and self._sdk_client is not None:
            return self._chat_sdk(messages, temperature, tools, sig_to_use)
        else:
            return self._chat_rest(messages, temperature, tools, sig_to_use)

    def _chat_sdk(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        tools: Optional[List[Dict[str, Any]]],
        thought_signature: Optional[str],
    ) -> Dict[str, Any]:
        """Chat using google-genai SDK."""
        temp = temperature if temperature is not None else self.temperature
        
        # Convert messages to SDK format
        sdk_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                # SDK handles system messages differently
                sdk_messages.append({"role": "user", "parts": [{"text": f"System: {content}"}]})
            elif role == "user":
                sdk_messages.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                sdk_messages.append({"role": "model", "parts": [{"text": content}]})
        
        try:
            # Build generation config
            generation_config = self._build_generation_config()
            if temp is not None:
                generation_config["temperature"] = temp
            
            # Create request
            request_params: Dict[str, Any] = {
                "model": self.model,
                "contents": sdk_messages,
                "generation_config": generation_config,
            }
            
            if thought_signature:
                request_params["thought_signature"] = thought_signature
            
            if tools:
                # Convert tools to SDK format
                request_params["tools"] = self._convert_tools_to_sdk_format(tools)
            
            logger.debug(
                "Sending Gemini SDK chat request",
                extra={
                    "event": "llm_request",
                    "provider": "gemini",
                    "mode": "sdk",
                    "model": self.model,
                    "temperature": temp,
                    "thinking_level": self.thinking_level,
                    "messages_count": len(messages),
                    "tools_count": len(tools) if tools else 0,
                    "has_thought_signature": bool(thought_signature),
                },
            )
            
            # Call SDK
            response = self._sdk_client.models.generate_content(**request_params)
            
            # Extract thought_signature from response
            extracted_sig = self._extract_thought_signature_from_sdk_response(response)
            if extracted_sig:
                self._thought_signature = extracted_sig
            
            # Convert SDK response to OpenAI-compatible format
            return self._convert_sdk_response_to_openai_format(response)
            
        except Exception as e:
            logger.warning(f"SDK request failed, falling back to REST: {e}")
            # Fall back to REST
            return self._chat_rest(messages, temperature, tools, thought_signature)

    def _chat_rest(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        tools: Optional[List[Dict[str, Any]]],
        thought_signature: Optional[str],
    ) -> Dict[str, Any]:
        """Chat using REST API (OpenAI-compatible endpoint).
        
        Note: The OpenAI-compatible endpoint follows OpenAI's API schema and does not
        support Gemini-specific fields like generation_config or thinking_level.
        These features are only available when using the SDK (native API).
        """
        temp = temperature if temperature is not None else self.temperature

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
        }

        if tools:
            payload["tools"] = tools
        
        if thought_signature:
            payload["thought_signature"] = thought_signature

        logger.debug(
            "Sending Gemini REST chat request",
            extra={
                "event": "llm_request",
                "provider": "gemini",
                "mode": "rest",
                "model": self.model,
                "temperature": temp,
                "thinking_level": self.thinking_level,
                "messages_count": len(messages),
                "tools_count": len(tools) if tools else 0,
                "has_thought_signature": bool(thought_signature),
                "last_user_message_preview": self._last_user_preview(messages),
            },
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Retry logic for transient errors
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                resp = self._client.post("/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                
                # Extract and store thought_signature
                extracted_sig = self.extract_thought_signature(data)
                if extracted_sig:
                    self._thought_signature = extracted_sig

                logger.debug(
                    "Received Gemini REST chat response",
                    extra={
                        "event": "llm_response",
                        "provider": "gemini",
                        "mode": "rest",
                        "model": self.model,
                        "usage": data.get("usage", {}),
                        "choices_count": len(data.get("choices", [])),
                        "has_thought_signature": bool(extracted_sig),
                    },
                )

                return data

            except httpx.HTTPStatusError as e:
                last_exception = e
                if attempt < max_retries and self._should_retry_error(e):
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    status_code = e.response.status_code if e.response else "unknown"
                    logger.warning(
                        f"Gemini API transient error {status_code}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_error_retry",
                            "provider": "gemini",
                            "status_code": status_code,
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                        }
                    )
                    time.sleep(wait_time)
                    continue
                # Not retryable or out of retries - break and handle below
                break
            except httpx.ReadTimeout as e:
                # Timeout errors are not retried
                logger.error(
                    "Gemini API request timed out",
                    exc_info=True,
                )
                raise TimeoutError(
                    "Gemini API request timed out. Try reducing conversation length or "
                    "increasing the configured timeout."
                ) from e
            except httpx.RequestError as e:
                # Network errors are not retried
                logger.error(
                    f"Network error during Gemini API request: {e}",
                    exc_info=True,
                )
                raise ConnectionError(f"Network error: {e}") from e
        
        # Handle HTTPStatusError that wasn't retried or failed all retries
        if isinstance(last_exception, httpx.HTTPStatusError):
            error_detail = ""
            try:
                if last_exception.response is not None:
                    body = last_exception.response.text
                    error_detail = f" Response body: {body[:500]}"
            except Exception:
                pass

            logger.error(
                f"Gemini API returned error status: {last_exception.response.status_code if last_exception.response else 'unknown'}{error_detail}",
                extra={
                    "event": "api_error",
                    "provider": "gemini",
                    "model": self.model,
                },
                exc_info=True,
            )
            raise last_exception

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Iterator[str]:
        """Stream chat completion, yielding text chunks as they arrive.

        Note: Streaming with thought_signature may not be fully supported in SDK mode.
        Falls back to REST API for streaming.
        """
        sig_to_use = thought_signature if thought_signature is not None else self._thought_signature
        
        # For now, use REST API for streaming (SDK streaming is more complex)
        return self._chat_stream_rest(messages, temperature, tools, sig_to_use)

    def _chat_stream_rest(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        tools: Optional[List[Dict[str, Any]]],
        thought_signature: Optional[str],
    ) -> Iterator[str]:
        """Stream using REST API.
        
        Note: The OpenAI-compatible endpoint follows OpenAI's API schema and does not
        support Gemini-specific fields like generation_config or thinking_level.
        These features are only available when using the SDK (native API).
        """
        temp = temperature if temperature is not None else self.temperature

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
        if thought_signature:
            payload["thought_signature"] = thought_signature

        logger.debug(
            "Sending Gemini streaming REST chat request",
            extra={
                "event": "llm_request_stream",
                "provider": "gemini",
                "mode": "rest",
                "model": self.model,
                "temperature": temp,
                "thinking_level": self.thinking_level,
                "messages_count": len(messages),
                "tools_count": len(tools) if tools else 0,
                "has_thought_signature": bool(thought_signature),
                "last_user_message_preview": self._last_user_preview(messages),
            },
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_chunk_thought_sig: Optional[str] = None

        # Retry logic for transient errors (retries the initial request)
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                with self._client.stream("POST", "/chat/completions", json=payload, headers=headers) as response:
                    response.raise_for_status()

                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                # Check final chunk for thought_signature
                                if last_chunk_thought_sig:
                                    self._thought_signature = last_chunk_thought_sig
                                break
                            try:
                                chunk = httpx.Response(200, text=data_str).json()
                            except Exception:
                                continue
                            choices = chunk.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            content = delta.get("content")
                            
                            # Check for thought_signature in chunk (may be in final empty chunk)
                            chunk_sig = chunk.get("thought_signature") or choices[0].get("thought_signature")
                            if chunk_sig:
                                last_chunk_thought_sig = chunk_sig
                            
                            if content:
                                yield content
                                
                    # Store signature from final chunk if found
                    if last_chunk_thought_sig:
                        self._thought_signature = last_chunk_thought_sig
                    
                    # Success - return (generator completes)
                    return
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                if attempt < max_retries and self._should_retry_error(e):
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    status_code = e.response.status_code if e.response else "unknown"
                    logger.warning(
                        f"Gemini API transient error {status_code} during streaming, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_error_retry_stream",
                            "provider": "gemini",
                            "status_code": status_code,
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                        }
                    )
                    time.sleep(wait_time)
                    continue
                # Not retryable or out of retries - break and handle below
                break
            except httpx.ReadTimeout as e:
                # Timeout errors are not retried
                logger.error(
                    "Gemini API streaming request timed out",
                    exc_info=True,
                )
                raise TimeoutError(
                    "Gemini streaming request timed out. Try reducing conversation "
                    "length or increasing the configured timeout."
                ) from e
            except httpx.RequestError as e:
                # Network errors are not retried
                logger.error(
                    f"Network error during Gemini streaming API request: {e}",
                    exc_info=True,
                )
                raise ConnectionError(f"Network error: {e}") from e
        
        # Handle HTTPStatusError that wasn't retried or failed all retries
        if isinstance(last_exception, httpx.HTTPStatusError):
            error_detail = ""
            try:
                if last_exception.response is not None:
                    body = last_exception.response.text
                    error_detail = f" Response body: {body[:500]}"
            except Exception:
                pass

            logger.error(
                f"Gemini API returned error status during streaming: {last_exception.response.status_code if last_exception.response else 'unknown'}{error_detail}",
                extra={
                    "event": "api_error_stream",
                    "provider": "gemini",
                    "model": self.model,
                },
                exc_info=True,
            )
            raise last_exception

    @staticmethod
    def extract_assistant_content(response: Dict[str, Any]) -> str:
        """Extract the assistant's textual content from a response."""
        try:
            return response["choices"][0]["message"].get("content", "")
        except (KeyError, IndexError, AttributeError):
            return ""

    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from an LLM response.

        Returns a list of `tool_calls` objects compatible with the rest of
        BrocaOS's tool routing.
        """
        try:
            message = response.get("choices", [{}])[0].get("message", {})
            tool_calls = message.get("tool_calls")
            return tool_calls or []
        except (KeyError, IndexError, AttributeError):
            return []

    @staticmethod
    def extract_thought_signature(response: Dict[str, Any]) -> Optional[str]:
        """Extract thought_signature from a response.
        
        Handles multiple response formats:
        - REST API: thought_signature in response root or in choices
        - Function calls: thought_signature in tool_calls
        """
        # Check response root
        if "thought_signature" in response:
            return response["thought_signature"]
        
        # Check in choices
        try:
            choices = response.get("choices", [])
            if choices:
                # Check first choice
                choice = choices[0]
                if "thought_signature" in choice:
                    return choice["thought_signature"]
                
                # Check in message
                message = choice.get("message", {})
                if "thought_signature" in message:
                    return message["thought_signature"]
                
                # Check in tool_calls (function calls)
                tool_calls = message.get("tool_calls", [])
                if tool_calls:
                    # For function calls, check first tool_call
                    first_call = tool_calls[0]
                    if "thought_signature" in first_call:
                        return first_call["thought_signature"]
        except (KeyError, IndexError, AttributeError, TypeError):
            pass
        
        return None

    def _extract_thought_signature_from_sdk_response(self, response: Any) -> Optional[str]:
        """Extract thought_signature from SDK response object."""
        try:
            # SDK response structure may vary - check common attributes
            if hasattr(response, "thought_signature") and response.thought_signature:
                return str(response.thought_signature)
            
            # Check in candidates
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "thought_signature") and candidate.thought_signature:
                    return str(candidate.thought_signature)
            
            # Check in content parts
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "thought_signature") and part.thought_signature:
                            return str(part.thought_signature)
        except (AttributeError, IndexError, TypeError):
            pass
        
        return None

    def _convert_sdk_response_to_openai_format(self, response: Any) -> Dict[str, Any]:
        """Convert SDK response to OpenAI-compatible format."""
        try:
            content = ""
            tool_calls = []
            
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "text"):
                            content += part.text
                        elif hasattr(part, "function_call"):
                            # Convert function call format
                            tool_calls.append({
                                "id": f"call_{len(tool_calls)}",
                                "type": "function",
                                "function": {
                                    "name": part.function_call.name,
                                    "arguments": str(part.function_call.args),
                                }
                            })
            
            result: Dict[str, Any] = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": content if content else None,
                    }
                }]
            }
            
            if tool_calls:
                result["choices"][0]["message"]["tool_calls"] = tool_calls
                result["choices"][0]["message"]["content"] = None
            
            # Add usage if available
            if hasattr(response, "usage_metadata"):
                result["usage"] = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(response.usage_metadata, "completion_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }
            
            return result
        except Exception as e:
            logger.warning(f"Failed to convert SDK response: {e}")
            # Return minimal response
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "",
                    }
                }]
            }

    def _convert_tools_to_sdk_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI function calling format to SDK format."""
        # This is a simplified conversion - may need adjustment based on actual SDK format
        sdk_tools = []
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                sdk_tools.append({
                    "function_declarations": [{
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {}),
                    }]
                })
        return sdk_tools

    @staticmethod
    def _last_user_preview(messages: List[Dict[str, str]], max_len: int = 200) -> str:
        """Return a short preview of the last user message for logging."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content[:max_len] + ("..." if len(content) > max_len else "")
        return ""
