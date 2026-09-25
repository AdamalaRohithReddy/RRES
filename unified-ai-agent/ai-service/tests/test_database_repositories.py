"""Tests for database repositories (Milestone 7).

Verifies CRUD operations, parameterized querying, and entity lifecycle
across Citizen, Application, Document, Need, and Eligibility audit repositories.
"""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.database.repositories.citizen_repo import CitizenRepository
from src.database.repositories.application_repo import ApplicationRepository
from src.database.repositories.document_repo import DocumentRepository
from src.database.repositories.need_repo import NeedRepository
from src.database.repositories.eligibility_repo import EligibilityAuditRepository


@pytest.fixture
def repo_session():
    """In-memory SQLite session for repository testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_citizen_repository_crud(repo_session):
    """Verify CitizenRepository creation, profile association, updates, and list operations."""
    repo = CitizenRepository(session=repo_session)

    # 1. Create Citizen
    citizen = repo.create_or_update_citizen(
        citizen_id="demo-user",
        name="Ramesh Kumar",
        date_of_birth=date(1998, 5, 15),
        gender="Male",
        phone="+91-9876543210",
    )
    assert citizen.citizen_id == "demo-user"

    # 2. Add Profile
    profile = repo.create_or_update_profile(
        citizen_id="demo-user",
        state="Telangana",
        district="Hyderabad",
        annual_income=240000.0,
        occupation="Tech Startup Founder",
        has_dpiit_recognition=True,
        business_incorporated_years=1,
    )
    repo_session.commit()

    # 3. Retrieve Consolidated Profile
    data = repo.get_citizen_with_profile("demo-user")
    assert data is not None
    assert data["citizen_id"] == "demo-user"
    assert data["name"] == "Ramesh Kumar"
    assert data["state"] == "Telangana"
    assert data["annual_income"] == 240000.0
    assert data["has_dpiit_recognition"] is True
    assert data["age"] is not None

    # 4. Update Profile
    repo.create_or_update_profile(
        citizen_id="demo-user",
        state="Telangana",
        annual_income=300000.0,
    )
    repo_session.commit()
    updated = repo.get_citizen_with_profile("demo-user")
    assert updated["annual_income"] == 300000.0

    # 5. List Citizens
    all_citizens = repo.list_citizens()
    assert len(all_citizens) == 1
    assert all_citizens[0]["citizen_id"] == "demo-user"


def test_application_repository_crud_and_audit(repo_session):
    """Verify ApplicationRepository tracking and atomic status history generation."""
    # Pre-requisite: Citizen
    c_repo = CitizenRepository(session=repo_session)
    c_repo.create_or_update_citizen(citizen_id="cit-002", name="Priya")
    repo_session.commit()

    app_repo = ApplicationRepository(session=repo_session)

    # 1. Create Application
    app = app_repo.create_application(
        application_id="DEMO-001",
        citizen_id="cit-002",
        scheme_name="Startup India Seed Fund Scheme",
        status="Under Evaluation",
        submitted_date=date(2026, 8, 15),
        incubator_preference="T-Hub",
        next_step="Awaiting interview",
    )
    repo_session.commit()

    # 2. Get Application
    rec = app_repo.get_application("DEMO-001")
    assert rec is not None
    assert rec["status"] == "Under Evaluation"
    assert rec["incubator_preference"] == "T-Hub"

    # 3. Update Status
    app_repo.update_status(
        application_id="DEMO-001",
        new_status="Approved",
        comment="ISMC approved proposal",
        changed_by="evaluator_chair",
        next_step="Grant disbursement within 14 days",
    )
    repo_session.commit()

    updated = app_repo.get_application("DEMO-001")
    assert updated["status"] == "Approved"
    assert updated["next_step"] == "Grant disbursement within 14 days"

    # 4. Check Status History
    history = app_repo.get_status_history("DEMO-001")
    assert len(history) == 2
    assert history[0]["status"] == "Under Evaluation"
    assert history[1]["status"] == "Approved"
    assert history[1]["changed_by"] == "evaluator_chair"


def test_document_repository(repo_session):
    """Verify DocumentRepository metadata and extracted facts persistence with provenance."""
    c_repo = CitizenRepository(session=repo_session)
    c_repo.create_or_update_citizen(citizen_id="cit-003", name="Anil")
    repo_session.commit()

    doc_repo = DocumentRepository(session=repo_session)
    doc = doc_repo.create_document(
        citizen_id="cit-003",
        filename="dpiit_cert.pdf",
        sha256_hash="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
        apparent_type="DPIIT_CERTIFICATE",
        storage_path="/docs/dpiit_cert.pdf",
    )
    repo_session.commit()

    doc_repo.add_extracted_fields(
        document_id=doc.document_id,
        fields=[
            {
                "field_name": "has_dpiit_recognition",
                "field_value": "True",
                "confidence": 0.99,
                "provenance_method": "REGEX_EXTRACTION",
            },
            {
                "field_name": "certificate_number",
                "field_value": "DPIIT-2026-9988",
                "confidence": 0.95,
                "provenance_method": "TESSERACT_OCR",
            },
        ],
    )
    repo_session.commit()

    doc_data = doc_repo.get_document_with_fields(doc.document_id)
    assert doc_data is not None
    assert doc_data["apparent_type"] == "DPIIT_CERTIFICATE"
    assert len(doc_data["extracted_fields"]) == 2
    assert doc_data["extracted_fields"][0]["confidence"] == 0.99


def test_need_and_eligibility_audit_repositories(repo_session):
    """Verify NeedRepository and EligibilityAuditRepository integration."""
    c_repo = CitizenRepository(session=repo_session)
    c_repo.create_or_update_citizen(citizen_id="cit-004", name="Sunil")
    repo_session.commit()

    # 1. Need persistence (M6 integration)
    need_repo = NeedRepository(session=repo_session)
    need_repo.record_needs(
        citizen_id="cit-004",
        needs=[
            {
                "category": "BUSINESS_AND_ENTREPRENEURSHIP",
                "urgency": "HIGH",
                "need_type": "EXPLICIT",
                "statement": "Need grant funding for seed capital",
            },
            {
                "category": "EMPLOYMENT_AND_SKILLING",
                "urgency": "MEDIUM",
                "need_type": "INFERRED",
                "statement": "Looking for incubator support",
            },
        ],
        session_id="sess-xyz",
    )
    repo_session.commit()

    needs = need_repo.get_needs_by_citizen("cit-004")
    assert len(needs) == 2
    assert needs[0]["need_type"] in ("EXPLICIT", "INFERRED")

    # 2. Eligibility audit persistence (M5 integration)
    audit_repo = EligibilityAuditRepository(session=repo_session)
    audit_repo.record_assessment(
        citizen_id="cit-004",
        scheme_name="Startup India Seed Fund Scheme",
        decision="ELIGIBLE",
        passed_rules=["has_dpiit_recognition", "business_incorporated_years <= 2"],
        failed_rules=[],
        missing_evidence=[],
    )
    repo_session.commit()

    audits = audit_repo.list_assessments_by_citizen("cit-004")
    assert len(audits) == 1
    assert audits[0]["decision"] == "ELIGIBLE"
    assert audits[0]["scheme_name"] == "Startup India Seed Fund Scheme"
