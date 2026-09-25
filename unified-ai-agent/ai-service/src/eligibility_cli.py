"""Standalone Command Line Interface for Deterministic Scheme Eligibility Verification."""
import argparse
import json
import sys
from pathlib import Path

from src.tools.eligibility_tool import EligibilityCheckTool
from src.eligibility.rules import SchemeRulesRegistry


def format_cli_output(res: dict) -> str:
    """Format eligibility evaluation results into clear, readable terminal output."""
    status = res.get("eligibility_status", "UNKNOWN")
    scheme_name = res.get("scheme_name", res.get("scheme_id", "Unknown Scheme"))
    citizen_id = res.get("citizen_id", "N/A")

    status_colors = {
        "ELIGIBLE": "\033[92m[ELIGIBLE]\033[0m",
        "NOT_ELIGIBLE": "\033[91m[NOT ELIGIBLE]\033[0m",
        "INSUFFICIENT_INFORMATION": "\033[93m[INSUFFICIENT INFORMATION]\033[0m",
    }
    status_badge = status_colors.get(status, f"[{status}]")

    lines = []
    lines.append("=" * 80)
    lines.append(f"  SCHEME ELIGIBILITY EVALUATION: {scheme_name}")
    lines.append("=" * 80)
    lines.append(f"  * Citizen ID:         {citizen_id}")
    lines.append(f"  * Scheme ID:          {res.get('scheme_id')}")
    lines.append(f"  * Final Assessment:   {status_badge}")
    lines.append(f"  * Rules Passed:       {res.get('passed_rules_count', 0)}")
    lines.append(f"  * Rules Failed:       {res.get('failed_rules_count', 0)}")
    lines.append(f"  * Rules Inconclusive: {res.get('unknown_rules_count', 0)}")

    if res.get("is_synthetic_scheme"):
        lines.append("  * Scheme Type:        DEMO (Simulated Welfare Criteria)")

    lines.append("\n" + "-" * 80)
    lines.append("DETAILED RULE BREAKDOWN")
    lines.append("-" * 80)

    breakdown = res.get("rule_breakdown", {})
    passed = breakdown.get("passed", [])
    failed = breakdown.get("failed", [])
    unknown = breakdown.get("unknown", [])

    if passed:
        lines.append("\n  PASSED REQUIREMENTS:")
        for p in passed:
            lines.append(f"    [PASS] {p['rule_id']}: {p['description']}")
            lines.append(f"           Observed: {p['citizen_value']} | Threshold: {p['threshold']}")
            if p.get("source"):
                lines.append(f"           Source: {p['source']}")

    if failed:
        lines.append("\n  FAILED REQUIREMENTS:")
        for f in failed:
            lines.append(f"    [FAIL] {f['rule_id']}: {f['description']}")
            lines.append(f"           Observed: {f['citizen_value']} | Threshold: {f['threshold']}")
            src_str = f"Source: {f.get('source', 'Official Guidelines')}"
            if f.get("page"):
                src_str += f", Page {f['page']}"
            lines.append(f"           {src_str}")

    if unknown:
        lines.append("\n  INCONCLUSIVE / MISSING REQUIREMENTS:")
        for u in unknown:
            lines.append(f"    [UNKNOWN] {u['rule_id']}: {u['description']}")
            lines.append(f"              Missing Field: '{u.get('missing_field')}'")
            lines.append(f"              Note: {u.get('reason')}")

    lines.append("\n" + "-" * 80)
    lines.append("SUMMARY REASONS")
    lines.append("-" * 80)
    for reason in res.get("summary_reasons", []):
        lines.append(f"  * {reason}")

    next_steps = res.get("next_steps", [])
    if next_steps:
        lines.append("\n" + "-" * 80)
        lines.append("RECOMMENDED NEXT STEPS")
        lines.append("-" * 80)
        for step in next_steps:
            lines.append(f"  -> {step}")

    warnings = res.get("warnings", [])
    if warnings:
        lines.append("\n" + "-" * 80)
        lines.append("WARNINGS & DISCREPANCIES")
        lines.append("-" * 80)
        for warn in warnings:
            lines.append(f"  ! {warn}")

    lines.append("\n" + "=" * 80)
    lines.append("LEGAL DISCLAIMER:")
    lines.append(f"  {res.get('disclaimer')}")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="Deterministic Scheme Eligibility Verification CLI"
    )
    parser.add_argument(
        "--scheme",
        "-s",
        type=str,
        default="SISFS",
        help="Scheme ID to evaluate (e.g. 'SISFS' or 'TELANGANA_YOUTH_SUPPORT'). Default: 'SISFS'",
    )
    parser.add_argument(
        "--citizen",
        "-c",
        type=str,
        default="demo-user",
        help="Citizen ID to evaluate (e.g. 'demo-user', 'senior-citizen', 'rural-farmer'). Default: 'demo-user'",
    )
    parser.add_argument(
        "--document",
        "-d",
        type=str,
        default=None,
        help="Optional path to citizen document for Document AI fact extraction (e.g. tests/fixtures/documents/sample_income_cert.pdf)",
    )
    parser.add_argument(
        "--list-schemes",
        action="store_true",
        help="List all registered government schemes and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted text.",
    )

    args = parser.parse_args()

    if args.list_schemes:
        registry = SchemeRulesRegistry()
        schemes = registry.list_schemes()
        print("\nRegistered Government Schemes:")
        print("=" * 70)
        for s in schemes:
            synth = " [DEMO]" if s["is_synthetic"] else " [OFFICIAL]"
            print(f"* ID:          {s['scheme_id']}{synth}")
            print(f"  Name:        {s['scheme_name']}")
            print(f"  Description: {s['description']}")
            print(f"  Rules:       {s['rule_count']} criteria")
            print("-" * 70)
        return

    tool = EligibilityCheckTool()
    result = tool.execute(
        scheme_id=args.scheme,
        citizen_id=args.citizen,
        document_path=args.document,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("status") == "error":
            print(f"\n[ERROR] {result.get('error_type')}: {result.get('error')}", file=sys.stderr)
            print(f"Disclaimer: {result.get('disclaimer')}", file=sys.stderr)
            sys.exit(1)
        print(format_cli_output(result))


if __name__ == "__main__":
    main()
