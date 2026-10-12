from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    """
    Request body for explicitly creating a new chat session.
    """
    title: Optional[str] = Field(default="New Chat", max_length=255, description="Initial session title")
    provider: Optional[str] = Field(default=None, description="Model provider for this session. Defaults to configured DEFAULT_MODEL_PROVIDER.")


class SessionResponse(BaseModel):
    """
    Response schema representing a conversation session.
    """
    id: str = Field(..., description="Unique session identifier")
    title: str = Field(..., description="Session title")
    model_provider: str = Field(..., description="Model provider configured for this session")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last updated timestamp")
    message_count: int = Field(default=0, description="Total messages in this session")


class MessageResponse(BaseModel):
    """
    Response schema representing an individual message.
    """
    id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session identifier")
    role: str = Field(..., description="Message author role: 'user', 'assistant', 'system'")
    content: str = Field(..., description="Message text content")
    provider: Optional[str] = Field(default=None, description="Model provider used")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="List of source citations")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    artifact_id: Optional[str] = Field(default=None, description="Associated artifact identifier")
    artifact_title: Optional[str] = Field(default=None, description="Associated artifact title")
    artifact_type: Optional[str] = Field(default=None, description="Associated artifact type ('markdown', 'html', 'essay')")
