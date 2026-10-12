from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """
    Incoming Chat Request Schema.
    """
    message: str = Field(
        ...,
        description="The user's query or prompt. Must be non-empty.",
        max_length=4000,
        examples=["How can a startup improve customer retention?"]
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier. If omitted, a new session ID will be generated.",
        examples=["session-123e4567-e89b-12d3-a456-426614174000"]
    )
    provider: Optional[str] = Field(
        default=None,
        description="Optional model provider override (e.g. 'ollama', 'anthropic', 'openai').",
        examples=["ollama"]
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message cannot be empty or whitespace only.")
        return trimmed


class ArtifactMetadata(BaseModel):
    """
    Metadata representation of an artifact returned with a chat response.
    """
    id: str = Field(..., description="Unique artifact identifier")
    title: str = Field(..., description="Artifact title")
    type: str = Field(..., description="Artifact type ('markdown', 'html', 'essay')")
    content: Optional[str] = Field(default=None, description="Artifact content preview or body")
    session_id: Optional[str] = Field(default=None, description="Associated session ID")
    message_id: Optional[str] = Field(default=None, description="Associated assistant message ID")
    version: Optional[int] = Field(default=1, description="Version number")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    is_demonstration: bool = Field(default=False, description="Whether this is a demo artifact")


class ChatResponse(BaseModel):
    """
    Chat Response Schema.
    Accurately indicates processing status without fabricating AI answers or citations.
    """
    status: str = Field(
        ...,
        description="Status of the chat processing (e.g. 'not_configured', 'success', 'error').",
        examples=["not_configured"]
    )
    session_id: str = Field(
        ...,
        description="Session identifier associated with this conversation thread.",
        examples=["session-123e4567-e89b-12d3-a456-426614174000"]
    )
    message: str = Field(
        ...,
        description="Response information or status explanation.",
        examples=["AI integration and transcript retrieval are planned for Steps 05–07."]
    )
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of verified transcript source citations. Empty when retrieval is not configured."
    )
    provider: str = Field(
        ...,
        description="Target model provider specified or default.",
        examples=["ollama"]
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 formatted timestamp of the response.",
        examples=["2026-10-10T16:35:00Z"]
    )
    artifact: Optional[ArtifactMetadata] = Field(
        default=None,
        description="Generated artifact metadata if created for this turn."
    )
    artifact_id: Optional[str] = Field(
        default=None,
        description="Unique ID of the generated artifact if created for this turn."
    )
