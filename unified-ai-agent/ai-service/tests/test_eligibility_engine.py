"""Unit and integration tests for the Deterministic Eligibility Engine resolution algorithm."""
from src.eligibility.engine import EligibilityEngine
from src.eligibility.models import (
    FinalEligibilityStatus,
    EligibilityEvidence,
    EvidenceSource,
)


def make_evidence_store(data: dict) -> dict:
    """Helper to construct an evidence store from key-values."""
    store = {}
    for k, v in data.items():
        store[k] = EligibilityEvidence(
            field_name=k,
            value=v,
            raw_value=v,
            source=EvidenceSource.CITIZEN_PROFILE,
            confidence=0.95,
            confidence_level="HIGH",
        )
    return store


def test_engine_sisfs_eligible():
    """Verify SISFS evaluates to ELIGIBLE when all 4 mandatory criteria are met."""
    engine = EligibilityEngine()
    evidence = make_evidence_store({
        "has_dpiit_recognition": True,
        "business_incorporated_years": 1,
        "previous_govt_monetary_support": 500000,
        "indian_promoter_shareholding": 60,
    })

    result = engine.evaluate(scheme_id="SISFS", evidence_store=evidence, citizen_id="test-founder")

    assert result.status == FinalEligibilityStatus.ELIGIBLE
    assert len(result.passed_rules) == 4
    assert len(result.failed_rules) == 0
    assert len(result.unknown_rules) == 0
    assert any("meets all 4 mandatory requirements" in r for r in result.summary_reasons)
    assert any("startupindia.gov.in" in s for s in result.next_steps)
    assert "Preliminary eligibility assessment" in result.disclaimer


def test_engine_sisfs_not_eligible_no_dpiit():
    """Verify SISFS evaluates to NOT_ELIGIBLE when DPIIT recognition is missing."""
    engine = EligibilityEngine()
    evidence = make_evidence_store({
        "has_dpiit_recognition": False,
        "business_incorporated_years": 1,
        "previous_govt_monetary_support": 0,
        "indian_promoter_shareholding": 100,
    })

    result = engine.evaluate(scheme_id="SISFS", evidence_store=evidence)

    assert result.status == FinalEligibilityStatus.NOT_ELIGIBLE
    assert len(result.failed_rules) == 1
    assert result.failed_rules[0].rule.field_name == "has_dpiit_recognition"
    assert any("does not meet 1 mandatory criterion" in r for r in result.summary_reasons)
    assert any("Page 2" in r for r in result.summary_reasons)
    assert any("Register your entity on the Startup India portal" in s for s in result.next_steps)


def test_engine_sisfs_not_eligible_over_two_years():
    """Verify SISFS evaluates to NOT_ELIGIBLE when incorporated > 2 years ago."""
    engine = EligibilityEngine()
    evidence = make_evidence_store({
        "has_dpiit_recognition": True,
        "business_incorporated_years": 3,  # > 2
        "previous_govt_monetary_support": 0,
        "indian_promoter_shareholding": 75,
    })

    result = engine.evaluate(scheme_id="SISFS", evidence_store=evidence)

    assert result.status == FinalEligibilityStatus.NOT_ELIGIBLE
    assert any(f.rule.field_name == "business_incorporated_years" for f in result.failed_rules)
    assert any("incorporated >2 years ago" in s for s in result.next_steps)


def test_engine_sisfs_not_eligible_prior_funding_exceeded():
    """Verify SISFS evaluates to NOT_ELIGIBLE when prior government funding > 10 Lakhs."""
    engine = EligibilityEngine()
    evidence = make_evidence_store({
        "has_dpiit_recognition": True,
        "business_incorporated_years": 1,
        "previous_govt_monetary_support": 1500000,  # 15 Lakhs > 10 Lakhs
        "indian_promoter_shareholding": 75,
    })

    result = engine.evaluate(scheme_id="SISFS", evidence_store=evidence)

    assert result.status == FinalEligibilityStatus.NOT_ELIGIBLE
    assert any(f.rule.field_name == "previous_govt_monetary_support" for f in result.failed_rules)


def test_engine_sisfs_not_eligible_low_indian_shareholding():
    """Verify SISFS evaluates to NOT_ELIGIBLE when Indian promoter shareholding < 51%."""
    engine = EligibilityEngine()
    evidence = make_evidence_store({
        "has_dpiit_recognition": True,
        "business_incorporated_years": 1,
        "previous_govt_monetary_support": 0,
        "indian_promoter_shareholding": 45,  # < 51%
    })

    result = engine.evaluate(scheme_id="SISFS", evidence_store=evidence)

    assert result.status == FinalEligibilityStatus.NOT_ELIGIBLE
    assert any(f.rule.field_name == "indian_promoter_shareholding" for f in result.failed_rules)


def test_engine_sisfs_insufficient_information():
    """Verify SISFS evaluates to INSUFFICIENT_INFORMATION when mandatory fields are missing."""
    engine = EligibilityEngine()
    # Missing previous_govt_monetary_support and indian_promoter_shareholding
    evidence = make_evidence_store({
        "has_dpiit_recognition": True,
        "business_incorporated_years": 1,
    })

    result = engine.evaluate(scheme_id="SISFS", evidence_store=evidence)

    assert result.status == FinalEligibilityStatus.INSUFFICIENT_INFORMATION
    assert len(result.passed_rules) == 2
    assert len(result.failed_rules) == 0
    assert len(result.unknown_rules) == 2
    assert any("lack verifiable evidence" in r for r in result.summary_reasons)
    assert any("Provide declaration of prior government monetary grants" in s for s in result.next_steps)
    assert any("Provide certified shareholding ledger" in s for s in result.next_steps)


def test_failure_precedence_over_insufficient_information():
    """Verify that if one mandatory rule FAILS and another is UNKNOWN, status is NOT_ELIGIBLE."""
    engine = EligibilityEngine()
    # has_dpiit_recognition fails, indian_promoter_shareholding is unknown
    evidence = make_evidence_store({
        "has_dpiit_recognition": False,  # FAIL
        "business_incorporated_years": 1,  # PASS
    })

    result = engine.evaluate(scheme_id="SISFS", evidence_store=evidence)

    # Definitive failure takes precedence over missing information
    assert result.status == FinalEligibilityStatus.NOT_ELIGIBLE
    assert len(result.failed_rules) == 1
    assert len(result.unknown_rules) == 2


def test_demo_scheme_youth_support_eligible():
    """Verify synthetic demo scheme evaluates to ELIGIBLE for qualifying youth."""
    engine = EligibilityEngine()
    evidence = make_evidence_store({
        "age": 25,
        "annual_income": 200000,
        "state": "Telangana",
    })

    result = engine.evaluate(scheme_id="TELANGANA_YOUTH_SUPPORT", evidence_store=evidence)

    assert result.status == FinalEligibilityStatus.ELIGIBLE
    assert result.is_synthetic_scheme is True
    assert len(result.passed_rules) == 4


def test_demo_scheme_youth_support_age_failed():
    """Verify synthetic demo scheme fails when citizen age > 35."""
    engine = EligibilityEngine()
    evidence = make_evidence_store({
        "age": 42,
        "annual_income": 150000,
        "state": "Telangana",
    })

    result = engine.evaluate(scheme_id="TELANGANA_YOUTH_SUPPORT", evidence_store=evidence)

    assert result.status == FinalEligibilityStatus.NOT_ELIGIBLE
    assert any(f.rule.rule_id == "TYS-02" for f in result.failed_rules)
