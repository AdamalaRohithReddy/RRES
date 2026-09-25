"""RAG Answer Generator combining retrieval, context building, and LLM synthesis."""
from typing import List, Optional
from pydantic import BaseModel, Field

from src.retrieval.retriever import SchemeRetriever
from src.rag.context_builder import ContextBuilder, SourceReference
from src.llm.client import OpenAIClientWrapper
from src.llm.prompts import CITIZEN_RAG_SYSTEM_INSTRUCTIONS, format_user_prompt


class GroundedAnswer(BaseModel):
    """Structured response returned by the RAG answer generator."""
    answer: str = Field(description="Grounded, citizen-friendly explanation")
    sources: List[SourceReference] = Field(default_factory=list, description="List of authoritative source citations")
    retrieved_chunks: int = Field(description="Number of chunks retrieved above the score threshold")
    grounded: bool = Field(description="Whether the answer is grounded in retrieved documents")


class RAGAnswerGenerator:
    """Orchestrates document retrieval, context compilation, and grounded OpenAI LLM completion."""

    INSUFFICIENT_INFO_MESSAGE = (
        "The available verified government scheme documents do not contain sufficient information "
        "to answer your question. Please consult official scheme portals or contact the administering department."
    )

    def __init__(
        self,
        retriever: SchemeRetriever,
        llm_client: Optional[OpenAIClientWrapper] = None,
        context_builder: Optional[ContextBuilder] = None,
        default_top_k: int = 3,
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.context_builder = context_builder or ContextBuilder()
        self.default_top_k = default_top_k

    def generate(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> GroundedAnswer:
        """Generate a grounded answer for the citizen's query.

        Args:
            query: Natural language citizen question.
            top_k: Maximum number of chunks to retrieve (defaults to 3).
            score_threshold: Minimum similarity threshold (uses settings if None).

        Returns:
            GroundedAnswer containing the answer, sources, chunk count, and grounding flag.
        """
        k = top_k if top_k is not None else self.default_top_k

        # Step 1: Retrieve relevant scheme chunks
        retrieved_chunks = self.retriever.retrieve(
            query=query,
            top_k=k,
            score_threshold=score_threshold,
        )

        # Step 2: Guard against empty or below-threshold retrieval
        # If no chunks pass the threshold, do NOT call the LLM to prevent hallucinations
        if not retrieved_chunks:
            return GroundedAnswer(
                answer=self.INSUFFICIENT_INFO_MESSAGE,
                sources=[],
                retrieved_chunks=0,
                grounded=False,
            )

        # Step 3: Build structured context from retrieved evidence
        context = self.context_builder.build_context(retrieved_chunks)

        # Step 4: Ensure LLM client is available
        if self.llm_client is None:
            self.llm_client = OpenAIClientWrapper()

        # Step 5: Format prompt and call OpenAI Responses API
        user_prompt = format_user_prompt(query=query, context=context.formatted_context)
        llm_resp = self.llm_client.generate_response(
            input_text=user_prompt,
            instructions=CITIZEN_RAG_SYSTEM_INSTRUCTIONS,
        )

        # Step 6: Return structured grounded answer
        return GroundedAnswer(
            answer=llm_resp.content,
            sources=context.sources,
            retrieved_chunks=len(retrieved_chunks),
            grounded=True,
        )
