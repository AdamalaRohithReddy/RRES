"""Evidence Harvester: aggregates and reconciles citizen profile data and Document AI facts."""
from typing import Dict, Any, Optional, List, Union
from src.eligibility.models import (
    EligibilityEvidence,
    EvidenceSource,
)
from src.eligibility.normalizer import ValueNormalizer
from src.document_ai.models import DocumentAnalysisResult, ExtractedField, ConfidenceLevel


class EvidenceHarvester:
    """Aggregates, normalizes, and reconciles citizen profile attributes and Document AI facts."""

    def __init__(self):
        self.evidence_store: Dict[str, EligibilityEvidence] = {}
        self.warnings: List[str] = []

    def harvest(
        self,
        profile_data: Optional[Dict[str, Any]] = None,
        document_data: Optional[Union[Dict[str, Any], DocumentAnalysisResult]] = None,
        user_overrides: Optional[Dict[str, Any]] = None,
        api_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, EligibilityEvidence]:
        """Aggregate evidence from citizen profile, document analysis, explicit overrides, and government APIs."""
        # 1. Ingest Citizen Profile
        if profile_data:
            self._ingest_profile(profile_data)

        # 2. Ingest Document AI facts with conflict reconciliation
        if document_data:
            self._ingest_document(document_data)

        # 3. Ingest Government API verified facts with conflict policy (M8)
        if api_data:
            self._ingest_government_api(api_data)

        # 4. Ingest User Overrides
        if user_overrides:
            self._ingest_overrides(user_overrides)

        return self.evidence_store

    def _ingest_profile(self, profile_data: Dict[str, Any]) -> None:
        """Process citizen profile attributes (e.g. from MySQL mock)."""
        data = profile_data
        # If output of CitizenProfileTool.execute is passed
        if "profile" in data and isinstance(data["profile"], dict):
            citizen_id = data.get("citizen_id", "demo-user")
            data = data["profile"]
        else:
            citizen_id = data.get("citizen_id", "demo-user")

        for k, v in data.items():
            if k in {"status", "data_source", "notice", "is_mock"}:
                continue
            self.evidence_store[k] = EligibilityEvidence(
                field_name=k,
                value=v,
                raw_value=v,
                source=EvidenceSource.CITIZEN_PROFILE,
                confidence=0.90,
                confidence_level="HIGH",
                source_reference=f"citizen_profile:{citizen_id}",
                fact_type="LOCAL_STORED_FACT",
                verification_status="UNVERIFIED",
            )

    def _ingest_document(self, document_data: Union[Dict[str, Any], DocumentAnalysisResult]) -> None:
        """Process extracted fields from Document AI analysis and reconcile conflicts."""
        doc_type = "document"
        fields: Dict[str, Any] = {}

        if isinstance(document_data, DocumentAnalysisResult):
            doc_type = document_data.apparent_document_type.value
            fields = document_data.fields
        elif isinstance(document_data, dict):
            doc_type = document_data.get("apparent_document_type", "document")
            fields = document_data.get("fields", {})

        for field_name, field_obj in fields.items():
            # Parse field representation
            if isinstance(field_obj, ExtractedField):
                val = field_obj.value
                conf = field_obj.confidence
                conf_level = field_obj.confidence_level.value
                page = field_obj.page
                src_txt = field_obj.source_text
            elif isinstance(field_obj, dict):
                val = field_obj.get("value")
                conf = float(field_obj.get("confidence", 0.0))
                conf_level = str(field_obj.get("confidence_level", "UNRELIABLE"))
                page = field_obj.get("page")
                src_txt = field_obj.get("source_text")
            else:
                val = field_obj
                conf = 0.85
                conf_level = "HIGH"
                page = 1
                src_txt = str(field_obj)

            # Check for conflict with existing profile evidence
            existing = self.evidence_store.get(field_name)
            if existing is not None:
                # If document extraction is unreliable or empty, ignore it and keep existing profile
                if val is None or conf < 0.50 or conf_level == "UNRELIABLE":
                    msg = (
                        f"Ignored unreliable document extraction for '{field_name}' "
                        f"(confidence {conf:.2f} < 0.50)."
                    )
                    self.warnings.append(msg)
                    continue

                # Compare values using normalized representations
                norm_existing, _ = ValueNormalizer.normalize_for_comparison(existing.value, type(val) if val is not None else str)
                norm_doc, _ = ValueNormalizer.normalize_for_comparison(val, type(norm_existing) if norm_existing is not None else str)

                if norm_existing != norm_doc and norm_doc is not None and norm_existing is not None:
                    if conf >= 0.85:
                        # High confidence document evidence takes precedence
                        msg = (
                            f"Evidence Conflict on '{field_name}': Profile reported '{existing.value}', "
                            f"but verified document ({doc_type}) indicates '{val}' (confidence {conf:.2f}). "
                            f"Document evidence prioritized."
                        )
                        self.warnings.append(msg)
                        self.evidence_store[field_name] = EligibilityEvidence(
                            field_name=field_name,
                            value=val,
                            raw_value=val,
                            source=EvidenceSource.DOCUMENT_AI,
                            confidence=conf,
                            confidence_level=conf_level,
                            source_reference=f"document_ai:{doc_type}",
                            page=page,
                            source_text=src_txt,
                        )
                        continue
                    else:
                        # Uncertain document evidence - retain profile or flag discrepancy
                        msg = (
                            f"Evidence Discrepancy on '{field_name}': Profile reported '{existing.value}' vs "
                            f"document value '{val}' (confidence {conf:.2f}, UNCERTAIN). Retaining profile with warning."
                        )
                        self.warnings.append(msg)
                        continue


            # No prior conflict, store document evidence
            self.evidence_store[field_name] = EligibilityEvidence(
                field_name=field_name,
                value=val,
                raw_value=val,
                source=EvidenceSource.DOCUMENT_AI,
                confidence=conf,
                confidence_level=conf_level,
                source_reference=f"document_ai:{doc_type}",
                page=page,
                source_text=src_txt,
            )

    def _ingest_overrides(self, overrides: Dict[str, Any]) -> None:
        """Process explicit overrides provided by caller."""
        for k, v in overrides.items():
            self.evidence_store[k] = EligibilityEvidence(
                field_name=k,
                value=v,
                raw_value=v,
                source=EvidenceSource.USER_INPUT,
                confidence=1.0,
                confidence_level="HIGH",
                source_reference="user_override",
            )

    def _ingest_government_api(self, api_data: Dict[str, Any]) -> None:
        """Process externally verified facts from official Government APIs and reconcile conflicts (M8)."""
        data = api_data
        provider = data.get("provider", "Official Government API")
        endpoint = data.get("endpoint_identifier", "government_api")
        ver_status = data.get("verification_status", "CONTRACT_VERIFIED")

        if "payload" in data and isinstance(data["payload"], dict):
            data = data["payload"]

        for k, v in data.items():
            if k in {"status", "data_source", "verification_status", "provider", "retrieved_at", "source_url", "source_system"}:
                continue
            if v is None:
                continue

            existing = self.evidence_store.get(k)
            conflict_detected = False
            conflicting_values = None

            if existing is not None and existing.value is not None:
                norm_existing, _ = ValueNormalizer.normalize_for_comparison(existing.value, type(v))
                norm_api, _ = ValueNormalizer.normalize_for_comparison(v, type(norm_existing) if norm_existing is not None else str)

                if norm_existing != norm_api:
                    conflict_detected = True
                    conflicting_values = {
                        "prior_value": existing.value,
                        "prior_source": existing.source.value,
                        "api_verified_value": v,
                    }
                    msg = (
                        f"Evidence Conflict on '{k}': Prior {existing.source.value} recorded '{existing.value}', "
                        f"but official Government API verified value is '{v}'. "
                        f"Externally verified government evidence prioritized for statutory assessment with discrepancy flag."
                    )
                    self.warnings.append(msg)

            self.evidence_store[k] = EligibilityEvidence(
                field_name=k,
                value=v,
                raw_value=v,
                source=EvidenceSource.GOVERNMENT_API,
                confidence=1.0,
                confidence_level="HIGH",
                source_reference=f"gov_api:{endpoint}:{provider}",
                fact_type="EXTERNALLY_VERIFIED_FACT",
                verification_status=ver_status,
                conflict_detected=conflict_detected,
                conflicting_values=conflicting_values,
            )
