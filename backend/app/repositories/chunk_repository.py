"""
Chunk repository — CRUD operations for the `chunks` table.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.core.models import Chunk


@dataclass
class ChunkCreate:
    """Value object used to create multiple chunks in a single call."""
    document_id: uuid.UUID
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None


class ChunkRepository:
    """
    All database interactions for Chunk entities.
    """

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def create_many(db: Session, chunks: list[ChunkCreate]) -> list[Chunk]:
        """
        Bulk-insert a list of chunks in a single transaction.
        Returns the persisted Chunk objects with their generated IDs.
        """
        orm_chunks = [
            Chunk(
                document_id=c.document_id,
                content=c.content,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                section=c.section,
                metadata=c.metadata or {},
                embedding=c.embedding,
            )
            for c in chunks
        ]
        db.add_all(orm_chunks)
        db.commit()
        for chunk in orm_chunks:
            db.refresh(chunk)
        return orm_chunks

    # ── Read ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_document(db: Session, document_id: uuid.UUID) -> list[Chunk]:
        """Return all chunks for a document, ordered by chunk_index."""
        return (
            db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
            .all()
        )

    # ── Delete ────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_by_document(db: Session, document_id: uuid.UUID) -> int:
        """
        Delete all chunks belonging to a document.
        Returns the number of deleted rows.
        Note: normally handled by CASCADE, but useful for partial re-indexing.
        """
        deleted = (
            db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted

