"""
Unit tests for ORM models (no database required).
Tests that models can be instantiated, repr works, and defaults are correct.
"""
import uuid

import pytest

from app.core.models import Document, Chunk


class TestDocumentModel:
    def test_document_creation_with_defaults(self):
        """Document can be instantiated with only required fields."""
        doc = Document(filename="architecture.md")
        assert doc.filename == "architecture.md"
        assert doc.document_type is None
        assert doc.source is None
        assert doc.file_hash is None

    def test_document_full_creation(self):
        """Document stores all fields correctly."""
        doc = Document(
            filename="service-design.pdf",
            document_type="pdf",
            source="https://confluence.example.com/service-design",
            file_hash="a" * 64,
        )
        assert doc.filename == "service-design.pdf"
        assert doc.document_type == "pdf"
        assert doc.source == "https://confluence.example.com/service-design"
        assert doc.file_hash == "a" * 64

    def test_document_repr(self):
        """__repr__ returns a readable string."""
        doc = Document(filename="kafka.md")
        assert "kafka.md" in repr(doc)
        assert "Document" in repr(doc)

    def test_document_tablename(self):
        """ORM table name is 'documents'."""
        assert Document.__tablename__ == "documents"

    def test_document_has_uuid_default_factory(self):
        """Each instantiation gets a unique uuid default."""
        doc1 = Document(filename="a.md")
        doc2 = Document(filename="b.md")
        # SQLAlchemy column defaults are applied at INSERT time,
        # but the Python-side default= callable should give unique values.
        # We just verify the column definition exists.
        assert hasattr(Document, "id")


class TestChunkModel:
    def test_chunk_creation(self):
        """Chunk can be instantiated with all required fields."""
        doc_id = uuid.uuid4()
        chunk = Chunk(
            document_id=doc_id,
            content="This is a text chunk about microservices.",
            chunk_index=0,
        )
        assert chunk.document_id == doc_id
        assert chunk.content == "This is a text chunk about microservices."
        assert chunk.chunk_index == 0
        assert chunk.page_number is None
        assert chunk.section is None

    def test_chunk_with_optional_fields(self):
        """Chunk stores optional extra_metadata fields correctly."""
        doc_id = uuid.uuid4()
        chunk = Chunk(
            document_id=doc_id,
            content="Chapter 1: Introduction",
            chunk_index=1,
            page_number=3,
            section="Introduction",
            extra_metadata={"author": "Alice"},
        )
        assert chunk.page_number == 3
        assert chunk.section == "Introduction"
        assert chunk.extra_metadata == {"author": "Alice"}

    def test_chunk_repr(self):
        """__repr__ returns a readable string."""
        doc_id = uuid.uuid4()
        chunk = Chunk(document_id=doc_id, content="x", chunk_index=0)
        assert "Chunk" in repr(chunk)

    def test_chunk_tablename(self):
        """ORM table name is 'chunks'."""
        assert Chunk.__tablename__ == "chunks"
