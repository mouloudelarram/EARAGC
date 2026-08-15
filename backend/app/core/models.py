"""
SQLAlchemy ORM models — Document and Chunk.
Centralised here (app/core/) to avoid package-resolution issues.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base  # Base is already loaded before this module

# ── pgvector (optional) ───────────────────────────────────────────────────────
try:
    from pgvector.sqlalchemy import Vector as _Vector  # noqa: N811

    _VECTOR_AVAILABLE = True
except Exception:  # graceful fallback — pgvector may not be installed / compatible
    _Vector = None  # type: ignore[assignment,misc]
    _VECTOR_AVAILABLE = False


# ─── Document ─────────────────────────────────────────────────────────────────

class Document(Base):
    """Stores metadata for every uploaded / ingested document."""

    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique document identifier (UUID v4)",
    )
    filename = Column(String(255), nullable=False, comment="Original filename")
    document_type = Column(
        String(50),
        nullable=True,
        comment="File type: pdf | md | yaml | json | tf | txt",
    )
    source = Column(Text, nullable=True, comment="Original URL")
    file_hash = Column(
        String(64),
        unique=True,
        nullable=True,
        index=True,
        comment="SHA-256 hex digest — used for deduplication",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename!r}>"


# ─── Chunk ────────────────────────────────────────────────────────────────────

class Chunk(Base):
    """
    One text chunk produced by the chunking pipeline.
    Stores raw content, optional metadata, and its dense vector embedding.
    """

    __tablename__ = "chunks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique chunk identifier (UUID v4)",
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent document FK",
    )
    content = Column(Text, nullable=False, comment="Raw chunk text")
    chunk_index = Column(
        Integer,
        nullable=False,
        comment="0-based position of the chunk within the document",
    )
    page_number = Column(Integer, nullable=True, comment="Source page number (PDFs only)")
    section = Column(String(512), nullable=True, comment="Section heading")
    extra_metadata = Column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Arbitrary key/value pairs",
    )
    embedding = Column(
        _Vector(384) if _VECTOR_AVAILABLE else Text,
        nullable=True,
        comment="Dense embedding (pgvector) or placeholder",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk id={self.id} doc={self.document_id} idx={self.chunk_index}>"
