from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ProviderInfo(BaseModel):
    """Status details for a single model provider."""
    name: str
    configured: bool
    status: str = Field(
        description="One of: 'connected', 'configured', 'unavailable', 'authentication_failed', 'model_not_found'"
    )
    model: str
    available_models: List[str] = Field(default_factory=list)
    detail: Optional[str] = None


class ProviderStatusResponse(BaseModel):
    """Aggregate status for all AI model providers."""
    default_provider: str
    providers: Dict[str, ProviderInfo]
