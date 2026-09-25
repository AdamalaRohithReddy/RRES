"""Application Tracking Repository for Milestone 7.

Implements parameterized SQLAlchemy ORM queries for scheme applications
and status audit history with strict identifier validation.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.database.connection import get_db_session
from src.database.models import ApplicationModel, ApplicationStatusHistoryModel

logger = logging.getLogger(__name__)

# Strict identifier pattern: 1-64 alphanumeric characters, underscores, and hyphens.
APPLICATION_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_application_id(app_id: str) -> str:
    """Validate application_id against strict regex to reject malformed or injection strings.
    
    Raises:
        ValueError: If app_id is empty, invalid type, or contains illegal characters.
    """
    if not app_id or not isinstance(app_id, str):
        raise ValueError("Application ID must be a non-empty string.")
    cleaned = app_id.strip()
    if not APPLICATION_ID_REGEX.match(cleaned):
        raise ValueError(
            f"Invalid application ID format: '{cleaned}'. "
            "Must be 1-64 characters containing only alphanumeric characters, underscores, or hyphens."
        )
    return cleaned


class ApplicationRepository:
    """Repository handling all government scheme application tracking operations."""

    def __init__(self, session: Optional[Session] = None):
        """Optionally accept an existing session (e.g. for transactions or testing)."""
        self._session = session

    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve application tracking record by application ID.
        
        Guarantees parameterized query execution. Returns None if application does not exist.
        """
        valid_id = validate_application_id(application_id)

        def _execute(s: Session) -> Optional[Dict[str, Any]]:
            stmt = select(ApplicationModel).where(ApplicationModel.application_id == valid_id)
            app = s.execute(stmt).scalars().first()
            if not app:
                return None
            return app.to_dict()

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def list_applications_by_citizen(self, citizen_id: str) -> List[Dict[str, Any]]:
        """List all application records for a specific citizen."""
        from src.database.repositories.citizen_repo import validate_citizen_id
        valid_cid = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> List[Dict[str, Any]]:
            stmt = select(ApplicationModel).where(ApplicationModel.citizen_id == valid_cid)
            apps = s.execute(stmt).scalars().all()
            return [a.to_dict() for a in apps]

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def create_application(
        self,
        application_id: str,
        citizen_id: str,
        scheme_name: str,
        status: str,
        submitted_date: Optional[date] = None,
        incubator_preference: Optional[str] = None,
        milestone_stage: Optional[str] = None,
        pran_status: Optional[str] = None,
        next_step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> ApplicationModel:
        """Create a new application tracking record and initial status history entry."""
        from src.database.repositories.citizen_repo import validate_citizen_id
        valid_app_id = validate_application_id(application_id)
        valid_cid = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> ApplicationModel:
            app = ApplicationModel(
                application_id=valid_app_id,
                citizen_id=valid_cid,
                scheme_name=scheme_name,
                status=status,
                submitted_date=submitted_date,
                incubator_preference=incubator_preference,
                milestone_stage=milestone_stage,
                pran_status=pran_status,
                next_step=next_step,
                details=details,
            )
            s.add(app)
            # Create initial status history entry
            history = ApplicationStatusHistoryModel(
                application_id=valid_app_id,
                status=status,
                comment="Initial application submission",
                changed_by="system",
            )
            s.add(history)
            s.flush()
            return app

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def update_status(
        self,
        application_id: str,
        new_status: str,
        comment: Optional[str] = None,
        changed_by: Optional[str] = "system",
        next_step: Optional[str] = None,
    ) -> Optional[ApplicationModel]:
        """Update the status of an application and record an audit history entry atomically."""
        valid_id = validate_application_id(application_id)

        def _execute(s: Session) -> Optional[ApplicationModel]:
            stmt = select(ApplicationModel).where(ApplicationModel.application_id == valid_id)
            app = s.execute(stmt).scalars().first()
            if not app:
                return None

            app.status = new_status
            if next_step:
                app.next_step = next_step
            app.last_updated = datetime.now(timezone.utc)

            history = ApplicationStatusHistoryModel(
                application_id=valid_id,
                status=new_status,
                comment=comment,
                changed_by=changed_by,
            )
            s.add(history)
            s.flush()
            return app

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def get_status_history(self, application_id: str) -> List[Dict[str, Any]]:
        """Retrieve ordered status history entries for an application."""
        valid_id = validate_application_id(application_id)

        def _execute(s: Session) -> List[Dict[str, Any]]:
            stmt = (
                select(ApplicationStatusHistoryModel)
                .where(ApplicationStatusHistoryModel.application_id == valid_id)
                .order_by(ApplicationStatusHistoryModel.created_at.asc())
            )
            rows = s.execute(stmt).scalars().all()
            return [
                {
                    "history_id": r.history_id,
                    "application_id": r.application_id,
                    "status": r.status,
                    "comment": r.comment,
                    "changed_by": r.changed_by,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)
