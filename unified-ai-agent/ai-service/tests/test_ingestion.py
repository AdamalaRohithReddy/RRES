"""Unit tests for PDF Ingestion Engine."""
import pytest
from pathlib import Path
import pymupdf

from src.ingestion.pdf_loader import (
    PDFIngestionEngine,
    PDFNotFoundError,
    CorruptedPDFError,
    DuplicateDocumentError,
)
from src.ingestion.models import ExtractionStatus


@pytest.fixture
def sample_text_pdf(tmp_path) -> Path:
    """Create a sample valid text PDF using PyMuPDF."""
    pdf_path = tmp_path / "sample_scheme.pdf"
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "Atal Pension Yojana (APY)\n\n"
        "1. Overview\n"
        "Atal Pension Yojana is a pension scheme for citizens in the unorganised sector.\n\n"
        "2. Eligibility Criteria\n"
        "Citizens between 18 and 40 years of age having a savings bank account can apply."
    )
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "3. Benefits\n"
        "Subscribers receive guaranteed minimum monthly pension of Rs. 1,000 to Rs. 5,000 at age 60.\n\n"
        "4. Required Documents\n"
        "Aadhaar card and bank account details are mandatory."
    )
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_empty_pdf(tmp_path) -> Path:
    """Create a PDF with an empty page."""
    pdf_path = tmp_path / "empty.pdf"
    doc = pymupdf.open()
    doc.new_page()  # Blank page without text or image
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_scanned_pdf(tmp_path) -> Path:
    """Create a synthetic scanned PDF (contains image, negligible text)."""
    pdf_path = tmp_path / "scanned.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    # Create a small pixmap image and insert it
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 100, 100), 0)
    page.insert_image(page.rect, pixmap=pix)
    # Negligible text (less than threshold of 50 chars)
    page.insert_text((50, 50), "p. 1")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_missing_pdf_raises_error():
    engine = PDFIngestionEngine()
    with pytest.raises(PDFNotFoundError):
        engine.ingest_pdf("non_existent_file.pdf")


def test_corrupted_zero_byte_pdf(tmp_path):
    empty_file = tmp_path / "zero_byte.pdf"
    empty_file.write_bytes(b"")
    engine = PDFIngestionEngine()
    with pytest.raises(CorruptedPDFError):
        engine.ingest_pdf(empty_file)


def test_successful_text_pdf_extraction(sample_text_pdf):
    engine = PDFIngestionEngine()
    extracted = engine.ingest_pdf(
        file_path=sample_text_pdf,
        scheme_id="APY",
        scheme_name="Atal Pension Yojana",
        source_url="https://www.npscra.nsdl.co.in",
    )

    assert extracted.extraction_status == ExtractionStatus.SUCCESS
    assert not extracted.ocr_required
    assert len(extracted.pages) == 2
    assert extracted.metadata.scheme_id == "APY"
    assert "Atal Pension Yojana" in extracted.pages[0].cleaned_text
    assert "18 and 40 years" in extracted.pages[0].cleaned_text
    assert "Rs. 1,000" in extracted.pages[1].cleaned_text


def test_empty_page_handling(sample_empty_pdf):
    engine = PDFIngestionEngine()
    extracted = engine.ingest_pdf(sample_empty_pdf)
    assert extracted.pages[0].status == ExtractionStatus.EMPTY_DOCUMENT
    assert extracted.pages[0].char_count == 0


def test_scanned_pdf_detection(sample_scanned_pdf):
    engine = PDFIngestionEngine(ocr_char_threshold=50)
    extracted = engine.ingest_pdf(sample_scanned_pdf)
    assert extracted.ocr_required is True
    assert extracted.extraction_status == ExtractionStatus.SCANNED_OCR_REQUIRED
    assert extracted.ocr_recommendation is not None
    assert "OCR is required" in extracted.ocr_recommendation


def test_duplicate_detection(sample_text_pdf):
    engine = PDFIngestionEngine()
    engine.ingest_pdf(sample_text_pdf)
    # Second ingestion of the same file should raise DuplicateDocumentError
    with pytest.raises(DuplicateDocumentError):
        engine.ingest_pdf(sample_text_pdf, allow_duplicate=False)
    # But should succeed if allow_duplicate is True
    doc2 = engine.ingest_pdf(sample_text_pdf, allow_duplicate=True)
    assert doc2 is not None
