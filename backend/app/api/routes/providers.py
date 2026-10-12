from fastapi import APIRouter
from app.core.llm import get_all_providers_status
from app.schemas.provider import ProviderStatusResponse

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get(
    "/status",
    response_model=ProviderStatusResponse,
    summary="Get AI Providers Health & Configuration Status",
    description=(
        "Returns the connectivity, configuration readiness, and installed models "
        "across all supported LLM providers (Ollama, Anthropic, OpenAI) without exposing secrets."
    ),
)
async def get_providers_status() -> ProviderStatusResponse:
    """
    Checks provider availability safely without raising unhandled errors if a service is offline.
    """
    status_data = await get_all_providers_status()
    return ProviderStatusResponse(**status_data)
