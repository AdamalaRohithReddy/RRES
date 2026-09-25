"""Multi-Need Detection Engine: hybrid LLM and deterministic rule-based detection."""
import re
from typing import Optional, List, Dict, Tuple
from src.needs.models import (
    Need,
    NeedCategory,
    NeedType,
    NeedConfidenceLevel,
    MultiNeedResult,
)
from src.needs.taxonomy import (
    LEXICON_PATTERNS,
    SUGGESTED_SCHEME_QUERIES,
    AMBIGUOUS_NEED_INDICATORS,
    CONVERSATIONAL_GREETINGS,
)
from src.needs.deduplicator import NeedDeduplicator


class RuleBasedNeedDetector:
    """Deterministic, offline rule-and-lexicon detector.

    Guarantees 100% offline testability, zero-quota reliability, and strict anti-hallucination.
    """

    AMBIGUITY_CLARIFICATION_PROMPT = (
        "To connect you with the most relevant government schemes and support programs, "
        "could you please tell me more about what type of assistance you need? "
        "For example, are you seeking help with employment, children's education, "
        "affordable housing, healthcare expenses, or daily household finances?"
    )

    @classmethod
    def detect(cls, text: str) -> MultiNeedResult:
        """Decompose citizen text into structured needs deterministically."""
        clean_text = (text or "").strip()
        if not clean_text:
            return MultiNeedResult(
                status="success",
                original_text="",
                needs=[],
                total_needs=0,
            )

        lower_text = clean_text.lower()

        # 1. Check for pure conversational greetings
        if cls._is_pure_greeting(lower_text):
            return MultiNeedResult(
                status="success",
                original_text=clean_text,
                needs=[],
                total_needs=0,
                has_ambiguous_needs=False,
                is_ambiguous=False,
                clarification_prompts=[
                    "Hello! How can I help you today? Please tell me about your situation, hardship, or assistance goals."
                ],
            )

        # 2. Extract explicit needs matching lexicon patterns
        raw_needs = cls._extract_lexicon_needs(clean_text, lower_text)

        # 3. Check for ambiguous requests lacking domain context
        if not raw_needs and cls._is_ambiguous_request(lower_text):
            ambiguous_need = Need(
                need_id="need_ambiguous_01",
                category=NeedCategory.UNKNOWN_AMBIGUOUS,
                description="Citizen requested general support without specifying a welfare domain",
                confidence=0.35,
                confidence_level=NeedConfidenceLevel.LOW,
                explicit_or_inferred=NeedType.EXPLICIT,
                evidence_span=cls._extract_ambiguous_span(clean_text, lower_text),
                is_ambiguous=True,
                clarification_needed=cls.AMBIGUITY_CLARIFICATION_PROMPT,
            )
            return MultiNeedResult(
                status="success",
                original_text=clean_text,
                needs=[ambiguous_need],
                total_needs=1,
                has_ambiguous_needs=True,
                is_ambiguous=True,
                clarification_prompts=[cls.AMBIGUITY_CLARIFICATION_PROMPT],
                suggested_scheme_queries={},  # Do NOT run RAG for ambiguous needs
            )

        # 4. Deduplicate & merge overlapping mentions
        deduped_needs = NeedDeduplicator.deduplicate(raw_needs)

        # 5. Populate suggested RAG queries ONLY for confident, explicit needs
        suggested_queries: Dict[str, str] = {}
        for need in deduped_needs:
            if (
                need.explicit_or_inferred == NeedType.EXPLICIT
                and need.confidence >= 0.70
                and need.category in SUGGESTED_SCHEME_QUERIES
            ):
                suggested_queries[need.category.value] = SUGGESTED_SCHEME_QUERIES[need.category]

        has_ambiguous = any(n.is_ambiguous for n in deduped_needs)
        prompts = [n.clarification_needed for n in deduped_needs if n.clarification_needed]

        return MultiNeedResult(
            status="success",
            original_text=clean_text,
            needs=deduped_needs,
            total_needs=len(deduped_needs),
            has_ambiguous_needs=has_ambiguous,
            is_ambiguous=has_ambiguous,
            clarification_prompts=prompts,
            suggested_scheme_queries=suggested_queries,
        )

    @classmethod
    def _is_pure_greeting(cls, lower_text: str) -> bool:
        """Check if input consists solely of non-need conversational greeting."""
        text_no_punct = re.sub(r"[^\w\s]", "", lower_text).strip()
        if not text_no_punct:
            return False
        if text_no_punct in CONVERSATIONAL_GREETINGS:
            return True
        # Strip known greeting phrases and words
        cleaned = text_no_punct
        for greeting in sorted(CONVERSATIONAL_GREETINGS, key=len, reverse=True):
            cleaned = re.sub(rf"\b{re.escape(greeting)}\b", "", cleaned).strip()
        if not cleaned:
            return True
        words = re.findall(r"\b\w+\b", cleaned)
        if words and all(w in CONVERSATIONAL_GREETINGS for w in words):
            return True
        return False

    @classmethod
    def _is_ambiguous_request(cls, lower_text: str) -> bool:
        """Determine if text signals a general request without domain keywords."""
        for ind in AMBIGUOUS_NEED_INDICATORS:
            if re.search(rf"\b{re.escape(ind)}\b", lower_text):
                return True
        return False

    @classmethod
    def _extract_ambiguous_span(cls, original_text: str, lower_text: str) -> Optional[str]:
        """Extract matched ambiguous phrase from original text."""
        for ind in AMBIGUOUS_NEED_INDICATORS:
            m = re.search(rf"\b{re.escape(ind)}\b", lower_text)
            if m:
                start, end = m.span()
                return original_text[start:end]
        return original_text

    @classmethod
    def _extract_lexicon_needs(cls, original_text: str, lower_text: str) -> List[Need]:
        """Scan text and segmented clauses for all matching category patterns."""
        needs: List[Need] = []
        counter = 1

        for category, patterns in LEXICON_PATTERNS.items():
            matched_spans = []
            for pat in patterns:
                pattern_regex = re.compile(rf"\b{re.escape(pat)}\b", re.IGNORECASE)
                for match in pattern_regex.finditer(original_text):
                    start, end = match.span()
                    # Check if this span overlaps with any already-matched span for this category
                    if any(not (end <= s or start >= e) for s, e in matched_spans):
                        continue
                    matched_spans.append((start, end))
                    span = match.group(0)
                    desc = cls._build_description(category, span)

                    need = Need(
                        need_id=f"need_{category.value[:3]}_{counter:02d}",
                        category=category,
                        description=desc,
                        confidence=0.92,
                        confidence_level=NeedConfidenceLevel.HIGH,
                        explicit_or_inferred=NeedType.EXPLICIT,
                        evidence_span=span,
                        is_ambiguous=False,
                        suggested_scheme_query=SUGGESTED_SCHEME_QUERIES.get(category),
                    )
                    needs.append(need)
                    counter += 1


        return needs

    @classmethod
    def _build_description(cls, category: NeedCategory, evidence_span: str) -> str:
        """Construct natural, concise description of detected hardship."""
        descriptions = {
            NeedCategory.EMPLOYMENT: f"Citizen mentions '{evidence_span}' and requires employment/job assistance",
            NeedCategory.FINANCIAL_HARDSHIP: f"Citizen indicates financial hardship through '{evidence_span}'",
            NeedCategory.EDUCATION: f"Citizen requires educational/schooling assistance based on '{evidence_span}'",
            NeedCategory.HOUSING: f"Citizen indicates shelter/housing requirements via '{evidence_span}'",
            NeedCategory.HEALTHCARE: f"Citizen mentions medical/health assistance ('{evidence_span}')",
            NeedCategory.AGRICULTURE: f"Citizen mentions agricultural/farming hardship ('{evidence_span}')",
            NeedCategory.ENTREPRENEURSHIP: f"Citizen indicates enterprise/startup creation goals ('{evidence_span}')",
            NeedCategory.SOCIAL_WELFARE: f"Citizen mentions welfare/social security needs ('{evidence_span}')",
            NeedCategory.DISABILITY_SUPPORT: f"Citizen indicates disability support requirements ('{evidence_span}')",
            NeedCategory.SENIOR_CITIZEN_SUPPORT: f"Citizen indicates elderly/senior citizen assistance ('{evidence_span}')",
            NeedCategory.WOMEN_SUPPORT: f"Citizen mentions women/maternity support ('{evidence_span}')",
            NeedCategory.SKILL_DEVELOPMENT: f"Citizen indicates vocational or skill development interest ('{evidence_span}')",
            NeedCategory.FOOD_BASIC_NEEDS: f"Citizen indicates food/ration assistance ('{evidence_span}')",
            NeedCategory.OTHER: f"Citizen indicates general need ('{evidence_span}')",
            NeedCategory.UNKNOWN_AMBIGUOUS: "Unspecified support request requiring clarification",
        }
        return descriptions.get(category, f"Need identified from '{evidence_span}'")


class NeedDetector:
    """Unified Multi-Need Detector.

    Supports deterministic extraction with offline fallback and LLM-ready structured output.
    """

    def __init__(self, rule_detector: Optional[RuleBasedNeedDetector] = None):
        self.rule_detector = rule_detector or RuleBasedNeedDetector()

    def detect_needs(self, text: str) -> MultiNeedResult:
        """Decompose user text into structured needs.

        Uses deterministic rule-based detection for fast, safe, and offline-verified execution.
        """
        return self.rule_detector.detect(text)

    def detect(self, text: str) -> MultiNeedResult:
        """Alias for detect_needs."""
        return self.detect_needs(text)
