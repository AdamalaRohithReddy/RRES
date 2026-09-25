"""Deterministic value normalization utility for eligibility evidence attributes."""
import re
from typing import Any, Optional, Tuple


class ValueNormalizer:
    """Normalizes raw citizen and document values into clean types for deterministic comparison."""

    @staticmethod
    def normalize_currency(val: Any) -> Optional[float]:
        """Convert currency strings (e.g. '₹ 2,40,000', 'Rs. 10 Lakhs', '150000') to float."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)

        s = str(val).strip()
        if not s:
            return None

        # Check for Lakhs / Crores
        lakh_match = re.search(r"([\d\.]+)\s*(?:lakh|lakhs|lac|lacs)", s, re.IGNORECASE)
        if lakh_match:
            try:
                num = float(lakh_match.group(1))
                return num * 100000.0
            except ValueError:
                pass

        crore_match = re.search(r"([\d\.]+)\s*(?:crore|crores|cr)", s, re.IGNORECASE)
        if crore_match:
            try:
                num = float(crore_match.group(1))
                return num * 10000000.0
            except ValueError:
                pass

        # Strip currency symbols, commas, and whitespace
        clean_s = re.sub(r"[₹Rs\.\,\s/–-]", "", s)
        # Extract remaining digits and optional decimal
        match = re.search(r"(\d+(?:\.\d+)?)", clean_s)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def normalize_number(val: Any) -> Optional[float]:
        """Normalize numeric values (e.g. '28', 28, '2.5', '2 years')."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)

        s = str(val).strip()
        if not s:
            return None

        # Try direct conversion
        try:
            return float(s)
        except ValueError:
            pass

        # Extract leading or standalone number
        match = re.search(r"(\d+(?:\.\d+)?)", s)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def normalize_boolean(val: Any) -> Optional[bool]:
        """Normalize boolean inputs (True, False, 'yes', 'no', 'true', 'false', '1', '0')."""
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)

        s = str(val).strip().lower()
        if s in {"true", "yes", "y", "1", "recognized", "active", "eligible"}:
            return True
        if s in {"false", "no", "n", "0", "unrecognized", "inactive", "ineligible"}:
            return False
        return None

    @staticmethod
    def normalize_string(val: Any) -> Optional[str]:
        """Clean and trim string for case-insensitive comparison."""
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    @classmethod
    def normalize_for_comparison(cls, val: Any, expected_type: type) -> Tuple[Any, bool]:
        """Attempt to cast `val` to match the type of threshold.

        Returns (normalized_value, success).
        """
        if val is None:
            return None, False

        if expected_type is bool or isinstance(expected_type, bool):
            norm = cls.normalize_boolean(val)
            return (norm, norm is not None)

        if expected_type in (int, float):
            # Check if this could be currency or number
            norm = cls.normalize_currency(val)
            if norm is None:
                norm = cls.normalize_number(val)
            if norm is not None:
                if expected_type is int:
                    return int(round(norm)), True
                return float(norm), True
            return None, False

        if expected_type is str:
            norm = cls.normalize_string(val)
            return (norm, norm is not None)

        return val, True
