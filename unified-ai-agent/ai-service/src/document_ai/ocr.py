"""Tesseract OCR Engine wrapper using PyMuPDF native C/C++ bindings."""
import os
from pathlib import Path
from typing import Optional
import pymupdf


class OCREngineError(Exception):
    """Base exception for OCR engine failures."""
    pass


class OCREngineUnavailableError(OCREngineError):
    """Raised when Tesseract OCR engine or trained data cannot be located."""
    pass


class TesseractOCREngine:
    """Performs optical character recognition using PyMuPDF's integrated Tesseract engine."""

    STANDARD_TESSDATA_LOCATIONS = [
        Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tessdata"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tessdata",
    ]

    def __init__(self, tessdata_path: Optional[str | Path] = None):
        self.tessdata_path = self._find_tessdata(tessdata_path)

    def _find_tessdata(self, explicit_path: Optional[str | Path] = None) -> Optional[str]:
        """Locate the tessdata directory containing traineddata models."""
        # 1. Explicit path
        if explicit_path:
            p = Path(explicit_path)
            if p.exists() and (p / "eng.traineddata").exists():
                return str(p)

        # 2. Environment variable TESSDATA_PREFIX
        env_prefix = os.environ.get("TESSDATA_PREFIX")
        if env_prefix:
            p = Path(env_prefix)
            if (p / "eng.traineddata").exists():
                return str(p)
            elif (p / "tessdata" / "eng.traineddata").exists():
                return str(p / "tessdata")

        # 3. Standard Windows locations
        for loc in self.STANDARD_TESSDATA_LOCATIONS:
            if loc.exists() and (loc / "eng.traineddata").exists():
                return str(loc)

        return None

    def is_available(self) -> bool:
        """Indicate whether the OCR engine and English language models are available."""
        return self.tessdata_path is not None

    def ocr_page(self, page: pymupdf.Page, dpi: int = 150) -> str:
        """Perform OCR on a single PyMuPDF page.

        Args:
            page: The PyMuPDF document page to OCR.
            dpi: Resolution for rasterizing the page.

        Returns:
            Extracted text string from OCR.
        """
        if not self.is_available():
            raise OCREngineUnavailableError(
                "Tesseract OCR engine is not available. Please install Tesseract-OCR "
                "with English language data or configure TESSDATA_PREFIX."
            )

        try:
            pix = page.get_pixmap(dpi=dpi)
            ocr_pdf_bytes = pix.pdfocr_tobytes(tessdata=self.tessdata_path)
            ocr_doc = pymupdf.open("pdf", ocr_pdf_bytes)
            ocr_text = ""
            for p in ocr_doc:
                ocr_text += p.get_text("text") or ""
            ocr_doc.close()
            return ocr_text
        except Exception as e:
            raise OCREngineError(f"OCR execution failed on page: {e}") from e

    def ocr_image(self, image_path: str | Path, dpi: int = 150) -> str:
        """Perform OCR directly on an image file (PNG, JPG, JPEG)."""
        if not self.is_available():
            raise OCREngineUnavailableError(
                "Tesseract OCR engine is not available. Please install Tesseract-OCR."
            )

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        try:
            doc = pymupdf.open(str(path))
            if len(doc) == 0:
                doc.close()
                return ""
            page = doc[0]
            text = self.ocr_page(page, dpi=dpi)
            doc.close()
            return text
        except Exception as e:
            if isinstance(e, OCREngineError):
                raise
            raise OCREngineError(f"Failed to OCR image '{path.name}': {e}") from e
