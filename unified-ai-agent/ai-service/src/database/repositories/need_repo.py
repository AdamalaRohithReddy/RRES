"""Citizen Needs Repository for Milestone 7 (M6 Integration).

Persists detected citizen needs distinguishing between explicit and inferred needs
with urgency and optional session identification.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.connection import get_db_session
from src.database.models import CitizenNeedModel
from src.database.repositories.citizen_repo import validate_citizen_id

logger = logging.getLogger(__name__)


class NeedRepository:
    """Repository handling persistence and retrieval of detected citizen needs."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def record_needs(
        self,
        citizen_id: str,
        needs: List[Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> List[CitizenNeedModel]:
        """Record detected needs for a citizen.
        
        Preserves need classification (EXPLICIT vs INFERRED) and urgency.
        """
        valid_cid = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> List[CitizenNeedModel]:
            models: List[CitizenNeedModel] = []
            for n in needs:
                category = n.get("category")
                if hasattr(category, "value"):
                    category_str = category.value
                else:
                    category_str = str(category)

                urgency = n.get("urgency", "MEDIUM")
                if hasattr(urgency, "value"):
                    urgency_str = urgency.value
                else:
                    urgency_str = str(urgency)

                need_type = n.get("need_type", "EXPLICIT")
                if hasattr(need_type, "value"):
                    need_type_str = need_type.value
                else:
                    need_type_str = str(need_type)

                nm = CitizenNeedModel(
                    citizen_id=valid_cid,
                    category=category_str,
                    urgency=urgency_str,
                    need_type=need_type_str,
                    statement=n.get("statement") or n.get("description"),
                    session_id=session_id,
                )
                s.add(nm)
                models.append(nm)
            s.flush()
            return models

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def get_needs_by_citizen(
        self, citizen_id: str, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve detected needs for a citizen, optionally filtering by session."""
        valid_cid = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> List[Dict[str, Any]]:
            stmt = select(CitizenNeedModel).where(CitizenNeedModel.citizen_id == valid_cid)
            if session_id:
                stmt = stmt.where(CitizenNeedModel.session_id == session_id)
            stmt = stmt.order_by(CitizenNeedModel.created_at.desc())

            rows = s.execute(stmt).scalars().all()
            return [
                {
                    "need_id": r.need_id,
                    "citizen_id": r.citizen_id,
                    "category": r.category,
                    "urgency": r.urgency,
                    "need_type": r.need_type,
                    "statement": r.statement,
                    "session_id": r.session_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)
