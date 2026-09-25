"""Standalone Command Line Interface for Multi-Need Detection (Milestone 6)."""
import argparse
import json
import sys

from src.tools.need_tool import NeedDetectionTool


def format_cli_output(res: dict) -> str:
    """Format detected needs result for clear terminal display."""
    lines = []
    lines.append("=" * 80)
    lines.append("  CITIZEN MULTI-NEED DETECTION")
    lines.append("=" * 80)
    lines.append(f"  * Input Text:        \"{res.get('original_text', '')}\"")
    lines.append(f"  * Total Needs:       {res.get('total_needs', 0)}")
    lines.append(f"  * Has Ambiguity:     {res.get('has_ambiguous_needs', False)}")

    needs = res.get("needs", [])
    if needs:
        lines.append("\n" + "-" * 80)
        lines.append("DETECTED NEEDS BREAKDOWN")
        lines.append("-" * 80)
        for idx, n in enumerate(needs, start=1):
            conf_badge = f"{n.get('confidence_level')} ({n.get('confidence'):.0%})"
            lines.append(f"\n  [{idx}] Category:     {n.get('category').upper()}")
            lines.append(f"      Type:         {n.get('explicit_or_inferred')}")
            lines.append(f"      Confidence:   {conf_badge}")
            lines.append(f"      Description:  {n.get('description')}")
            if n.get("evidence_span"):
                lines.append(f"      Evidence:     \"{n.get('evidence_span')}\"")
            if n.get("is_ambiguous"):
                lines.append("      Ambiguous:    YES (Requires clarification)")

    prompts = res.get("clarification_prompts", [])
    if prompts:
        lines.append("\n" + "-" * 80)
        lines.append("CLARIFICATION REQUIRED")
        lines.append("-" * 80)
        for p in prompts:
            lines.append(f"  ? {p}")

    queries = res.get("suggested_scheme_queries", {})
    if queries:
        lines.append("\n" + "-" * 80)
        lines.append("INTERNAL RETRIEVAL QUERIES (RAG SEARCH)")
        lines.append("-" * 80)
        for cat, q in queries.items():
            lines.append(f"  -> [{cat.upper()}]: \"{q}\"")

    lines.append("\n" + "=" * 80)
    lines.append("DISCLAIMER:")
    lines.append(f"  {res.get('disclaimer')}")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Multi-Need Detection CLI")
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        default="I lost my job, have low income, and need housing help",
        help="Citizen message or problem description to analyze.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted text.",
    )

    args = parser.parse_args()

    tool = NeedDetectionTool()
    result = tool.execute(text=args.text)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("status") == "error":
            print(f"\n[ERROR] {result.get('error_type')}: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
        print(format_cli_output(result))


if __name__ == "__main__":
    main()
