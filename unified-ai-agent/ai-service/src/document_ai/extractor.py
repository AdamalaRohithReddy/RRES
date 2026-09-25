"""Multi-format text extraction engine with selective OCR fallback."""
from pathlib import Path
from typing import List, Tuple, Optional
import pymupdf

from src.document_ai.models import ExtractedPageText
from src.document_ai.cleaner import DocumentTextCleaner
from src.document_ai.ocr import TesseractOCREngine
from src.config.settings import get_settings


class DocumentExtractionError(Exception):
    """Raised when text extraction fails from a document."""
    pass


class DocumentTextExtractor:
    """Extracts selectable text from PDFs or falls back to OCR for scanned pages and images."""

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        ocr_engine: Optional[TesseractOCREngine] = None,
        char_threshold: Optional[int] = None,
    ):
        settings = get_settings()
        self.ocr_engine = ocr_engine or TesseractOCREngine()
        self.char_threshold = (
            char_threshold if char_threshold is not None else settings.ocr_char_threshold_per_page
        )

    def extract(self, file_path: str | Path) -> Tuple[List[ExtractedPageText], bool]:
        """Extract text page-by-page from PDF or image, selecting OCR only when necessary.

        Args:
            file_path: Path to the target document.

        Returns:
            Tuple of (list of ExtractedPageText, bool indicating if OCR was used anywhere).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {path}")

        ext = path.suffix.lower()
        is_image = ext in self.IMAGE_EXTENSIONS

        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            raise DocumentExtractionError(f"Failed to open document '{path.name}': {e}") from e

        try:
            total_pages = len(doc)
            if total_pages == 0:
                return [], False

            pages: List[ExtractedPageText] = []
            any_ocr_used = False

            for page_idx in range(total_pages):
                page = doc[page_idx]
                page_num = page_idx + 1

                raw_text = page.get_text("text") or ""
                char_count = len(raw_text.strip())

                # For images or scanned pages with insufficient digital text, use OCR
                if is_image or char_count < self.char_threshold:
                    if self.ocr_engine.is_available():
                        ocr_text = self.ocr_engine.ocr_page(page)
                        cleaned_text = DocumentTextCleaner.clean(ocr_text)
                        pages.append(
                            ExtractedPageText(
                                page_number=page_num,
                                raw_text=ocr_text,
                                cleaned_text=cleaned_text,
                                ocr_used=True,
                                char_count=len(cleaned_text),
                            )
                        )
                        any_ocr_used = True
                    else:
                        # If OCR is needed but engine is unavailable, retain raw digital text if any
                        cleaned_text = DocumentTextCleaner.clean(raw_text)
                        pages.append(
                            ExtractedPageText(
                                page_number=page_num,
                                raw_text=raw_text,
                                cleaned_text=cleaned_text,
                                ocr_used=False,
                                char_count=len(cleaned_text),
                            )
                        )
                else:
                    # Selectable digital text is sufficient
                    cleaned_text = DocumentTextCleaner.clean(raw_text)
                    pages.append(
                        ExtractedPageText(
                            page_number=page_num,
                            raw_text=raw_text,
                            cleaned_text=cleaned_text,
                            ocr_used=False,
                            char_count=len(cleaned_text),
                        )
                    )

            return pages, any_ocr_used
        finally:
            doc.close()
