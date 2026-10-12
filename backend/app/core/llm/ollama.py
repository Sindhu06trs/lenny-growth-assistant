import httpx
from typing import List, Optional, Dict
from app.core.config import settings
from app.core.logging_config import logger
from app.core.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    ProviderHealth,
    LLMConnectionError,
    LLMTimeoutError,
    LLMModelNotFoundError,
    LLMProviderError,
)


class OllamaProvider(BaseLLMProvider):
    """
    Local offline LLM provider communicating with Ollama REST API.
    """
    name = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or getattr(settings, "OLLAMA_TIMEOUT", settings.LLM_REQUEST_TIMEOUT)

    async def check_health(self) -> ProviderHealth:
        """
        Queries Ollama GET /api/tags to verify connectivity and installed models.
        """
        tags_url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(tags_url)
                if response.status_code != 200:
                    return ProviderHealth(
                        name=self.name,
                        configured=True,
                        status="unavailable",
                        model=self.model,
                        detail=f"Ollama returned HTTP {response.status_code}",
                    )
                data = response.json()
                raw_models = data.get("models", [])
                available_models = [m.get("name", "") for m in raw_models if m.get("name")]

                # Check if configured model is installed (match exact name or normalized tag)
                def _is_match(target: str, candidate: str) -> bool:
                    if target == candidate:
                        return True
                    if target == f"{candidate}:latest" or candidate == f"{target}:latest":
                        return True
                    if ":" not in target and candidate.startswith(f"{target}:"):
                        return True
                    return False

                model_installed = any(_is_match(self.model, m) for m in available_models)

                if model_installed:
                    return ProviderHealth(
                        name=self.name,
                        configured=True,
                        status="connected",
                        model=self.model,
                        available_models=available_models,
                        detail=f"Ollama active with {len(available_models)} model(s) installed.",
                    )
                else:
                    return ProviderHealth(
                        name=self.name,
                        configured=True,
                        status="model_not_found",
                        model=self.model,
                        available_models=available_models,
                        detail=(
                            f"Model '{self.model}' is not installed in Ollama. "
                            f"Run 'ollama run {self.model}' or 'ollama pull {self.model}' to install."
                        ),
                    )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            return ProviderHealth(
                name=self.name,
                configured=True,
                status="unavailable",
                model=self.model,
                available_models=[],
                detail=f"Ollama service is not reachable at {self.base_url}. Ensure Ollama is running.",
            )
        except httpx.TimeoutException:
            return ProviderHealth(
                name=self.name,
                configured=True,
                status="unavailable",
                model=self.model,
                available_models=[],
                detail="Connection to Ollama timed out.",
            )
        except Exception as e:
            logger.warning(f"Ollama health check unexpected error: {type(e).__name__}")
            return ProviderHealth(
                name=self.name,
                configured=True,
                status="unavailable",
                model=self.model,
                available_models=[],
                detail=f"Ollama health check failed: {type(e).__name__}",
            )

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Sends chat completion request to Ollama POST /api/chat.
        """
        chat_url = f"{self.base_url}/api/chat"

        # Prepare messages array
        formatted_messages: List[Dict[str, str]] = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(chat_url, json=payload)

                if response.status_code == 404:
                    raise LLMModelNotFoundError(
                        f"Model '{self.model}' not found in Ollama. Run 'ollama run {self.model}' to download it.",
                        provider=self.name,
                    )
                elif response.status_code != 200:
                    raise LLMProviderError(
                        f"Ollama returned HTTP error {response.status_code}",
                        provider=self.name,
                    )

                data = response.json()
                message_content = data.get("message", {}).get("content", "")
                if not message_content:
                    message_content = data.get("response", "")

                return LLMResponse(
                    text=message_content,
                    provider=self.name,
                    model=self.model,
                    usage={
                        "total_duration": data.get("total_duration"),
                        "eval_count": data.get("eval_count"),
                    },
                )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            logger.warning(f"Ollama connection error: {type(e).__name__}")
            raise LLMConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Verify that the Ollama process is running.",
                provider=self.name,
            )
        except httpx.TimeoutException:
            logger.warning("Ollama request timed out.")
            raise LLMTimeoutError(
                f"Ollama request timed out after {self.timeout}s.",
                provider=self.name,
            )
        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"Ollama generation failed: {type(e).__name__}", exc_info=False)
            raise LLMProviderError(
                f"Ollama error: {type(e).__name__}",
                provider=self.name,
            )
