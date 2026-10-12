from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Health check response model confirming the API process is running.
    """
    status: str = Field(default="healthy", description="Status of the API server process")
    service: str = Field(default="lenny-growth-assistant-api", description="Service identifier name")
