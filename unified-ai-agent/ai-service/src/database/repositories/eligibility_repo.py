"""Eligibility Assessment Audit Repository for Milestone 7 (M5 Integration).

Records deterministic eligibility assessment decisions, passed/failed rules,
and missing evidence for governance auditing.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.connection import get_db_session
from src.database.models import EligibilityAssessmentModel
from src.database.repositories.citizen_repo import validate_citizen_id

logger = logging.getLogger(__name__)


class EligibilityAuditRepository:
    """Repository handling persistence of deterministic eligibility decisions."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def record_assessment(
        self,
        citizen_id: str,
        scheme_name: str,
        decision: str,
        passed_rules: Optional[List[str]] = None,
        failed_rules: Optional[List[str]] = None,
        missing_evidence: Optional[List[str]] = None,
    ) -> Optional[EligibilityAssessmentModel]:
        """Record an eligibility assessment outcome.
        
        Designed to be non-blocking: catches exceptions and logs warnings so
        eligibility determination in M5 is never interrupted by audit logging failures.
        """
        try:
            valid_cid = validate_citizen_id(citizen_id)
        except ValueError as e:
            logger.warning(f"Could not record eligibility audit due to invalid citizen_id '{citizen_id}': {e}")
            return None

        def _execute(s: Session) -> EligibilityAssessmentModel:
            record = EligibilityAssessmentModel(
                citizen_id=valid_cid,
                scheme_name=scheme_name,
                decision=decision,
                passed_rules=passed_rules or [],
                failed_rules=failed_rules or [],
                missing_evidence=missing_evidence or [],
            )
            s.add(record)
            s.flush()
            return record

        try:
            if self._session is not None:
                return _execute(self._session)

            with get_db_session() as s:
                return _execute(s)
        except Exception as exc:
            logger.warning(f"Failed to record eligibility assessment audit log: {exc}")
            return None

    def list_assessments_by_citizen(self, citizen_id: str) -> List[Dict[str, Any]]:
        """List past eligibility assessments for a citizen."""
        valid_cid = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> List[Dict[str, Any]]:
            stmt = (
                select(EligibilityAssessmentModel)
                .where(EligibilityAssessmentModel.citizen_id == valid_cid)
                .order_by(EligibilityAssessmentModel.assessed_at.desc())
            )
            rows = s.execute(stmt).scalars().all()
            return [
                {
                    "assessment_id": r.assessment_id,
                    "citizen_id": r.citizen_id,
                    "scheme_name": r.scheme_name,
                    "decision": r.decision,
                    "passed_rules": r.passed_rules,
                    "failed_rules": r.failed_rules,
                    "missing_evidence": r.missing_evidence,
                    "assessed_at": r.assessed_at.isoformat() if r.assessed_at else None,
                }
                for r in rows
            ]

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)
