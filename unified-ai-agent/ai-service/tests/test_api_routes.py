"""Unit and integration tests for FastAPI internal routes (Milestone 9.1)."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.config.settings import get_settings

client = TestClient(app)
INTERNAL_KEY = get_settings().ai_service_internal_key


def test_health_live():
    """Verify /health/live returns UP without external service dependency."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"


def test_health_ready():
    """Verify /health/ready evaluates core dependencies."""
    response = client.get("/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "components" in data
    assert "mysql" in data["components"]
    assert "vector_store" in data["components"]
    assert "embeddings" in data["components"]
    assert "llm" in data["components"]


def test_needs_detect_endpoint():
    """Verify direct multi-need detection endpoint."""
    headers = {
        "X-Internal-API-Key": INTERNAL_KEY,
        "X-Correlation-ID": "test-corr-1",
    }
    payload = {
        "text": "I lost my job and my two children need help with school fees."
    }
    response = client.post("/v1/needs/detect", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_needs"] >= 2
    cats = [n["category"] for n in data["needs"]]
    assert "employment" in cats
    assert "education" in cats
    assert "disclaimer" in data


def test_scheme_search_endpoint():
    """Verify direct semantic RAG search endpoint."""
    headers = {
        "X-Internal-API-Key": INTERNAL_KEY,
        "X-Correlation-ID": "test-corr-2",
    }
    payload = {
        "query": "Startup India Seed Fund eligibility criteria",
        "top_k": 2,
    }
    response = client.post("/v1/schemes/search", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert len(data["results"]) > 0
    assert "scheme" in data["results"][0]
    assert "content" in data["results"][0]


def test_scheme_discovery_endpoint():
    """Verify external government scheme discovery endpoint (M8 adapter)."""
    headers = {
        "X-Internal-API-Key": INTERNAL_KEY,
        "X-Correlation-ID": "test-corr-3",
    }
    payload = {
        "keyword": "seed fund",
        "state": "All India",
    }
    response = client.post("/v1/schemes/discover", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_schemes"] > 0
    assert data["verification_status"] in ("CONTRACT_VERIFIED", "SANDBOX_VERIFIED")
    assert len(data["schemes"]) > 0


def test_eligibility_evaluation_endpoint():
    """Verify deterministic eligibility evaluation endpoint."""
    headers = {
        "X-Internal-API-Key": INTERNAL_KEY,
        "X-Citizen-ID": "demo-user",
        "X-Correlation-ID": "test-corr-4",
    }
    payload = {
        "scheme_id": "SISFS",
    }
    response = client.post("/v1/eligibility/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_id"] == "SISFS"
    assert data["citizen_id"] == "demo-user"
    assert data["eligibility_status"] in ("ELIGIBLE", "NOT_ELIGIBLE", "INSUFFICIENT_INFORMATION")
    assert len(data["rules"]) > 0


def test_document_analysis_endpoint():
    """Verify document AI analysis endpoint with test fixture."""
    headers = {
        "X-Internal-API-Key": INTERNAL_KEY,
        "X-Correlation-ID": "test-corr-5",
    }
    payload = {
        "file_path": "tests/fixtures/documents/digital_income_certificate.pdf",
    }
    response = client.post("/v1/documents/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["apparent_document_type"].upper() == "INCOME_CERTIFICATE"
    assert "annual_income" in data["fields"]
    assert data["fields"]["annual_income"]["value"] is not None


def test_agent_chat_endpoint():
    """Verify primary agent orchestration endpoint."""
    headers = {
        "X-Internal-API-Key": INTERNAL_KEY,
        "X-Citizen-ID": "demo-user",
        "X-Correlation-ID": "test-corr-6",
    }
    payload = {
        "query": "What is my registered profile annual income?",
    }
    response = client.post("/v1/agent/chat", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "tools_called" in data
