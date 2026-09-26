"""Direct Document AI Analysis endpoint (M4)."""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import verify_internal_api_key, get_correlation_id, get_optional_citizen_id
from src.api.schemas.documents import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    ExtractedFieldItem,
)
from src.tools.document_tool import DocumentAnalysisTool, SecurityViolationError
from src.database.repositories.document_repo import DocumentRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/documents", tags=["Document AI"])
_doc_tool = DocumentAnalysisTool()
_doc_repo = DocumentRepository()


@router.post("/analyze", response_model=DocumentAnalysisResponse)
def analyze_document(
    request: DocumentAnalysisRequest,
    _auth: str = Depends(verify_internal_api_key),
    correlation_id: str = Depends(get_correlation_id),
    citizen_id: str = Depends(get_optional_citizen_id),
) -> DocumentAnalysisResponse:
    """Classify apparent document type and extract structured citizen attributes (M4 Document AI).
    
    If document_id is provided, extracted facts are persisted to MySQL document_extracted_fields,
    and apparent_type and extracted_text are updated on the existing documents record under
    narrowly scoped AI-processing update permissions.
    """
    logger.info(f"[{correlation_id}] Document analysis requested for path: {request.file_path}")

    try:
        res = _doc_tool.execute(document_path=request.file_path)
    except SecurityViolationError as sec_err:
        logger.warning(f"[{correlation_id}] Security violation analyzing document: {sec_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(sec_err),
        )
    except Exception as exc:
        logger.error(f"[{correlation_id}] Error analyzing document: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document analysis failed: {exc}",
        )

    if res.get("status") == "error":
        err_msg = res.get("error", "Document processing error")
        if res.get("security_violation") or "Access denied" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err_msg,
        )

    raw_fields: Dict[str, Any] = res.get("fields", {})
    output_fields: Dict[str, ExtractedFieldItem] = {}
    db_fields_to_persist: List[Dict[str, Any]] = []

    for f_name, f_data in raw_fields.items():
        if isinstance(f_data, dict):
            val = f_data.get("value")
            conf = float(f_data.get("confidence", 0.0) or 0.0)
            conf_level = str(f_data.get("confidence_level", "LOW"))
            prov = str(f_data.get("provenance_method", "PATTERN_MATCH"))
            raw_page = f_data.get("page")
            page = int(raw_page) if raw_page is not None else 1

            output_fields[f_name] = ExtractedFieldItem(
                value=val,
                confidence_score=round(conf, 3),
                confidence_level=conf_level,
                provenance_method=prov,
                page=page,
            )

            if val is not None:
                db_fields_to_persist.append({
                    "field_name": f_name,
                    "field_value": str(val),
                    "confidence": conf,
                    "provenance_method": prov,
                })

    # If document_id is provided, record extracted facts and update AI-processing fields
    if request.document_id is not None:
        try:
            if db_fields_to_persist:
                _doc_repo.add_extracted_fields(
                    document_id=request.document_id,
                    fields=db_fields_to_persist,
                )
            _doc_repo.update_document_ai_fields(
                document_id=request.document_id,
                apparent_type=res.get("apparent_document_type"),
                extracted_text=res.get("extracted_text"),
            )
            logger.info(f"[{correlation_id}] Persisted {len(db_fields_to_persist)} facts for document_id={request.document_id}")
        except Exception as db_err:
            logger.warning(f"[{correlation_id}] Could not persist extracted facts to database: {db_err}")

    return DocumentAnalysisResponse(
        document_path=request.file_path,
        apparent_document_type=res.get("apparent_document_type", "UNKNOWN"),
        document_type_confidence=res.get("document_type_confidence", 0.0),
        ocr_used=res.get("ocr_used", False),
        fields=output_fields,
        warnings=res.get("warnings", []),
        disclaimer=res.get("disclaimer", "Structured facts extracted by Document AI. Does not constitute official government authentication."),
    )
