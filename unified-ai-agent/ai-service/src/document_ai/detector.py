"""Apparent document type classification using observable textual features."""
import re
from typing import Tuple, Dict, List
from src.document_ai.models import DocumentType


class DocumentTypeDetector:
    """Classifies the apparent document type based on observable textual features.

    IMPORTANT: Document type classification is not document authenticity verification.
    The system identifies what a document appears to be based on text evidence;
    it does NOT verify whether a document is genuine, legally valid, or government-authenticated.
    """

    FEATURE_KEYWORDS: Dict[DocumentType, List[Tuple[str, float]]] = {
        DocumentType.INCOME_CERTIFICATE: [
            (r"\bincome\s+certificate\b", 0.45),
            (r"\bannual\s+(?:family\s+)?income\b", 0.30),
            (r"\btotal\s+(?:annual\s+)?income\b", 0.25),
            (r"\btahasildar\b", 0.20),
            (r"\brevenue\s+department\b", 0.20),
            (r"\bmeeseva\b", 0.15),
            (r"\bfrom\s+all\s+sources\b", 0.15),
        ],
        DocumentType.IDENTITY_DOCUMENT: [
            (r"\belection\s+commission\b", 0.40),
            (r"\bvoter\s+(?:id|card)\b", 0.40),
            (r"\belectoral\s+photo\b", 0.35),
            (r"\bdriving\s+licen[cs]e\b", 0.40),
            (r"\bidentity\s+card\b", 0.30),
            (r"\bpassport\b", 0.40),
        ],
        DocumentType.ADDRESS_DOCUMENT: [
            (r"\bresidence\s+certificate\b", 0.40),
            (r"\bdomicile\s+certificate\b", 0.40),
            (r"\belectricity\s+bill\b", 0.35),
            (r"\bwater\s+bill\b", 0.35),
            (r"\bration\s+card\b", 0.35),
            (r"\bconsumer\s+no\b", 0.25),
        ],
        DocumentType.EDUCATION_CERTIFICATE: [
            (r"\bmarks\s+(?:memo|sheet)\b", 0.40),
            (r"\bboard\s+of\s+intermediate\b", 0.40),
            (r"\bsecondary\s+school\b", 0.35),
            (r"\bdegree\s+certificate\b", 0.40),
            (r"\buniversity\b", 0.25),
            (r"\bprovisional\s+certificate\b", 0.35),
        ],
    }

    CONFIDENCE_THRESHOLD = 0.35

    @classmethod
    def classify(cls, full_text: str) -> Tuple[DocumentType, float]:
        """Classify the apparent document type from observable text content.

        Args:
            full_text: Complete concatenated text extracted from the document.

        Returns:
            Tuple of (apparent DocumentType, confidence score 0.0 to 1.0).
        """
        if not full_text or len(full_text.strip()) < 10:
            return DocumentType.UNKNOWN, 0.0

        text_lower = full_text.lower()
        scores: Dict[DocumentType, float] = {dtype: 0.0 for dtype in cls.FEATURE_KEYWORDS}

        for dtype, patterns in cls.FEATURE_KEYWORDS.items():
            for pattern, weight in patterns:
                if re.search(pattern, text_lower):
                    scores[dtype] += weight

        # Normalize score capped at 0.98 (we never claim 1.00 authenticity)
        best_type = DocumentType.UNKNOWN
        best_score = 0.0

        for dtype, score in scores.items():
            capped = min(round(score, 2), 0.98)
            if capped > best_score:
                best_score = capped
                best_type = dtype

        if best_score >= cls.CONFIDENCE_THRESHOLD:
            return best_type, best_score

        return DocumentType.UNKNOWN, round(best_score, 2)
