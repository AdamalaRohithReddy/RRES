"""Security boundary and authorization tests for FastAPI internal endpoints (Milestone 9.1)."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.config.settings import get_settings

client = TestClient(app)
INTERNAL_KEY = get_settings().ai_service_internal_key


def test_missing_internal_key_rejected():
    """Verify endpoint rejects requests missing X-Internal-API-Key with 401."""
    response = client.post(
        "/v1/needs/detect",
        json={"text": "I need help with employment."},
        # No X-Internal-API-Key header
    )
    assert response.status_code == 401
    assert "Invalid or missing internal service API key" in response.json()["detail"]


def test_invalid_internal_key_rejected():
    """Verify endpoint rejects requests with invalid X-Internal-API-Key with 401."""
    response = client.post(
        "/v1/needs/detect",
        json={"text": "I need help with employment."},
        headers={"X-Internal-API-Key": "wrong-secret-key-999"},
    )
    assert response.status_code == 401
    assert "Invalid or missing internal service API key" in response.json()["detail"]


def test_missing_citizen_id_on_chat_rejected():
    """Verify /v1/agent/chat rejects requests missing X-Citizen-ID with 400."""
    response = client.post(
        "/v1/agent/chat",
        json={"query": "Check my eligibility"},
        headers={"X-Internal-API-Key": INTERNAL_KEY},
        # No X-Citizen-ID header
    )
    assert response.status_code == 400
    assert "Missing or empty X-Citizen-ID header" in response.json()["detail"]


def test_missing_citizen_id_on_eligibility_rejected():
    """Verify /v1/eligibility/evaluate rejects requests missing X-Citizen-ID with 400."""
    response = client.post(
        "/v1/eligibility/evaluate",
        json={"scheme_id": "SISFS"},
        headers={"X-Internal-API-Key": INTERNAL_KEY},
        # No X-Citizen-ID header
    )
    assert response.status_code == 400
    assert "Missing or empty X-Citizen-ID header" in response.json()["detail"]


def test_document_path_traversal_rejected():
    """Verify Document AI rejects attempts to analyze paths outside sandbox with 400."""
    response = client.post(
        "/v1/documents/analyze",
        json={"file_path": "../../../Windows/System32/drivers/etc/hosts"},
        headers={"X-Internal-API-Key": INTERNAL_KEY},
    )
    assert response.status_code == 400
    assert "Access denied" in response.json()["detail"]


def test_document_dangerous_extension_rejected():
    """Verify Document AI rejects executable file extensions with 400."""
    response = client.post(
        "/v1/documents/analyze",
        json={"file_path": "data/documents/malicious_payload.exe"},
        headers={"X-Internal-API-Key": INTERNAL_KEY},
    )
    assert response.status_code == 400
    assert "Access denied" in response.json()["detail"]
