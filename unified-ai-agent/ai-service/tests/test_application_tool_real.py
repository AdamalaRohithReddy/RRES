"""Tests for ApplicationStatusTool with real MySQL repository integration (Milestone 7).

Verifies tracking record retrieval from database, non-mock fallback policy by default,
safe rejection of invalid identifiers, and structured error handling.
"""
from datetime import date
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import OperationalError

from src.database.models import Base
from src.database.repositories.citizen_repo import CitizenRepository
from src.database.repositories.application_repo import ApplicationRepository
from src.tools.api_tool import ApplicationStatusTool


@pytest.fixture
def seeded_app_repo():
    """Create in-memory SQLite database seeded with demo citizen and application."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    c_repo = CitizenRepository(session=session)
    c_repo.create_or_update_citizen(citizen_id="demo-user", name="Ramesh Kumar")

    app_repo = ApplicationRepository(session=session)
    app_repo.create_application(
        application_id="DEMO-001",
        citizen_id="demo-user",
        scheme_name="Startup India Seed Fund Scheme",
        status="Under Evaluation by Incubator Seed Management Committee (ISMC)",
        submitted_date=date(2026, 8, 15),
        incubator_preference="T-Hub Hyderabad",
        milestone_stage="Proof of Concept Validation",
        next_step="Awaiting final interview schedule notification by email.",
    )
    session.commit()

    try:
        yield app_repo
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_tool_retrieves_application_from_real_database(seeded_app_repo):
    """Verify tool returns official application record from database with is_mock=False."""
    tool = ApplicationStatusTool(repository=seeded_app_repo)
    result = tool.execute(application_id="DEMO-001")

    assert result["status"] == "success"
    assert result["is_mock"] is False
    assert result["data_source"] == "MYSQL_DATABASE"
    assert result["application_id"] == "DEMO-001"

    rec = result["record"]
    assert rec is not None
    assert rec["scheme_name"] == "Startup India Seed Fund Scheme"
    assert "Under Evaluation" in rec["status"]
    assert rec["incubator_preference"] == "T-Hub Hyderabad"


def test_tool_handles_unknown_application_without_mock_fallback(seeded_app_repo):
    """Verify that querying a non-existent application returns not_found, NOT mock data."""
    tool = ApplicationStatusTool(repository=seeded_app_repo)
    result = tool.execute(application_id="UNKNOWN-APP-999")

    assert result["status"] == "not_found"
    assert result["is_mock"] is False
    assert result["record"] is None
    assert "No application record found" in result["notice"]


def test_tool_rejects_sql_injection_input(seeded_app_repo):
    """Verify tool rejects malicious input with status=invalid_input without hitting database."""
    tool = ApplicationStatusTool(repository=seeded_app_repo)
    result = tool.execute(application_id="'; DROP TABLE applications; --")

    assert result["status"] == "invalid_input"
    assert result["is_mock"] is False
    assert "error" in result


def test_tool_database_failure_returns_service_unavailable_by_default(seeded_app_repo):
    """Verify that a database failure returns service_unavailable by default."""
    mock_failing_repo = MagicMock(spec=ApplicationRepository)
    mock_failing_repo.get_application.side_effect = OperationalError("connection refused", {}, None)

    # Test default production policy: fallback disabled
    with patch("src.tools.api_tool.get_settings") as mock_settings_fn:
        mock_settings = MagicMock()
        mock_settings.allow_mock_fallback = False
        mock_settings_fn.return_value = mock_settings

        tool = ApplicationStatusTool(repository=mock_failing_repo)
        result = tool.execute(application_id="DEMO-001")

        assert result["status"] == "service_unavailable"
        assert result["is_mock"] is False
        assert result["record"] is None
        assert "temporarily unavailable" in result["error"]


def test_tool_database_failure_with_explicit_mock_fallback_allowed():
    """Verify explicit mock fallback only activates when ALLOW_MOCK_FALLBACK=True."""
    mock_failing_repo = MagicMock(spec=ApplicationRepository)
    mock_failing_repo.get_application.side_effect = OperationalError("connection refused", {}, None)

    with patch("src.tools.api_tool.get_settings") as mock_settings_fn:
        mock_settings = MagicMock()
        mock_settings.allow_mock_fallback = True
        mock_settings_fn.return_value = mock_settings

        tool = ApplicationStatusTool(repository=mock_failing_repo)
        result = tool.execute(application_id="DEMO-001")

        assert result["status"] == "success"
        assert result["is_mock"] is True
        assert result["data_source"] == "MOCK_EXTERNAL_API"
        assert result["record"]["scheme_name"] == "Startup India Seed Fund Scheme"
