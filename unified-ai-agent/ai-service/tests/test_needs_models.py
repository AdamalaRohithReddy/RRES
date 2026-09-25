"""Unit tests for Milestone 6 Need Models and Enums."""
import pytest
from pydantic import ValidationError

from src.needs.models import (
    NeedCategory,
    NeedType,
    NeedConfidenceLevel,
    Need,
    MultiNeedResult,
    DISCLAIMER_TEXT,
)


def test_need_category_enum_values():
    """Verify standard domain categories are defined."""
    assert NeedCategory.EMPLOYMENT.value == "employment"
    assert NeedCategory.EDUCATION.value == "education"
    assert NeedCategory.FINANCIAL_HARDSHIP.value == "financial_hardship"
    assert NeedCategory.HOUSING.value == "housing"
    assert NeedCategory.HEALTHCARE.value == "healthcare"
    assert NeedCategory.ENTREPRENEURSHIP.value == "entrepreneurship"
    assert NeedCategory.UNKNOWN_AMBIGUOUS.value == "unknown_ambiguous"
    assert len(NeedCategory) >= 15


def test_need_type_enum():
    """Verify need types."""
    assert NeedType.EXPLICIT.value == "EXPLICIT"
    assert NeedType.INFERRED.value == "INFERRED"


def test_need_confidence_level_enum():
    """Verify confidence levels."""
    assert NeedConfidenceLevel.HIGH.value == "HIGH"
    assert NeedConfidenceLevel.MEDIUM.value == "MEDIUM"
    assert NeedConfidenceLevel.LOW.value == "LOW"


def test_need_model_creation():
    """Verify creation of a valid Need instance."""
    need = Need(
        category=NeedCategory.EMPLOYMENT,
        description="Citizen reported job loss and seeking employment",
        confidence=0.92,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="I lost my job yesterday",
        suggested_scheme_query="employment assistance job placement unemployment support",
    )
    assert need.category == NeedCategory.EMPLOYMENT
    assert need.confidence == 0.92
    assert need.confidence_level == NeedConfidenceLevel.HIGH
    assert need.explicit_or_inferred == NeedType.EXPLICIT
    assert need.evidence_span == "I lost my job yesterday"
    assert "employment assistance" in need.suggested_scheme_query


def test_need_model_confidence_validation():
    """Verify confidence must be bounded between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        Need(
            category=NeedCategory.HOUSING,
            description="Housing help",
            confidence=1.5,
            confidence_level=NeedConfidenceLevel.HIGH,
            explicit_or_inferred=NeedType.EXPLICIT,
        )

    with pytest.raises(ValidationError):
        Need(
            category=NeedCategory.HOUSING,
            description="Housing help",
            confidence=-0.1,
            confidence_level=NeedConfidenceLevel.LOW,
            explicit_or_inferred=NeedType.EXPLICIT,
        )


def test_multi_need_result_defaults():
    """Verify MultiNeedResult default values and mandatory disclaimer."""
    res = MultiNeedResult()
    assert res.needs == []
    assert res.total_needs == 0
    assert res.is_ambiguous is False
    assert res.clarification_prompts == []
    assert res.suggested_scheme_queries == {}
    assert res.disclaimer == DISCLAIMER_TEXT
    assert "does NOT determine eligibility" in res.disclaimer


def test_multi_need_result_serialization():
    """Verify MultiNeedResult serializes correctly to dict."""
    need = Need(
        category=NeedCategory.EDUCATION,
        description="Education fees support",
        confidence=0.88,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="school fees",
    )
    result = MultiNeedResult(
        needs=[need],
        total_needs=1,
        suggested_scheme_queries={"education": "education scholarship fee waiver scheme"},
    )
    data = result.model_dump()
    assert data["total_needs"] == 1
    assert data["needs"][0]["category"] == "education"
    assert data["needs"][0]["evidence_span"] == "school fees"
    assert "education" in data["suggested_scheme_queries"]
    assert data["disclaimer"] == DISCLAIMER_TEXT
