"""Conservative deterministic field extraction for citizen-support documents."""
import re
from typing import Dict, List, Optional, Tuple, Any
from src.document_ai.models import ExtractedField, ConfidenceLevel, ExtractedPageText


class DeterministicFieldExtractor:
    """Extracts citizen-relevant document fields using conservative regex patterns and heuristics.

    NOTE: English-oriented patterns initially. Multilingual expansion (Telugu, Hindi,
    complex regional scripts) is marked as a future enhancement.
    """

    INDIAN_STATES = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry"
    ]

    @classmethod
    def extract_fields(cls, pages: List[ExtractedPageText]) -> Dict[str, ExtractedField]:
        """Extract all supported fields across document pages.

        Args:
            pages: List of ExtractedPageText with page numbers and cleaned text.

        Returns:
            Dictionary of field_name -> ExtractedField.
        """
        fields: Dict[str, ExtractedField] = {}

        # 1. Annual Income
        fields["annual_income"] = cls._extract_income(pages)

        # 2. Citizen Name
        fields["name"] = cls._extract_name(pages)

        # 3. Age
        fields["age"] = cls._extract_age(pages)

        # 4. Gender
        fields["gender"] = cls._extract_gender(pages)

        # 5. Date of Birth
        fields["date_of_birth"] = cls._extract_dob(pages)

        # 6. State
        fields["state"] = cls._extract_state(pages)

        # 7. District
        fields["district"] = cls._extract_district(pages)

        # 8. Occupation
        fields["occupation"] = cls._extract_occupation(pages)

        # 9. Document / Application Number
        fields["document_number"] = cls._extract_doc_number(pages)

        # 10. Issue Date
        fields["issue_date"] = cls._extract_issue_date(pages)

        return fields

    @classmethod
    def _create_field(
        cls,
        field_name: str,
        value: Optional[Any],
        confidence: float,
        page: Optional[int],
        source_text: Optional[str],
    ) -> ExtractedField:
        """Create an ExtractedField adhering to the operational confidence policy."""
        if confidence >= 0.85:
            level = ConfidenceLevel.HIGH
        elif confidence >= 0.50:
            level = ConfidenceLevel.UNCERTAIN
        else:
            level = ConfidenceLevel.UNRELIABLE

        # If unreliable, force value to None (NO guessing)
        final_value = value if level != ConfidenceLevel.UNRELIABLE else None

        return ExtractedField(
            field=field_name,
            value=final_value,
            confidence=round(confidence, 2),
            confidence_level=level,
            page=page,
            source_text=source_text,
        )

    @classmethod
    def _extract_income(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        patterns = [
            (r"(?:Annual\s+Income|Total\s+(?:Annual\s+)?(?:Family\s+)?Income)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)", 0.95),
            (r"(?:from\s+all\s+sources\s+is\s+(?:Rs\.?|INR|₹)?\s*([\d,]+))", 0.90),
            (r"(?:Income\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+))", 0.82),
        ]
        for p in pages:
            for pattern, base_conf in patterns:
                match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
                if match:
                    raw_val = match.group(1).replace(",", "")
                    try:
                        income_num = int(float(raw_val))
                        # Snippet for provenance
                        snippet = match.group(0).strip()
                        return cls._create_field(
                            field_name="annual_income",
                            value=income_num,
                            confidence=base_conf if not p.ocr_used else base_conf - 0.05,
                            page=p.page_number,
                            source_text=snippet,
                        )
                    except ValueError:
                        continue

        return cls._create_field("annual_income", None, 0.0, None, None)

    @classmethod
    def _extract_name(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        patterns = [
            (r"(?:Name(?:\s+of\s+the\s+Citizen|\s+of\s+Applicant)?)\s*[:\-]?\s*(?:Sri/Smt\.?|Sri\.?|Smt\.?|Mr\.?|Ms\.?)?\s*([A-Za-z\s]{3,35})(?=\n|$|,|\s{2,})", 0.94),
            (r"This\s+is\s+to\s+certify\s+that\s+(?:Sri/Smt\.?|Sri\.?|Smt\.?|Mr\.?|Ms\.?)?\s*([A-Za-z\s]{3,35})(?=,|\s+Son|\s+Daughter|\s+Wife|\s+residing)", 0.92),
        ]
        for p in pages:
            for pattern, base_conf in patterns:
                match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
                if match:
                    name_val = match.group(1).strip()
                    # Filter out obvious false positives
                    if len(name_val) >= 3 and not any(k in name_val.lower() for k in ["certificate", "department", "telangana", "revenue", "annual"]):
                        snippet = match.group(0).strip()
                        return cls._create_field(
                            field_name="name",
                            value=name_val,
                            confidence=base_conf if not p.ocr_used else base_conf - 0.05,
                            page=p.page_number,
                            source_text=snippet,
                        )

        return cls._create_field("name", None, 0.0, None, None)

    @classmethod
    def _extract_age(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        patterns = [
            (r"\bAge\s*[:\-]?\s*(\d{1,3})\b", 0.95),
            (r"\b(\d{1,3})\s*years\s*(?:of\s*age)?\b", 0.85),
        ]
        for p in pages:
            for pattern, base_conf in patterns:
                match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
                if match:
                    try:
                        age_val = int(match.group(1))
                        return cls._create_field(
                            field_name="age",
                            value=age_val,
                            confidence=base_conf if not p.ocr_used else base_conf - 0.05,
                            page=p.page_number,
                            source_text=match.group(0).strip(),
                        )
                    except ValueError:
                        continue

        return cls._create_field("age", None, 0.0, None, None)

    @classmethod
    def _extract_gender(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        pattern = r"\b(?:Gender|Sex)\s*[:\-]?\s*(Male|Female|Transgender)\b"
        for p in pages:
            match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
            if match:
                g_val = match.group(1).capitalize()
                return cls._create_field(
                    field_name="gender",
                    value=g_val,
                    confidence=0.95 if not p.ocr_used else 0.90,
                    page=p.page_number,
                    source_text=match.group(0).strip(),
                )
        return cls._create_field("gender", None, 0.0, None, None)

    @classmethod
    def _extract_dob(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        pattern = r"\b(?:DOB|Date\s+of\s+Birth)\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})\b"
        for p in pages:
            match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
            if match:
                dob_val = match.group(1).replace(".", "/").replace("-", "/")
                return cls._create_field(
                    field_name="date_of_birth",
                    value=dob_val,
                    confidence=0.92 if not p.ocr_used else 0.86,
                    page=p.page_number,
                    source_text=match.group(0).strip(),
                )
        return cls._create_field("date_of_birth", None, 0.0, None, None)

    @classmethod
    def _extract_state(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        for p in pages:
            # Check explicit State: <Name>
            match = re.search(r"\bState\s*[:\-]?\s*([A-Za-z\s]+?)(?=\n|$|,|\s{2,})", p.cleaned_text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                for state in cls.INDIAN_STATES:
                    if candidate.lower() == state.lower():
                        return cls._create_field(
                            field_name="state",
                            value=state,
                            confidence=0.95 if not p.ocr_used else 0.90,
                            page=p.page_number,
                            source_text=match.group(0).strip(),
                        )

            # Check known state mentions in text
            for state in cls.INDIAN_STATES:
                if re.search(rf"\b{re.escape(state)}\s*(?:State)?\b", p.cleaned_text, re.IGNORECASE):
                    return cls._create_field(
                        field_name="state",
                        value=state,
                        confidence=0.88 if not p.ocr_used else 0.83,
                        page=p.page_number,
                        source_text=f"Mentioned: {state}",
                    )

        return cls._create_field("state", None, 0.0, None, None)

    @classmethod
    def _extract_district(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        patterns = [
            r"\bDistrict\s*[:\-]?\s*([A-Za-z]+)\b",
            r"\b([A-Za-z]+)\s+District\b",
        ]
        for p in pages:
            for pattern in patterns:
                match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
                if match:
                    dist = match.group(1).strip()
                    if dist.lower() not in ["revenue", "the", "this", "state", "income"]:
                        return cls._create_field(
                            field_name="district",
                            value=dist.capitalize(),
                            confidence=0.88 if not p.ocr_used else 0.82,
                            page=p.page_number,
                            source_text=match.group(0).strip(),
                        )
        return cls._create_field("district", None, 0.0, None, None)

    @classmethod
    def _extract_occupation(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        pattern = r"\bOccupation\s*[:\-]?\s*([A-Za-z\s]+?)(?=\n|$|,|\s{2,})"
        for p in pages:
            match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
            if match:
                occ = match.group(1).strip()
                if len(occ) >= 3:
                    return cls._create_field(
                        field_name="occupation",
                        value=occ,
                        confidence=0.86 if not p.ocr_used else 0.80,
                        page=p.page_number,
                        source_text=match.group(0).strip(),
                    )
        return cls._create_field("occupation", None, 0.0, None, None)

    @classmethod
    def _extract_doc_number(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        patterns = [
            r"\b(?:Certificate\s+No|Application\s+No|Doc\s+No|Registration\s+No)\s*[:\-]?\s*([A-Za-z0-9\-/]+)\b",
        ]
        for p in pages:
            for pattern in patterns:
                match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
                if match:
                    doc_no = match.group(1).strip()
                    return cls._create_field(
                        field_name="document_number",
                        value=doc_no,
                        confidence=0.92 if not p.ocr_used else 0.86,
                        page=p.page_number,
                        source_text=match.group(0).strip(),
                    )
        return cls._create_field("document_number", None, 0.0, None, None)

    @classmethod
    def _extract_issue_date(cls, pages: List[ExtractedPageText]) -> ExtractedField:
        pattern = r"\b(?:Date\s+of\s+Issue|Issued\s+on)\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})\b"
        for p in pages:
            match = re.search(pattern, p.cleaned_text, re.IGNORECASE)
            if match:
                date_val = match.group(1).replace(".", "/").replace("-", "/")
                return cls._create_field(
                    field_name="issue_date",
                    value=date_val,
                    confidence=0.90 if not p.ocr_used else 0.85,
                    page=p.page_number,
                    source_text=match.group(0).strip(),
                )
        return cls._create_field("issue_date", None, 0.0, None, None)
