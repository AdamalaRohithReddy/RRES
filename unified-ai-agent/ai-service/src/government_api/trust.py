"""Application-controlled Source Trust Model for Government APIs."""

from typing import Dict, Optional
from src.government_api.models import GovernmentSource, SourceType, VerificationStatus


# Canonical source definitions
SOURCE_API_SETU_MYSCHEME = GovernmentSource(
    source_id="API_SETU_MYSCHEME",
    organization="National e-Governance Division (NeGD), Ministry of Electronics & IT",
    source_type=SourceType.OFFICIAL_GOVERNMENT_API,
    official_domain="apisetu.gov.in",
    verification_status=VerificationStatus.CONTRACT_VERIFIED,
    allowed_operations=["search_schemes", "get_scheme_details"],
    documentation_url="https://apisetu.gov.in/",
)

SOURCE_API_SETU_DIGILOCKER = GovernmentSource(
    source_id="API_SETU_DIGILOCKER",
    organization="DigiLocker / NeGD, Ministry of Electronics & IT",
    source_type=SourceType.OFFICIAL_GOVERNMENT_API,
    official_domain="apisetu.gov.in",
    verification_status=VerificationStatus.CONTRACT_VERIFIED,
    allowed_operations=["verify_income_certificate"],
    documentation_url="https://apisetu.gov.in/",
)

SOURCE_DATA_GOV_IN = GovernmentSource(
    source_id="DATA_GOV_IN",
    organization="National Informatics Centre (NIC), Ministry of Electronics & IT",
    source_type=SourceType.OFFICIAL_GOVERNMENT_PORTAL,
    official_domain="data.gov.in",
    verification_status=VerificationStatus.VERIFIED_AT_PLATFORM_LEVEL,
    allowed_operations=["get_catalog_records"],
    documentation_url="https://data.gov.in/",
)

SOURCE_LOCAL_MYSQL = GovernmentSource(
    source_id="LOCAL_MYSQL_DB",
    organization="Citizen AI Internal Application Store",
    source_type=SourceType.LOCAL_MYSQL,
    official_domain="localhost",
    verification_status=VerificationStatus.VERIFIED,
    allowed_operations=["get_citizen_profile", "get_application_status"],
    documentation_url="local://mysql/citizen_ai_db",
)

SOURCE_SANDBOX_FIXTURE = GovernmentSource(
    source_id="SANDBOX_CONTRACT_FIXTURE",
    organization="Official API Contract Test Environment",
    source_type=SourceType.SANDBOX_FIXTURE,
    official_domain="localhost",
    verification_status=VerificationStatus.CONTRACT_VERIFIED,
    allowed_operations=["search_schemes", "get_scheme_details", "verify_income_certificate"],
    documentation_url="file://tests/fixtures/government_api/",
)


class GovernmentSourceRegistry:
    """Registry maintaining authoritative sources and their operational constraints."""

    def __init__(self):
        self._sources: Dict[str, GovernmentSource] = {
            SOURCE_API_SETU_MYSCHEME.source_id: SOURCE_API_SETU_MYSCHEME,
            SOURCE_API_SETU_DIGILOCKER.source_id: SOURCE_API_SETU_DIGILOCKER,
            SOURCE_DATA_GOV_IN.source_id: SOURCE_DATA_GOV_IN,
            SOURCE_LOCAL_MYSQL.source_id: SOURCE_LOCAL_MYSQL,
            SOURCE_SANDBOX_FIXTURE.source_id: SOURCE_SANDBOX_FIXTURE,
        }

    def get_source(self, source_id: str) -> Optional[GovernmentSource]:
        """Retrieve source descriptor by unique ID."""
        return self._sources.get(source_id)

    def is_operation_permitted(self, source_id: str, operation: str) -> bool:
        """Check if an operation is explicitly authorized for a source."""
        source = self.get_source(source_id)
        if not source:
            return False
        return operation in source.allowed_operations


_GLOBAL_SOURCE_REGISTRY: Optional[GovernmentSourceRegistry] = None


def get_source_registry() -> GovernmentSourceRegistry:
    """Get singleton instance of GovernmentSourceRegistry."""
    global _GLOBAL_SOURCE_REGISTRY
    if _GLOBAL_SOURCE_REGISTRY is None:
        _GLOBAL_SOURCE_REGISTRY = GovernmentSourceRegistry()
    return _GLOBAL_SOURCE_REGISTRY
