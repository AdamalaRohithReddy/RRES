"""Deterministic rule evaluator for individual eligibility conditions."""
from typing import Dict, Any, Optional
from src.eligibility.models import (
    EligibilityRule,
    EligibilityEvidence,
    RuleEvaluation,
    RuleOperator,
    RuleStatus,
)
from src.eligibility.normalizer import ValueNormalizer


class RuleEvaluator:
    """Evaluates an individual EligibilityRule against available evidence."""

    @classmethod
    def evaluate(
        cls,
        rule: EligibilityRule,
        evidence_store: Dict[str, EligibilityEvidence],
    ) -> RuleEvaluation:
        """Evaluate a single rule against the provided evidence store."""
        evidence = evidence_store.get(rule.field_name)

        # 1. Missing evidence guard
        if evidence is None or evidence.value is None:
            return RuleEvaluation(
                rule=rule,
                status=RuleStatus.UNKNOWN,
                citizen_value=None,
                threshold_value=rule.threshold,
                reason=(
                    f"Missing evidence for required field '{rule.field_name}': {rule.description}. "
                    f"Official verification required."
                ),
                evidence_used=None,
                missing_evidence=True,
            )

        # 2. Confidence guard: unreliable extraction (<0.50) cannot be used
        if evidence.confidence < 0.50 or evidence.confidence_level == "UNRELIABLE":
            return RuleEvaluation(
                rule=rule,
                status=RuleStatus.UNKNOWN,
                citizen_value=evidence.value,
                threshold_value=rule.threshold,
                reason=(
                    f"Unreliable evidence for '{rule.field_name}' (confidence {evidence.confidence:.2f} < 0.50). "
                    f"Requires clear supporting document."
                ),
                evidence_used=evidence,
                missing_evidence=True,
            )

        # 3. Normalization for comparison
        raw_val = evidence.value
        norm_val, success = ValueNormalizer.normalize_for_comparison(raw_val, type(rule.threshold))

        if not success or norm_val is None:
            return RuleEvaluation(
                rule=rule,
                status=RuleStatus.UNKNOWN,
                citizen_value=raw_val,
                threshold_value=rule.threshold,
                reason=(
                    f"Could not normalize value '{raw_val}' for comparison against {rule.threshold} "
                    f"for rule '{rule.description}'."
                ),
                evidence_used=evidence,
                missing_evidence=True,
            )

        # 4. Operator execution
        passed = cls._execute_operator(rule.operator, norm_val, rule.threshold)

        if passed:
            reason = (
                f"Requirement satisfied: {rule.description}. "
                f"Observed value ({norm_val}) satisfies condition ({rule.operator.value} {rule.threshold})."
            )
            return RuleEvaluation(
                rule=rule,
                status=RuleStatus.PASS,
                citizen_value=norm_val,
                threshold_value=rule.threshold,
                reason=reason,
                evidence_used=evidence,
                missing_evidence=False,
            )
        else:
            reason = (
                f"Requirement not satisfied: {rule.description}. "
                f"Observed value ({norm_val}) does not meet condition ({rule.operator.value} {rule.threshold})."
            )
            return RuleEvaluation(
                rule=rule,
                status=RuleStatus.FAIL,
                citizen_value=norm_val,
                threshold_value=rule.threshold,
                reason=reason,
                evidence_used=evidence,
                missing_evidence=False,
            )

    @classmethod
    def _execute_operator(cls, op: RuleOperator, actual: Any, threshold: Any) -> bool:
        """Execute the comparison operator deterministically."""
        try:
            if op == RuleOperator.GTE:
                return float(actual) >= float(threshold)
            elif op == RuleOperator.LTE:
                return float(actual) <= float(threshold)
            elif op == RuleOperator.GT:
                return float(actual) > float(threshold)
            elif op == RuleOperator.LT:
                return float(actual) < float(threshold)
            elif op == RuleOperator.EQ:
                if isinstance(actual, str) and isinstance(threshold, str):
                    return actual.strip().lower() == threshold.strip().lower()
                return actual == threshold
            elif op == RuleOperator.NEQ:
                if isinstance(actual, str) and isinstance(threshold, str):
                    return actual.strip().lower() != threshold.strip().lower()
                return actual != threshold
            elif op == RuleOperator.IN:
                if isinstance(threshold, (list, tuple, set)):
                    if isinstance(actual, str):
                        lower_list = [str(x).strip().lower() for x in threshold]
                        return actual.strip().lower() in lower_list
                    return actual in threshold
                return False
            elif op == RuleOperator.NOT_IN:
                if isinstance(threshold, (list, tuple, set)):
                    if isinstance(actual, str):
                        lower_list = [str(x).strip().lower() for x in threshold]
                        return actual.strip().lower() not in lower_list
                    return actual not in threshold
                return True
            elif op == RuleOperator.REQUIRED:
                return actual is not None and str(actual).strip() != ""
            return False
        except (ValueError, TypeError):
            return False
