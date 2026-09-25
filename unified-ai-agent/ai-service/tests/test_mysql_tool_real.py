"""Tests for CitizenProfileTool with real MySQL repository integration (Milestone 7).

Verifies official database retrieval, safe handling of missing records,
strict rejection of invalid identifiers, and non-mock fallback policy by default.
"""
from datetime import date
from decimal import Decimal
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import OperationalError

from src.database.models import Base
from src.database.repositories.citizen_repo import CitizenRepository
from src.tools.mysql_tool import CitizenProfileTool
from src.config.settings import Settings


@pytest.fixture
def seeded_repo():
    """Create in-memory SQLite database seeded with demo citizen."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    repo = CitizenRepository(session=session)
    repo.create_or_update_citizen(
        citizen_id="demo-user",
        name="Ramesh Kumar",
        date_of_birth=date(1998, 5, 15),
        gender="Male",
        phone="+91-9876543210",
    )
    repo.create_or_update_profile(
        citizen_id="demo-user",
        state="Telangana",
        district="Hyderabad",
        annual_income=240000.0,
        occupation="Tech Startup Founder",
        has_dpiit_recognition=True,
        business_incorporated_years=1,
        category="General",
        is_taxpayer=False,
    )
    session.commit()

    try:
        yield repo
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_tool_retrieves_citizen_from_real_database(seeded_repo):
    """Verify tool returns official database record with is_mock=False."""
    tool = CitizenProfileTool(repository=seeded_repo)
    result = tool.execute(citizen_id="demo-user")

    assert result["status"] == "success"
    assert result["is_mock"] is False
    assert result["data_source"] == "MYSQL_DATABASE"
    assert result["citizen_id"] == "demo-user"

    profile = result["profile"]
    assert profile is not None
    assert profile["name"] == "Ramesh Kumar"
    assert profile["state"] == "Telangana"
    assert profile["has_dpiit_recognition"] is True
    assert profile["age"] is not None


def test_tool_handles_unknown_citizen_without_mock_fallback(seeded_repo):
    """Verify that querying a non-existent citizen returns not_found, NOT mock data."""
    tool = CitizenProfileTool(repository=seeded_repo)
    result = tool.execute(citizen_id="unknown-citizen-999")

    assert result["status"] == "not_found"
    assert result["is_mock"] is False
    assert result["profile"] is None
    assert "No citizen profile found" in result["notice"]


def test_tool_rejects_sql_injection_input(seeded_repo):
    """Verify tool rejects malicious input with status=invalid_input without hitting database."""
    tool = CitizenProfileTool(repository=seeded_repo)
    result = tool.execute(citizen_id="' OR 1=1 --")

    assert result["status"] == "invalid_input"
    assert result["is_mock"] is False
    assert "error" in result


def test_tool_database_failure_returns_service_unavailable_by_default(seeded_repo):
    """Verify that a database failure returns service_unavailable, NEVER silently returning mock data."""
    mock_failing_repo = MagicMock(spec=CitizenRepository)
    mock_failing_repo.get_citizen_with_profile.side_effect = OperationalError("connection refused", {}, None)

    # Test default production policy: fallback disabled
    with patch("src.tools.mysql_tool.get_settings") as mock_settings_fn:
        mock_settings = MagicMock()
        mock_settings.allow_mock_fallback = False
        mock_settings_fn.return_value = mock_settings

        tool = CitizenProfileTool(repository=mock_failing_repo)
        result = tool.execute(citizen_id="demo-user")

        assert result["status"] == "service_unavailable"
        assert result["is_mock"] is False
        assert result["profile"] is None
        assert "temporarily unavailable" in result["error"]


def test_tool_database_failure_with_explicit_mock_fallback_allowed():
    """Verify explicit development mock fallback only activates when ALLOW_MOCK_FALLBACK=True."""
    mock_failing_repo = MagicMock(spec=CitizenRepository)
    mock_failing_repo.get_citizen_with_profile.side_effect = OperationalError("connection refused", {}, None)

    with patch("src.tools.mysql_tool.get_settings") as mock_settings_fn:
        mock_settings = MagicMock()
        mock_settings.allow_mock_fallback = True
        mock_settings_fn.return_value = mock_settings

        tool = CitizenProfileTool(repository=mock_failing_repo)
        result = tool.execute(citizen_id="demo-user")

        assert result["status"] == "success"
        assert result["is_mock"] is True
        assert result["data_source"] == "MOCK_DEVELOPMENT_DATABASE"
        assert result["profile"]["name"] == "Ramesh Kumar"
