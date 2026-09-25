"""Database package for Milestone 7 (Real MySQL Integration)."""
from src.database.connection import (
    get_engine,
    get_session_factory,
    get_db_session,
    check_connection_health,
    init_db,
    drop_db,
    mask_connection_url,
)
from src.database.models import (
    Base,
    CitizenModel,
    CitizenProfileModel,
    ApplicationModel,
    ApplicationStatusHistoryModel,
    DocumentModel,
    DocumentExtractedFieldModel,
    CitizenNeedModel,
    EligibilityAssessmentModel,
)

__all__ = [
    "get_engine",
    "get_session_factory",
    "get_db_session",
    "check_connection_health",
    "init_db",
    "drop_db",
    "mask_connection_url",
    "Base",
    "CitizenModel",
    "CitizenProfileModel",
    "ApplicationModel",
    "ApplicationStatusHistoryModel",
    "DocumentModel",
    "DocumentExtractedFieldModel",
    "CitizenNeedModel",
    "EligibilityAssessmentModel",
]
