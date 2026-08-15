"""
Documents API — upload, list, and delete ingested documents.
"""
import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.models import Chunk, Document
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository, ChunkCreate

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Upload directory ─────────────────────────────────────────────────────────

UPLOAD_DIR = Path("/app/data/documents")
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt", ".json", ".yaml", ".yml", ".tf"}

EXTENSION_TO_TYPE: dict[str, str] = {
    ".pdf": "pdf",
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".tf": "terraform",
}


# ─── Response schema ──────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    document_type: Optional[str] = None
    source: Optional[str] = None
    file_hash: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_text(content: bytes, extension: str) -> str:
    """Extract plain text from file bytes based on file extension."""
    if extension == ".pdf":
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as exc:
            logger.warning("PDF extraction failed: %s", exc)
            return content.decode("utf-8", errors="replace")
    # All other formats: decode as UTF-8 text
    return content.decode("utf-8", errors="replace")


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c for c in chunks if c.strip()]


def _doc_to_response(doc: Document, db: Session) -> DocumentResponse:
    chunk_count = db.query(Chunk).filter(Chunk.document_id == doc.id).count()
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        document_type=doc.document_type,
        source=doc.source,
        file_hash=doc.file_hash,
        chunk_count=chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a document",
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """
    Upload a document file (.pdf, .md, .txt, .json, .yaml, .yml, .tf).

    - Validates file type and size.
    - Deduplicates via SHA-256 hash.
    - Chunks the text and stores it in the database.
    """
    # ── Validate extension ────────────────────────────────────────────────────
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # ── Read content ──────────────────────────────────────────────────────────
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB} MB",
        )

    # ── Deduplication ─────────────────────────────────────────────────────────
    file_hash = _sha256(content)
    existing = DocumentRepository.get_by_hash(db, file_hash)
    if existing:
        return _doc_to_response(existing, db)

    # ── Persist document record ───────────────────────────────────────────────
    doc_type = EXTENSION_TO_TYPE.get(ext, "unknown")
    doc = DocumentRepository.create(
        db,
        filename=filename,
        document_type=doc_type,
        file_hash=file_hash,
    )

    # ── Save raw file to disk ─────────────────────────────────────────────────
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        dest = UPLOAD_DIR / f"{doc.id}{ext}"
        dest.write_bytes(content)
    except OSError as exc:
        logger.warning("Could not save file to disk: %s", exc)

    # ── Extract text & chunk ──────────────────────────────────────────────────
    try:
        text = _extract_text(content, ext)
        raw_chunks = _chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        chunk_creates = [
            ChunkCreate(
                document_id=doc.id,
                content=chunk,
                chunk_index=i,
            )
            for i, chunk in enumerate(raw_chunks)
        ]
        if chunk_creates:
            ChunkRepository.create_many(db, chunk_creates)
            logger.info(
                "Indexed %d chunks for document %s (%s)",
                len(chunk_creates),
                filename,
                doc.id,
            )
    except Exception as exc:  # noqa: BLE001
        logger.error("Chunking failed for %s: %s", filename, exc)

    return _doc_to_response(doc, db)


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List all indexed documents",
)
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    """Return all documents ordered by creation date (newest first)."""
    docs = DocumentRepository.list_all(db)
    return [_doc_to_response(d, db) for d in docs]


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its chunks",
)
def delete_document(doc_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a document and all its associated chunks (CASCADE)."""
    deleted = DocumentRepository.delete(db, doc_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found",
        )


