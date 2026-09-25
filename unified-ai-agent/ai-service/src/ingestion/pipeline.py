"""High-Level Ingestion Pipeline for Scheme Documents."""
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from src.ingestion.pdf_loader import PDFIngestionEngine
from src.ingestion.models import ExtractedDocument, ExtractionStatus
from src.chunking.semantic_chunker import SemanticChunker
from src.chunking.models import DocumentChunk
from src.embeddings.base import BaseEmbedder
from src.vector_store.qdrant_store import QdrantVectorStore


class IngestionReport(BaseModel):
    """Structured report returned upon document ingestion."""
    document_id: str
    file_name: str
    scheme_id: Optional[str]
    scheme_name: Optional[str]
    total_pages: int
    total_chunks: int
    extraction_status: ExtractionStatus
    ocr_required: bool
    ocr_recommendation: Optional[str]
    sections_indexed: List[str]


class SchemeIngestionPipeline:
    """Orchestrates end-to-end ingestion from raw PDF to vector database storage."""

    def __init__(
        self,
        pdf_engine: Optional[PDFIngestionEngine] = None,
        chunker: Optional[SemanticChunker] = None,
        embedder: Optional[BaseEmbedder] = None,
        vector_store: Optional[QdrantVectorStore] = None,
    ):
        self.pdf_engine = pdf_engine or PDFIngestionEngine()
        self.chunker = chunker or SemanticChunker()
        self.embedder = embedder
        self.vector_store = vector_store

    def process_and_index_pdf(
        self,
        file_path: str | Path,
        scheme_id: Optional[str] = None,
        scheme_name: Optional[str] = None,
        source_url: Optional[str] = None,
        source_type: str = "official",
        last_verified: Optional[str] = None,
        allow_duplicate: bool = False,
    ) -> IngestionReport:
        """Process a PDF document and index its chunks into Qdrant."""
        if not self.embedder or not self.vector_store:
            raise ValueError("Embedder and VectorStore must be provided for full pipeline indexing.")

        # 1. Ingest PDF and extract text
        doc: ExtractedDocument = self.pdf_engine.ingest_pdf(
            file_path=file_path,
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            source_url=source_url,
            source_type=source_type,
            last_verified=last_verified,
            allow_duplicate=allow_duplicate,
        )

        # If document is empty or scanned without OCR, halt indexing and report
        if doc.ocr_required or doc.extraction_status in (
            ExtractionStatus.SCANNED_OCR_REQUIRED,
            ExtractionStatus.EMPTY_DOCUMENT,
            ExtractionStatus.FAILED,
        ):
            return IngestionReport(
                document_id=doc.document_id,
                file_name=doc.metadata.file_name,
                scheme_id=doc.metadata.scheme_id,
                scheme_name=doc.metadata.scheme_name,
                total_pages=doc.metadata.total_pages,
                total_chunks=0,
                extraction_status=doc.extraction_status,
                ocr_required=doc.ocr_required,
                ocr_recommendation=doc.ocr_recommendation,
                sections_indexed=[],
            )

        # 2. Chunk document into semantic sections
        chunks: List[DocumentChunk] = self.chunker.chunk_document(doc)

        if not chunks:
            return IngestionReport(
                document_id=doc.document_id,
                file_name=doc.metadata.file_name,
                scheme_id=doc.metadata.scheme_id,
                scheme_name=doc.metadata.scheme_name,
                total_pages=doc.metadata.total_pages,
                total_chunks=0,
                extraction_status=ExtractionStatus.EMPTY_DOCUMENT,
                ocr_required=False,
                ocr_recommendation="No extractable text segments found to chunk.",
                sections_indexed=[],
            )

        # 3. Generate embeddings
        chunk_texts = [c.text for c in chunks]
        embeddings = self.embedder.embed_batch(chunk_texts)

        # 4. Upsert into Qdrant
        self.vector_store.upsert_chunks(chunks, embeddings)

        sections = sorted(list(set(c.section for c in chunks)))

        return IngestionReport(
            document_id=doc.document_id,
            file_name=doc.metadata.file_name,
            scheme_id=doc.metadata.scheme_id,
            scheme_name=doc.metadata.scheme_name,
            total_pages=doc.metadata.total_pages,
            total_chunks=len(chunks),
            extraction_status=doc.extraction_status,
            ocr_required=False,
            ocr_recommendation=None,
            sections_indexed=sections,
        )
