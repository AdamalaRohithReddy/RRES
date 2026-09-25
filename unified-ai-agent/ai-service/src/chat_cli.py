"""Interactive terminal chat interface for testing the Scheme RAG retriever."""
import sys
from src.retrieval.retriever import SchemeRetriever, InvalidQueryError
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config.settings import get_settings


def start_interactive_chat():
    settings = get_settings()
    print("=" * 70)
    print("  CITIZEN SCHEME RAG ASSISTANT — INTERACTIVE CHAT (MILESTONE 1)")
    print("=" * 70)
    print("Loading embedding model and connecting to verified scheme vector store...")

    embedder = get_embedder()
    vector_store = QdrantVectorStore(path=settings.qdrant_path, dimension=embedder.dimension)
    retriever = SchemeRetriever(embedder=embedder, vector_store=vector_store, default_top_k=2)

    print("\n[READY] Connected to knowledge base. You can now test queries!")
    print("Type your questions below. Type 'exit', 'quit', or 'q' to stop.\n")

    while True:
        try:
            query = input("Citizen Query > ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("\nExiting chat. Thank you!")
                break

            results = retriever.retrieve(query=query, top_k=2)

            if not results:
                print("\n[No Match] No verified government information found above the similarity threshold.")
                print("Try rephrasing or asking about scheme rules, eligibility, benefits, or documents.\n")
                continue

            print(f"\n--- Verified Information ({len(results)} match{'es' if len(results) > 1 else ''}) ---")
            for idx, r in enumerate(results, start=1):
                print(f"\n[{idx}] Scheme  : {r.scheme_name} (Section: {r.section} | Page: {r.page})")
                print(f"    Source  : {r.source_url or 'Official circular'}")
                print(f"    Match   : Cosine Similarity {r.score:.2%}")
                print("    Excerpt :")
                for line in r.text.split("\n"):
                    print(f"      {line}")
            print("-" * 70 + "\n")

        except InvalidQueryError as e:
            print(f"[Input Error]: {e}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat. Goodbye!")
            break
        except Exception as e:
            print(f"[Error]: {e}\n")


if __name__ == "__main__":
    start_interactive_chat()
