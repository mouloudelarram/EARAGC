"""
Tests for the health endpoint.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Root endpoint should return API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Enterprise Architecture RAG Copilot"
    assert "version" in data
    assert "docs" in data


def test_health_check_returns_ok():
    """Health check should return status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_check_has_required_fields():
    """Health response must contain all required fields."""
    response = client.get("/health")
    data = response.json()
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data
    assert "environment" in data


def test_health_check_services_status():
    """API service should be reported as ok."""
    response = client.get("/health")
    data = response.json()
    assert data["services"]["api"]["status"] == "ok"


def test_health_check_environment_info():
    """Environment section should include key config values."""
    response = client.get("/health")
    data = response.json()
    env = data["environment"]
    assert "ollama_model" in env
    assert "embedding_model" in env
    assert "chunk_size" in env

