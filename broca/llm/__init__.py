"""
LLM client abstraction and factory.

This module provides a Protocol defining the LLM client interface and a factory
function to create appropriate client instances based on configuration.
"""

from __future__ import annotations

from typing import Protocol, List, Dict, Any, Optional

from ..config import config
from .deepseek_client import DeepSeekClient
from .openai_client import OpenAIClient


class LLMClient(Protocol):
    """
    Protocol defining the interface for LLM clients.
    
    All LLM client implementations (DeepSeek, OpenAI, etc.) must conform to this
    interface to ensure compatibility throughout the codebase.
    """
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request and return the raw JSON response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Optional temperature override
            tools: Optional list of tools in OpenAI function calling format
            
        Returns:
            Raw API response dictionary
        """
        ...
    
    @staticmethod
    def extract_assistant_content(response: Dict[str, Any]) -> str:
        """
        Extract the assistant's textual content from an API response.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            Assistant's message content as a string, empty string if not found
        """
        ...
    
    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool calls from an LLM response.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            List of tool call dictionaries, empty list if no tool calls
        """
        ...


def create_llm_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[float] = None,
    provider: Optional[str] = None,
) -> LLMClient:
    """
    Factory function to create an appropriate LLM client based on configuration.
    
    Creates either a DeepSeekClient or OpenAIClient instance based on the
    configured provider. Supports dependency injection for testing.
    
    Args:
        api_key: Optional API key override
        base_url: Optional base URL override
        model: Optional model name override
        temperature: Optional temperature override
        timeout: Optional timeout override
        provider: Optional provider override ("deepseek" or "openai")
        
    Returns:
        LLMClient instance (either DeepSeekClient or OpenAIClient)
        
    Raises:
        ValueError: If provider is not "deepseek" or "openai"
    """
    # Determine provider
    provider_name = provider or config.llm.provider.lower()
    
    # Build kwargs for client initialization
    client_kwargs: Dict[str, Any] = {}
    if api_key is not None:
        client_kwargs["api_key"] = api_key
    if base_url is not None:
        client_kwargs["base_url"] = base_url
    if model is not None:
        client_kwargs["model"] = model
    if temperature is not None:
        client_kwargs["temperature"] = temperature
    if timeout is not None:
        client_kwargs["timeout"] = timeout
    
    # Create appropriate client
    if provider_name == "deepseek":
        return DeepSeekClient(**client_kwargs)
    elif provider_name == "openai":
        return OpenAIClient(**client_kwargs)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            "Supported providers are 'deepseek' and 'openai'."
        )

