"""
Pydantic schemas for query (RAG pipeline) request/response.
Used by the POST /query endpoint (Phase 9).
"""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ── Source citation ───────────────────────────────────────────────────────────

class Source(BaseModel):
    """A document chunk cited in the answer."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    content: str = Field(description="Chunk text excerpt shown to the user")
    score: float = Field(description="Relevance score after reranking (0–1)")
    page_number: Optional[int] = None
    section: Optional[str] = None


# ── Retrieval metadata ────────────────────────────────────────────────────────

class RetrievalMetadata(BaseModel):
    """Performance and pipeline metadata attached to every query response."""

    retrieval_strategy: str = Field(
        default="hybrid+reranker",
        description="vector | bm25 | hybrid | hybrid+reranker",
    )
    candidates_retrieved: int = Field(
        description="Number of chunks retrieved before reranking"
    )
    chunks_used: int = Field(
        description="Number of chunks passed to the LLM after reranking"
    )
    latency_ms: float = Field(description="End-to-end latency in milliseconds")
    model: str = Field(description="Ollama model used for generation")


# ── Query request ─────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Payload sent by the client for a RAG query."""

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Natural language question",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Override RETRIEVAL_TOP_K for this request",
    )
    rerank_top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Override RERANK_TOP_K for this request",
    )
    strategy: Optional[str] = Field(
        default=None,
        description="Force a retrieval strategy: vector | bm25 | hybrid | hybrid+reranker",
    )


# ── Query response ────────────────────────────────────────────────────────────

class QueryResponse(BaseModel):
    """Full response returned by POST /query."""

    answer: str = Field(description="LLM-generated answer grounded in the sources")
    sources: list[Source] = Field(
        default_factory=list,
        description="Cited chunks used to generate the answer",
    )
    metadata: RetrievalMetadata

