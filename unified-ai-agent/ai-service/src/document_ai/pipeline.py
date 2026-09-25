"""End-to-end Document AI processing pipeline."""
import hashlib
from pathlib import Path
from typing import Optional, List
import pymupdf

from src.document_ai.models import (
    DocumentAnalysisResult,
    DocumentMetadata,
    DocumentType,
)
from src.document_ai.extractor import DocumentTextExtractor
from src.document_ai.detector import DocumentTypeDetector
from src.document_ai.field_extractor import DeterministicFieldExtractor
from src.document_ai.validator import DocumentFieldValidator
from src.document_ai.ocr import TesseractOCREngine


class DocumentProcessingError(Exception):
    """Base exception for document processing failures."""
    pass


class DocumentNotFoundError(DocumentProcessingError):
    """Raised when the specified document file does not exist."""
    pass


class CorruptedDocumentError(DocumentProcessingError):
    """Raised when the document is empty (0 bytes) or corrupted."""
    pass


class UnsupportedDocumentFormatError(DocumentProcessingError):
    """Raised when an unapproved file extension is provided."""
    pass


class DocumentSizeLimitExceededError(DocumentProcessingError):
    """Raised when file size exceeds the 20 MB limit."""
    pass


class DocumentProcessingPipeline:
    """Coordinates validation, text extraction, OCR fallback, classification, field extraction, and validation."""

    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB limit
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        ocr_engine: Optional[TesseractOCREngine] = None,
        char_threshold: Optional[int] = None,
    ):
        self.ocr_engine = ocr_engine or TesseractOCREngine()
        self.extractor = DocumentTextExtractor(
            ocr_engine=self.ocr_engine,
            char_threshold=char_threshold,
        )

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute SHA256 checksum of document bytes."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process(self, file_path: str | Path) -> DocumentAnalysisResult:
        """Process a document file through the full Document AI pipeline.

        Args:
            file_path: Absolute or resolved path to target document.

        Returns:
            DocumentAnalysisResult containing apparent document type, extracted fields,
            operational confidence levels, warnings, and page provenance.
        """
        path = Path(file_path).resolve()

        # 1. Existence check
        if not path.exists() or not path.is_file():
            raise DocumentNotFoundError(f"Document file not found at: {path}")

        # 2. Extension validation
        ext = path.suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise UnsupportedDocumentFormatError(
                f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )

        # 3. File size checks (empty or oversized)
        size_bytes = path.stat().st_size
        if size_bytes == 0:
            raise CorruptedDocumentError(f"Document file is empty (0 bytes): {path.name}")
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            raise DocumentSizeLimitExceededError(
                f"Document size ({size_bytes / (1024*1024):.1f} MB) exceeds maximum limit of 20 MB."
            )

        # 4. Checksum and initial metadata
        checksum = self.compute_sha256(path)
        mime_type = "application/pdf" if ext == ".pdf" else f"image/{ext.lstrip('.')}"

        # 5. Extract text (with OCR fallback when required)
        try:
            pages, ocr_used = self.extractor.extract(path)
        except Exception as e:
            raise CorruptedDocumentError(f"Failed to read or parse document '{path.name}': {e}") from e

        if not pages:
            raise CorruptedDocumentError(f"Document '{path.name}' contains no readable pages.")

        total_pages = len(pages)
        metadata = DocumentMetadata(
            file_name=path.name,
            file_path=str(path),
            file_size_bytes=size_bytes,
            total_pages=total_pages,
            sha256_checksum=checksum,
            mime_type=mime_type,
        )

        full_text = "\n".join(p.cleaned_text for p in pages)

        # 6. Classify apparent document type
        apparent_type, type_confidence = DocumentTypeDetector.classify(full_text)

        # 7. Extract deterministic structured fields
        raw_fields = DeterministicFieldExtractor.extract_fields(pages)

        # 8. Validate extracted fields & compile diagnostics
        validated_fields, warnings = DocumentFieldValidator.validate(raw_fields)

        # Add global warning if document unreadable or unknown
        if apparent_type == DocumentType.UNKNOWN and not any(f.value is not None for f in validated_fields.values()):
            warnings.append(
                "Document appears unreadable or could not be classified into a recognized category. "
                "Please verify document quality."
            )

        return DocumentAnalysisResult(
            status="success",
            apparent_document_type=apparent_type,
            document_type_confidence=type_confidence,
            ocr_used=ocr_used,
            fields=validated_fields,
            warnings=warnings,
            metadata=metadata,
        )
