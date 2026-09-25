"""Unit tests for the Scheme Rules Registry and official rule grounding."""
import pytest
from src.eligibility.rules import SchemeRulesRegistry, SchemeNotFoundError
from src.eligibility.models import EligibilityRule, RuleOperator


def test_registry_scheme_discovery():
    """Verify registry lists official and synthetic schemes."""
    registry = SchemeRulesRegistry()
    schemes = registry.list_schemes()
    assert len(schemes) >= 2

    scheme_ids = [s["scheme_id"] for s in schemes]
    assert "SISFS" in scheme_ids
    assert "TELANGANA_YOUTH_SUPPORT" in scheme_ids


def test_sisfs_official_grounding():
    """Verify Startup India Seed Fund Scheme rules are grounded in official PDF guidelines."""
    registry = SchemeRulesRegistry()
    rules = registry.get_rules("SISFS")
    assert len(rules) == 4

    rule_map = {r.rule_id: r for r in rules}

    # DPIIT recognition
    r1 = rule_map["SISFS-01"]
    assert r1.field_name == "has_dpiit_recognition"
    assert r1.threshold is True
    assert r1.is_mandatory is True
    assert r1.is_synthetic is False
    assert r1.official_page == 2
    assert "Guidelines_for_Startup_India_Seed_Fund_Scheme.pdf" in r1.official_source
    assert "recognized by DPIIT" in r1.official_quote

    # Age <= 2 years
    r2 = rule_map["SISFS-02"]
    assert r2.field_name == "business_incorporated_years"
    assert r2.operator == RuleOperator.LTE
    assert r2.threshold == 2
    assert r2.official_page == 2

    # Prior funding <= 10 Lakhs
    r3 = rule_map["SISFS-03"]
    assert r3.field_name == "previous_govt_monetary_support"
    assert r3.operator == RuleOperator.LTE
    assert r3.threshold == 1000000
    assert r3.official_page == 2

    # Indian promoter shareholding >= 51%
    r4 = rule_map["SISFS-04"]
    assert r4.field_name == "indian_promoter_shareholding"
    assert r4.operator == RuleOperator.GTE
    assert r4.threshold == 51
    assert r4.official_page == 3


def test_synthetic_scheme_metadata():
    """Verify demo scheme is explicitly tagged as synthetic."""
    registry = SchemeRulesRegistry()
    scheme = registry.get_scheme("TELANGANA_YOUTH_SUPPORT")
    assert scheme["is_synthetic"] is True
    rules = scheme["rules"]
    for r in rules:
        assert r.is_synthetic is True


def test_scheme_not_found_handling():
    """Verify error raised on unknown scheme."""
    registry = SchemeRulesRegistry()
    with pytest.raises(SchemeNotFoundError) as exc_info:
        registry.get_rules("NON_EXISTENT_SCHEME")
    assert "Available schemes:" in str(exc_info.value)


def test_scheme_alias_matching():
    """Verify case-insensitivity and alias resolution."""
    registry = SchemeRulesRegistry()
    s1 = registry.get_scheme("sisfs")
    assert s1["scheme_id"] == "SISFS"

    s2 = registry.get_scheme("STARTUP_INDIA")
    assert s2["scheme_id"] == "SISFS"

    s3 = registry.get_scheme("TYS")
    assert s3["scheme_id"] == "TELANGANA_YOUTH_SUPPORT"


def test_custom_scheme_registration():
    """Verify dynamic scheme registration at runtime."""
    registry = SchemeRulesRegistry()
    custom_rules = [
        EligibilityRule(
            rule_id="CUSTOM-01",
            scheme_id="FARMER_GRANT",
            scheme_name="Farmer Equipment Grant",
            field_name="landholding_acres",
            operator=RuleOperator.LTE,
            threshold=5.0,
            description="Landholding must not exceed 5 acres",
            official_source="Demo Agriculture Policy",
        )
    ]
    registry.register_scheme(
        scheme_id="FARMER_GRANT",
        scheme_name="Farmer Equipment Grant",
        description="Subsidy for small and marginal farmers",
        rules=custom_rules,
    )

    scheme = registry.get_scheme("FARMER_GRANT")
    assert scheme["scheme_name"] == "Farmer Equipment Grant"
    assert len(registry.get_rules("FARMER_GRANT")) == 1
