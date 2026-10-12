from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.database.connection import check_db_connection

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API Process Health Check",
    description="Confirms that the FastAPI server process is running and accepting HTTP requests."
)
async def check_health() -> HealthResponse:
    """
    Returns the basic health status of the API service process.
    Note: Does not falsely claim database or external LLMs are connected.
    """
    return HealthResponse(
        status="healthy",
        service="lenny-growth-assistant-api"
    )


@router.get(
    "/health/db",
    summary="Database Connectivity Check",
    description="Checks if the PostgreSQL database is reachable and accepting queries."
)
async def check_database_health() -> dict:
    """
    Performs a live database connection check.
    Returns status and dialect without exposing credentials.
    """
    return await check_db_connection()
