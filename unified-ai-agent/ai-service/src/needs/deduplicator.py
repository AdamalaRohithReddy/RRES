"""Need deduplication and merging engine for Milestone 6."""
from typing import List, Dict
from src.needs.models import Need, NeedCategory, NeedType, NeedConfidenceLevel


class NeedDeduplicator:
    """Consolidates duplicate or co-occurring need mentions within the same domain category."""

    @classmethod
    def deduplicate(cls, needs: List[Need]) -> List[Need]:
        """Merge needs sharing the same category into a single, comprehensive Need representation."""
        if not needs:
            return []

        grouped: Dict[NeedCategory, List[Need]] = {}
        for n in needs:
            grouped.setdefault(n.category, []).append(n)

        merged: List[Need] = []
        for cat, items in grouped.items():
            if len(items) == 1:
                merged.append(items[0])
                continue

            # Merge multiple occurrences within the same category
            best_confidence = max(item.confidence for item in items)
            if best_confidence >= 0.80:
                best_conf_level = NeedConfidenceLevel.HIGH
            elif best_confidence >= 0.50:
                best_conf_level = NeedConfidenceLevel.MEDIUM
            else:
                best_conf_level = NeedConfidenceLevel.LOW

            # If any mention is explicit, the consolidated need is explicit
            has_explicit = any(item.explicit_or_inferred == NeedType.EXPLICIT for item in items)
            final_type = NeedType.EXPLICIT if has_explicit else NeedType.INFERRED

            # Consolidate evidence spans uniquely
            unique_spans = []
            for item in items:
                if item.evidence_span and item.evidence_span not in unique_spans:
                    unique_spans.append(item.evidence_span)
            merged_span = ", ".join(unique_spans) if unique_spans else None

            # Consolidate descriptions
            unique_descs = []
            for item in items:
                if item.description and item.description not in unique_descs:
                    unique_descs.append(item.description)
            merged_desc = "; ".join(unique_descs)

            # Consolidate related categories
            all_related = []
            for item in items:
                for r in item.related_categories:
                    if r not in all_related and r != cat:
                        all_related.append(r)

            # Check ambiguity
            is_ambiguous = any(item.is_ambiguous for item in items)
            clarification = next((item.clarification_needed for item in items if item.clarification_needed), None)

            consolidated = Need(
                need_id=items[0].need_id,
                category=cat,
                description=merged_desc,
                confidence=round(best_confidence, 2),
                confidence_level=best_conf_level,
                explicit_or_inferred=final_type,
                evidence_span=merged_span,
                is_ambiguous=is_ambiguous,
                clarification_needed=clarification,
                related_categories=all_related,
                suggested_scheme_query=items[0].suggested_scheme_query,
            )
            merged.append(consolidated)

        # Sort by confidence descending (highest confidence first)
        merged.sort(key=lambda n: n.confidence, reverse=True)
        return merged
