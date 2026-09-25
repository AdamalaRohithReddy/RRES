"""Citizen and Profile Repository for Milestone 7.

Implements parameterized SQLAlchemy ORM queries for citizen identities and
demographic profiles with strict identifier validation and dynamic age calculation.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.database.connection import get_db_session
from src.database.models import CitizenModel, CitizenProfileModel

logger = logging.getLogger(__name__)

# Strict identifier pattern: 1-64 alphanumeric characters, underscores, and hyphens.
CITIZEN_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_citizen_id(citizen_id: str) -> str:
    """Validate citizen_id against strict regex to reject malformed or injection strings.
    
    Raises:
        ValueError: If citizen_id is empty, invalid type, or contains illegal characters.
    """
    if not citizen_id or not isinstance(citizen_id, str):
        raise ValueError("Citizen ID must be a non-empty string.")
    cleaned = citizen_id.strip()
    if not CITIZEN_ID_REGEX.match(cleaned):
        raise ValueError(
            f"Invalid citizen ID format: '{cleaned}'. "
            "Must be 1-64 characters containing only alphanumeric characters, underscores, or hyphens."
        )
    return cleaned


class CitizenRepository:
    """Repository handling all citizen identity and profile database operations."""

    def __init__(self, session: Optional[Session] = None):
        """Optionally accept an existing session (e.g. for transactions or testing)."""
        self._session = session

    def _get_session(self):
        """Return the current session or acquire a new one via context manager."""
        if self._session is not None:
            return self._session
        return None

    def get_citizen_with_profile(self, citizen_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve consolidated citizen data and profile as a dictionary.
        
        Guarantees parameterized query execution. Computes age dynamically from date_of_birth.
        Returns None if citizen does not exist.
        """
        valid_id = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> Optional[Dict[str, Any]]:
            stmt = (
                select(CitizenModel)
                .options(joinedload(CitizenModel.profile))
                .where(CitizenModel.citizen_id == valid_id)
            )
            citizen = s.execute(stmt).scalars().first()
            if not citizen:
                return None
            return citizen.to_dict()

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def get_citizen(self, citizen_id: str) -> Optional[CitizenModel]:
        """Fetch citizen model by ID."""
        valid_id = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> Optional[CitizenModel]:
            stmt = select(CitizenModel).where(CitizenModel.citizen_id == valid_id)
            return s.execute(stmt).scalars().first()

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def create_or_update_citizen(
        self,
        citizen_id: str,
        name: str,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> CitizenModel:
        """Create a new citizen or update existing record."""
        valid_id = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> CitizenModel:
            citizen = s.execute(
                select(CitizenModel).where(CitizenModel.citizen_id == valid_id)
            ).scalars().first()

            if citizen:
                citizen.name = name
                citizen.date_of_birth = date_of_birth
                citizen.gender = gender
                citizen.phone = phone
                citizen.updated_at = datetime.now(timezone.utc)
            else:
                citizen = CitizenModel(
                    citizen_id=valid_id,
                    name=name,
                    date_of_birth=date_of_birth,
                    gender=gender,
                    phone=phone,
                )
                s.add(citizen)
            s.flush()
            return citizen

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def create_or_update_profile(
        self,
        citizen_id: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        annual_income: Optional[float | Decimal] = None,
        occupation: Optional[str] = None,
        category: Optional[str] = None,
        is_taxpayer: bool = False,
        has_dpiit_recognition: bool = False,
        business_incorporated_years: Optional[int] = None,
        landholding_acres: Optional[float | Decimal] = None,
        is_differently_abled: bool = False,
        disability_percentage: Optional[float | Decimal] = None,
        additional_attributes: Optional[Dict[str, Any]] = None,
    ) -> CitizenProfileModel:
        """Create or update demographic profile for a citizen."""
        valid_id = validate_citizen_id(citizen_id)

        def _execute(s: Session) -> CitizenProfileModel:
            stmt = select(CitizenProfileModel).where(CitizenProfileModel.citizen_id == valid_id)
            profile = s.execute(stmt).scalars().first()

            income_dec = Decimal(str(annual_income)) if annual_income is not None else None
            land_dec = Decimal(str(landholding_acres)) if landholding_acres is not None else None
            dis_dec = Decimal(str(disability_percentage)) if disability_percentage is not None else None

            if profile:
                profile.state = state
                profile.district = district
                profile.annual_income = income_dec
                profile.occupation = occupation
                profile.category = category
                profile.is_taxpayer = is_taxpayer
                profile.has_dpiit_recognition = has_dpiit_recognition
                profile.business_incorporated_years = business_incorporated_years
                profile.landholding_acres = land_dec
                profile.is_differently_abled = is_differently_abled
                profile.disability_percentage = dis_dec
                profile.additional_attributes = additional_attributes
                profile.updated_at = datetime.now(timezone.utc)
            else:
                profile = CitizenProfileModel(
                    citizen_id=valid_id,
                    state=state,
                    district=district,
                    annual_income=income_dec,
                    occupation=occupation,
                    category=category,
                    is_taxpayer=is_taxpayer,
                    has_dpiit_recognition=has_dpiit_recognition,
                    business_incorporated_years=business_incorporated_years,
                    landholding_acres=land_dec,
                    is_differently_abled=is_differently_abled,
                    disability_percentage=dis_dec,
                    additional_attributes=additional_attributes,
                )
                s.add(profile)
            s.flush()
            return profile

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)

    def list_citizens(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List citizen records with pagination."""
        def _execute(s: Session) -> List[Dict[str, Any]]:
            stmt = select(CitizenModel).offset(offset).limit(limit)
            citizens = s.execute(stmt).scalars().all()
            return [c.to_dict() for c in citizens]

        if self._session is not None:
            return _execute(self._session)

        with get_db_session() as s:
            return _execute(s)
