from typing import List, Optional, Dict
import openai
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
    "your_openai_api_key_here",
    "placeholder",
    "none",
}


class OpenAIProvider(BaseLLMProvider):
    """
    Cloud LLM provider utilizing OpenAI's Chat Completions API.
    """
    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout or settings.LLM_REQUEST_TIMEOUT

    def _is_configured() -> bool:
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
                detail="OPENAI_API_KEY is not configured in .env",
            )

        return ProviderHealth(
            name=self.name,
            configured=True,
            status="configured",
            model=self.model,
            available_models=[self.model],
            detail="OpenAI API key is configured and ready for requests.",
        )

    def _is_configured(self) -> bool:
        if not self.api_key:
            return False
        clean = self.api_key.strip().lower()
        return clean not in PLACEHOLDER_KEYS and not clean.startswith("your_")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Executes a real OpenAI chat completion request.
        """
        if not self._is_configured():
            raise LLMConfigurationError(
                "OpenAI API key is not configured. Add OPENAI_API_KEY to your .env file.",
                provider=self.name,
            )

        formatted_messages: List[Dict[str, str]] = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted_messages.append({"role": m["role"], "content": m["content"]})

        try:
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                timeout=float(self.timeout),
            )

            response = await client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
            )

            choice = response.choices[0]
            text = choice.message.content or ""

            usage_info = None
            if response.usage:
                usage_info = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                text=text,
                provider=self.name,
                model=self.model,
                usage=usage_info,
            )
        except openai.AuthenticationError:
            logger.warning("OpenAI authentication failed (invalid API key).")
            raise LLMAuthenticationError(
                "OpenAI authentication failed. Verify OPENAI_API_KEY in .env.",
                provider=self.name,
            )
        except openai.RateLimitError:
            logger.warning("OpenAI rate limit reached.")
            raise LLMProviderError(
                "OpenAI rate limit exceeded. Please wait a moment before trying again.",
                provider=self.name,
            )
        except openai.APITimeoutError:
            logger.warning("OpenAI request timed out.")
            raise LLMTimeoutError(
                f"OpenAI request timed out after {self.timeout}s.",
                provider=self.name,
            )
        except openai.APIConnectionError:
            logger.warning("OpenAI API connection failure.")
            raise LLMConnectionError(
                "Could not connect to OpenAI API servers. Check your internet connection.",
                provider=self.name,
            )
        except openai.APIStatusError as e:
            logger.warning(f"OpenAI API status error: {e.status_code}")
            raise LLMProviderError(
                f"OpenAI returned error (HTTP {e.status_code}): {e.message}",
                provider=self.name,
            )
        except Exception as e:
            logger.error(f"Unexpected OpenAI generation error: {type(e).__name__}", exc_info=False)
            raise LLMProviderError(
                f"OpenAI request failed: {type(e).__name__}",
                provider=self.name,
            )
