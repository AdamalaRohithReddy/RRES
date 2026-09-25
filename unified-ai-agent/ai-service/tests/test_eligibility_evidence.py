"""Unit tests for EvidenceHarvester and multi-source conflict reconciliation."""
from src.eligibility.evidence import EvidenceHarvester
from src.eligibility.models import EvidenceSource
from src.document_ai.models import (
    DocumentAnalysisResult,
    DocumentType,
    ExtractedField,
    ConfidenceLevel,
)


def test_harvest_from_citizen_profile():
    """Verify harvesting attributes from citizen profile repository."""
    profile_data = {
        "citizen_id": "demo-user",
        "name": "Ramesh Kumar",
        "age": 28,
        "annual_income": 240000,
        "state": "Telangana",
        "has_dpiit_recognition": True,
    }
    harvester = EvidenceHarvester()
    evidence = harvester.harvest(profile_data=profile_data)

    assert "age" in evidence
    assert evidence["age"].value == 28
    assert evidence["age"].source == EvidenceSource.CITIZEN_PROFILE
    assert evidence["age"].confidence == 0.90
    assert evidence["has_dpiit_recognition"].value is True


def test_harvest_from_document_ai():
    """Verify harvesting facts from Document AI analysis result."""
    doc_res = DocumentAnalysisResult(
        status="success",
        apparent_document_type=DocumentType.INCOME_CERTIFICATE,
        document_type_confidence=0.92,
        ocr_used=False,
        fields={
            "annual_income": ExtractedField(
                field="annual_income",
                value=150000,
                confidence=0.95,
                confidence_level=ConfidenceLevel.HIGH,
                page=1,
                source_text="Annual Income: Rs. 1,50,000",
            ),
            "state": ExtractedField(
                field="state",
                value="Telangana",
                confidence=0.88,
                confidence_level=ConfidenceLevel.HIGH,
                page=1,
                source_text="State: Telangana",
            ),
        },
    )

    harvester = EvidenceHarvester()
    evidence = harvester.harvest(document_data=doc_res)

    assert "annual_income" in evidence
    assert evidence["annual_income"].value == 150000
    assert evidence["annual_income"].source == EvidenceSource.DOCUMENT_AI
    assert evidence["annual_income"].confidence == 0.95
    assert evidence["annual_income"].page == 1


def test_conflict_reconciliation_high_confidence_document_prioritized():
    """Verify high-confidence document evidence overrides profile with warning."""
    profile_data = {
        "citizen_id": "demo-user",
        "annual_income": 240000,
    }
    doc_data = {
        "apparent_document_type": "income_certificate",
        "fields": {
            "annual_income": {
                "value": 150000,
                "confidence": 0.95,
                "confidence_level": "HIGH",
                "page": 1,
                "source_text": "Rs. 1,50,000",
            }
        },
    }

    harvester = EvidenceHarvester()
    evidence = harvester.harvest(profile_data=profile_data, document_data=doc_data)

    # Document value 150,000 should override profile value 240,000
    assert evidence["annual_income"].value == 150000
    assert evidence["annual_income"].source == EvidenceSource.DOCUMENT_AI
    assert len(harvester.warnings) >= 1
    assert "Evidence Conflict on 'annual_income'" in harvester.warnings[0]
    assert "Document evidence prioritized" in harvester.warnings[0]


def test_conflict_reconciliation_uncertain_document_retains_profile():
    """Verify uncertain document evidence (<0.85) retains profile with discrepancy warning."""
    profile_data = {
        "citizen_id": "demo-user",
        "annual_income": 240000,
    }
    doc_data = {
        "apparent_document_type": "income_certificate",
        "fields": {
            "annual_income": {
                "value": 180000,
                "confidence": 0.65,
                "confidence_level": "UNCERTAIN",
                "page": 1,
            }
        },
    }

    harvester = EvidenceHarvester()
    evidence = harvester.harvest(profile_data=profile_data, document_data=doc_data)

    # Profile value retained due to uncertainty
    assert evidence["annual_income"].value == 240000
    assert evidence["annual_income"].source == EvidenceSource.CITIZEN_PROFILE
    assert len(harvester.warnings) >= 1
    assert "Evidence Discrepancy on 'annual_income'" in harvester.warnings[0]


def test_conflict_reconciliation_unreliable_document_ignored():
    """Verify unreliable document extraction (<0.50) is ignored."""
    profile_data = {
        "citizen_id": "demo-user",
        "annual_income": 240000,
    }
    doc_data = {
        "apparent_document_type": "unknown",
        "fields": {
            "annual_income": {
                "value": None,
                "confidence": 0.20,
                "confidence_level": "UNRELIABLE",
            }
        },
    }

    harvester = EvidenceHarvester()
    evidence = harvester.harvest(profile_data=profile_data, document_data=doc_data)

    assert evidence["annual_income"].value == 240000
    assert any("Ignored unreliable document extraction" in w for w in harvester.warnings)


def test_user_overrides_priority():
    """Verify caller override_fields take highest precedence."""
    profile_data = {"age": 28}
    doc_data = {
        "fields": {
            "age": {"value": 29, "confidence": 0.90, "confidence_level": "HIGH"}
        }
    }
    overrides = {"age": 30}

    harvester = EvidenceHarvester()
    evidence = harvester.harvest(
        profile_data=profile_data,
        document_data=doc_data,
        user_overrides=overrides,
    )

    assert evidence["age"].value == 30
    assert evidence["age"].source == EvidenceSource.USER_INPUT
