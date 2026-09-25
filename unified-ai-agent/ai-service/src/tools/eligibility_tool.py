"""Eligibility Check Tool for Agent Orchestrator."""
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.tools.base import BaseTool
from src.tools.mysql_tool import CitizenProfileTool
from src.tools.document_tool import DocumentAnalysisTool
from src.eligibility.engine import EligibilityEngine
from src.eligibility.evidence import EvidenceHarvester
from src.eligibility.rules import SchemeRulesRegistry, SchemeNotFoundError
from src.config.settings import get_settings


class EligibilityCheckTool(BaseTool):
    """Deterministic eligibility assessment tool for citizen support schemes."""

    def __init__(
        self,
        engine: Optional[EligibilityEngine] = None,
        profile_tool: Optional[CitizenProfileTool] = None,
        document_tool: Optional[DocumentAnalysisTool] = None,
    ):
        self.engine = engine or EligibilityEngine()
        self.profile_tool = profile_tool or CitizenProfileTool()
        self.document_tool = document_tool or DocumentAnalysisTool()

    @property
    def name(self) -> str:
        return "check_eligibility"

    @property
    def description(self) -> str:
        return (
            "Evaluate whether a citizen is eligible for a specific government support scheme (e.g. 'SISFS' "
            "for Startup India Seed Fund Scheme, or 'TELANGANA_YOUTH_SUPPORT') using deterministic rule evaluation "
            "based on verified citizen profile attributes and document evidence. "
            "Calculates mathematically authoritative outcomes (ELIGIBLE, NOT_ELIGIBLE, or INSUFFICIENT_INFORMATION) "
            "with official source citations, specific reasons, and recommended next steps."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scheme_id": {
                    "type": "string",
                    "description": "Identifier of the scheme to evaluate (e.g. 'SISFS' or 'TELANGANA_YOUTH_SUPPORT').",
                },
                "citizen_id": {
                    "type": "string",
                    "description": "Unique citizen identifier (e.g. 'demo-user', 'senior-citizen', 'rural-farmer'). Defaults to 'demo-user'.",
                    "default": "demo-user",
                },
                "document_path": {
                    "type": "string",
                    "description": "Optional path to an approved citizen support document (e.g. income certificate or PDF) for Document AI fact extraction.",
                },
                "override_fields": {
                    "type": "object",
                    "description": "Optional direct key-value attribute overrides for testing specific criteria.",
                },
            },
            "required": ["scheme_id"],
        }

    def execute(
        self,
        scheme_id: str,
        citizen_id: Optional[str] = "demo-user",
        document_path: Optional[str] = None,
        override_fields: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute deterministic eligibility evaluation with multi-source evidence harvesting."""
        try:
            cid = (citizen_id or "demo-user").strip()

            # 1. Harvest citizen profile attributes
            profile_res = self.profile_tool.execute(citizen_id=cid)
            profile_data = profile_res.get("profile", {})

            # 2. Harvest document facts if document path provided
            doc_data = None
            doc_warnings = []
            if document_path:
                doc_res = self.document_tool.execute(document_path=document_path)
                if doc_res.get("status") == "success":
                    doc_data = doc_res
                else:
                    doc_warnings.append(
                        f"Document analysis warning for '{document_path}': {doc_res.get('error', 'Unknown error')}"
                    )

            # 3. Aggregate evidence with conflict resolution
            harvester = EvidenceHarvester()
            evidence_store = harvester.harvest(
                profile_data=profile_data,
                document_data=doc_data,
                user_overrides=override_fields,
            )

            all_warnings = harvester.warnings + doc_warnings

            # 4. Evaluate using Deterministic Eligibility Engine
            result = self.engine.evaluate(
                scheme_id=scheme_id,
                evidence_store=evidence_store,
                citizen_id=cid,
                additional_warnings=all_warnings,
            )

            # 5. Format structured response
            return {
                "status": "success",
                "scheme_id": result.scheme_id,
                "scheme_name": result.scheme_name,
                "citizen_id": result.citizen_id,
                "eligibility_status": result.status.value,
                "summary_reasons": result.summary_reasons,
                "passed_rules_count": len(result.passed_rules),
                "failed_rules_count": len(result.failed_rules),
                "unknown_rules_count": len(result.unknown_rules),
                "rule_breakdown": {
                    "passed": [
                        {
                            "rule_id": p.rule.rule_id,
                            "description": p.rule.description,
                            "citizen_value": p.citizen_value,
                            "threshold": p.threshold_value,
                            "reason": p.reason,
                            "source": p.rule.official_source,
                        }
                        for p in result.passed_rules
                    ],
                    "failed": [
                        {
                            "rule_id": f.rule.rule_id,
                            "description": f.rule.description,
                            "citizen_value": f.citizen_value,
                            "threshold": f.threshold_value,
                            "reason": f.reason,
                            "source": f.rule.official_source,
                            "page": f.rule.official_page,
                        }
                        for f in result.failed_rules
                    ],
                    "unknown": [
                        {
                            "rule_id": u.rule.rule_id,
                            "description": u.rule.description,
                            "reason": u.reason,
                            "missing_field": u.rule.field_name,
                        }
                        for u in result.unknown_rules
                    ],
                },
                "next_steps": result.next_steps,
                "warnings": result.warnings,
                "disclaimer": result.disclaimer,
                "is_synthetic_scheme": result.is_synthetic_scheme,
                "is_mock": False,
            }
        except SchemeNotFoundError as e:
            return {
                "status": "error",
                "error_type": "SchemeNotFoundError",
                "error": str(e),
                "disclaimer": (
                    "Preliminary eligibility assessment based on available structured rules and evidence. "
                    "Does NOT constitute official government sanction, legal eligibility, or guaranteed benefit approval."
                ),
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "UnexpectedError",
                "error": f"Failed to execute eligibility evaluation: {e}",
                "disclaimer": (
                    "Preliminary eligibility assessment based on available structured rules and evidence. "
                    "Does NOT constitute official government sanction, legal eligibility, or guaranteed benefit approval."
                ),
            }
