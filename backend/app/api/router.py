from fastapi import APIRouter
from app.api.routes import health, chat, sessions, providers, artifacts

api_router = APIRouter()

# Root health check endpoints (accessible at /health and /health/db)
api_router.include_router(health.router)

# API routes grouped under /api
api_router.include_router(chat.router, prefix="/api")
api_router.include_router(sessions.router, prefix="/api")
api_router.include_router(providers.router, prefix="/api")
api_router.include_router(artifacts.router, prefix="/api")

