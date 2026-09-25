"""Agent tool for Multi-Need Detection (Milestone 6)."""
from typing import Dict, Any, Optional
from src.tools.base import BaseTool
from src.needs.detector import NeedDetector


class NeedDetectionTool(BaseTool):
    """Tool allowing the agent orchestrator to decompose compound user problems into structured needs."""

    def __init__(self, detector: Optional[NeedDetector] = None):
        self.detector = detector or NeedDetector()

    @property
    def name(self) -> str:
        return "detect_citizen_needs"

    @property
    def description(self) -> str:
        return (
            "Decompose citizen natural-language problem descriptions into structured, categorized needs "
            "with evidence spans and confidence scores. Use this tool whenever a citizen describes their "
            "situation, hardship, or multiple assistance goals (such as job loss, low income, school fees, "
            "or housing needs)."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Citizen message, situation, or problem description to decompose into structured needs.",
                }
            },
            "required": ["text"],
        }

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Alias for parameters."""
        return self.parameters

    def execute(self, text: str, **kwargs) -> Dict[str, Any]:
        """Execute deterministic multi-need detection."""
        try:
            result = self.detector.detect_needs(text)

            needs_list = [
                {
                    "need_id": n.need_id,
                    "category": n.category.value,
                    "description": n.description,
                    "confidence": n.confidence,
                    "confidence_level": n.confidence_level.value,
                    "explicit_or_inferred": n.explicit_or_inferred.value,
                    "evidence_span": n.evidence_span,
                    "is_ambiguous": n.is_ambiguous,
                    "clarification_needed": n.clarification_needed,
                }
                for n in result.needs
            ]

            return {
                "status": "success",
                "original_text": result.original_text,
                "needs": needs_list,
                "total_needs": result.total_needs,
                "has_ambiguous_needs": result.has_ambiguous_needs,
                "is_ambiguous": result.has_ambiguous_needs,
                "clarification_prompts": result.clarification_prompts,
                "suggested_scheme_queries": result.suggested_scheme_queries,
                "disclaimer": result.disclaimer,
                "is_mock": False,
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error": f"Failed to detect needs: {e}",
                "disclaimer": (
                    "Need classification interprets citizen-described requirements to identify relevant assistance; "
                    "it does NOT determine eligibility or guarantee government benefit approval."
                ),
            }
