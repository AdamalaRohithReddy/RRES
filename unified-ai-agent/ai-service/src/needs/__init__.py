"""Multi-Need Detection package for Milestone 6."""
from src.needs.models import (
    NeedCategory,
    NeedType,
    NeedConfidenceLevel,
    Need,
    MultiNeedResult,
    DISCLAIMER_TEXT,
)
from src.needs.taxonomy import (
    CATEGORY_DESCRIPTIONS,
    LEXICON_PATTERNS,
    SUGGESTED_SCHEME_QUERIES,
)
from src.needs.deduplicator import NeedDeduplicator
from src.needs.detector import RuleBasedNeedDetector, NeedDetector
from src.needs.tracker import NeedTracker

__all__ = [
    "NeedCategory",
    "NeedType",
    "NeedConfidenceLevel",
    "Need",
    "MultiNeedResult",
    "DISCLAIMER_TEXT",
    "CATEGORY_DESCRIPTIONS",
    "LEXICON_PATTERNS",
    "SUGGESTED_SCHEME_QUERIES",
    "NeedDeduplicator",
    "RuleBasedNeedDetector",
    "NeedDetector",
    "NeedTracker",
]
