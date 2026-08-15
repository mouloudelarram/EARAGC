"""
Document repository — CRUD operations for the `documents` table.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    """
    All database interactions for Document entities.
    Methods receive a SQLAlchemy Session (injected by FastAPI dependency).
    """

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def create(
        db: Session,
        *,
        filename: str,
        document_type: Optional[str] = None,
        source: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Document:
        """Persist a new document record and return it."""
        doc = Document(
            filename=filename,
            document_type=document_type,
            source=source,
            file_hash=file_hash,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    # ── Read ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(db: Session, doc_id: uuid.UUID) -> Optional[Document]:
        """Return a document by its primary key, or None if not found."""
        return db.get(Document, doc_id)

    @staticmethod
    def get_by_hash(db: Session, file_hash: str) -> Optional[Document]:
        """
        Return a document by its SHA-256 hash.
        Used to prevent re-ingestion of identical files.
        """
        return (
            db.query(Document)
            .filter(Document.file_hash == file_hash)
            .first()
        )

    @staticmethod
    def list_all(db: Session) -> list[Document]:
        """Return all documents ordered by creation date (newest first)."""
        return (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )

    # ── Delete ────────────────────────────────────────────────────────────────

    @staticmethod
    def delete(db: Session, doc_id: uuid.UUID) -> bool:
        """
        Delete a document (and its chunks via CASCADE).
        Returns True if the document existed, False otherwise.
        """
        doc = db.get(Document, doc_id)
        if doc is None:
            return False
        db.delete(doc)
        db.commit()
        return True

