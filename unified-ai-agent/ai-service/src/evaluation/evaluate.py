"""Retrieval Evaluation Module for Government Scheme RAG Foundation."""
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.retrieval.retriever import SchemeRetriever
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config.settings import get_settings


class EvaluationQuery(BaseModel):
    id: str
    category: str
    query: str
    expected_section: Optional[str] = None
    expected_scheme: Optional[str] = None
    is_unrelated: bool = False


# Benchmark dataset containing at least 10 required categories
BENCHMARK_DATASET: List[EvaluationQuery] = [
    EvaluationQuery(
        id="Q01",
        category="eligibility",
        query="What are the eligibility criteria for a startup to apply under the Startup India Seed Fund Scheme?",
        expected_section="Eligibility",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q02",
        category="startup_age",
        query="What is the eligibility criterion for DPIIT recognized startups incorporated not more than 2 years ago at application?",
        expected_section="Eligibility",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q03",
        category="technology_requirement",
        query="Does a startup need to use technology in its core product, service, or business model?",
        expected_section="Eligibility",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q04",
        category="previous_government_funding",
        query="What is the restriction on receiving more than Rs 10 lakh monetary support from other Central or State Government schemes?",
        expected_section="Eligibility",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q05",
        category="indian_promoter_shareholding",
        query="What is the minimum shareholding percentage required for Indian promoters in the startup?",
        expected_section="Eligibility",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q06",
        category="benefits",
        query="What financial assistance and seed fund grant amounts are disbursed to eligible startups by incubators?",
        expected_section="Benefits",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q07",
        category="incubator_eligibility",
        query="What are the eligibility criteria for an incubator to apply and participate in the Startup India Seed Fund Scheme?",
        expected_section="Eligibility",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q08",
        category="fund_disbursement",
        query="How will seed funds be disbursed to eligible startups in milestone-based installments for prototype development and product trials?",
        expected_section="Benefits",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q09",
        category="application_tracking_selection",
        query="How are startups evaluated and selected by the incubator selection committee and how to track the application?",
        expected_section="Benefits",
        expected_scheme="SISFS",
    ),
    EvaluationQuery(
        id="Q10",
        category="unrelated_query",
        query="What is the best recipe for baking chocolate chip cookies with butter and vanilla?",
        expected_section=None,
        expected_scheme=None,
        is_unrelated=True,
    ),
]


class EvaluationResult(BaseModel):
    query_id: str
    category: str
    query: str
    expected_section: Optional[str]
    retrieved_sections: List[str]
    retrieved_scores: List[float]
    hit_at_1: bool
    hit_at_3: bool
    hit_at_5: bool
    reciprocal_rank: float
    is_unrelated: bool
    unrelated_properly_filtered: bool


class BenchmarkSummary(BaseModel):
    total_queries: int
    relevant_queries: int
    hit_at_1_rate: float
    hit_at_3_rate: float
    hit_at_5_rate: float
    mean_reciprocal_rank: float
    unrelated_queries: int
    unrelated_filtering_accuracy: float
    query_details: List[EvaluationResult]


def run_retrieval_evaluation(
    retriever: SchemeRetriever,
    dataset: Optional[List[EvaluationQuery]] = None,
    unrelated_score_cutoff: float = 0.35,
) -> BenchmarkSummary:
    """Execute evaluation over the benchmark queries and calculate Hit@K and MRR metrics."""
    data = dataset or BENCHMARK_DATASET
    results: List[EvaluationResult] = []

    hit1_count = 0
    hit3_count = 0
    hit5_count = 0
    reciprocal_ranks = []

    unrelated_count = 0
    unrelated_passed = 0

    for item in data:
        # Retrieve top 5 chunks without threshold filtering so we can evaluate raw ranking
        matches = retriever.retrieve(query=item.query, top_k=5, score_threshold=0.0)

        retrieved_sections = [m.section for m in matches]
        retrieved_scores = [round(m.score, 4) for m in matches]

        if item.is_unrelated:
            unrelated_count += 1
            # Unrelated query passes if top score is below threshold or no matches found
            top_score = retrieved_scores[0] if retrieved_scores else 0.0
            filtered = top_score < unrelated_score_cutoff
            if filtered:
                unrelated_passed += 1

            results.append(
                EvaluationResult(
                    query_id=item.id,
                    category=item.category,
                    query=item.query,
                    expected_section=None,
                    retrieved_sections=retrieved_sections,
                    retrieved_scores=retrieved_scores,
                    hit_at_1=False,
                    hit_at_3=False,
                    hit_at_5=False,
                    reciprocal_rank=0.0,
                    is_unrelated=True,
                    unrelated_properly_filtered=filtered,
                )
            )
            continue

        # Evaluate Hit@K for relevant query
        target_sec = (item.expected_section or "").lower()
        rank = 0
        for idx, sec in enumerate(retrieved_sections, start=1):
            if target_sec in sec.lower() or sec.lower() in target_sec:
                rank = idx
                break

        h1 = rank == 1
        h3 = 1 <= rank <= 3
        h5 = 1 <= rank <= 5
        rr = 1.0 / rank if rank > 0 else 0.0

        if h1:
            hit1_count += 1
        if h3:
            hit3_count += 1
        if h5:
            hit5_count += 1
        reciprocal_ranks.append(rr)

        results.append(
            EvaluationResult(
                query_id=item.id,
                category=item.category,
                query=item.query,
                expected_section=item.expected_section,
                retrieved_sections=retrieved_sections,
                retrieved_scores=retrieved_scores,
                hit_at_1=h1,
                hit_at_3=h3,
                hit_at_5=h5,
                reciprocal_rank=round(rr, 4),
                is_unrelated=False,
                unrelated_properly_filtered=True,
            )
        )

    rel_total = len(data) - unrelated_count
    summary = BenchmarkSummary(
        total_queries=len(data),
        relevant_queries=rel_total,
        hit_at_1_rate=round(hit1_count / rel_total, 4) if rel_total else 0.0,
        hit_at_3_rate=round(hit3_count / rel_total, 4) if rel_total else 0.0,
        hit_at_5_rate=round(hit5_count / rel_total, 4) if rel_total else 0.0,
        mean_reciprocal_rank=round(sum(reciprocal_ranks) / rel_total, 4) if rel_total else 0.0,
        unrelated_queries=unrelated_count,
        unrelated_filtering_accuracy=round(unrelated_passed / unrelated_count, 4) if unrelated_count else 1.0,
        query_details=results,
    )
    return summary


def format_evaluation_markdown(summary: BenchmarkSummary) -> str:
    """Format evaluation summary into a GitHub-style markdown table."""
    md = []
    md.append("## Retrieval Evaluation Report\n")
    md.append(f"**Total Queries Evaluated:** {summary.total_queries}")
    md.append(f"- **Hit@1:** {summary.hit_at_1_rate * 100:.1f}%")
    md.append(f"- **Hit@3:** {summary.hit_at_3_rate * 100:.1f}%")
    md.append(f"- **Hit@5:** {summary.hit_at_5_rate * 100:.1f}%")
    md.append(f"- **Mean Reciprocal Rank (MRR):** {summary.mean_reciprocal_rank:.4f}")
    md.append(f"- **Unrelated Query Discrimination:** {summary.unrelated_filtering_accuracy * 100:.1f}%\n")

    md.append("| Query ID | Category | Query | Expected Section | Top Retrieved Section | Top Score | Hit@1 | Hit@3 |")
    md.append("|---|---|---|---|---|---|---|---|")
    for q in summary.query_details:
        top_sec = q.retrieved_sections[0] if q.retrieved_sections else "None"
        top_score = f"{q.retrieved_scores[0]:.4f}" if q.retrieved_scores else "N/A"
        if q.is_unrelated:
            status = "Filtered" if q.unrelated_properly_filtered else "Leaked"
            md.append(f"| {q.query_id} | {q.category} | *{q.query}* | None (Unrelated) | {top_sec} | {top_score} | {status} | - |")
        else:
            h1_icon = "Yes" if q.hit_at_1 else "No"
            h3_icon = "Yes" if q.hit_at_3 else "No"
            md.append(f"| {q.query_id} | {q.category} | *{q.query}* | {q.expected_section} | {top_sec} | {top_score} | {h1_icon} | {h3_icon} |")

    return "\n".join(md)


def main():
    settings = get_settings()
    embedder = get_embedder()
    store = QdrantVectorStore(path=settings.qdrant_path, dimension=embedder.dimension)
    retriever = SchemeRetriever(embedder=embedder, vector_store=store, default_top_k=5)

    print("Running retrieval evaluation across benchmark dataset...")
    summary = run_retrieval_evaluation(retriever=retriever, unrelated_score_cutoff=settings.score_threshold)
    report_md = format_evaluation_markdown(summary)
    print("\n" + report_md)


if __name__ == "__main__":
    main()
