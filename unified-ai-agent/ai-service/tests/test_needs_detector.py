"""Unit tests for Milestone 6 Need Detector."""
import pytest
from src.needs.models import NeedCategory, NeedType, NeedConfidenceLevel
from src.needs.detector import NeedDetector, RuleBasedNeedDetector


@pytest.fixture
def detector() -> NeedDetector:
    return NeedDetector()


def test_detect_single_employment_need(detector: NeedDetector):
    """Verify single employment need is detected accurately with high confidence."""
    text = "I recently lost my job and I am looking for a job to support myself."
    res = detector.detect(text)

    assert res.total_needs >= 1
    categories = [n.category for n in res.needs]
    assert NeedCategory.EMPLOYMENT in categories

    emp_need = next(n for n in res.needs if n.category == NeedCategory.EMPLOYMENT)
    assert emp_need.explicit_or_inferred == NeedType.EXPLICIT
    assert emp_need.confidence >= 0.8
    assert emp_need.confidence_level == NeedConfidenceLevel.HIGH
    assert emp_need.evidence_span != ""
    assert NeedCategory.EMPLOYMENT.value in res.suggested_scheme_queries


def test_detect_compound_four_needs(detector: NeedDetector):
    """Verify compound statement decomposing into 4 distinct needs."""
    text = "I lost my job, my income is very low, I have two children studying, and I need help with housing."
    res = detector.detect(text)

    categories = [n.category for n in res.needs]
    assert NeedCategory.EMPLOYMENT in categories
    assert NeedCategory.FINANCIAL_HARDSHIP in categories
    assert NeedCategory.EDUCATION in categories
    assert NeedCategory.HOUSING in categories
    assert res.total_needs == 4
    assert res.is_ambiguous is False

    # Suggested queries should be provided for all explicit needs
    for cat in [
        NeedCategory.EMPLOYMENT.value,
        NeedCategory.FINANCIAL_HARDSHIP.value,
        NeedCategory.EDUCATION.value,
        NeedCategory.HOUSING.value,
    ]:
        assert cat in res.suggested_scheme_queries


def test_detect_education_and_housing(detector: NeedDetector):
    """Verify education scholarship + housing/shelter needs."""
    text = "We need an educational scholarship for university college fees and an affordable house or pucca home."
    res = detector.detect(text)

    categories = [n.category for n in res.needs]
    assert NeedCategory.EDUCATION in categories
    assert NeedCategory.HOUSING in categories


def test_detect_healthcare_and_disability(detector: NeedDetector):
    """Verify healthcare medical support + disability assistance."""
    text = "My father is a disabled person with high hospital and medicine costs."
    res = detector.detect(text)

    categories = [n.category for n in res.needs]
    assert NeedCategory.HEALTHCARE in categories
    assert NeedCategory.DISABILITY_SUPPORT in categories


def test_detect_agriculture_and_senior(detector: NeedDetector):
    """Verify farmer crop assistance + elderly pension needs."""
    text = "I am a small farmer suffering crop failure, and my elderly mother needs an old age pension."
    res = detector.detect(text)

    categories = [n.category for n in res.needs]
    assert NeedCategory.AGRICULTURE in categories
    assert NeedCategory.SENIOR_CITIZEN_SUPPORT in categories


def test_detect_startup_and_skill_training(detector: NeedDetector):
    """Verify startup seed capital + vocational skill development."""
    text = "We are launching an early-stage startup looking for seed fund grant, and we need skill training for our interns."
    res = detector.detect(text)

    categories = [n.category for n in res.needs]
    assert NeedCategory.ENTREPRENEURSHIP in categories
    assert NeedCategory.SKILL_DEVELOPMENT in categories


def test_conversational_greeting_bypass(detector: NeedDetector):
    """Verify polite greetings do not trigger false positive needs or ambiguous alerts."""
    greetings = ["Hello", "Good morning!", "Hi assistant, how are you?"]
    for text in greetings:
        res = detector.detect(text)
        assert res.total_needs == 0
        assert res.is_ambiguous is False
        assert len(res.clarification_prompts) > 0
        assert "How can I help" in res.clarification_prompts[0]


def test_ambiguous_vague_assistance_request(detector: NeedDetector):
    """Verify ambiguous requests trigger UNKNOWN_AMBIGUOUS and NO suggested scheme queries."""
    vague_texts = [
        "I need help for my family.",
        "Can the government support me?",
        "I need some assistance please.",
    ]
    for text in vague_texts:
        res = detector.detect(text)
        assert res.is_ambiguous is True
        assert res.total_needs == 1
        assert res.needs[0].category == NeedCategory.UNKNOWN_AMBIGUOUS
        assert res.needs[0].confidence_level == NeedConfidenceLevel.LOW
        # Crucial architectural guard: Ambiguous queries must NEVER hallucinate or output suggested scheme queries
        assert res.suggested_scheme_queries == {}
        assert len(res.clarification_prompts) > 0


def test_empty_and_whitespace_input(detector: NeedDetector):
    """Verify empty or blank text produces 0 needs safely."""
    for empty in ["", "   ", "\n\t"]:
        res = detector.detect(empty)
        assert res.total_needs == 0
        assert res.needs == []
        assert res.is_ambiguous is False
