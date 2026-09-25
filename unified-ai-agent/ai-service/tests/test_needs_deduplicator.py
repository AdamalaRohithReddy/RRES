"""Unit tests for Milestone 6 Need Deduplicator."""
from src.needs.models import Need, NeedCategory, NeedType, NeedConfidenceLevel
from src.needs.deduplicator import NeedDeduplicator


def test_deduplicate_empty_and_single():
    """Verify deduplication of empty list and single item."""
    assert NeedDeduplicator.deduplicate([]) == []

    single = Need(
        category=NeedCategory.EMPLOYMENT,
        description="Job search",
        confidence=0.85,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="unemployed",
    )
    res = NeedDeduplicator.deduplicate([single])
    assert len(res) == 1
    assert res[0].category == NeedCategory.EMPLOYMENT


def test_deduplicate_multiple_spans_same_category():
    """Verify consolidating multiple mentions of the same category merges spans and picks max confidence."""
    need1 = Need(
        category=NeedCategory.EMPLOYMENT,
        description="Citizen mentioned: unemployed",
        confidence=0.75,
        confidence_level=NeedConfidenceLevel.MEDIUM,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="unemployed",
    )
    need2 = Need(
        category=NeedCategory.EMPLOYMENT,
        description="Citizen mentioned: looking for a job",
        confidence=0.90,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="looking for a job",
    )

    merged = NeedDeduplicator.deduplicate([need1, need2])
    assert len(merged) == 1
    m = merged[0]
    assert m.category == NeedCategory.EMPLOYMENT
    assert m.confidence == 0.90
    assert m.confidence_level == NeedConfidenceLevel.HIGH
    assert "unemployed" in m.evidence_span
    assert "looking for a job" in m.evidence_span


def test_deduplicate_distinct_categories_preserved():
    """Verify distinct categories remain separate and sorted by confidence."""
    need_emp = Need(
        category=NeedCategory.EMPLOYMENT,
        description="Unemployed",
        confidence=0.80,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
    )
    need_edu = Need(
        category=NeedCategory.EDUCATION,
        description="Tuition fees",
        confidence=0.95,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
    )
    need_house = Need(
        category=NeedCategory.HOUSING,
        description="Rent support",
        confidence=0.70,
        confidence_level=NeedConfidenceLevel.MEDIUM,
        explicit_or_inferred=NeedType.EXPLICIT,
    )

    res = NeedDeduplicator.deduplicate([need_emp, need_edu, need_house])
    assert len(res) == 3
    # Sorted by confidence descending
    assert res[0].category == NeedCategory.EDUCATION
    assert res[1].category == NeedCategory.EMPLOYMENT
    assert res[2].category == NeedCategory.HOUSING
