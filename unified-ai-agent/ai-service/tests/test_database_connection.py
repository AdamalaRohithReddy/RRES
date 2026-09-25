"""Tests for database connection management and health checks (Milestone 7).

Verifies engine creation, URL password masking, transaction commit/rollback,
and connection health diagnostics without credential leakage.
"""
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.database.connection import (
    check_connection_health,
    get_db_session,
    init_db,
    mask_connection_url,
)
from src.database.models import CitizenModel


def test_mask_connection_url():
    """Verify that credentials are fully masked from database connection strings."""
    url = "mysql+pymysql://root:super_secret_password@127.0.0.1:3306/citizen_db?charset=utf8mb4"
    masked = mask_connection_url(url)
    assert "super_secret_password" not in masked
    assert "root:***@" in masked

    # URL without password
    no_pwd_url = "sqlite:///:memory:"
    assert mask_connection_url(no_pwd_url) == "sqlite:///:memory:"


def test_connection_health_check_success():
    """Verify health check returns healthy=True with latency on active engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    result = check_connection_health(engine=engine)
    assert result["healthy"] is True
    assert result["latency_ms"] is not None
    assert result["error"] is None
    assert "sqlite" in result["url"]


def test_connection_health_check_failure():
    """Verify health check safely handles unreachable host without leaking secrets."""
    # Use invalid host with masked credentials
    fake_engine = create_engine("mysql+pymysql://user:secret123@192.0.2.1:3306/db?connect_timeout=1")
    result = check_connection_health(engine=fake_engine)
    assert result["healthy"] is False
    assert result["error"] is not None
    # Password must NEVER appear in the error or url
    assert "secret123" not in result["error"]
    assert "secret123" not in result["url"]
    assert "***" in result["url"]


def test_get_db_session_commit_and_rollback():
    """Verify transactional behavior of get_db_session context manager."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine=engine)

    # 1. Commit on normal exit
    with get_db_session(engine=engine) as session:
        citizen = CitizenModel(citizen_id="user-commit", name="Commit User")
        session.add(citizen)

    with get_db_session(engine=engine) as session:
        found = session.get(CitizenModel, "user-commit")
        assert found is not None
        assert found.name == "Commit User"

    # 2. Rollback on exception
    with pytest.raises(RuntimeError):
        with get_db_session(engine=engine) as session:
            citizen_fail = CitizenModel(citizen_id="user-rollback", name="Rollback User")
            session.add(citizen_fail)
            raise RuntimeError("Forced simulation error")

    with get_db_session(engine=engine) as session:
        not_found = session.get(CitizenModel, "user-rollback")
        assert not_found is None
