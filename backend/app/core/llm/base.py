from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Normalized Data Models
# ------------------------------------------------------------------------------

class ChatMessagePayload(BaseModel):
    """Normalized message representation for LLM conversation history."""
    role: str  # 'system', 'user', 'assistant'
    content: str


class LLMResponse(BaseModel):
    """Normalized response returned across all model providers."""
    text: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class ProviderHealth(BaseModel):
    """Safe provider status information with no credentials or secrets."""
    name: str
    configured: bool
    status: str  # 'connected', 'configured', 'unavailable', 'authentication_failed', 'model_not_found'
    model: str
    available_models: List[str] = Field(default_factory=list)
    detail: Optional[str] = None


# ------------------------------------------------------------------------------
# Exceptions Hierarchy
# ------------------------------------------------------------------------------

class LLMProviderError(Exception):
    """Base exception for all LLM provider failures."""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.provider = provider


class LLMConfigurationError(LLMProviderError):
    """Raised when required configuration or API key is missing."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when authentication against the provider fails."""
    pass


class LLMConnectionError(LLMProviderError):
    """Raised when the provider host/service cannot be reached."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when provider request exceeds configured timeout."""
    pass


class LLMModelNotFoundError(LLMProviderError):
    """Raised when the requested model is not installed or available."""
    pass


# ------------------------------------------------------------------------------
# Base LLM Provider
# ------------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Abstract base class establishing uniform interface for all providers."""

    name: str

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """
        Performs non-destructive check to verify configuration and connectivity.
        Does NOT expose secrets or credentials in the returned data.
        """
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Executes a normalized chat completion request.
        """
        pass
