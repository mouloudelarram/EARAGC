"""
Enterprise Architecture RAG Copilot — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.core.config import settings
from app.core.logging import setup_logging

# Pre-load ORM models so Base.metadata is populated before init_db()
import app.core.models  # noqa: F401

# Initialize structured logging
setup_logging()

logger = logging.getLogger(__name__)


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info(
        "Starting Enterprise Architecture RAG Copilot",
        extra={
            "ollama_model": settings.OLLAMA_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
        },
    )
    try:
        from app.core.database import init_db
        init_db()
        logger.info("Database initialisation complete")
    except Exception as exc:  # noqa: BLE001
        logger.error("Database initialisation failed: %s", exc)

    yield  # application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down Enterprise Architecture RAG Copilot")


# ─── Application ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Enterprise Architecture RAG Copilot",
    description=(
        "AI assistant for enterprise software architecture. "
        "Upload your technical docs and ask architecture questions."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(documents_router, prefix="/documents", tags=["Documents"])

# ─── Root ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint — returns API metadata."""
    return {
        "name": "Enterprise Architecture RAG Copilot",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
