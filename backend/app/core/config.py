"""
Application configuration — loaded from environment variables / .env file.
"""
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings, configurable via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://raguser:ragpass@postgres:5432/ragdb"

    # ── Ollama ────────────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # ── Embedding / Reranker ──────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"

    # ── Chunking ──────────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100

    # ── Retrieval ─────────────────────────────────────────────────────────────
    VECTOR_WEIGHT: float = 0.6
    BM25_WEIGHT: float = 0.4
    RETRIEVAL_TOP_K: int = 20
    RERANK_TOP_K: int = 5

    # ── Upload ────────────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ─── Computed Properties ─────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        """Max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Singleton settings instance
settings = Settings()

