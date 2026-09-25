"""DigiLocker Income Certificate Adapter implementing API Setu Pull contract (Milestone 8.3)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.government_api.adapters.base import BaseGovernmentAPIAdapter
from src.government_api.client import GovernmentAPIClient
from src.government_api.exceptions import GovernmentAPIError, TimeoutError, RateLimitError
from src.government_api.models import (
    APIResponseStatus,
    DataFreshness,
    GovernmentSource,
    NormalizedGovernmentResponse,
    SourceType,
    VerificationStatus,
)
from src.government_api.provenance import build_government_response
from src.government_api.trust import SOURCE_API_SETU_DIGILOCKER

logger = logging.getLogger(__name__)


class DigiLockerIncomeCertificate(BaseModel):
    """Schema for verified income certificate from DigiLocker."""
    certificate_id: str
    certificate_type: str = "INCER"
    holder_name: str
    annual_income: float
    state: str
    issuing_authority: str
    issue_date: str
    valid_until: Optional[str] = None
    verification_status: str = "VALID"
    source_system: str


class DigiLockerCertificateAdapter(BaseGovernmentAPIAdapter):
    """Adapter for verifying income certificates via API Setu DigiLocker contract."""

    def __init__(
        self,
        client: Optional[GovernmentAPIClient] = None,
        fixtures_dir: Optional[Path] = None,
    ):
        self._client = client or GovernmentAPIClient()
        self._fixtures_dir = fixtures_dir or (Path(__file__).resolve().parent.parent.parent.parent / "tests" / "fixtures" / "government_api")

    @property
    def adapter_id(self) -> str:
        return "digilocker_incer"

    @property
    def source(self) -> GovernmentSource:
        return SOURCE_API_SETU_DIGILOCKER

    def execute(self, operation: str, params: Dict[str, Any]) -> NormalizedGovernmentResponse:
        """Execute certificate verification without caching sensitive citizen records."""
        self.validate_operation(operation)

        if operation == "verify_income_certificate":
            return self._verify_income_certificate(params)
        else:
            raise GovernmentAPIError(f"Unsupported operation '{operation}' for DigiLocker adapter.")

    def _verify_income_certificate(self, params: Dict[str, Any]) -> NormalizedGovernmentResponse:
        """Verify an electronic income certificate.

        SECURITY INVARIANT:
        Certificate verification results are NEVER stored in public metadata cache to protect citizen PII.
        """
        cert_id = (params.get("certificate_id") or "").strip()
        state = (params.get("state") or "").strip()
        holder_name = (params.get("holder_name") or "").strip()

        if not cert_id:
            return build_government_response(
                status=APIResponseStatus.SCHEMA_ERROR,
                data_source=SourceType.SANDBOX_FIXTURE,
                verification_status=VerificationStatus.UNVERIFIED,
                provider=self.source.organization,
                api_name="DigiLocker Certificate Verification API",
                endpoint_identifier="APISETU_DIGILOCKER_INCER",
                source_url=self.source.documentation_url,
                error_details={"message": "Missing certificate_id for verification."},
            )

        settings = get_settings()

        # Check if actual external API endpoint (production or official sandbox) is configured
        if settings.gov_api_enabled and settings.apisetu_api_key:
            try:
                headers = {
                    "X-APISETU-CLIENTID": settings.apisetu_client_id or "",
                    "X-APISETU-APIKEY": settings.apisetu_api_key.get_secret_value() if hasattr(settings.apisetu_api_key, "get_secret_value") else str(settings.apisetu_api_key),
                }
                api_url = f"{settings.apisetu_base_url.rstrip('/')}/digilocker/certificate/incer/{cert_id}"
                live_payload = self._client.get(api_url, params={"state": state}, headers=headers)

                # Actual authorized production API vs actual official sandbox endpoint
                ver_tier = (
                    VerificationStatus.PRODUCTION_CONNECTED
                    if settings.gov_api_environment == "production"
                    else VerificationStatus.SANDBOX_VERIFIED
                )

                return build_government_response(
                    status=APIResponseStatus.SUCCESS,
                    data_source=SourceType.OFFICIAL_GOVERNMENT_API,
                    verification_status=ver_tier,
                    provider=self.source.organization,
                    api_name="DigiLocker Certificate Verification API",
                    endpoint_identifier="APISETU_DIGILOCKER_INCER",
                    source_url=self.source.documentation_url,
                    payload=live_payload,
                    data_freshness=DataFreshness.LIVE,
                )
            except (TimeoutError, RateLimitError, GovernmentAPIError) as exc:
                logger.warning("Live DigiLocker certificate verification failed: %s", str(exc))
                return build_government_response(
                    status=APIResponseStatus.VERIFICATION_UNAVAILABLE,
                    data_source=SourceType.OFFICIAL_GOVERNMENT_API,
                    verification_status=VerificationStatus.UNVERIFIED,
                    provider=self.source.organization,
                    api_name="DigiLocker Certificate Verification API",
                    endpoint_identifier="APISETU_DIGILOCKER_INCER",
                    source_url=self.source.documentation_url,
                    error_details={"error_type": type(exc).__name__, "message": str(exc)},
                )

        # Local Synthetic Fixture Mode: strictly CONTRACT_VERIFIED
        fixture_file = self._fixtures_dir / "apisetu_digilocker_incer.json"
        if not fixture_file.exists():
            return build_government_response(
                status=APIResponseStatus.VERIFICATION_UNAVAILABLE,
                data_source=SourceType.SANDBOX_FIXTURE,
                verification_status=VerificationStatus.UNVERIFIED,
                provider=self.source.organization,
                api_name="DigiLocker Certificate Verification API",
                endpoint_identifier="APISETU_DIGILOCKER_INCER",
                source_url=self.source.documentation_url,
                error_details={"message": f"Contract fixture missing at {fixture_file}"},
            )

        with open(fixture_file, "r", encoding="utf-8") as f:
            raw_fixture = json.load(f)

        fixture_data = raw_fixture.get("data", {})

        # Verify whether requested ID matches contract fixture
        if cert_id != fixture_data.get("certificate_id") and cert_id != "DEFAULT":
            return build_government_response(
                status=APIResponseStatus.NOT_FOUND,
                data_source=SourceType.SANDBOX_FIXTURE,
                verification_status=VerificationStatus.UNVERIFIED,
                provider=self.source.organization,
                api_name="DigiLocker Certificate Verification API",
                endpoint_identifier="APISETU_DIGILOCKER_INCER",
                source_url=self.source.documentation_url,
                error_details={"message": f"Certificate '{cert_id}' not found in verification records."},
            )

        # Local synthetic fixture is strictly CONTRACT_VERIFIED
        return build_government_response(
            status=APIResponseStatus.SUCCESS,
            data_source=SourceType.SANDBOX_FIXTURE,
            verification_status=VerificationStatus.CONTRACT_VERIFIED,
            provider=self.source.organization,
            api_name="DigiLocker Certificate Verification API",
            endpoint_identifier="APISETU_DIGILOCKER_INCER",
            source_url=self.source.documentation_url,
            payload=fixture_data,
            data_freshness=DataFreshness.LIVE,
        )
