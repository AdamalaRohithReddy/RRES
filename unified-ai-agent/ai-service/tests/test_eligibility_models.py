"""Unit tests for eligibility data models, value normalizer, and comparison operators."""
import pytest
from src.eligibility.models import (
    RuleOperator,
    RuleStatus,
    FinalEligibilityStatus,
    EvidenceSource,
    EligibilityEvidence,
    EligibilityRule,
    RuleEvaluation,
    EligibilityResult,
)
from src.eligibility.normalizer import ValueNormalizer
from src.eligibility.evaluator import RuleEvaluator


def test_models_instantiation():
    """Verify all Pydantic models can be instantiated and serialized."""
    rule = EligibilityRule(
        rule_id="TEST-01",
        scheme_id="TEST_SCHEME",
        scheme_name="Test Welfare Scheme",
        field_name="age",
        operator=RuleOperator.GTE,
        threshold=18,
        description="Must be at least 18 years old",
        is_mandatory=True,
        is_synthetic=True,
        official_source="Test Specs",
    )
    assert rule.rule_id == "TEST-01"
    assert rule.operator == RuleOperator.GTE

    evidence = EligibilityEvidence(
        field_name="age",
        value=20,
        source=EvidenceSource.CITIZEN_PROFILE,
        confidence=0.9,
    )
    assert evidence.value == 20
    assert evidence.confidence == 0.9

    evaluation = RuleEvaluation(
        rule=rule,
        status=RuleStatus.PASS,
        citizen_value=20,
        threshold_value=18,
        reason="Age satisfied",
        evidence_used=evidence,
    )
    assert evaluation.status == RuleStatus.PASS

    result = EligibilityResult(
        status=FinalEligibilityStatus.ELIGIBLE,
        scheme_id="TEST_SCHEME",
        scheme_name="Test Welfare Scheme",
        passed_rules=[evaluation],
    )
    assert result.status == FinalEligibilityStatus.ELIGIBLE
    assert "Preliminary eligibility assessment" in result.disclaimer


def test_value_normalizer_currency():
    """Test parsing and normalising varied Indian currency formats."""
    assert ValueNormalizer.normalize_currency("Rs. 2,40,000") == 240000.0
    assert ValueNormalizer.normalize_currency("₹ 10 Lakhs") == 1000000.0
    assert ValueNormalizer.normalize_currency("10,00,000") == 1000000.0
    assert ValueNormalizer.normalize_currency("2.5 Lacs") == 250000.0
    assert ValueNormalizer.normalize_currency(150000) == 150000.0
    assert ValueNormalizer.normalize_currency("1.5 Crore") == 15000000.0
    assert ValueNormalizer.normalize_currency(None) is None
    assert ValueNormalizer.normalize_currency("invalid") is None


def test_value_normalizer_boolean():
    """Test normalizing boolean representations."""
    assert ValueNormalizer.normalize_boolean(True) is True
    assert ValueNormalizer.normalize_boolean("yes") is True
    assert ValueNormalizer.normalize_boolean("TRUE") is True
    assert ValueNormalizer.normalize_boolean("1") is True
    assert ValueNormalizer.normalize_boolean("recognized") is True

    assert ValueNormalizer.normalize_boolean(False) is False
    assert ValueNormalizer.normalize_boolean("no") is False
    assert ValueNormalizer.normalize_boolean("false") is False
    assert ValueNormalizer.normalize_boolean("0") is False
    assert ValueNormalizer.normalize_boolean(None) is None


def test_value_normalizer_number():
    """Test normalizing numeric strings and years."""
    assert ValueNormalizer.normalize_number("28") == 28.0
    assert ValueNormalizer.normalize_number("2 years") == 2.0
    assert ValueNormalizer.normalize_number(1.5) == 1.5
    assert ValueNormalizer.normalize_number(None) is None


def test_operator_execution():
    """Test deterministic evaluation of all supported comparison operators."""
    # GTE
    assert RuleEvaluator._execute_operator(RuleOperator.GTE, 25, 18) is True
    assert RuleEvaluator._execute_operator(RuleOperator.GTE, 18, 18) is True
    assert RuleEvaluator._execute_operator(RuleOperator.GTE, 17, 18) is False

    # LTE
    assert RuleEvaluator._execute_operator(RuleOperator.LTE, 2, 2) is True
    assert RuleEvaluator._execute_operator(RuleOperator.LTE, 3, 2) is False

    # GT & LT
    assert RuleEvaluator._execute_operator(RuleOperator.GT, 10, 5) is True
    assert RuleEvaluator._execute_operator(RuleOperator.LT, 5, 10) is True

    # EQ & NEQ
    assert RuleEvaluator._execute_operator(RuleOperator.EQ, "Telangana", "telangana") is True
    assert RuleEvaluator._execute_operator(RuleOperator.EQ, True, True) is True
    assert RuleEvaluator._execute_operator(RuleOperator.EQ, "Gujarat", "Telangana") is False
    assert RuleEvaluator._execute_operator(RuleOperator.NEQ, "General", "OBC") is True

    # IN & NOT_IN
    assert RuleEvaluator._execute_operator(RuleOperator.IN, "Telangana", ["Telangana", "Andhra Pradesh"]) is True
    assert RuleEvaluator._execute_operator(RuleOperator.IN, "Maharashtra", ["Telangana", "Andhra Pradesh"]) is False
    assert RuleEvaluator._execute_operator(RuleOperator.NOT_IN, "Maharashtra", ["Telangana", "Andhra Pradesh"]) is True

    # REQUIRED
    assert RuleEvaluator._execute_operator(RuleOperator.REQUIRED, "ABCDE1234F", None) is True
    assert RuleEvaluator._execute_operator(RuleOperator.REQUIRED, "", None) is False
    assert RuleEvaluator._execute_operator(RuleOperator.REQUIRED, None, None) is False
