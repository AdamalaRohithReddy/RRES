"""Tests for DigiLocker Adapter and M5 Evidence Conflict Resolution (Milestone 8.3)."""

import pytest

from src.government_api.adapters.digilocker_adapter import DigiLockerCertificateAdapter
from src.government_api.models import (
    APIResponseStatus,
    SourceType,
    VerificationStatus,
)
from src.eligibility.evidence import EvidenceHarvester
from src.eligibility.engine import EligibilityEngine
from src.eligibility.models import EvidenceSource, FinalEligibilityStatus
from src.tools.eligibility_tool import EligibilityCheckTool


# ---------------------------------------------------------------------------
# 1. DigiLocker Adapter Contract & Terminology Tests
# ---------------------------------------------------------------------------

def test_digilocker_adapter_success_fixture():
    adapter = DigiLockerCertificateAdapter()
    res = adapter.execute("verify_income_certificate", {"certificate_id": "TS-INC-2026-0091823"})

    assert res.status == APIResponseStatus.SUCCESS
    assert res.data_source == SourceType.SANDBOX_FIXTURE
    assert res.verification_status == VerificationStatus.CONTRACT_VERIFIED
    assert res.payload["certificate_id"] == "TS-INC-2026-0091823"
    assert res.payload["annual_income"] == 240000.0
    assert res.payload["verification_status"] == "VALID"


def test_digilocker_adapter_not_found():
    adapter = DigiLockerCertificateAdapter()
    res = adapter.execute("verify_income_certificate", {"certificate_id": "UNKNOWN-999"})

    assert res.status == APIResponseStatus.NOT_FOUND
    assert res.verification_status == VerificationStatus.UNVERIFIED
    assert "not found" in res.error_details["message"].lower()


def test_digilocker_adapter_empty_id():
    adapter = DigiLockerCertificateAdapter()
    res = adapter.execute("verify_income_certificate", {"certificate_id": ""})

    assert res.status == APIResponseStatus.SCHEMA_ERROR
    assert res.verification_status == VerificationStatus.UNVERIFIED


# ---------------------------------------------------------------------------
# 2. M5 Multi-Source Evidence Conflict Policy Tests
# ---------------------------------------------------------------------------

def test_m5_evidence_conflict_resolution_matching():
    harvester = EvidenceHarvester()
    profile = {"annual_income": 240000.0, "citizen_id": "demo-user"}
    api_data = {
        "provider": "MeeSeva Telangana",
        "endpoint_identifier": "APISETU_DIGILOCKER_INCER",
        "verification_status": "CONTRACT_VERIFIED",
        "payload": {"annual_income": 240000.0, "certificate_id": "TS-INC-2026-0091823"},
    }

    evidence = harvester.harvest(profile_data=profile, api_data=api_data)
    income_ev = evidence["annual_income"]

    assert income_ev.value == 240000.0
    assert income_ev.source == EvidenceSource.GOVERNMENT_API
    assert income_ev.fact_type == "EXTERNALLY_VERIFIED_FACT"
    assert income_ev.conflict_detected is False
    assert income_ev.conflicting_values is None


def test_m5_evidence_conflict_resolution_discrepancy():
    harvester = EvidenceHarvester()
    # Profile claims ₹2,40,000, but official API returns ₹3,10,000
    profile = {"annual_income": 240000.0, "citizen_id": "demo-user"}
    api_data = {
        "provider": "MeeSeva Telangana",
        "endpoint_identifier": "APISETU_DIGILOCKER_INCER",
        "verification_status": "CONTRACT_VERIFIED",
        "payload": {"annual_income": 310000.0, "certificate_id": "TS-INC-2026-0091823"},
    }

    evidence = harvester.harvest(profile_data=profile, api_data=api_data)
    income_ev = evidence["annual_income"]

    # Statutory rule uses externally verified value
    assert income_ev.value == 310000.0
    assert income_ev.source == EvidenceSource.GOVERNMENT_API
    assert income_ev.fact_type == "EXTERNALLY_VERIFIED_FACT"
    assert income_ev.conflict_detected is True
    assert income_ev.conflicting_values is not None
    assert income_ev.conflicting_values["prior_value"] == 240000.0
    assert income_ev.conflicting_values["api_verified_value"] == 310000.0

    # Verify warning generated
    assert any("Evidence Conflict on 'annual_income'" in w for w in harvester.warnings)


def test_m5_eligibility_evaluation_with_conflicting_income():
    eligibility_tool = EligibilityCheckTool()

    # Telangana Youth Support income threshold is <= ₹2,50,000
    # demo-user profile has annual_income = ₹2,40,000 (would be ELIGIBLE without conflict)
    # Inject API verified income = ₹3,10,000
    conflicting_api_data = {
        "provider": "MeeSeva Telangana",
        "endpoint_identifier": "APISETU_DIGILOCKER_INCER",
        "verification_status": "CONTRACT_VERIFIED",
        "payload": {"annual_income": 310000.0},
    }

    result = eligibility_tool.execute(
        scheme_id="TELANGANA_YOUTH_SUPPORT",
        citizen_id="demo-user",
        api_data=conflicting_api_data,
    )

    assert result["status"] == "success"
    # Should now be NOT_ELIGIBLE due to externally verified income exceeding threshold
    assert result["eligibility_status"] == FinalEligibilityStatus.NOT_ELIGIBLE.value
    assert result["failed_rules_count"] >= 1

    # Warnings must contain the conflict explanation
    warnings = result["warnings"]
    assert any("Evidence Conflict on 'annual_income'" in w for w in warnings)
