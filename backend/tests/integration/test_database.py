"""
Integration tests for the database layer.
Requires a live PostgreSQL instance (run via docker compose).

These tests are skipped automatically when the database is unreachable.
Run them inside the container:
    docker compose exec backend pytest tests/integration/test_database.py -v
"""
from __future__ import annotations

import hashlib
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.database import Base, init_db
from app.core.models import Document, Chunk
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository, ChunkCreate


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _db_available() -> bool:
    """Return True if the test database is reachable."""
    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except OperationalError:
        return False


requires_db = pytest.mark.skipif(
    not _db_available(),
    reason="PostgreSQL not reachable — run inside docker compose",
)


@pytest.fixture(scope="module")
def db_engine():
    """Module-scoped engine pointing at the test database."""
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    # Ensure pgvector extension + tables exist
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """
    Function-scoped session with savepoint isolation.
    Every session.commit() inside the test creates a SAVEPOINT instead of a
    real commit, so the outer transaction.rollback() undoes everything after
    the test — no data leaks between tests or across runs.
    """
    connection = db_engine.connect()
    trans = connection.begin()
    # join_transaction_mode="create_savepoint" turns every session.commit()
    # into a SAVEPOINT / RELEASE SAVEPOINT, keeping the outer tx open.
    session = Session(connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    trans.rollback()
    connection.close()


# ─── Tests ────────────────────────────────────────────────────────────────────

@requires_db
class TestDatabaseConnection:
    def test_select_one(self, db_session):
        """Basic connectivity check."""
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_pgvector_extension(self, db_session):
        """pgvector extension must be installed."""
        result = db_session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()
        assert result is not None, "pgvector extension not found"


@requires_db
class TestDocumentRepository:
    def test_create_document(self, db_session):
        """Can create and retrieve a document."""
        doc = DocumentRepository.create(
            db_session,
            filename="test-arch.md",
            document_type="md",
            source="https://wiki.example.com/test-arch",
            file_hash=hashlib.sha256(b"test content").hexdigest(),
        )
        assert doc.id is not None
        assert doc.filename == "test-arch.md"
        assert doc.document_type == "md"

    def test_get_by_id(self, db_session):
        """Can look up a document by primary key."""
        doc = DocumentRepository.create(
            db_session,
            filename="lookup-test.pdf",
            file_hash=hashlib.sha256(b"lookup content").hexdigest(),
        )
        found = DocumentRepository.get_by_id(db_session, doc.id)
        assert found is not None
        assert found.id == doc.id

    def test_get_by_id_not_found(self, db_session):
        """Returns None for an unknown UUID."""
        result = DocumentRepository.get_by_id(db_session, uuid.uuid4())
        assert result is None

    def test_get_by_hash_deduplication(self, db_session):
        """get_by_hash returns existing document (deduplication logic)."""
        file_hash = hashlib.sha256(b"dedup-content").hexdigest()
        doc = DocumentRepository.create(
            db_session,
            filename="dedup.md",
            file_hash=file_hash,
        )
        found = DocumentRepository.get_by_hash(db_session, file_hash)
        assert found is not None
        assert found.id == doc.id

    def test_get_by_hash_not_found(self, db_session):
        """Returns None when no document matches the hash."""
        result = DocumentRepository.get_by_hash(db_session, "0" * 64)
        assert result is None

    def test_list_all(self, db_session):
        """list_all returns at least the documents created in this test."""
        DocumentRepository.create(
            db_session,
            filename="list-test-1.md",
            file_hash=hashlib.sha256(b"list1").hexdigest(),
        )
        DocumentRepository.create(
            db_session,
            filename="list-test-2.md",
            file_hash=hashlib.sha256(b"list2").hexdigest(),
        )
        docs = DocumentRepository.list_all(db_session)
        filenames = [d.filename for d in docs]
        assert "list-test-1.md" in filenames
        assert "list-test-2.md" in filenames

    def test_delete_document(self, db_session):
        """delete returns True and the document is gone afterwards."""
        doc = DocumentRepository.create(
            db_session,
            filename="to-delete.md",
            file_hash=hashlib.sha256(b"delete me").hexdigest(),
        )
        deleted = DocumentRepository.delete(db_session, doc.id)
        assert deleted is True
        assert DocumentRepository.get_by_id(db_session, doc.id) is None

    def test_delete_nonexistent(self, db_session):
        """delete returns False for an unknown UUID."""
        result = DocumentRepository.delete(db_session, uuid.uuid4())
        assert result is False


@requires_db
class TestChunkRepository:
    def _make_doc(self, db_session) -> Document:
        return DocumentRepository.create(
            db_session,
            filename="chunk-source.md",
            file_hash=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
        )

    def test_create_many(self, db_session):
        """create_many inserts all chunks and returns them with IDs."""
        doc = self._make_doc(db_session)
        chunks_in = [
            ChunkCreate(document_id=doc.id, content=f"Chunk {i}", chunk_index=i)
            for i in range(3)
        ]
        chunks_out = ChunkRepository.create_many(db_session, chunks_in)
        assert len(chunks_out) == 3
        for chunk in chunks_out:
            assert chunk.id is not None

    def test_get_by_document(self, db_session):
        """get_by_document returns chunks ordered by chunk_index."""
        doc = self._make_doc(db_session)
        chunks_in = [
            ChunkCreate(document_id=doc.id, content=f"Chunk {i}", chunk_index=i)
            for i in range(5)
        ]
        ChunkRepository.create_many(db_session, chunks_in)
        chunks = ChunkRepository.get_by_document(db_session, doc.id)
        assert len(chunks) == 5
        assert [c.chunk_index for c in chunks] == list(range(5))

    def test_cascade_delete_on_document_delete(self, db_session):
        """Deleting a document removes all its chunks (CASCADE)."""
        doc = self._make_doc(db_session)
        chunks_in = [
            ChunkCreate(document_id=doc.id, content="chunk", chunk_index=0)
        ]
        ChunkRepository.create_many(db_session, chunks_in)

        DocumentRepository.delete(db_session, doc.id)

        remaining = ChunkRepository.get_by_document(db_session, doc.id)
        assert remaining == []

    def test_delete_by_document(self, db_session):
        """delete_by_document returns count of deleted rows."""
        doc = self._make_doc(db_session)
        chunks_in = [
            ChunkCreate(document_id=doc.id, content=f"c{i}", chunk_index=i)
            for i in range(4)
        ]
        ChunkRepository.create_many(db_session, chunks_in)
        deleted_count = ChunkRepository.delete_by_document(db_session, doc.id)
        assert deleted_count == 4
        assert ChunkRepository.get_by_document(db_session, doc.id) == []

