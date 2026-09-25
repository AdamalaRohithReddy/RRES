"""Interactive terminal chat interface for the Citizen Scheme Assistant (Milestone 3 Agent Mode)."""
import argparse
import sys
from typing import Optional

from src.retrieval.retriever import SchemeRetriever, InvalidQueryError
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config.settings import get_settings
from src.llm.client import (
    OpenAIClientWrapper,
    MissingAPIKeyError,
    LLMClientError,
    LLMGenerationError,
)
from src.tools.rag_tool import SchemeSearchTool
from src.tools.mysql_tool import CitizenProfileTool
from src.tools.api_tool import ApplicationStatusTool
from src.tools.document_tool import DocumentAnalysisTool
from src.tools.eligibility_tool import EligibilityCheckTool
from src.tools.need_tool import NeedDetectionTool
from src.tools.government_api_tool import GovernmentSchemeDiscoveryTool
from src.needs.tracker import NeedTracker
from src.needs.detector import NeedDetector
from src.agent.tool_registry import ToolRegistry
from src.agent.agent import AgentOrchestrator


def create_default_tool_registry(retriever: SchemeRetriever) -> ToolRegistry:
    """Instantiate and register all available tools (M3, M4, M5, M6, M8)."""
    registry = ToolRegistry()
    registry.register(SchemeSearchTool(retriever=retriever))
    registry.register(CitizenProfileTool())
    registry.register(ApplicationStatusTool())
    registry.register(DocumentAnalysisTool())
    registry.register(EligibilityCheckTool())
    registry.register(NeedDetectionTool())
    registry.register(GovernmentSchemeDiscoveryTool())
    return registry



from src.needs.models import Need


def _handle_query(
    query: str,
    orchestrator: Optional[AgentOrchestrator],
    retriever: SchemeRetriever,
    tracker: Optional[NeedTracker] = None,
) -> None:
    """Execute a single query through either agent orchestrator or direct retrieval."""
    if orchestrator is not None:
        response = orchestrator.run(query=query)
        print("\nAssistant:")
        print(response.answer)
        if response.sources:
            print("\nSources / Evidence:")
            for s in response.sources:
                print(f"- {s.get('scheme', 'Official Scheme')}")
                print(f"  Page {s.get('page', 1)} — {s.get('section', 'General')} ({s.get('source', 'Official publication')})")

        # M6 Cumulative Session Need Tracking
        if tracker is not None and getattr(response, "detected_needs", None):
            try:
                new_needs = [Need.model_validate(n) for n in response.detected_needs]
                tracker.add_needs(new_needs)
                active_cats = [c.value for c in tracker.get_categories()]
                if active_cats:
                    print(f"\n[Session Cumulative Needs]: {', '.join(active_cats)}")
            except Exception:
                pass

        print("-" * 70 + "\n")
    else:
        results = retriever.retrieve(query=query, top_k=2)
        if not results:
            print("\n[No Match] No verified government information found above the similarity threshold.")
            print("Try rephrasing or asking about scheme rules, eligibility, benefits, or documents.\n")
            return
        print(f"\n--- Verified Information ({len(results)} match{'es' if len(results) > 1 else ''}) ---")
        for idx, r in enumerate(results, start=1):
            print(f"\n[{idx}] Scheme  : {r.scheme_name} (Section: {r.section} | Page: {r.page})")
            print(f"    Source  : {r.source_url or 'Official circular'}")
            print(f"    Match   : Cosine Similarity {r.score:.2%}")
            print("    Excerpt :")
            for line in r.text.split("\n"):
                print(f"      {line}")
        print("-" * 70 + "\n")


def start_interactive_chat(retrieval_only: bool = False, query: Optional[str] = None):
    """Start interactive citizen assistant chat session in Agent Orchestrator Mode."""
    settings = get_settings()

    print("=" * 70)
    print("  CITIZEN SCHEME AI ASSISTANT — AGENT MODE (M3, M4, M5, M6, M7)")
    print("=" * 70)
    print("Available tools:")
    print("  - Government Scheme Search (RAG)")
    print("  - Citizen Profile (Relational MySQL Database)")
    print("  - Application Status (Relational MySQL Database)")
    print("  - Document Analysis (Document AI / OCR interface)")
    print("  - Eligibility Assessment (Deterministic Rule Engine)")
    print("  - Multi-Need Detection (Problem Decomposition)")
    print("=" * 70)
    print("Connecting to verified scheme vector store...")

    embedder = get_embedder()
    vector_store = QdrantVectorStore(path=settings.qdrant_path, dimension=embedder.dimension)
    retriever = SchemeRetriever(embedder=embedder, vector_store=vector_store, default_top_k=3)
    tool_registry = create_default_tool_registry(retriever=retriever)

    orchestrator: Optional[AgentOrchestrator] = None
    mode_label = "Agent Orchestrator (Responses API)"

    if retrieval_only:
        mode_label = "Retrieval Only (Milestone 1)"
        print("[MODE] Retrieval-only mode explicitly requested.")
    else:
        try:
            llm_client = OpenAIClientWrapper()
            orchestrator = AgentOrchestrator(
                llm_client=llm_client,
                tool_registry=tool_registry,
                max_steps=5,
                verbose=True,
            )
            print(f"[MODE] Agent Orchestrator active with model: '{llm_client.model}'")
        except MissingAPIKeyError:
            print("[NOTICE] OPENAI_API_KEY is not configured in .env or environment.")
            print("[NOTICE] Falling back to verified chunk retrieval mode.")
            mode_label = "Retrieval Only (No API Key)"
        except LLMClientError as e:
            print(f"[WARNING] LLM client initialization error: {e}")
            print("[WARNING] Falling back to retrieval-only mode.")
            mode_label = "Retrieval Only"

    print(f"\n[READY] Assistant online in [{mode_label}] mode.")

    need_tracker = NeedTracker()

    try:
        if query:
            print(f"\nCitizen Query > {query}")
            _handle_query(query, orchestrator, retriever, tracker=need_tracker)
            return

        print("Ask any question about schemes, profile, or application status. Type 'exit' or 'q' to stop.\n")
        while True:
            try:
                user_input = input("Citizen Query > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "q"):
                    print("\nThank you for using the Citizen Scheme Assistant. Goodbye!")
                    break

                _handle_query(user_input, orchestrator, retriever, tracker=need_tracker)

            except InvalidQueryError as e:
                print(f"[Input Error]: {e}\n")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting chat. Goodbye!")
                break
            except Exception as e:
                print(f"[Error]: {e}\n")
    finally:
        try:
            if hasattr(vector_store, "client") and hasattr(vector_store.client, "close"):
                vector_store.client.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Citizen Scheme Assistant Interactive Chat (Agent Mode)")
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Run in retrieval-only mode without calling Agent Orchestrator / LLM",
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default=None,
        help="Run a single citizen query non-interactively and display results",
    )
    args = parser.parse_args()
    start_interactive_chat(retrieval_only=args.retrieval_only, query=args.query)


if __name__ == "__main__":
    main()
