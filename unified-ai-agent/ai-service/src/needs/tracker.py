"""Cumulative Multi-Turn Need Tracking Engine for Milestone 6."""
from typing import List, Dict, Optional
from src.needs.models import Need, NeedCategory, NeedType
from src.needs.deduplicator import NeedDeduplicator


class NeedTracker:
    """Maintains cumulative citizen needs across multi-turn conversational interactions.

    Implements simple, reliable cumulative aggregation:
    Turn 1: EMPLOYMENT
    Turn 2: + EDUCATION -> [EMPLOYMENT, EDUCATION]
    """

    def __init__(self, initial_needs: Optional[List[Need]] = None):
        self._needs_by_category: Dict[NeedCategory, Need] = {}
        if initial_needs:
            self.add_needs(initial_needs)

    def add_needs(self, new_needs: List[Need]) -> List[Need]:
        """Incorporate needs detected in the current turn into the cumulative session store."""
        for need in new_needs:
            # Ignore ambiguous needs if we already have concrete, domain-specific needs recorded
            if need.category == NeedCategory.UNKNOWN_AMBIGUOUS and len(self._needs_by_category) > 0:
                continue

            existing = self._needs_by_category.get(need.category)
            if existing is None:
                self._needs_by_category[need.category] = need
            else:
                # Merge existing and new mention for the same category
                merged = NeedDeduplicator.deduplicate([existing, need])
                if merged:
                    self._needs_by_category[need.category] = merged[0]

        return self.get_active_needs()

    def get_active_needs(self) -> List[Need]:
        """Return all cumulative needs recorded across the session."""
        return list(self._needs_by_category.values())

    def get_categories(self) -> List[NeedCategory]:
        """Return all unique need categories currently accumulated."""
        return list(self._needs_by_category.keys())

    def clear(self) -> None:
        """Reset the tracker."""
        self._needs_by_category.clear()

    def to_dict_list(self) -> List[dict]:
        """Export cumulative needs as list of dictionary records."""
        return [n.model_dump() for n in self.get_active_needs()]
