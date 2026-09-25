"""Sanity checks and range validation for extracted document fields."""
from typing import Dict, List, Tuple
from src.document_ai.models import ExtractedField, ConfidenceLevel


class DocumentFieldValidator:
    """Validates extracted fields against business logic constraints and emits diagnostics."""

    @classmethod
    def validate(cls, fields: Dict[str, ExtractedField]) -> Tuple[Dict[str, ExtractedField], List[str]]:
        """Validate field values, adjust confidence if sanity checks fail, and compile warnings.

        Args:
            fields: Dictionary of field_name -> ExtractedField.

        Returns:
            Tuple of (validated fields dictionary, list of warning strings).
        """
        warnings: List[str] = []
        validated = dict(fields)

        # 1. Validate Age
        age_field = validated.get("age")
        if age_field and age_field.value is not None:
            if not isinstance(age_field.value, int) or age_field.value < 0 or age_field.value > 120:
                warnings.append(
                    f"Extracted age '{age_field.value}' is outside the plausible range (0-120 years)."
                )
                validated["age"] = ExtractedField(
                    field="age",
                    value=None,
                    confidence=0.2,
                    confidence_level=ConfidenceLevel.UNRELIABLE,
                    page=age_field.page,
                    source_text=age_field.source_text,
                )

        # 2. Validate Annual Income
        income_field = validated.get("annual_income")
        if income_field and income_field.value is not None:
            if not isinstance(income_field.value, (int, float)) or income_field.value < 0:
                warnings.append(
                    f"Extracted annual income '{income_field.value}' is invalid (must be a non-negative number)."
                )
                validated["annual_income"] = ExtractedField(
                    field="annual_income",
                    value=None,
                    confidence=0.2,
                    confidence_level=ConfidenceLevel.UNRELIABLE,
                    page=income_field.page,
                    source_text=income_field.source_text,
                )
            elif income_field.confidence_level == ConfidenceLevel.UNCERTAIN:
                warnings.append(
                    f"Annual income '{income_field.value}' was extracted with UNCERTAIN confidence. Please verify with citizen."
                )

        # 3. Validate Dates (Issue Date & Date of Birth)
        for date_key in ["issue_date", "date_of_birth"]:
            df = validated.get(date_key)
            if df and df.value is not None:
                parts = str(df.value).split("/")
                if len(parts) == 3:
                    try:
                        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                        if not (1 <= d <= 31 and 1 <= m <= 12 and 1900 <= y <= 2100):
                            warnings.append(f"Extracted {date_key} '{df.value}' contains out-of-range calendar values.")
                    except ValueError:
                        warnings.append(f"Extracted {date_key} '{df.value}' has an unparseable format.")
                else:
                    warnings.append(f"Extracted {date_key} '{df.value}' does not conform to DD/MM/YYYY format.")

        return validated, warnings
