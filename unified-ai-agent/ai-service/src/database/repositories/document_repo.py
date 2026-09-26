"""Document Metadata and Extracted Facts Repository for Milestone 7.

Stores document metadata, apparent classifications, SHA-256 integrity hashes,
and structured facts extracted by Document AI with assigned confidence and provenance.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.database.connection import get_db_session
from src.database.models import DocumentModel, DocumentExtractedFieldModel
from src.database.repositories.citizen_repo import validate_citizen_id

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository handling document metadata and extracted fact persistence."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def create_document(
        self,
        citizen_id: str,
        filename: str,
        sha256_hash: str,
        apparent_type: Optional[str] = None,
        storage_path: Optional[str] = None,
        extracted_text: Optional[str] = None,
    ) -> DocumentModel:
        """Record document metadata and integrity hash."""
        valid_cid = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> DocumentModel:
            doc = DocumentModel(
                citizen_id=valid_cid,
                filename=filename,
                sha256_hash=sha256_hash,
                apparent_type=apparent_type,
                storage_path=storage_path,
                extracted_text=extracted_text,
            )
            s.add(doc)
            s.flush()
            return doc

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def add_extracted_fields(
        self,
        document_id: int,
        fields: List[Dict[str, Any]],
    ) -> List[DocumentExtractedFieldModel]:
        """Record structured facts extracted by Document AI with confidence and provenance."""
        def _execute(s: Session) -> List[DocumentExtractedFieldModel]:
            field_models: List[DocumentExtractedFieldModel] = []
            for f in fields:
                conf = Decimal(str(f.get("confidence", 1.0)))
                fm = DocumentExtractedFieldModel(
                    document_id=document_id,
                    field_name=f["field_name"],
                    field_value=str(f["field_value"]),
                    confidence=conf,
                    provenance_method=f.get("provenance_method"),
                )
                s.add(fm)
                field_models.append(fm)
            s.flush()
            return field_models

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def get_document_with_fields(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve document metadata and all extracted fields."""
        def _execute(s: Session) -> Optional[Dict[str, Any]]:
            stmt = (
                select(DocumentModel)
                .options(joinedload(DocumentModel.extracted_fields))
                .where(DocumentModel.document_id == document_id)
            )
            doc = s.execute(stmt).scalars().first()
            if not doc:
                return None

            return {
                "document_id": doc.document_id,
                "citizen_id": doc.citizen_id,
                "filename": doc.filename,
                "apparent_type": doc.apparent_type,
                "sha256_hash": doc.sha256_hash,
                "storage_path": doc.storage_path,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "extracted_fields": [
                    {
                        "field_id": ef.field_id,
                        "field_name": ef.field_name,
                        "field_value": ef.field_value,
                        "confidence": float(ef.confidence),
                        "provenance_method": ef.provenance_method,
                    }
                    for ef in doc.extracted_fields
                ],
            }

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def list_documents_by_citizen(self, citizen_id: str) -> List[Dict[str, Any]]:
        """List documents and extracted facts for a citizen."""
        valid_cid = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> List[Dict[str, Any]]:
            stmt = (
                select(DocumentModel)
                .options(joinedload(DocumentModel.extracted_fields))
                .where(DocumentModel.citizen_id == valid_cid)
                .order_by(DocumentModel.uploaded_at.desc())
            )
            docs = s.execute(stmt).scalars().unique().all()
            results = []
            for doc in docs:
                results.append({
                    "document_id": doc.document_id,
                    "citizen_id": doc.citizen_id,
                    "filename": doc.filename,
                    "apparent_type": doc.apparent_type,
                    "sha256_hash": doc.sha256_hash,
                    "storage_path": doc.storage_path,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "extracted_fields": [
                        {
                            "field_name": ef.field_name,
                            "field_value": ef.field_value,
                            "confidence": float(ef.confidence),
                            "provenance_method": ef.provenance_method,
                        }
                        for ef in doc.extracted_fields
                    ],
                })
            return results

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def update_document_ai_fields(
        self,
        document_id: int,
        apparent_type: Optional[str] = None,
        extracted_text: Optional[str] = None,
    ) -> bool:
        """Narrowly scoped update to AI-processing fields only (M9 rule 13).
        
        Strictly updates apparent_type and extracted_text for an existing document.
        Does not modify filename, storage_path, citizen_id, or lifecycle status.
        """
        def _execute(s: Session) -> bool:
            doc = s.get(DocumentModel, document_id)
            if not doc:
                return False
            if apparent_type is not None:
                doc.apparent_type = apparent_type
            if extracted_text is not None:
                doc.extracted_text = extracted_text
            s.flush()
            return True

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)
