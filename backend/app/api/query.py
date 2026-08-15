"""
Query endpoint — BM25 retrieval + Ollama generation.
POST /query
"""
import logging
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.models import Chunk, Document

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas (aligned with frontend api.ts) ────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None


class Source(BaseModel):
    id: int
    document: str
    section: Optional[str] = None
    page: Optional[int] = None
    content: Optional[str] = None


class QueryMetadata(BaseModel):
    retrieval_method: str
    candidates: int
    reranked: int
    retrieval_latency_ms: float
    generation_latency_ms: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    metadata: QueryMetadata


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bm25_retrieve(question: str, db: Session, top_k: int) -> list[tuple]:
    """Retrieve top-k chunks using BM25Okapi over all indexed chunks."""
    chunks: list[Chunk] = db.query(Chunk).all()
    if not chunks:
        return []

    tokenized = [c.content.lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(question.lower().split())

    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


def _call_ollama(question: str, context: str) -> str:
    """Call Ollama /api/generate and return the answer text."""
    prompt = (
        "You are an enterprise software architecture assistant.\n"
        "Use ONLY the following document extracts to answer the question.\n"
        "If the context does not contain enough information, say so clearly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\nAnswer:"
    )
    try:
        ollama_base_url = settings.ollama_base_url_resolved
        model_name = settings.OLLAMA_MODEL

        try:
            with httpx.Client(timeout=10.0) as client:
                tags = client.get(f"{ollama_base_url}/api/tags")
                tags.raise_for_status()
                available = [
                    model.get("name") for model in tags.json().get("models", []) if model.get("name")
                ]
                preferred = [settings.OLLAMA_MODEL, "llama3.1:latest", "phi3:latest", *available]
                model_name = next((name for name in preferred if name in available), available[0] if available else model_name)
        except Exception:
            pass

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{ollama_base_url}/api/generate",
                json={"model": model_name, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json().get("response", "No response from model.")
    except httpx.TimeoutException:
        return "The model took too long to respond. Try a shorter question or check Ollama."
    except Exception as exc:  # noqa: BLE001
        logger.error("Ollama call failed: %s", exc)
        return (
            f"Could not reach the language model: {exc}. "
            "Make sure Ollama is running and the model is pulled "
            f"(`ollama pull {settings.OLLAMA_MODEL}`)."
        )


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("", response_model=QueryResponse, summary="RAG query")
def query(req: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """
    1. BM25 retrieval over all indexed chunks.
    2. Build context string from top-k results.
    3. Generate answer via Ollama.
    """
    top_k = req.top_k or settings.RETRIEVAL_TOP_K

    # ── Retrieval ─────────────────────────────────────────────────────────────
    t0 = time.monotonic()
    ranked = _bm25_retrieve(req.question, db, top_k)
    retrieval_ms = round((time.monotonic() - t0) * 1000, 1)

    # ── Build context & sources ───────────────────────────────────────────────
    context_parts: list[str] = []
    sources: list[Source] = []

    for idx, (chunk, _score) in enumerate(ranked, start=1):
        doc: Optional[Document] = db.get(Document, chunk.document_id)
        filename = doc.filename if doc else "unknown"
        context_parts.append(f"[{idx}] {filename}\n{chunk.content[:800]}")
        sources.append(Source(
            id=idx,
            document=filename,
            section=chunk.section,
            page=chunk.page_number,
            content=chunk.content[:300],
        ))

    # ── Generation ────────────────────────────────────────────────────────────
    t1 = time.monotonic()
    if not ranked:
        answer = (
            "No documents are indexed yet. "
            "Please upload your architecture documents in the **Documents** tab first."
        )
    else:
        context = "\n\n".join(context_parts)
        answer = _call_ollama(req.question, context)
    generation_ms = round((time.monotonic() - t1) * 1000, 1)

    return QueryResponse(
        answer=answer,
        sources=sources,
        metadata=QueryMetadata(
            retrieval_method="bm25",
            candidates=len(ranked),
            reranked=len(ranked),
            retrieval_latency_ms=retrieval_ms,
            generation_latency_ms=generation_ms,
        ),
    )

