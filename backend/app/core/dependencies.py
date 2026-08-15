"""
FastAPI dependency injection helpers.
Re-exports and extends core database dependencies.
"""
from typing import Generator

from sqlalchemy.orm import Session

from app.core.database import get_db  # noqa: F401 — re-export for convenience

__all__ = ["get_db"]

