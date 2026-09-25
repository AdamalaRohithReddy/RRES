"""Unit tests for Milestone 4 Document AI and OCR pipeline."""
from pathlib import Path
import pytest

from src.document_ai.models import DocumentType, ConfidenceLevel
from src.document_ai.pipeline import DocumentProcessingPipeline
from src.document_ai.ocr import TesseractOCREngine
from src.document_ai.validator import DocumentFieldValidator
from src.document_ai.models import ExtractedField


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "documents"


# ---------------------------------------------------------------------------
# Test A: Digital Document Pipeline
# ---------------------------------------------------------------------------
def test_digital_document_pipeline_extraction_and_classification():
    pdf_path = FIXTURES_DIR / "digital_income_certificate.pdf"
    assert pdf_path.exists(), f"Fixture missing: {pdf_path}"

    pipeline = DocumentProcessingPipeline()
    result = pipeline.process(pdf_path)

    assert result.status == "success"
    # Verify no OCR was needed for selectable digital text
    assert result.ocr_used is False

    # Verify apparent document type classification (NOT authenticity verification)
    assert result.apparent_document_type == DocumentType.INCOME_CERTIFICATE
    assert result.document_type_confidence >= 0.70

    # Verify extracted fields
    fields = result.fields
    assert fields["annual_income"].value == 150000
    assert fields["annual_income"].confidence_level == ConfidenceLevel.HIGH
    assert fields["name"].value == "Demo Citizen"
    assert fields["age"].value == 28
    assert fields["gender"].value == "Male"
    assert fields["state"].value == "Telangana"
    assert fields["district"].value == "Hyderabad"

    # Verify page-level provenance
    assert fields["annual_income"].page == 1
    assert "1,50,000" in (fields["annual_income"].source_text or "")
    assert fields["name"].page == 1

    # Verify metadata
    assert result.metadata is not None
    assert result.metadata.total_pages == 1
    assert len(result.metadata.sha256_checksum) == 64


# ---------------------------------------------------------------------------
# Test B: Scanned Document OCR & Actual Field Recovery
# ---------------------------------------------------------------------------
def test_scanned_document_ocr_field_recovery():
    png_path = FIXTURES_DIR / "scanned_income_certificate.png"
    assert png_path.exists(), f"Fixture missing: {png_path}"

    ocr_engine = TesseractOCREngine()
    if not ocr_engine.is_available():
        pytest.skip(
            "Tesseract OCR engine / tessdata is not installed on this host. "
            "Skipping live OCR test with explicit notice rather than falsely passing."
        )

    pipeline = DocumentProcessingPipeline(ocr_engine=ocr_engine)
    result = pipeline.process(png_path)

    assert result.status == "success"
    # 1. Verify OCR was actually invoked
    assert result.ocr_used is True

    # 2. Verify actual recovery of known synthetic field data
    fields = result.fields
    assert fields["annual_income"].value == 150000, (
        f"Expected OCR to recover annual_income = 150000, got: {fields['annual_income'].value}"
    )
    assert fields["name"].value == "Demo Citizen", (
        f"Expected OCR to recover name = 'Demo Citizen', got: {fields['name'].value}"
    )
    assert fields["state"].value == "Telangana"
    assert fields["annual_income"].page == 1


# ---------------------------------------------------------------------------
# Test C: Missing Field Handling (Never Guess)
# ---------------------------------------------------------------------------
def test_missing_field_returns_none_without_guessing():
    pdf_path = FIXTURES_DIR / "missing_income_certificate.pdf"
    assert pdf_path.exists(), f"Fixture missing: {pdf_path}"

    pipeline = DocumentProcessingPipeline()
    result = pipeline.process(pdf_path)

    assert result.status == "success"
    fields = result.fields

    # Name is present
    assert fields["name"].value == "Demo Citizen"

    # Annual Income is completely absent: MUST be None, NEVER guessed
    assert fields["annual_income"].value is None
    assert fields["annual_income"].confidence_level == ConfidenceLevel.UNRELIABLE
    assert fields["annual_income"].source_text is None


# ---------------------------------------------------------------------------
# Test D: Operational Confidence Levels
# ---------------------------------------------------------------------------
def test_operational_confidence_levels_and_thresholds():
    # HIGH confidence
    high_field = ExtractedField(
        field="annual_income",
        value=150000,
        confidence=0.95,
        confidence_level=ConfidenceLevel.HIGH,
        page=1,
        source_text="Annual Income: Rs. 150000",
    )
    assert high_field.confidence_level == ConfidenceLevel.HIGH
    assert high_field.value == 150000

    # UNCERTAIN confidence emits warning during validation
    uncertain_field = ExtractedField(
        field="annual_income",
        value=150000,
        confidence=0.65,
        confidence_level=ConfidenceLevel.UNCERTAIN,
        page=1,
        source_text="Income: 150000",
    )
    validated, warnings = DocumentFieldValidator.validate({"annual_income": uncertain_field})
    assert validated["annual_income"].value == 150000
    assert any("UNCERTAIN confidence" in w for w in warnings)

    # UNRELIABLE confidence (< 0.50) forces value to None
    from src.document_ai.field_extractor import DeterministicFieldExtractor
    unreliable_field = DeterministicFieldExtractor._create_field(
        field_name="annual_income",
        value=150000,
        confidence=0.30,
        page=1,
        source_text="ambiguous text",
    )
    assert unreliable_field.confidence_level == ConfidenceLevel.UNRELIABLE
    assert unreliable_field.value is None


# ---------------------------------------------------------------------------
# Test E: Field Validation & Sanity Diagnostics
# ---------------------------------------------------------------------------
def test_field_validation_captures_diagnostics_without_crashing():
    # Negative income & out-of-range age
    fields = {
        "annual_income": ExtractedField(
            field="annual_income",
            value=-50000,
            confidence=0.90,
            confidence_level=ConfidenceLevel.HIGH,
        ),
        "age": ExtractedField(
            field="age",
            value=250,
            confidence=0.90,
            confidence_level=ConfidenceLevel.HIGH,
        ),
        "issue_date": ExtractedField(
            field="issue_date",
            value="99/99/2026",
            confidence=0.90,
            confidence_level=ConfidenceLevel.HIGH,
        ),
    }

    validated, warnings = DocumentFieldValidator.validate(fields)

    # Values should be invalidated to None
    assert validated["annual_income"].value is None
    assert validated["age"].value is None

    # Informative warnings compiled
    assert any("must be a non-negative number" in w for w in warnings)
    assert any("outside the plausible range" in w for w in warnings)
    assert any("out-of-range calendar values" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test G: Provenance Preservation
# ---------------------------------------------------------------------------
def test_document_provenance_preservation():
    pdf_path = FIXTURES_DIR / "digital_income_certificate.pdf"
    pipeline = DocumentProcessingPipeline()
    result = pipeline.process(pdf_path)

    for field_name, f in result.fields.items():
        if f.value is not None:
            assert f.page is not None, f"Field {field_name} missing page provenance"
            assert f.source_text is not None, f"Field {field_name} missing source_text provenance"
            assert f.confidence >= 0.50

    # Verify top-level integrity
    assert result.metadata.sha256_checksum is not None
    assert "authenticity" in result.disclaimer.lower()
