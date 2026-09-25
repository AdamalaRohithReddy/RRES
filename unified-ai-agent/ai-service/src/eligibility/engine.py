"""Deterministic Eligibility Engine: authoritative resolution of scheme eligibility."""
from typing import Dict, List, Optional
from src.eligibility.models import (
    EligibilityEvidence,
    EligibilityResult,
    FinalEligibilityStatus,
    RuleEvaluation,
    RuleStatus,
)
from src.eligibility.rules import SchemeRulesRegistry, SchemeNotFoundError
from src.eligibility.evaluator import RuleEvaluator


class EligibilityEngine:
    """Core deterministic engine that computes scheme eligibility outcomes based on evidence.

    Follows the core principle:
    "Eligibility Engine determines eligibility. The Agent orchestrates. The LLM explains the result."
    """

    def __init__(self, registry: Optional[SchemeRulesRegistry] = None):
        self.registry = registry or SchemeRulesRegistry()

    def evaluate(
        self,
        scheme_id: str,
        evidence_store: Dict[str, EligibilityEvidence],
        citizen_id: Optional[str] = None,
        additional_warnings: Optional[List[str]] = None,
    ) -> EligibilityResult:
        """Evaluate a scheme against available evidence and produce an authoritative outcome."""
        scheme_meta = self.registry.get_scheme(scheme_id)
        rules = scheme_meta["rules"]

        passed_rules: List[RuleEvaluation] = []
        failed_rules: List[RuleEvaluation] = []
        unknown_rules: List[RuleEvaluation] = []

        # Evaluate each rule deterministically
        for rule in rules:
            evaluation = RuleEvaluator.evaluate(rule, evidence_store)
            if evaluation.status == RuleStatus.PASS:
                passed_rules.append(evaluation)
            elif evaluation.status == RuleStatus.FAIL:
                failed_rules.append(evaluation)
            else:
                unknown_rules.append(evaluation)

        # Count mandatory rules
        mandatory_rules = [r for r in rules if r.is_mandatory]
        mandatory_fails = [e for e in failed_rules if e.rule.is_mandatory]
        mandatory_unknowns = [e for e in unknown_rules if e.rule.is_mandatory]

        # Resolution Algorithm
        if len(mandatory_fails) > 0:
            final_status = FinalEligibilityStatus.NOT_ELIGIBLE
        elif len(mandatory_unknowns) > 0:
            final_status = FinalEligibilityStatus.INSUFFICIENT_INFORMATION
        else:
            final_status = FinalEligibilityStatus.ELIGIBLE

        # Build summary reasons
        summary_reasons = self._build_summary_reasons(
            final_status=final_status,
            scheme_name=scheme_meta["scheme_name"],
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            unknown_rules=unknown_rules,
            is_synthetic=scheme_meta["is_synthetic"],
        )

        # Build actionable next steps
        next_steps = self._build_next_steps(
            final_status=final_status,
            scheme_id=scheme_meta["scheme_id"],
            failed_rules=failed_rules,
            unknown_rules=unknown_rules,
        )

        # Aggregate warnings
        all_warnings: List[str] = []
        if additional_warnings:
            all_warnings.extend(additional_warnings)
        for e in failed_rules + unknown_rules + passed_rules:
            if e.discrepancy_warning:
                all_warnings.append(e.discrepancy_warning)

        return EligibilityResult(
            status=final_status,
            scheme_id=scheme_meta["scheme_id"],
            scheme_name=scheme_meta["scheme_name"],
            citizen_id=citizen_id,
            total_rules=len(rules),
            mandatory_rules=len(mandatory_rules),
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            unknown_rules=unknown_rules,
            summary_reasons=summary_reasons,
            next_steps=next_steps,
            warnings=all_warnings,
            is_synthetic_scheme=scheme_meta["is_synthetic"],
        )

    def _build_summary_reasons(
        self,
        final_status: FinalEligibilityStatus,
        scheme_name: str,
        passed_rules: List[RuleEvaluation],
        failed_rules: List[RuleEvaluation],
        unknown_rules: List[RuleEvaluation],
        is_synthetic: bool,
    ) -> List[str]:
        """Construct deterministic, verifiable human-readable explanation bullet points."""
        reasons: List[str] = []

        if is_synthetic:
            reasons.append("DEMO SCHEME ASSESSMENT: Evaluated using simulated developmental criteria.")

        if final_status == FinalEligibilityStatus.ELIGIBLE:
            reasons.append(f"Candidate meets all {len(passed_rules)} mandatory requirements for {scheme_name}.")
            for p in passed_rules:
                reasons.append(f"PASS: {p.rule.description} (Observed value: {p.citizen_value}).")

        elif final_status == FinalEligibilityStatus.NOT_ELIGIBLE:
            reasons.append(
                f"Candidate does not meet {len(failed_rules)} mandatory criterion/criteria for {scheme_name}."
            )
            for f in failed_rules:
                src_cite = f" [Source: {f.rule.official_source}"
                if f.rule.official_page:
                    src_cite += f", Page {f.rule.official_page}"
                src_cite += "]"
                reasons.append(
                    f"FAIL: {f.rule.description}. Observed: {f.citizen_value}, "
                    f"Required: {f.rule.operator.value} {f.rule.threshold}.{src_cite}"
                )

        elif final_status == FinalEligibilityStatus.INSUFFICIENT_INFORMATION:
            reasons.append(
                f"Eligibility cannot be confirmed because {len(unknown_rules)} mandatory criterion/criteria "
                f"lack verifiable evidence or require official documentation."
            )
            for u in unknown_rules:
                reasons.append(f"UNKNOWN: {u.rule.description} (field: '{u.rule.field_name}').")

        return reasons

    def _build_next_steps(
        self,
        final_status: FinalEligibilityStatus,
        scheme_id: str,
        failed_rules: List[RuleEvaluation],
        unknown_rules: List[RuleEvaluation],
    ) -> List[str]:
        """Generate clear, actionable next steps for citizen guidance."""
        steps: List[str] = []

        if final_status == FinalEligibilityStatus.ELIGIBLE:
            if scheme_id == "SISFS":
                steps.append("Apply through the official Startup India Seed Fund portal (startupindia.gov.in).")
                steps.append("Select up to 3 approved incubators in order of preference.")
                steps.append("Keep DPIIT certificate, incorporation certificate, and Indian shareholding proofs ready.")
            else:
                steps.append("Proceed to complete the online scheme application form.")
                steps.append("Carry original identity and residential proofs for verification.")

        elif final_status == FinalEligibilityStatus.NOT_ELIGIBLE:
            for f in failed_rules:
                if f.rule.field_name == "has_dpiit_recognition":
                    steps.append("Register your entity on the Startup India portal to obtain official DPIIT recognition.")
                elif f.rule.field_name == "business_incorporated_years":
                    steps.append("Since the entity was incorporated >2 years ago, explore alternate growth-stage grant or loan schemes.")
                elif f.rule.field_name == "previous_govt_monetary_support":
                    steps.append("Review whether prior funding exceeded Rs. 10 Lakhs; explore schemes designed for later-stage ventures.")
                elif f.rule.field_name == "indian_promoter_shareholding":
                    steps.append("Review your cap table; SISFS requires minimum 51% shareholding by Indian promoters at application.")
                elif f.rule.field_name == "annual_income":
                    steps.append("Income exceeds the maximum limit for this specific welfare scheme. Check general-category schemes.")
                elif f.rule.field_name == "age":
                    steps.append("Applicant age falls outside the eligible bracket for this youth-specific program.")
            steps.append("Inquire with support helpdesk if you believe official records contain typographical errors.")

        elif final_status == FinalEligibilityStatus.INSUFFICIENT_INFORMATION:
            for u in unknown_rules:
                if u.rule.field_name == "has_dpiit_recognition":
                    steps.append("Provide your DPIIT Recognition Number or upload your Startup India Certificate.")
                elif u.rule.field_name == "business_incorporated_years":
                    steps.append("Upload Certificate of Incorporation (MCA/RoC) to verify date of incorporation.")
                elif u.rule.field_name == "previous_govt_monetary_support":
                    steps.append("Provide declaration of prior government monetary grants received to date.")
                elif u.rule.field_name == "indian_promoter_shareholding":
                    steps.append("Provide certified shareholding ledger or cap table confirming Indian promoter ownership percentage.")
                elif u.rule.field_name == "annual_income":
                    steps.append("Upload an authorized Income Certificate or latest ITR acknowledgement.")
                elif u.rule.field_name in {"age", "state"}:
                    steps.append("Upload an identity/residence document (Aadhaar or domicile certificate) to verify age/residence.")
            steps.append("Run check_eligibility again after providing the requested documents.")

        return steps
