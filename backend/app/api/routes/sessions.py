from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.connection import get_db
from app.database.session_service import SessionService
from app.schemas.session import SessionCreateRequest, SessionResponse, MessageResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get(
    "",
    response_model=List[SessionResponse],
    summary="List Conversation Sessions",
    description="Returns a list of all active chat sessions ordered by last updated date."
)
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[SessionResponse]:
    """
    Lists conversation sessions.
    """
    sessions = await SessionService.list_sessions(db, limit=limit, offset=offset)
    return [SessionResponse(**s.to_dict()) for s in sessions]


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Chat Session",
    description="Initializes a clean, independent conversation session in the database."
)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """
    Creates a new conversation session.
    """
    session = await SessionService.get_or_create_session(
        db,
        provider=request.provider or settings.DEFAULT_MODEL_PROVIDER,
        title=request.title or "New Chat"
    )
    return SessionResponse(**session.to_dict())


@router.get(
    "/{session_id}/messages",
    response_model=List[MessageResponse],
    summary="Get Session Messages",
    description="Retrieves the chronological message history for a specific conversation session."
)
async def get_session_messages(
    session_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[MessageResponse]:
    """
    Returns message history for an existing session.
    """
    session = await SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    messages = await SessionService.get_session_messages(db, session_id, limit=limit)
    return [MessageResponse(**m.to_dict()) for m in messages]


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session",
    description="Deletes a conversation session and all its associated messages."
)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a session.
    """
    deleted = await SessionService.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
