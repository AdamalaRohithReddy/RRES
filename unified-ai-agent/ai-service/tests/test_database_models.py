"""Tests for SQLAlchemy 2.0 ORM models (Milestone 7).

Verifies entity definitions, table relationships, cascade deletion,
dynamic age calculation, and dictionary serialization.
"""
from datetime import date, datetime
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import (
    Base,
    CitizenModel,
    CitizenProfileModel,
    ApplicationModel,
    ApplicationStatusHistoryModel,
    DocumentModel,
    DocumentExtractedFieldModel,
    CitizenNeedModel,
    EligibilityAssessmentModel,
)


@pytest.fixture
def db_session():
    """In-memory SQLite session fixture for fast isolated model testing."""
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


def test_citizen_model_dynamic_age():
    """Verify dynamic age property computes age accurately from date_of_birth."""
    today = date.today()
    # Citizen born exactly 25 years ago
    dob_25 = date(today.year - 25, today.month, today.day)
    c1 = CitizenModel(citizen_id="test-1", name="Alice", date_of_birth=dob_25)
    assert c1.age == 25

    # Citizen with no DOB returns None
    c2 = CitizenModel(citizen_id="test-2", name="Bob", date_of_birth=None)
    assert c2.age is None


def test_citizen_and_profile_relationship(db_session: Session):
    """Verify citizen and citizen_profile one-to-one relationship and serialization."""
    citizen = CitizenModel(
        citizen_id="cit-001",
        name="Ramesh Kumar",
        date_of_birth=date(1996, 5, 10),
        gender="Male",
        phone="+91-9999999999",
    )
    profile = CitizenProfileModel(
        citizen=citizen,
        state="Telangana",
        district="Hyderabad",
        annual_income=Decimal("350000.00"),
        occupation="Software Engineer",
        category="General",
        is_taxpayer=True,
        has_dpiit_recognition=False,
    )
    db_session.add(citizen)
    db_session.commit()

    # Query citizen and verify consolidated dict
    retrieved = db_session.get(CitizenModel, "cit-001")
    assert retrieved is not None
    assert retrieved.profile is not None
    assert retrieved.profile.state == "Telangana"

    c_dict = retrieved.to_dict()
    assert c_dict["citizen_id"] == "cit-001"
    assert c_dict["name"] == "Ramesh Kumar"
    assert c_dict["state"] == "Telangana"
    assert c_dict["annual_income"] == 350000.0
    assert c_dict["is_taxpayer"] is True
    assert c_dict["age"] is not None


def test_application_and_history_relationship(db_session: Session):
    """Verify application tracking and ordered status history relationship."""
    citizen = CitizenModel(citizen_id="cit-app-1", name="Sunita Rao")
    app = ApplicationModel(
        application_id="APP-999",
        citizen=citizen,
        scheme_name="Atal Pension Yojana",
        status="Submitted",
        submitted_date=date(2026, 1, 15),
    )
    db_session.add(citizen)
    db_session.add(app)
    db_session.commit()

    # Add status history
    h1 = ApplicationStatusHistoryModel(
        application=app,
        status="Submitted",
        comment="Application received by portal",
        changed_by="system",
    )
    h2 = ApplicationStatusHistoryModel(
        application=app,
        status="Under Review",
        comment="Documents assigned to verification officer",
        changed_by="officer_1",
    )
    db_session.add_all([h1, h2])
    db_session.commit()

    retrieved_app = db_session.get(ApplicationModel, "APP-999")
    assert retrieved_app is not None
    assert len(retrieved_app.status_history) == 2
    app_dict = retrieved_app.to_dict()
    assert app_dict["application_id"] == "APP-999"
    assert app_dict["scheme_name"] == "Atal Pension Yojana"


def test_document_and_extracted_fields(db_session: Session):
    """Verify document metadata and extracted facts persistence with confidence and provenance."""
    citizen = CitizenModel(citizen_id="cit-doc-1", name="Prakash")
    doc = DocumentModel(
        citizen=citizen,
        filename="aadhaar_card.pdf",
        apparent_type="AADHAAR",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path="/storage/docs/cit-doc-1/aadhaar_card.pdf",
    )
    db_session.add(citizen)
    db_session.add(doc)
    db_session.commit()

    f1 = DocumentExtractedFieldModel(
        document=doc,
        field_name="age",
        field_value="35",
        confidence=Decimal("0.950"),
        provenance_method="REGEX",
    )
    f2 = DocumentExtractedFieldModel(
        document=doc,
        field_name="gender",
        field_value="Male",
        confidence=Decimal("0.980"),
        provenance_method="REGEX",
    )
    db_session.add_all([f1, f2])
    db_session.commit()

    retrieved_doc = db_session.get(DocumentModel, doc.document_id)
    assert retrieved_doc is not None
    assert len(retrieved_doc.extracted_fields) == 2
    assert retrieved_doc.extracted_fields[0].field_name in ("age", "gender")


def test_cascade_delete(db_session: Session):
    """Verify deleting a citizen cascades to all related entities."""
    citizen = CitizenModel(citizen_id="cit-cascade", name="To Delete")
    profile = CitizenProfileModel(citizen=citizen, state="Goa")
    app = ApplicationModel(
        application_id="APP-CASC",
        citizen=citizen,
        scheme_name="Test Scheme",
        status="Draft",
    )
    doc = DocumentModel(
        citizen=citizen,
        filename="test.pdf",
        sha256_hash="abc123hash",
    )
    need = CitizenNeedModel(
        citizen=citizen,
        category="EMPLOYMENT",
        urgency="HIGH",
        need_type="EXPLICIT",
    )
    audit = EligibilityAssessmentModel(
        citizen=citizen,
        scheme_name="Test Scheme",
        decision="ELIGIBLE",
    )
    db_session.add_all([citizen, profile, app, doc, need, audit])
    db_session.commit()

    # Verify rows exist
    assert db_session.get(CitizenModel, "cit-cascade") is not None
    assert db_session.get(ApplicationModel, "APP-CASC") is not None

    # Delete citizen
    db_session.delete(citizen)
    db_session.commit()

    # All related items should be cascade deleted
    assert db_session.get(CitizenModel, "cit-cascade") is None
    assert db_session.get(CitizenProfileModel, profile.profile_id) is None
    assert db_session.get(ApplicationModel, "APP-CASC") is None
    assert db_session.get(DocumentModel, doc.document_id) is None
    assert db_session.get(CitizenNeedModel, need.need_id) is None
    assert db_session.get(EligibilityAssessmentModel, audit.assessment_id) is None
