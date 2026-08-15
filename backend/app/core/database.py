"""
Database engine, session factory, and initialisation helpers.
"""
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError

from app.core.config import settings

logger = logging.getLogger(__name__)


# ─── Declarative base ─────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for all ORM models."""
    pass


# ─── Engine & Session ─────────────────────────────────────────────────────────

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # reconnect on stale connections
    pool_size=5,
    max_overflow=10,
    echo=False,                  # set True for SQL debug logs
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ─── Dependency injection helper ──────────────────────────────────────────────

def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy session.
    Automatically closes the session after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Initialisation ───────────────────────────────────────────────────────────

def init_db() -> None:
    """
    - Activates the pgvector extension in PostgreSQL.
    - Creates all tables defined in the ORM models (CREATE TABLE IF NOT EXISTS).

    Called once on application startup.
    """
    # Import models so their metadata is registered with Base before create_all()
    from app.core.models import Document, Chunk  # noqa: F401

    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("pgvector extension ensured")
    except OperationalError as exc:
        logger.warning("Could not activate pgvector extension: %s", exc)

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created / verified")
    except OperationalError as exc:
        logger.error("Failed to create database tables: %s", exc)
        raise

