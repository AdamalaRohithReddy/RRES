"""SQLAlchemy 2.0 ORM Declarative Models for Milestone 7 (Relational Database Integration).

Defines core citizen, demographic profile, application tracking, document metadata,
and audit entities for MySQL persistence.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for all database models."""
    pass


class CitizenModel(Base):
    """Core citizen identity model."""

    __tablename__ = "citizens"

    citizen_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    profile: Mapped[Optional["CitizenProfileModel"]] = relationship(
        "CitizenProfileModel",
        back_populates="citizen",
        uselist=False,
        cascade="all, delete-orphan",
    )
    applications: Mapped[List["ApplicationModel"]] = relationship(
        "ApplicationModel",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["DocumentModel"]] = relationship(
        "DocumentModel",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )
    needs: Mapped[List["CitizenNeedModel"]] = relationship(
        "CitizenNeedModel",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )
    eligibility_assessments: Mapped[List["EligibilityAssessmentModel"]] = relationship(
        "EligibilityAssessmentModel",
        back_populates="citizen",
        cascade="all, delete-orphan",
    )

    @property
    def age(self) -> Optional[int]:
        """Dynamically calculated age from date_of_birth to prevent stale demographic evidence."""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize citizen and profile into a consolidated dictionary for tools and evidence harvesting."""
        res: Dict[str, Any] = {
            "citizen_id": self.citizen_id,
            "name": self.name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "gender": self.gender,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if self.profile:
            prof_dict = self.profile.to_dict()
            prof_dict.pop("citizen_id", None)
            prof_dict.pop("profile_id", None)
            prof_dict.pop("updated_at", None)
            res.update(prof_dict)
        return res


class CitizenProfileModel(Base):
    """Detailed socio-economic and demographic attributes for scheme eligibility assessment."""

    __tablename__ = "citizen_profiles"

    profile_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citizen_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("citizens.citizen_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    annual_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # General, OBC, SC, ST
    is_taxpayer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_dpiit_recognition: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    business_incorporated_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    landholding_acres: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    is_differently_abled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disability_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    additional_attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    citizen: Mapped["CitizenModel"] = relationship("CitizenModel", back_populates="profile")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile attributes."""
        data: Dict[str, Any] = {
            "profile_id": self.profile_id,
            "citizen_id": self.citizen_id,
            "state": self.state,
            "district": self.district,
            "annual_income": float(self.annual_income) if self.annual_income is not None else None,
            "occupation": self.occupation,
            "category": self.category,
            "is_taxpayer": self.is_taxpayer,
            "has_dpiit_recognition": self.has_dpiit_recognition,
            "business_incorporated_years": self.business_incorporated_years,
            "landholding_acres": float(self.landholding_acres) if self.landholding_acres is not None else None,
            "is_differently_abled": self.is_differently_abled,
            "disability_percentage": float(self.disability_percentage) if self.disability_percentage is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if self.additional_attributes and isinstance(self.additional_attributes, dict):
            for k, v in self.additional_attributes.items():
                if k not in data:
                    data[k] = v
        return data


class ApplicationModel(Base):
    """External government application tracking records."""

    __tablename__ = "applications"

    application_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    citizen_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("citizens.citizen_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    submitted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    incubator_preference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    milestone_stage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pran_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    next_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    citizen: Mapped["CitizenModel"] = relationship("CitizenModel", back_populates="applications")
    status_history: Mapped[List["ApplicationStatusHistoryModel"]] = relationship(
        "ApplicationStatusHistoryModel",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistoryModel.created_at.desc()",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize application tracking record."""
        res: Dict[str, Any] = {
            "application_id": self.application_id,
            "citizen_id": self.citizen_id,
            "scheme_name": self.scheme_name,
            "status": self.status,
            "submitted_date": self.submitted_date.isoformat() if self.submitted_date else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "incubator_preference": self.incubator_preference,
            "milestone_stage": self.milestone_stage,
            "pran_status": self.pran_status,
            "next_step": self.next_step,
        }
        if self.details and isinstance(self.details, dict):
            for k, v in self.details.items():
                if k not in res:
                    res[k] = v
        return res


class ApplicationStatusHistoryModel(Base):
    """Audit log of status updates for scheme applications."""

    __tablename__ = "application_status_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    application: Mapped["ApplicationModel"] = relationship("ApplicationModel", back_populates="status_history")


class DocumentModel(Base):
    """Metadata and integrity hash for citizen uploaded documents.
    
    NOTE: Stores metadata, apparent classification, and SHA-256 integrity hash only;
    raw binary file blobs are stored in file storage.
    """

    __tablename__ = "documents"

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citizen_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("citizens.citizen_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    apparent_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    citizen: Mapped["CitizenModel"] = relationship("CitizenModel", back_populates="documents")
    extracted_fields: Mapped[List["DocumentExtractedFieldModel"]] = relationship(
        "DocumentExtractedFieldModel",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentExtractedFieldModel(Base):
    """Structured facts extracted by Document AI with assigned confidence and provenance."""

    __tablename__ = "document_extracted_fields"

    field_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    field_value: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    provenance_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="extracted_fields")


class CitizenNeedModel(Base):
    """Persisted citizen needs identified during multi-need detection (M6 integration)."""

    __tablename__ = "citizen_needs"

    need_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citizen_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("citizens.citizen_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    urgency: Mapped[str] = mapped_column(String(32), nullable=False)
    need_type: Mapped[str] = mapped_column(String(32), nullable=False)  # EXPLICIT or INFERRED
    statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    citizen: Mapped["CitizenModel"] = relationship("CitizenModel", back_populates="needs")


class EligibilityAssessmentModel(Base):
    """Audit log of deterministic eligibility assessments produced by Milestone 5 engine."""

    __tablename__ = "eligibility_assessments"

    assessment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citizen_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("citizens.citizen_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # ELIGIBLE, INELIGIBLE, INCONCLUSIVE
    passed_rules: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    failed_rules: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    missing_evidence: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    citizen: Mapped["CitizenModel"] = relationship("CitizenModel", back_populates="eligibility_assessments")


class GovernmentAPIAuditLogModel(Base):
    """Metadata-only audit log of external government API interactions (Milestone 8).

    SECURITY INVARIANT:
    Stores operational metadata only. Never records API keys, authorization tokens,
    citizen PII, or raw certificate responses.
    """

    __tablename__ = "government_api_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint_identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    data_freshness: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
