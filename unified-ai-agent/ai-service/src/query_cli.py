"""CLI utility to query the scheme knowledge base with provenance reporting."""
import argparse
import json

from src.retrieval.retriever import SchemeRetriever
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config.settings import get_settings


def main():
    parser = argparse.ArgumentParser(description="Query the official government scheme knowledge base.")
    parser.add_argument("--query", required=True, help="Natural language query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--scheme-id", default=None, help="Filter by scheme identifier")
    parser.add_argument("--section", default=None, help="Filter by section (e.g. Eligibility)")
    parser.add_argument("--threshold", type=float, default=None, help="Minimum score threshold")
    parser.add_argument("--json", action="store_true", help="Output in raw JSON format")

    args = parser.parse_args()
    settings = get_settings()

    embedder = get_embedder()
    vector_store = QdrantVectorStore(path=settings.qdrant_path, dimension=embedder.dimension)

    retriever = SchemeRetriever(
        embedder=embedder,
        vector_store=vector_store,
        default_top_k=args.top_k,
        score_threshold=args.threshold,
    )

    filter_criteria = {}
    if args.scheme_id:
        filter_criteria["scheme_id"] = args.scheme_id
    if args.section:
        filter_criteria["section"] = args.section

    results = retriever.retrieve(
        query=args.query,
        top_k=args.top_k,
        filter_criteria=filter_criteria or None,
        score_threshold=args.threshold,
    )

    if args.json:
        print(json.dumps([r.to_provenance_dict() for r in results], indent=2))
        return

    print("\n" + "=" * 70)
    print(f"QUERY: \"{args.query}\"")
    print(f"RESULTS RETURNED: {len(results)}")
    print("=" * 70)

    if not results:
        print("No matching information found above the similarity threshold.")
        return

    for idx, r in enumerate(results, start=1):
        print(f"\n[Result {idx}] Cosine Similarity: {r.score:.4f}")
        print(f"  • Scheme Name   : {r.scheme_name} ({r.scheme_id or 'N/A'})")
        print(f"  • Section       : {r.section}")
        print(f"  • Page Number   : {r.page} (Pages {r.page_start}-{r.page_end})")
        print(f"  • Source URL    : {r.source_url or 'Official circular'}")
        print(f"  • Document ID   : {r.document_id}")
        print(f"  • Chunk ID      : {r.chunk_id}")
        print("  • Text Excerpt  :")
        for line in r.text.split("\n"):
            print(f"      {line}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
