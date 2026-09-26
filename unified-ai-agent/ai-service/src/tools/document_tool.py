"""Document analysis tool for Agent Orchestrator with strict filesystem sandboxing."""
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.tools.base import BaseTool
from src.document_ai.pipeline import (
    DocumentProcessingPipeline,
    DocumentProcessingError,
)
from src.config.settings import get_settings


class SecurityViolationError(Exception):
    """Raised when an unauthorized or out-of-sandbox filesystem path is accessed."""
    pass


class DocumentAnalysisTool(BaseTool):
    """Agent tool that classifies apparent document type and extracts structured citizen attributes."""

    DANGEROUS_EXTENSIONS = {
        ".exe", ".bat", ".cmd", ".sh", ".py", ".dll", ".so", ".bin", ".msi", ".ps1", ".vbs"
    }

    def __init__(
        self,
        pipeline: Optional[DocumentProcessingPipeline] = None,
        approved_roots: Optional[List[Path]] = None,
    ):
        settings = get_settings()
        self.pipeline = pipeline or DocumentProcessingPipeline()

        # Define approved directory whitelist
        root = settings.ai_service_root
        self.approved_roots = approved_roots or [
            (root / "data" / "documents").resolve(),
            (root / "data" / "raw").resolve(),
            (root / "tests" / "fixtures" / "documents").resolve(),
            (root.parent / "uploads" / "documents").resolve(),
            (root.parent / "backend" / "uploads" / "documents").resolve(),
        ]
        # Ensure approved directories exist
        for d in self.approved_roots:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "analyze_document"

    @property
    def description(self) -> str:
        return (
            "Classify the apparent document type and extract structured citizen-support fields "
            "(such as annual income, name, age, state, district) from an approved citizen document. "
            "IMPORTANT: This tool performs apparent document type classification and textual fact extraction; "
            "it does NOT verify document authenticity or legal validity."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_path": {
                    "type": "string",
                    "description": (
                        "Path or filename of the uploaded document (PDF, PNG, JPG, JPEG) "
                        "located within approved document directories."
                    ),
                }
            },
            "required": ["document_path"],
        }

    def _resolve_and_validate_path(self, document_path: str) -> Path:
        """Enforce strict sandbox security on requested document path."""
        p = Path(document_path)

        # Check for banned executable/script extensions
        if p.suffix.lower() in self.DANGEROUS_EXTENSIONS:
            raise SecurityViolationError(
                f"Access denied: Executable or script file type '{p.suffix}' is prohibited."
            )

        # If path is relative, attempt resolution against approved roots
        resolved_path: Optional[Path] = None
        if not p.is_absolute():
            for root in self.approved_roots:
                candidate = (root / p).resolve()
                if candidate.exists() and candidate.is_file():
                    resolved_path = candidate
                    break
            # If not found in roots, check relative to cwd but ensure it falls inside a root
            if resolved_path is None:
                candidate = p.resolve()
                resolved_path = candidate
        else:
            resolved_path = p.resolve()

        # Enforce sandbox whitelist boundary
        is_safe = False
        for root in self.approved_roots:
            try:
                resolved_path.relative_to(root)
                is_safe = True
                break
            except ValueError:
                continue

        if not is_safe:
            raise SecurityViolationError(
                f"Access denied: Document path '{document_path}' resolves outside approved sandbox directories."
            )

        return resolved_path

    def execute(self, document_path: str) -> Dict[str, Any]:
        """Execute document analysis with security validation and provenance preservation."""
        try:
            safe_path = self._resolve_and_validate_path(document_path)
            result = self.pipeline.process(safe_path)

            fields_dict = {}
            for k, f in result.fields.items():
                fields_dict[k] = {
                    "value": f.value,
                    "confidence": f.confidence,
                    "confidence_level": f.confidence_level.value,
                    "page": f.page,
                    "source_text": f.source_text,
                }

            return {
                "status": "success",
                "apparent_document_type": result.apparent_document_type.value,
                "document_type_confidence": result.document_type_confidence,
                "ocr_used": result.ocr_used,
                "fields": fields_dict,
                "warnings": result.warnings,
                "metadata": result.metadata.model_dump() if result.metadata else None,
                "disclaimer": result.disclaimer,
                "is_mock": False,
            }
        except SecurityViolationError as e:
            return {
                "status": "error",
                "error_type": "SecurityViolationError",
                "error": str(e),
                "disclaimer": "Document type classification is not document authenticity verification.",
            }
        except DocumentProcessingError as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error": str(e),
                "disclaimer": "Document type classification is not document authenticity verification.",
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "UnexpectedError",
                "error": f"Failed to analyze document: {e}",
                "disclaimer": "Document type classification is not document authenticity verification.",
            }
