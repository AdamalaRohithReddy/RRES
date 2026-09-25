"""Unit tests for Semantic Chunker."""
from src.ingestion.models import ExtractedDocument, DocumentMetadata, PageExtraction, ExtractionStatus
from src.chunking.semantic_chunker import SemanticChunker


def create_mock_doc(text_p1: str, text_p2: str = "") -> ExtractedDocument:
    meta = DocumentMetadata(
        document_id="APY_doc1",
        file_name="apy.pdf",
        file_path="/data/apy.pdf",
        total_pages=2 if text_p2 else 1,
        checksum_sha256="abc123sha",
        scheme_id="APY",
        scheme_name="Atal Pension Yojana",
        source_url="https://financialservices.gov.in/apy",
        source_type="official",
        last_verified="2026-01-01",
    )
    pages = [
        PageExtraction(
            page_number=1,
            raw_text=text_p1,
            cleaned_text=text_p1,
            char_count=len(text_p1),
            status=ExtractionStatus.SUCCESS,
        )
    ]
    if text_p2:
        pages.append(
            PageExtraction(
                page_number=2,
                raw_text=text_p2,
                cleaned_text=text_p2,
                char_count=len(text_p2),
                status=ExtractionStatus.SUCCESS,
            )
        )
    return ExtractedDocument(
        document_id="APY_doc1",
        metadata=meta,
        pages=pages,
        extraction_status=ExtractionStatus.SUCCESS,
    )


def test_semantic_chunker_detects_sections():
    text_p1 = (
        "Overview of the Scheme\n"
        "Atal Pension Yojana is a pension scheme for unorganised workers.\n\n"
        "Eligibility Criteria\n"
        "The subscriber must be between 18 and 40 years old."
    )
    text_p2 = (
        "Benefits\n"
        "Guaranteed minimum pension of Rs 1,000 to Rs 5,000 per month.\n\n"
        "Required Documents\n"
        "Aadhaar card is mandatory for KYC."
    )
    doc = create_mock_doc(text_p1, text_p2)
    chunker = SemanticChunker(max_chunk_chars=500, chunk_overlap_chars=50)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 4
    sections = [c.section for c in chunks]
    assert "Overview" in sections
    assert "Eligibility" in sections
    assert "Benefits" in sections
    assert "Required Documents" in sections


def test_chunk_metadata_provenance_is_preserved():
    text_p1 = (
        "Eligibility Criteria\n"
        "The citizen must be aged 18 to 40 years."
    )
    doc = create_mock_doc(text_p1)
    chunker = SemanticChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.document_id == "APY_doc1"
    assert chunk.scheme_id == "APY"
    assert chunk.scheme_name == "Atal Pension Yojana"
    assert chunk.source_url == "https://financialservices.gov.in/apy"
    assert chunk.source_type == "official"
    assert chunk.last_verified == "2026-01-01"
    assert chunk.page_start == 1
    assert chunk.page_end == 1
    assert chunk.section == "Eligibility"
    assert "18 to 40 years" in chunk.text


def test_fallback_chunking_when_no_sections():
    text = (
        "This is an informal paragraph explaining support.\n"
        "Another paragraph with more details about financial assistance.\n"
        "A third paragraph describing the overall objectives."
    )
    doc = create_mock_doc(text)
    chunker = SemanticChunker(max_chunk_chars=120, chunk_overlap_chars=30)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 1
    assert all(c.section == "General" for c in chunks)
    assert chunks[0].scheme_id == "APY"


def test_empty_document_produces_no_chunks():
    doc = create_mock_doc("")
    doc.pages = []
    chunker = SemanticChunker()
    chunks = chunker.chunk_document(doc)
    assert chunks == []
