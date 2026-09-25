"""Standalone command-line interface for Document AI and OCR pipeline."""
import argparse
import sys
from pathlib import Path

from src.document_ai.pipeline import (
    DocumentProcessingPipeline,
    DocumentProcessingError,
)


def run_document_analysis(file_path: str) -> int:
    """Run document analysis on a file and display formatted results."""
    print("=" * 70)
    print("  CITIZEN SCHEME AI ASSISTANT — DOCUMENT AI / OCR CLI (MILESTONE 4)")
    print("=" * 70)

    pipeline = DocumentProcessingPipeline()
    path = Path(file_path)

    print(f"Target Document: {path.name}")
    print(f"Resolving path : {path.resolve()}\n")

    try:
        result = pipeline.process(path)
    except DocumentProcessingError as e:
        print(f"[Document Processing Error]: {e}")
        return 1
    except Exception as e:
        print(f"[Unexpected Error]: {e}")
        return 1

    print("=" * 70)
    print(f"STATUS                  : {result.status.upper()}")
    print(f"APPARENT DOCUMENT TYPE  : {result.apparent_document_type.value} (Confidence: {result.document_type_confidence:.0%})")
    print(f"OCR USED                : {'Yes (Scanned / Image)' if result.ocr_used else 'No (Selectable Digital Text)'}")
    if result.metadata:
        print(f"PAGES                   : {result.metadata.total_pages}")
        print(f"FILE SIZE               : {result.metadata.file_size_bytes:,} bytes")
        print(f"SHA-256 CHECKSUM        : {result.metadata.sha256_checksum[:16]}...")
    print("=" * 70)

    print("\nEXTRACTED CITIZEN ATTRIBUTES (DETERMINISTIC EXTRACTION):")
    print(f"{'Field':<20} | {'Value':<25} | {'Confidence':<12} | {'Page':<5} | {'Source Snippet'}")
    print("-" * 90)

    for field_name, f in sorted(result.fields.items()):
        val_str = str(f.value) if f.value is not None else "[Not Found]"
        conf_str = f"{f.confidence_level.value} ({f.confidence:.0%})"
        page_str = str(f.page) if f.page is not None else "-"
        snippet_str = f.source_text[:30] + "..." if f.source_text and len(f.source_text) > 30 else (f.source_text or "-")
        print(f"{field_name:<20} | {val_str:<25} | {conf_str:<12} | {page_str:<5} | {snippet_str}")

    if result.warnings:
        print("\nDIAGNOSTIC WARNINGS:")
        for w in result.warnings:
            print(f"  • {w}")

    print("\n" + "=" * 70)
    print(f"NOTICE: {result.disclaimer}")
    print("=" * 70 + "\n")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Analyze citizen documents using Document AI & OCR.")
    parser.add_argument(
        "--file",
        "-f",
        required=True,
        type=str,
        help="Path to the document to analyze (PDF, PNG, JPG, JPEG)",
    )
    args = parser.parse_args()
    sys.exit(run_document_analysis(args.file))


if __name__ == "__main__":
    main()
