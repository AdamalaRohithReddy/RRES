"""Document AI and OCR package for citizen support documents."""
from src.document_ai.models import (
    DocumentType,
    ConfidenceLevel,
    ExtractedField,
    ExtractedPageText,
    DocumentMetadata,
    DocumentAnalysisResult,
)
from src.document_ai.detector import DocumentTypeDetector
from src.document_ai.ocr import (
    TesseractOCREngine,
    OCREngineError,
    OCREngineUnavailableError,
)
from src.document_ai.cleaner import DocumentTextCleaner
from src.document_ai.extractor import (
    DocumentTextExtractor,
    DocumentExtractionError,
)
from src.document_ai.field_extractor import DeterministicFieldExtractor
from src.document_ai.validator import DocumentFieldValidator
from src.document_ai.pipeline import (
    DocumentProcessingPipeline,
    DocumentProcessingError,
    DocumentNotFoundError,
    CorruptedDocumentError,
    UnsupportedDocumentFormatError,
    DocumentSizeLimitExceededError,
)

__all__ = [
    "DocumentType",
    "ConfidenceLevel",
    "ExtractedField",
    "ExtractedPageText",
    "DocumentMetadata",
    "DocumentAnalysisResult",
    "DocumentTypeDetector",
    "TesseractOCREngine",
    "OCREngineError",
    "OCREngineUnavailableError",
    "DocumentTextCleaner",
    "DocumentTextExtractor",
    "DocumentExtractionError",
    "DeterministicFieldExtractor",
    "DocumentFieldValidator",
    "DocumentProcessingPipeline",
    "DocumentProcessingError",
    "DocumentNotFoundError",
    "CorruptedDocumentError",
    "UnsupportedDocumentFormatError",
    "DocumentSizeLimitExceededError",
]
