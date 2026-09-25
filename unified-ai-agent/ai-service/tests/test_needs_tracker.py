"""Unit tests for Milestone 6 Need Tracker (Cumulative Multi-Turn Session Tracking)."""
from src.needs.models import Need, NeedCategory, NeedType, NeedConfidenceLevel
from src.needs.tracker import NeedTracker


def test_tracker_initialization_empty():
    """Verify empty tracker initialization."""
    tracker = NeedTracker()
    assert tracker.get_active_needs() == []
    assert tracker.get_categories() == []


def test_tracker_multi_turn_accumulation():
    """Verify Turn 1: EMPLOYMENT, Turn 2: + EDUCATION accumulates to [EMPLOYMENT, EDUCATION]."""
    tracker = NeedTracker()

    # Turn 1
    turn1_need = Need(
        category=NeedCategory.EMPLOYMENT,
        description="Lost job",
        confidence=0.90,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="lost my job",
    )
    tracker.add_needs([turn1_need])

    assert len(tracker.get_active_needs()) == 1
    assert NeedCategory.EMPLOYMENT in tracker.get_categories()

    # Turn 2
    turn2_need = Need(
        category=NeedCategory.EDUCATION,
        description="Children school fees",
        confidence=0.88,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="school fees",
    )
    tracker.add_needs([turn2_need])

    active = tracker.get_active_needs()
    assert len(active) == 2
    categories = tracker.get_categories()
    assert NeedCategory.EMPLOYMENT in categories
    assert NeedCategory.EDUCATION in categories


def test_tracker_same_category_update_merges():
    """Verify adding the same category in subsequent turns merges information rather than duplicating."""
    tracker = NeedTracker()

    need1 = Need(
        category=NeedCategory.HOUSING,
        description="Looking for shelter",
        confidence=0.80,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="need a house",
    )
    tracker.add_needs([need1])
    assert len(tracker.get_active_needs()) == 1

    need2 = Need(
        category=NeedCategory.HOUSING,
        description="Affordable rent",
        confidence=0.92,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="affordable rent",
    )
    tracker.add_needs([need2])

    assert len(tracker.get_active_needs()) == 1
    merged = tracker.get_active_needs()[0]
    assert merged.confidence == 0.92
    assert "need a house" in merged.evidence_span
    assert "affordable rent" in merged.evidence_span


def test_tracker_ignores_ambiguous_when_concrete_needs_present():
    """Verify UNKNOWN_AMBIGUOUS does not overwrite or dilute concrete domain needs."""
    tracker = NeedTracker()

    concrete = Need(
        category=NeedCategory.HEALTHCARE,
        description="Medical bill",
        confidence=0.85,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
        evidence_span="medical bills",
    )
    tracker.add_needs([concrete])

    ambiguous = Need(
        category=NeedCategory.UNKNOWN_AMBIGUOUS,
        description="General assistance",
        confidence=0.35,
        confidence_level=NeedConfidenceLevel.LOW,
        explicit_or_inferred=NeedType.EXPLICIT,
    )
    tracker.add_needs([ambiguous])

    # Should still only have HEALTHCARE
    assert len(tracker.get_active_needs()) == 1
    assert tracker.get_categories() == [NeedCategory.HEALTHCARE]


def test_tracker_clear_and_to_dict():
    """Verify reset and dictionary serialization."""
    tracker = NeedTracker()
    need = Need(
        category=NeedCategory.AGRICULTURE,
        description="Crop loan",
        confidence=0.80,
        confidence_level=NeedConfidenceLevel.HIGH,
        explicit_or_inferred=NeedType.EXPLICIT,
    )
    tracker.add_needs([need])
    dicts = tracker.to_dict_list()
    assert len(dicts) == 1
    assert dicts[0]["category"] == "agriculture"

    tracker.clear()
    assert len(tracker.get_active_needs()) == 0
