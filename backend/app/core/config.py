import re
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import quote_plus
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root directory of the repository (3 levels up from app/core)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables or defaults.
    """
    model_config = SettingsConfigDict(
        env_file=(
            _PROJECT_ROOT / ".env",
            _BACKEND_ROOT / ".env",
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application info
    APP_NAME: str = "The Lenny Growth Assistant API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Server binding
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS Allowed Origins
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database Configuration (PostgreSQL + pgvector - Step 04)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "lenny_growth_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Model Provider selection & configuration (Step 06)
    DEFAULT_MODEL_PROVIDER: str = "ollama"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_REQUEST_TIMEOUT: int = 240
    OLLAMA_TIMEOUT: int = 240

    # Embeddings & RAG Configuration (Step 07)
    EMBEDDING_PROVIDER: str = "ollama"  # "openai" or "ollama"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSION: int = 768
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    RAG_TOP_K_CHUNKS: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.50
    TRANSCRIPT_DATA_DIR: str = "./data/raw"

    # Limits & Validation
    MAX_MESSAGE_LENGTH: int = 4000

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def async_database_url(self) -> str:
        """
        Constructs the async database URL using asyncpg for FastAPI runtime.
        """
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif self.DATABASE_URL.startswith("sqlite://"):
                return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
            return self.DATABASE_URL
        password = quote_plus(self.POSTGRES_PASSWORD) if self.POSTGRES_PASSWORD else ""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def sync_database_url(self) -> str:
        """
        Constructs the sync database URL using psycopg2 for Alembic migrations.
        """
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            elif self.DATABASE_URL.startswith("sqlite+aiosqlite://"):
                return self.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://", 1)
            return self.DATABASE_URL
        password = quote_plus(self.POSTGRES_PASSWORD) if self.POSTGRES_PASSWORD else ""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_safe_database_url(self) -> str:
        """
        Returns a sanitized database URL with password masked for safe logging.
        """
        try:
            from sqlalchemy.engine import make_url
            url = make_url(self.async_database_url)
            return url.render_as_string(hide_password=True)
        except Exception:
            return re.sub(r":([^:@]+)@", ":****@", self.async_database_url)


# Global settings instance
settings = Settings()
