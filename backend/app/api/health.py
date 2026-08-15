"""
Health check endpoint.
Returns service status and connectivity checks.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


class ServiceStatus(BaseModel):
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: dict
    services: dict[str, ServiceStatus]


def _check_database() -> ServiceStatus:
    """Attempt a lightweight SELECT 1 against PostgreSQL."""
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return ServiceStatus(status="ok")
        finally:
            db.close()
    except OperationalError as exc:
        logger.warning("Database health check failed: %s", exc)
        return ServiceStatus(status="error", detail="Cannot reach PostgreSQL")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database health check unexpected error: %s", exc)
        return ServiceStatus(status="error", detail=str(exc))


@router.get("", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """
    Returns the health status of the API and its dependent services.

    - **status**: overall status (ok / degraded / error)
    - **services**: per-service status
    - **environment**: non-sensitive configuration info
    """
    services: dict[str, ServiceStatus] = {
        "api": ServiceStatus(status="ok"),
        "database": _check_database(),
    }

    overall = "ok"
    if any(s.status != "ok" for s in services.values()):
        overall = "degraded"

    return HealthResponse(
        status=overall,
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        environment={
            "ollama_model": settings.OLLAMA_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "retrieval_top_k": settings.RETRIEVAL_TOP_K,
        },
        services=services,
    )


