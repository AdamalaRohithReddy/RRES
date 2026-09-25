"""RAG Tool wrapping the verified government scheme retriever (M1)."""
from typing import Dict, Any, Optional

from src.tools.base import BaseTool
from src.retrieval.retriever import SchemeRetriever
from src.config.settings import get_settings


class SchemeSearchTool(BaseTool):
    """Tool allowing the agent to retrieve verified clauses from official government scheme documents."""

    def __init__(self, retriever: SchemeRetriever):
        self.retriever = retriever
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "search_government_schemes"

    @property
    def description(self) -> str:
        return (
            "Search verified official government scheme documents (such as Startup India Seed Fund Scheme, "
            "Atal Pension Yojana, etc.) using semantic vector retrieval. Returns authoritative clauses, "
            "eligibility criteria, benefits, and source provenance (page numbers, section, official URL). "
            "Use this tool whenever answering questions regarding government policies, scheme rules, or benefits."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language query or keywords about scheme rules, eligibility, benefits, or documents."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of verified document chunks to return (default: 3).",
                    "default": 3
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, top_k: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Execute semantic search against Qdrant vector database using existing SchemeRetriever."""
        limit = top_k or 3
        # Uses the configured score threshold from settings
        results = self.retriever.retrieve(
            query=query,
            top_k=limit,
            score_threshold=self.settings.score_threshold,
        )

        formatted_results = []
        for r in results:
            formatted_results.append({
                "scheme": r.scheme_name,
                "section": r.section,
                "page": r.page,
                "score": round(r.score, 4),
                "content": r.text,
                "source": r.source_url or "Official circular",
                "document_id": r.document_id,
                "chunk_id": r.chunk_id,
            })

        return {
            "status": "success",
            "query": query,
            "total_found": len(formatted_results),
            "results": formatted_results,
            "threshold_applied": self.settings.score_threshold,
            "is_evidence_sufficient": len(formatted_results) > 0,
        }
