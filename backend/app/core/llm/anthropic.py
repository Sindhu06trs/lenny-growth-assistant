from typing import List, Optional, Dict
import anthropic
from app.core.config import settings
from app.core.logging_config import logger
from app.core.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    ProviderHealth,
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMProviderError,
)

PLACEHOLDER_KEYS = {
    "",
    "your_anthropic_api_key_here",
    "placeholder",
    "none",
}


class AnthropicProvider(BaseLLMProvider):
    """
    Cloud LLM provider utilizing Anthropic's Claude 3.5 Sonnet API.
    """
    name = "anthropic"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.timeout = timeout or settings.LLM_REQUEST_TIMEOUT

    def _is_configured(self) -> bool:
        """Returns True if a real API key is present and not a template placeholder."""
        if not self.api_key:
            return False
        clean = self.api_key.strip().lower()
        return clean not in PLACEHOLDER_KEYS and not clean.startswith("your_")

    async def check_health(self) -> ProviderHealth:
        """
        Validates configuration without making expensive paid model queries.
        """
        if not self._is_configured():
            return ProviderHealth(
                name=self.name,
                configured=False,
                status="unavailable",
                model=self.model,
                available_models=[self.model],
                detail="ANTHROPIC_API_KEY is not configured in .env",
            )

        return ProviderHealth(
            name=self.name,
            configured=True,
            status="configured",
            model=self.model,
            available_models=[self.model],
            detail="Anthropic API key is configured and ready for requests.",
        )

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Executes a real Claude message completion request.
        """
        if not self._is_configured():
            raise LLMConfigurationError(
                "Anthropic API key is not configured. Add ANTHROPIC_API_KEY to your .env file.",
                provider=self.name,
            )

        # Convert messages to Anthropic schema (system prompt passed via top-level 'system' param)
        anthropic_messages: List[Dict[str, str]] = []
        for m in messages:
            role = m["role"]
            if role == "system":
                # If a system message is in history, append its content to the system prompt
                system_prompt = f"{system_prompt}\n{m['content']}" if system_prompt else m["content"]
            else:
                anthropic_messages.append({"role": role, "content": m["content"]})

        # Ensure there is at least one message for Anthropic
        if not anthropic_messages:
            anthropic_messages.append({"role": "user", "content": "Hello"})

        try:
            client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                timeout=float(self.timeout),
            )

            kwargs = {
                "model": self.model,
                "max_tokens": 2048,
                "messages": anthropic_messages,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await client.messages.create(**kwargs)

            # Extract text from content blocks
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            usage_info = {
                "input_tokens": getattr(response.usage, "input_tokens", None),
                "output_tokens": getattr(response.usage, "output_tokens", None),
            }

            return LLMResponse(
                text=response_text,
                provider=self.name,
                model=self.model,
                usage=usage_info,
            )
        except anthropic.AuthenticationError as e:
            logger.warning("Anthropic authentication failed (invalid API key).")
            raise LLMAuthenticationError(
                "Anthropic authentication failed. Verify ANTHROPIC_API_KEY in .env.",
                provider=self.name,
            )
        except anthropic.RateLimitError:
            logger.warning("Anthropic rate limit reached.")
            raise LLMProviderError(
                "Anthropic rate limit exceeded. Please wait a moment before trying again.",
                provider=self.name,
            )
        except anthropic.APITimeoutError:
            logger.warning("Anthropic request timed out.")
            raise LLMTimeoutError(
                f"Anthropic request timed out after {self.timeout}s.",
                provider=self.name,
            )
        except anthropic.APIConnectionError:
            logger.warning("Anthropic API connection failure.")
            raise LLMConnectionError(
                "Could not connect to Anthropic API servers. Check your internet connection.",
                provider=self.name,
            )
        except anthropic.APIStatusError as e:
            logger.warning(f"Anthropic API status error: {e.status_code}")
            raise LLMProviderError(
                f"Anthropic returned error (HTTP {e.status_code}): {e.message}",
                provider=self.name,
            )
        except Exception as e:
            logger.error(f"Unexpected Anthropic generation error: {type(e).__name__}", exc_info=False)
            raise LLMProviderError(
                f"Anthropic request failed: {type(e).__name__}",
                provider=self.name,
            )
