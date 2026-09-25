"""End-to-End Integration Test for Milestone 1 RAG Foundation."""
from pathlib import Path
import pytest
import pymupdf

from src.ingestion.pdf_loader import PDFIngestionEngine
from src.chunking.semantic_chunker import SemanticChunker
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.retrieval.retriever import SchemeRetriever
from src.ingestion.pipeline import SchemeIngestionPipeline


@pytest.fixture(scope="module")
def e2e_pdf(tmp_path_factory) -> Path:
    """Generate a clean official test PDF."""
    temp_dir = tmp_path_factory.mktemp("e2e_data")
    pdf_path = temp_dir / "official_pmjjby_guidelines.pdf"

    doc = pymupdf.open()

    p1 = doc.new_page()
    p1.insert_text(
        (50, 72),
        "PRADHAN MANTRI JEEVAN JYOTI BIMA YOJANA (PMJJBY)\n\n"
        "1. Overview\n"
        "PMJJBY is a one-year life insurance scheme renewable year to year, offering coverage for death due to any cause.\n\n"
        "2. Eligibility\n"
        "Individuals aged 18 to 50 years having a savings bank account with participating banks are eligible to join PMJJBY."
    )

    p2 = doc.new_page()
    p2.insert_text(
        (50, 72),
        "3. Benefits\n"
        "Under PMJJBY, a life insurance cover of Rs. 2,00,000 (Two Lakh Rupees) is payable to the nominee upon the death of the insured member.\n\n"
        "4. Required Documents\n"
        "Aadhaar card is the primary KYC document, along with a self-certified consent-cum-declaration form."
    )

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_complete_e2e_pipeline(e2e_pdf):
    """Verify complete end-to-end pipeline:

    PDF -> extraction -> chunking -> embeddings -> Qdrant -> query -> retrieval with provenance.
    """
    # 1. Initialize components
    embedder = get_embedder()
    store = QdrantVectorStore(collection_name="e2e_collection", path=":memory:", dimension=embedder.dimension)
    store.initialize_collection()

    pipeline = SchemeIngestionPipeline(
        pdf_engine=PDFIngestionEngine(),
        chunker=SemanticChunker(),
        embedder=embedder,
        vector_store=store,
    )

    # 2. Ingest document
    report = pipeline.process_and_index_pdf(
        file_path=e2e_pdf,
        scheme_id="PMJJBY",
        scheme_name="Pradhan Mantri Jeevan Jyoti Bima Yojana",
        source_url="https://financialservices.gov.in/pmjjby",
        source_type="official",
        last_verified="2026-02-01",
    )

    assert report.extraction_status == "SUCCESS"
    assert report.total_pages == 2
    assert report.total_chunks >= 3
    assert not report.ocr_required
    assert "Eligibility" in report.sections_indexed
    assert "Benefits" in report.sections_indexed

    # 3. Initialize retriever
    retriever = SchemeRetriever(
        embedder=embedder,
        vector_store=store,
        default_top_k=3,
        score_threshold=0.30,
    )

    # 4. Semantic Query: Eligibility & Age
    elig_results = retriever.retrieve("What is the maximum age limit to join PMJJBY?")
    assert len(elig_results) >= 1
    top_elig = elig_results[0]
    assert top_elig.section == "Eligibility"
    assert top_elig.scheme_name == "Pradhan Mantri Jeevan Jyoti Bima Yojana"
    assert top_elig.scheme_id == "PMJJBY"
    assert top_elig.page == 1
    assert "18 to 50 years" in top_elig.text
    assert top_elig.source_url == "https://financialservices.gov.in/pmjjby"
    assert top_elig.score > 0.40

    # 5. Semantic Query: Benefits & Insurance sum
    ben_results = retriever.retrieve("How much life insurance cover is provided upon death?")
    assert len(ben_results) >= 1
    top_ben = ben_results[0]
    assert top_ben.section == "Benefits"
    assert top_ben.page == 2
    assert "Rs. 2,00,000" in top_ben.text
    assert top_ben.source_url == "https://financialservices.gov.in/pmjjby"
    assert top_ben.score > 0.40

    # 6. Verify dictionary provenance serialization
    provenance_dict = top_ben.to_provenance_dict()
    assert provenance_dict["score"] == top_ben.score
    assert provenance_dict["scheme_name"] == "Pradhan Mantri Jeevan Jyoti Bima Yojana"
    assert provenance_dict["page"] == 2
    assert provenance_dict["section"] == "Benefits"
    assert provenance_dict["source_url"] == "https://financialservices.gov.in/pmjjby"
    assert "chunk_id" in provenance_dict
    assert "document_id" in provenance_dict
