"""Semantic and Structure-Aware Document Chunker.

Divides official scheme documents into logical sections (Overview, Benefits, Eligibility, etc.)
and generates chunks with complete source provenance and page numbers.
"""
import re
from typing import List, Tuple, Optional
from src.ingestion.models import ExtractedDocument, PageExtraction
from src.chunking.models import DocumentChunk


# Known standard government scheme section categories and their regex patterns
KNOWN_SECTIONS = [
    ("Overview", re.compile(r"^(?:(?:1\.|section\s+1[:.]?|chapter\s+1[:.]?)\s*)?(?:overview|introduction|about\s+the\s+scheme|background|objective)", re.IGNORECASE)),
    ("Benefits", re.compile(r"^(?:(?:\d+\.|section\s+\d+[:.]?)\s*)?(?:benefits|entitlements|financial\s+assistance|pension\s+amount|coverage|sum\s+assured|assistance)", re.IGNORECASE)),
    ("Eligibility", re.compile(r"^(?:(?:\d+\.|section\s+\d+[:.]?)\s*)?(?:eligibility(?:\s+criteria)?|who\s+can\s+apply|who\s+is\s+eligible|target\s+beneficiaries|beneficiary\s+criteria|age\s+criteria|income\s+limit)", re.IGNORECASE)),
    ("Required Documents", re.compile(r"^(?:(?:\d+\.|section\s+\d+[:.]?)\s*)?(?:required\s+documents|documents?\s+required|documentation|mandatory\s+documents|kyc\s+documents)", re.IGNORECASE)),
    ("Application Process", re.compile(r"^(?:(?:\d+\.|section\s+\d+[:.]?)\s*)?(?:application\s+process|how\s+to\s+apply|enrolment(?:\s+process)?|registration(?:\s+process)?|procedure|application\s+procedure)", re.IGNORECASE)),
    ("Important Conditions", re.compile(r"^(?:(?:\d+\.|section\s+\d+[:.]?)\s*)?(?:important\s+conditions|terms\s+(?:and|&)\s+conditions|exit\s+(?:and|&)\s+discontinuation|default|penalty|tax\s+benefits|conditions)", re.IGNORECASE)),
    ("State Availability", re.compile(r"^(?:(?:\d+\.|section\s+\d+[:.]?)\s*)?(?:state\s+availability|geographic\s+scope|applicability|jurisdiction)", re.IGNORECASE)),
    ("FAQs", re.compile(r"^(?:(?:\d+\.|section\s+\d+[:.]?)\s*)?(?:faqs?|frequently\s+asked\s+questions|grievance\s+redressal|nodal\s+agencies)", re.IGNORECASE)),
]


class SemanticChunker:
    """Chunks documents into semantically coherent blocks using section awareness and sliding windows."""

    def __init__(
        self,
        max_chunk_chars: int = 1000,
        chunk_overlap_chars: int = 150,
        min_chunk_chars: int = 80,
    ):
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap_chars = chunk_overlap_chars
        self.min_chunk_chars = min_chunk_chars

    @staticmethod
    def _match_section(line: str) -> Optional[str]:
        """Detect whether a line is a section heading."""
        cleaned = line.strip().rstrip(":-.")
        for section_name, pattern in KNOWN_SECTIONS:
            if pattern.search(cleaned):
                return section_name
        return None

    def chunk_document(self, document: ExtractedDocument) -> List[DocumentChunk]:
        """Split an ExtractedDocument into DocumentChunks with full provenance."""
        if not document.pages:
            return []

        # Step 1: Collect text segments with page attribution
        # Each line or block has an associated page number
        elements: List[Tuple[str, int]] = []
        for page in document.pages:
            if not page.cleaned_text:
                continue
            lines = page.cleaned_text.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped:
                    elements.append((stripped, page.page_number))

        if not elements:
            return []

        # Step 2: Detect sections and group elements
        sections_found: List[Tuple[str, List[Tuple[str, int]]]] = []
        current_section = "Overview"
        current_elements: List[Tuple[str, int]] = []
        detected_any_section = False

        for text, page_num in elements:
            matched = self._match_section(text)
            if matched:
                detected_any_section = True
                if current_elements:
                    sections_found.append((current_section, current_elements))
                    current_elements = []
                current_section = matched
            current_elements.append((text, page_num))

        if current_elements:
            sections_found.append((current_section, current_elements))

        # If no explicit sections were found, treat everything as fallback sliding window
        if not detected_any_section:
            return self._fallback_chunking(document, elements)

        # Step 3: Within each section, produce bounded chunks
        chunks: List[DocumentChunk] = []
        chunk_idx = 1

        for section_name, sec_elements in sections_found:
            section_chunks = self._chunk_element_sequence(
                sec_elements=sec_elements,
                section_name=section_name,
                document=document,
                start_chunk_idx=chunk_idx,
            )
            chunks.extend(section_chunks)
            chunk_idx += len(section_chunks)

        return chunks

    def _chunk_element_sequence(
        self,
        sec_elements: List[Tuple[str, int]],
        section_name: str,
        document: ExtractedDocument,
        start_chunk_idx: int,
    ) -> List[DocumentChunk]:
        """Break a list of (text_line, page_num) into chunks bounded by max_chunk_chars."""
        chunks: List[DocumentChunk] = []
        curr_lines: List[str] = []
        curr_pages: List[int] = []
        curr_len = 0
        idx = start_chunk_idx

        for text, page_num in sec_elements:
            line_len = len(text) + 1  # including newline
            if curr_len + line_len > self.max_chunk_chars and curr_len >= self.min_chunk_chars:
                # Flush current chunk
                chunk_text = "\n".join(curr_lines).strip()
                page_start = min(curr_pages)
                page_end = max(curr_pages)
                chunk_id = f"{document.document_id}_chunk_{idx:03d}"

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        scheme_id=document.metadata.scheme_id,
                        scheme_name=document.metadata.scheme_name,
                        text=chunk_text,
                        page_start=page_start,
                        page_end=page_end,
                        section=section_name,
                        source_type=document.metadata.source_type,
                        source_url=document.metadata.source_url,
                        last_verified=document.metadata.last_verified,
                    )
                )
                idx += 1

                # Retain overlap lines
                overlap_lines: List[str] = []
                overlap_pages: List[int] = []
                overlap_len = 0
                for ol_line, ol_page in reversed(list(zip(curr_lines, curr_pages))):
                    if overlap_len + len(ol_line) > self.chunk_overlap_chars:
                        break
                    overlap_lines.insert(0, ol_line)
                    overlap_pages.insert(0, ol_page)
                    overlap_len += len(ol_line) + 1

                curr_lines = overlap_lines
                curr_pages = overlap_pages
                curr_len = overlap_len

            curr_lines.append(text)
            curr_pages.append(page_num)
            curr_len += line_len

        # Flush final residual chunk
        if curr_lines:
            chunk_text = "\n".join(curr_lines).strip()
            if len(chunk_text) >= 20:  # Avoid empty / trivial single punctuation leftovers
                page_start = min(curr_pages)
                page_end = max(curr_pages)
                chunk_id = f"{document.document_id}_chunk_{idx:03d}"

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        scheme_id=document.metadata.scheme_id,
                        scheme_name=document.metadata.scheme_name,
                        text=chunk_text,
                        page_start=page_start,
                        page_end=page_end,
                        section=section_name,
                        source_type=document.metadata.source_type,
                        source_url=document.metadata.source_url,
                        last_verified=document.metadata.last_verified,
                    )
                )

        return chunks

    def _fallback_chunking(
        self, document: ExtractedDocument, elements: List[Tuple[str, int]]
    ) -> List[DocumentChunk]:
        """Fallback chunking when no semantic headings are detected."""
        return self._chunk_element_sequence(
            sec_elements=elements,
            section_name="General",
            document=document,
            start_chunk_idx=1,
        )
