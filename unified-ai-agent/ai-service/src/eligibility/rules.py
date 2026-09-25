"""Authoritative Scheme Rules Registry: official and synthetic scheme criteria."""
from typing import Dict, List, Optional, Any
from src.eligibility.models import EligibilityRule, RuleOperator


class SchemeNotFoundError(Exception):
    """Raised when a requested scheme identifier is not found in the registry."""
    pass


class SchemeRulesRegistry:
    """Registry maintaining structured, deterministic eligibility rules for government schemes."""

    # Grounded official rules derived from Guidelines_for_Startup_India_Seed_Fund_Scheme.pdf
    SISFS_RULES: List[EligibilityRule] = [
        EligibilityRule(
            rule_id="SISFS-01",
            scheme_id="SISFS",
            scheme_name="Startup India Seed Fund Scheme",
            field_name="has_dpiit_recognition",
            operator=RuleOperator.EQ,
            threshold=True,
            description="Startup must be recognized by DPIIT",
            is_mandatory=True,
            is_synthetic=False,
            official_source="Guidelines_for_Startup_India_Seed_Fund_Scheme.pdf",
            official_page=2,
            official_section="Eligibility Criteria for Startups",
            official_quote="A startup, recognized by DPIIT, incorporated not more than 2 years ago at the time of application.",
        ),
        EligibilityRule(
            rule_id="SISFS-02",
            scheme_id="SISFS",
            scheme_name="Startup India Seed Fund Scheme",
            field_name="business_incorporated_years",
            operator=RuleOperator.LTE,
            threshold=2,
            description="Startup must be incorporated not more than 2 years ago at application",
            is_mandatory=True,
            is_synthetic=False,
            official_source="Guidelines_for_Startup_India_Seed_Fund_Scheme.pdf",
            official_page=2,
            official_section="Eligibility Criteria for Startups",
            official_quote="incorporated not more than 2 years ago at the time of application.",
        ),
        EligibilityRule(
            rule_id="SISFS-03",
            scheme_id="SISFS",
            scheme_name="Startup India Seed Fund Scheme",
            field_name="previous_govt_monetary_support",
            operator=RuleOperator.LTE,
            threshold=1000000,
            description="Must not have received more than Rs. 10 Lakhs monetary support under other government schemes",
            is_mandatory=True,
            is_synthetic=False,
            official_source="Guidelines_for_Startup_India_Seed_Fund_Scheme.pdf",
            official_page=2,
            official_section="Eligibility Criteria for Startups",
            official_quote="The startup must not have received more than Rs 10 lakh of monetary support under any other Central or State Government scheme.",
        ),
        EligibilityRule(
            rule_id="SISFS-04",
            scheme_id="SISFS",
            scheme_name="Startup India Seed Fund Scheme",
            field_name="indian_promoter_shareholding",
            operator=RuleOperator.GTE,
            threshold=51,
            description="Shareholding by Indian promoters must be at least 51% at application",
            is_mandatory=True,
            is_synthetic=False,
            official_source="Guidelines_for_Startup_India_Seed_Fund_Scheme.pdf",
            official_page=3,
            official_section="Eligibility Criteria for Startups",
            official_quote="Shareholding by Indian promoters in the startup should be at least 51% at the time of application to the incubator.",
        ),
    ]

    # Controlled synthetic scheme for testing citizen socio-economic demographic attributes
    DEMO_TELANGANA_YOUTH_SUPPORT_RULES: List[EligibilityRule] = [
        EligibilityRule(
            rule_id="TYS-01",
            scheme_id="TELANGANA_YOUTH_SUPPORT",
            scheme_name="Telangana Youth Financial Support (Demo Scheme)",
            field_name="age",
            operator=RuleOperator.GTE,
            threshold=18,
            description="Applicant minimum age must be at least 18 years",
            is_mandatory=True,
            is_synthetic=True,
            official_source="Demo Specification for Socio-Economic Rules Verification",
            official_section="Demographic Criteria",
            official_quote="Applicant must be at least 18 years of age.",
        ),
        EligibilityRule(
            rule_id="TYS-02",
            scheme_id="TELANGANA_YOUTH_SUPPORT",
            scheme_name="Telangana Youth Financial Support (Demo Scheme)",
            field_name="age",
            operator=RuleOperator.LTE,
            threshold=35,
            description="Applicant maximum age must be 35 years or younger",
            is_mandatory=True,
            is_synthetic=True,
            official_source="Demo Specification for Socio-Economic Rules Verification",
            official_section="Demographic Criteria",
            official_quote="Applicant must be 35 years of age or younger.",
        ),
        EligibilityRule(
            rule_id="TYS-03",
            scheme_id="TELANGANA_YOUTH_SUPPORT",
            scheme_name="Telangana Youth Financial Support (Demo Scheme)",
            field_name="annual_income",
            operator=RuleOperator.LTE,
            threshold=250000,
            description="Annual household income must not exceed Rs. 2,50,000",
            is_mandatory=True,
            is_synthetic=True,
            official_source="Demo Specification for Socio-Economic Rules Verification",
            official_section="Income Criteria",
            official_quote="Total annual household income must not exceed Rs. 2,50,000.",
        ),
        EligibilityRule(
            rule_id="TYS-04",
            scheme_id="TELANGANA_YOUTH_SUPPORT",
            scheme_name="Telangana Youth Financial Support (Demo Scheme)",
            field_name="state",
            operator=RuleOperator.EQ,
            threshold="Telangana",
            description="Applicant state of residence must be Telangana",
            is_mandatory=True,
            is_synthetic=True,
            official_source="Demo Specification for Socio-Economic Rules Verification",
            official_section="Domicile Criteria",
            official_quote="Applicant must be a permanent resident of Telangana.",
        ),
    ]

    def __init__(self):
        self._schemes: Dict[str, Dict[str, Any]] = {
            "SISFS": {
                "scheme_id": "SISFS",
                "scheme_name": "Startup India Seed Fund Scheme",
                "description": "Financial assistance to early-stage DPIIT-recognized startups for proof of concept, prototype development, product trials, market entry, and commercialization.",
                "is_synthetic": False,
                "rules": self.SISFS_RULES,
            },
            "TELANGANA_YOUTH_SUPPORT": {
                "scheme_id": "TELANGANA_YOUTH_SUPPORT",
                "scheme_name": "Telangana Youth Financial Support (Demo Scheme)",
                "description": "Simulated state welfare scheme for young entrepreneurs and low-income youth residing in Telangana.",
                "is_synthetic": True,
                "rules": self.DEMO_TELANGANA_YOUTH_SUPPORT_RULES,
            },
        }

    def register_scheme(
        self,
        scheme_id: str,
        scheme_name: str,
        description: str,
        rules: List[EligibilityRule],
        is_synthetic: bool = False,
    ) -> None:
        """Register a new scheme and its deterministic rules."""
        norm_id = scheme_id.strip().upper()
        self._schemes[norm_id] = {
            "scheme_id": norm_id,
            "scheme_name": scheme_name,
            "description": description,
            "is_synthetic": is_synthetic,
            "rules": rules,
        }

    def get_scheme(self, scheme_id: str) -> Dict[str, Any]:
        """Fetch scheme metadata and rules by ID."""
        norm_id = (scheme_id or "").strip().upper()
        # Also support common aliases
        if norm_id in {"STARTUP_INDIA", "SEED_FUND", "STARTUP_INDIA_SEED_FUND"}:
            norm_id = "SISFS"
        elif norm_id in {"TYS", "TELANGANA_YOUTH"}:
            norm_id = "TELANGANA_YOUTH_SUPPORT"

        scheme = self._schemes.get(norm_id)
        if not scheme:
            available = ", ".join(self._schemes.keys())
            raise SchemeNotFoundError(
                f"Scheme '{scheme_id}' is not recognized. Available schemes: {available}"
            )
        return scheme

    def get_rules(self, scheme_id: str) -> List[EligibilityRule]:
        """Get the rule set for a scheme."""
        return self.get_scheme(scheme_id)["rules"]

    def list_schemes(self) -> List[Dict[str, Any]]:
        """List all registered schemes."""
        return [
            {
                "scheme_id": s["scheme_id"],
                "scheme_name": s["scheme_name"],
                "description": s["description"],
                "is_synthetic": s["is_synthetic"],
                "rule_count": len(s["rules"]),
            }
            for s in self._schemes.values()
        ]
