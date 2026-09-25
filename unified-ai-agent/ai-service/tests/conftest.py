"""Test configuration for AI Service test suite.

Explicitly enables development/test mock fallback when running automated offline tests
without a live MySQL service, satisfying user correction #1:
'Mock fallback may remain available for explicitly enabled development/testing environments,
but a production/default MySQL failure must NEVER silently return demo-user or another mock citizen.'
"""
import os
import pytest
from src.config.settings import get_settings

# Enable mock fallback for the test runner environment
os.environ["ALLOW_MOCK_FALLBACK"] = "true"
get_settings.cache_clear()


@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch):
    """Ensure test environment has mock fallback enabled unless a test explicitly overrides it."""
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
