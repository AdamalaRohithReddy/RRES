"""Integration test connecting Milestone 7 MySQL data layer with M5 and M6.

Verifies:
1. Citizen demographic profile retrieved from database layer
2. Evidence harvested into M5 EvidenceHarvester
3. Deterministic eligibility evaluated via M5 EligibilityEngine
4. Eligibility audit decision recorded into EligibilityAuditRepository
5. Multi-needs detected via M6 NeedDetector and recorded into NeedRepository
"""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.database.repositories.citizen_repo import CitizenRepository
from src.database.repositories.need_repo import NeedRepository
from src.database.repositories.eligibility_repo import EligibilityAuditRepository
from src.tools.mysql_tool import CitizenProfileTool
from src.eligibility.evidence import EvidenceHarvester
from src.eligibility.engine import EligibilityEngine
from src.eligibility.rules import SchemeRulesRegistry
from src.eligibility.models import FinalEligibilityStatus
from src.needs.detector import NeedDetector
from src.needs.models import NeedCategory


@pytest.fixture
def integrated_environment():
    """Setup SQLite in-memory environment with full M7 seed and repositories."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    c_repo = CitizenRepository(session=session)
    c_repo.create_or_update_citizen(
        citizen_id="demo-user",
        name="Ramesh Kumar",
        date_of_birth=date(1998, 5, 15),
        gender="Male",
        phone="+91-9876543210",
    )
    c_repo.create_or_update_profile(
        citizen_id="demo-user",
        state="Telangana",
        district="Hyderabad",
        annual_income=240000.0,
        occupation="Tech Startup Founder",
        has_dpiit_recognition=True,
        business_incorporated_years=1,
        category="General",
        is_taxpayer=False,
        additional_attributes={
            "previous_govt_monetary_support": 0,
            "indian_promoter_shareholding": 100,
        },
    )
    session.commit()

    try:
        yield {
            "session": session,
            "citizen_repo": c_repo,
            "need_repo": NeedRepository(session=session),
            "audit_repo": EligibilityAuditRepository(session=session),
        }
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_end_to_end_database_m5_eligibility(integrated_environment):
    """Verify citizen profile from DB feeds directly into M5 deterministic evaluation."""
    citizen_repo = integrated_environment["citizen_repo"]
    audit_repo = integrated_environment["audit_repo"]

    # 1. Fetch profile via CitizenProfileTool
    tool = CitizenProfileTool(repository=citizen_repo)
    result = tool.execute(citizen_id="demo-user")
    assert result["status"] == "success"
    assert result["is_mock"] is False
    profile_dict = result["profile"]

    # 2. Ingest into EvidenceHarvester
    harvester = EvidenceHarvester()
    evidence_store = harvester.harvest(profile_data=profile_dict)
    assert "has_dpiit_recognition" in evidence_store
    assert evidence_store["has_dpiit_recognition"].value is True
    assert evidence_store["business_incorporated_years"].value == 1

    # 3. Deterministic Eligibility Engine (Startup India Seed Fund Scheme)
    engine = EligibilityEngine()
    eval_result = engine.evaluate(
        scheme_id="SISFS",
        evidence_store=evidence_store,
        citizen_id="demo-user",
    )

    assert eval_result.status == FinalEligibilityStatus.ELIGIBLE
    assert len(eval_result.passed_rules) >= 4
    assert len(eval_result.failed_rules) == 0

    # 4. Record Audit Log in M7 Repository
    audit_record = audit_repo.record_assessment(
        citizen_id="demo-user",
        scheme_name=eval_result.scheme_name,
        decision=eval_result.status.value,
        passed_rules=[r.rule.rule_id for r in eval_result.passed_rules],
        failed_rules=[r.rule.rule_id for r in eval_result.failed_rules],
        missing_evidence=[r.rule.rule_id for r in eval_result.unknown_rules],
    )
    assert audit_record is not None
    assert audit_record.decision == "ELIGIBLE"

    # Verify audit persistence
    audits = audit_repo.list_assessments_by_citizen("demo-user")
    assert len(audits) == 1
    assert audits[0]["decision"] == "ELIGIBLE"


def test_end_to_end_database_m6_needs(integrated_environment):
    """Verify detected needs from M6 detector are persisted to M7 database."""
    need_repo = integrated_environment["need_repo"]
    detector = NeedDetector()

    user_statement = "I am a startup founder looking for seed capital and incubator mentorship."
    detection_result = detector.detect(user_statement)

    assert len(detection_result.needs) > 0
    categories = [n.category for n in detection_result.needs]
    assert NeedCategory.ENTREPRENEURSHIP in categories

    # Persist needs to M7 database
    needs_to_save = [n.model_dump() for n in detection_result.needs]
    saved_models = need_repo.record_needs(
        citizen_id="demo-user",
        needs=needs_to_save,
        session_id="integration-sess-1",
    )
    assert len(saved_models) == len(detection_result.needs)

    # Retrieve from database
    persisted_needs = need_repo.get_needs_by_citizen("demo-user", session_id="integration-sess-1")
    assert len(persisted_needs) == len(detection_result.needs)
    cat_names = [p["category"] for p in persisted_needs]
    assert "entrepreneurship" in cat_names
