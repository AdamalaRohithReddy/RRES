"""Security and injection resilience tests (Milestone 7).

Verifies strict identifier regex validation, rejection of SQL injection payloads,
parameterized ORM querying, and secret redaction.
"""
import pytest
from src.database.repositories.citizen_repo import validate_citizen_id
from src.database.repositories.application_repo import validate_application_id
from src.database.connection import mask_connection_url

# Malicious SQL injection attempts, traversal payloads, and illegal character strings
MALICIOUS_INPUTS = [
    "' OR 1=1 --",
    "admin'; DROP TABLE citizens; --",
    "1 UNION SELECT null, username, password FROM users --",
    "\" OR \"\"=\"",
    "; EXEC xp_cmdshell('dir');--",
    "../../../etc/passwd",
    "<script>alert('xss')</script>",
    "user@domain.com",
    "citizen id with spaces",
    "user$name",
    "cid#1",
    "",  # empty string
    "   ",  # whitespace only
    "a" * 65,  # exceeds 64 char max length
]

VALID_INPUTS = [
    "demo-user",
    "senior-citizen",
    "rural-farmer",
    "DEMO-001",
    "APP_STATUS_2026",
    "citizen-123_abc",
    "A",
    "a" * 64,  # exactly 64 chars
]


@pytest.mark.parametrize("bad_input", MALICIOUS_INPUTS)
def test_citizen_id_validation_rejects_malicious_inputs(bad_input):
    """Verify validate_citizen_id raises ValueError on any SQL injection or malformed string."""
    with pytest.raises(ValueError):
        validate_citizen_id(bad_input)


@pytest.mark.parametrize("valid_input", VALID_INPUTS)
def test_citizen_id_validation_accepts_valid_inputs(valid_input):
    """Verify validate_citizen_id accepts standard alphanumeric identifiers."""
    cleaned = validate_citizen_id(valid_input)
    assert cleaned == valid_input


@pytest.mark.parametrize("bad_input", MALICIOUS_INPUTS)
def test_application_id_validation_rejects_malicious_inputs(bad_input):
    """Verify validate_application_id raises ValueError on any SQL injection or malformed string."""
    with pytest.raises(ValueError):
        validate_application_id(bad_input)


@pytest.mark.parametrize("valid_input", VALID_INPUTS)
def test_application_id_validation_accepts_valid_inputs(valid_input):
    """Verify validate_application_id accepts valid application reference strings."""
    cleaned = validate_application_id(valid_input)
    assert cleaned == valid_input


def test_password_redaction_in_connection_urls():
    """Verify that credentials are never exposed in loggable connection strings."""
    passwords = [
        "Pass123!@#",
        "very_complex_secret_pass",
        "mysql_root_pw",
    ]
    for pw in passwords:
        raw_url = f"mysql+pymysql://admin:{pw}@mysql-cluster.internal:3306/production_db"
        masked = mask_connection_url(raw_url)
        assert pw not in masked
        assert ":***@" in masked
