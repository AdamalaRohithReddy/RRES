"""PDF Ingestion Module for Official Scheme Documents using PyMuPDF."""
import hashlib
from pathlib import Path
from typing import Optional, Dict, Set
import pymupdf

from src.ingestion.models import (
    ExtractionStatus,
    PageExtraction,
    DocumentMetadata,
    ExtractedDocument,
)
from src.ingestion.cleaner import TextCleaner
from src.config.settings import get_settings


class DocumentIngestionError(Exception):
    """Base exception for document ingestion failures."""
    pass


class PDFNotFoundError(DocumentIngestionError):
    """Raised when the specified PDF file cannot be found."""
    pass


class CorruptedPDFError(DocumentIngestionError):
    """Raised when the PDF file is corrupted or unreadable."""
    pass


class DuplicateDocumentError(DocumentIngestionError):
    """Raised when attempting to re-ingest an already processed document."""
    pass


class OCRFallbackProvider:
    """Architectural interface for plugging in future OCR engines (e.g., Tesseract, EasyOCR)."""

    def is_available(self) -> bool:
        """Indicate whether an OCR engine is currently installed and active."""
        return False

    def extract_text_from_page(self, page: pymupdf.Page) -> str:
        """Extract text from a scanned page image."""
        raise NotImplementedError(
            "OCR Fallback engine is not yet configured for Milestone 1. "
            "Scanned document detected: please provide a text-based PDF or configure OCR in Milestone 2."
        )


class PDFIngestionEngine:
    """Ingests official government scheme PDFs, detects scanned documents, and extracts text."""

    def __init__(
        self,
        ocr_char_threshold: Optional[int] = None,
        ocr_provider: Optional[OCRFallbackProvider] = None,
    ):
        settings = get_settings()
        self.ocr_char_threshold = (
            ocr_char_threshold if ocr_char_threshold is not None else settings.ocr_char_threshold_per_page
        )
        self.ocr_provider = ocr_provider or OCRFallbackProvider()
        # In-memory registry of ingested document checksums to prevent accidental duplicates
        self._ingested_checksums: Set[str] = set()

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute the SHA256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def ingest_pdf(
        self,
        file_path: str | Path,
        scheme_id: Optional[str] = None,
        scheme_name: Optional[str] = None,
        source_url: Optional[str] = None,
        source_type: str = "official",
        last_verified: Optional[str] = None,
        allow_duplicate: bool = False,
    ) -> ExtractedDocument:
        """Ingest and extract structured text from a PDF file.

        Args:
            file_path: Path to the target PDF.
            scheme_id: Short scheme identifier (e.g., APY, PMJJBY).
            scheme_name: Full official name of the scheme.
            source_url: Provenance URL where document was published.
            source_type: Type of official source (official, circular, etc.).
            last_verified: Date the scheme data was verified.
            allow_duplicate: Whether to allow re-ingesting documents with identical checksum.

        Returns:
            ExtractedDocument containing metadata, page extractions, and status.
        """
        path = Path(file_path).resolve()

        # 1. Validate file existence
        if not path.exists() or not path.is_file():
            raise PDFNotFoundError(f"PDF file not found at path: {path}")

        # 2. Check for empty/zero-byte file
        if path.stat().st_size == 0:
            raise CorruptedPDFError(f"PDF file is empty (0 bytes): {path}")

        # 3. Check for duplicates via SHA-256
        checksum = self.compute_sha256(path)
        if not allow_duplicate and checksum in self._ingested_checksums:
            raise DuplicateDocumentError(
                f"Document '{path.name}' with checksum {checksum[:8]}... has already been ingested."
            )

        # 4. Open with PyMuPDF and handle corruption
        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            raise CorruptedPDFError(f"Failed to open PDF '{path.name}'. File may be corrupted or encrypted: {e}") from e

        total_pages = len(doc)
        if total_pages == 0:
            doc.close()
            raise CorruptedPDFError(f"PDF '{path.name}' contains 0 pages.")

        document_id = f"{scheme_id or path.stem}_{checksum[:8]}"
        doc_metadata = DocumentMetadata(
            document_id=document_id,
            file_name=path.name,
            file_path=str(path),
            total_pages=total_pages,
            checksum_sha256=checksum,
            scheme_id=scheme_id,
            scheme_name=scheme_name or path.stem.replace("_", " ").title(),
            source_url=source_url,
            source_type=source_type,
            last_verified=last_verified,
        )

        page_extractions = []
        scanned_page_count = 0
        empty_page_count = 0
        total_extracted_chars = 0

        # 5. Extract text page-by-page
        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1

            raw_text = page.get_text("text") or ""
            char_count = len(raw_text.strip())
            images = page.get_images()
            image_count = len(images) if images else 0

            # Determine if page is empty or likely scanned
            is_empty = char_count == 0
            is_scanned_likely = char_count < self.ocr_char_threshold and image_count > 0

            cleaned_text = TextCleaner.clean(raw_text)

            # If page is scanned and OCR provider is available, attempt fallback
            if is_scanned_likely and self.ocr_provider.is_available():
                ocr_text = self.ocr_provider.extract_text_from_page(page)
                if ocr_text:
                    cleaned_text = TextCleaner.clean(ocr_text)
                    char_count = len(cleaned_text)
                    is_scanned_likely = False

            if is_empty:
                empty_page_count += 1
                page_status = ExtractionStatus.EMPTY_DOCUMENT
            elif is_scanned_likely:
                scanned_page_count += 1
                page_status = ExtractionStatus.SCANNED_OCR_REQUIRED
            else:
                page_status = ExtractionStatus.SUCCESS

            total_extracted_chars += char_count

            page_extractions.append(
                PageExtraction(
                    page_number=page_num,
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    char_count=char_count,
                    image_count=image_count,
                    status=page_status,
                    is_scanned_likely=is_scanned_likely,
                )
            )

        doc.close()

        # 6. Assess overall document status
        is_document_scanned = (
            scanned_page_count > 0 and (scanned_page_count / total_pages >= 0.5)
        ) or (total_extracted_chars < self.ocr_char_threshold * total_pages and scanned_page_count > 0)

        if total_extracted_chars == 0 and scanned_page_count == 0:
            doc_status = ExtractionStatus.EMPTY_DOCUMENT
            ocr_required = False
            ocr_recommendation = "Document contains no text or images."
        elif is_document_scanned:
            doc_status = ExtractionStatus.SCANNED_OCR_REQUIRED
            ocr_required = True
            ocr_recommendation = (
                f"Document appears to be scanned ({scanned_page_count}/{total_pages} pages contain images with "
                f"low text density). OCR is required to extract information reliably."
            )
        elif scanned_page_count > 0:
            doc_status = ExtractionStatus.PARTIAL_SUCCESS
            ocr_required = True
            ocr_recommendation = f"{scanned_page_count} of {total_pages} pages appear to be scanned images."
        else:
            doc_status = ExtractionStatus.SUCCESS
            ocr_required = False
            ocr_recommendation = None

        self._ingested_checksums.add(checksum)

        return ExtractedDocument(
            document_id=document_id,
            metadata=doc_metadata,
            pages=page_extractions,
            extraction_status=doc_status,
            ocr_required=ocr_required,
            ocr_recommendation=ocr_recommendation,
        )
