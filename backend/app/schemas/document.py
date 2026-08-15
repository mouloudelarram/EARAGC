"""
Pydantic schemas for Document create/read operations.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Request ───────────────────────────────────────────────────────────────────

class DocumentCreate(BaseModel):
    """Payload sent by the client when uploading a document."""
    filename: str
    document_type: Optional[str] = None
    source: Optional[str] = None
    file_hash: Optional[str] = None


# ── Response ──────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    """Full document representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    document_type: Optional[str] = None
    source: Optional[str] = None
    file_hash: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

