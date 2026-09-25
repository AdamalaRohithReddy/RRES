"""CLI utility to ingest government scheme PDFs into the vector store."""
import argparse
import json
from pathlib import Path

from src.ingestion.pipeline import SchemeIngestionPipeline
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config.settings import get_settings


def main():
    parser = argparse.ArgumentParser(description="Ingest an official government scheme PDF.")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--scheme-id", default=None, help="Scheme identifier (e.g. APY)")
    parser.add_argument("--scheme-name", default=None, help="Full official scheme name")
    parser.add_argument("--source-url", default=None, help="Source URL of publication")
    parser.add_argument("--source-type", default="official", help="Source classification")
    parser.add_argument("--last-verified", default=None, help="Verification date (YYYY-MM-DD)")
    parser.add_argument("--allow-duplicate", action="store_true", help="Allow re-indexing same document")
    parser.add_argument("--in-memory", action="store_true", help="Use in-memory Qdrant instead of disk")

    args = parser.parse_args()

    settings = get_settings()
    pdf_path = Path(args.pdf).resolve()

    print(f"Loading embedder '{settings.embedding_model_name}' on '{settings.embedding_device}'...")
    embedder = get_embedder()

    qdrant_path = ":memory:" if args.in_memory else settings.qdrant_path
    print(f"Initializing Qdrant store at '{qdrant_path}'...")
    vector_store = QdrantVectorStore(path=qdrant_path, dimension=embedder.dimension)
    vector_store.initialize_collection()

    pipeline = SchemeIngestionPipeline(
        embedder=embedder,
        vector_store=vector_store,
    )

    print(f"Processing and indexing: {pdf_path.name}...")
    report = pipeline.process_and_index_pdf(
        file_path=pdf_path,
        scheme_id=args.scheme_id,
        scheme_name=args.scheme_name,
        source_url=args.source_url,
        source_type=args.source_type,
        last_verified=args.last_verified,
        allow_duplicate=args.allow_duplicate,
    )

    print("\n--- INGESTION REPORT ---")
    print(json.dumps(report.model_dump(), indent=2))

    if report.ocr_required:
        print(f"\n[ALERT] OCR Required: {report.ocr_recommendation}")
    else:
        print(f"\n[SUCCESS] Successfully indexed {report.total_chunks} chunks across {report.total_pages} pages.")
        print(f"Indexed Sections: {', '.join(report.sections_indexed)}")


if __name__ == "__main__":
    main()
