from typing import Optional
from pydantic import BaseModel, Field


class ArtifactResponse(BaseModel):
    """
    Response schema representing an individual persisted artifact.
    """
    id: str = Field(..., description="Unique artifact identifier")
    session_id: str = Field(..., description="Associated session identifier")
    message_id: Optional[str] = Field(default=None, description="Originating message identifier")
    type: str = Field(..., description="Artifact type ('markdown', 'html', 'essay')")
    title: str = Field(..., description="Artifact title")
    content: str = Field(..., description="Artifact payload content")
    version: int = Field(default=1, description="Version index")
    is_demonstration: bool = Field(default=False, description="Whether this is a demo artifact")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
