"""Unit tests for Milestone 2 RAG + OpenAI LLM layer."""
import os
import pytest
from unittest.mock import MagicMock, patch

from src.retrieval.models import RetrievalResult
from src.rag.context_builder import ContextBuilder, SourceReference, RAGContext
from src.rag.answer_generator import RAGAnswerGenerator, GroundedAnswer
from src.llm.client import (
    OpenAIClientWrapper,
    MissingAPIKeyError,
    LLMGenerationError,
    sanitize_secret_message,
)
from src.llm.models import LLMResponse
from src.llm.prompts import (
    CITIZEN_RAG_SYSTEM_INSTRUCTIONS,
    format_user_prompt,
)


def create_sample_retrieval_result(
    score: float = 0.85,
    text: str = "Startups recognized by DPIIT incorporated not more than 2 years ago are eligible.",
    page: int = 2,
    section: str = "Eligibility",
    scheme_name: str = "Startup India Seed Fund Scheme",
    document_id: str = "SISFS_001",
    source_url: str = "https://www.startupindia.gov.in",
) -> RetrievalResult:
    return RetrievalResult(
        score=score,
        text=text,
        chunk_id=f"{document_id}_chunk_01",
        document_id=document_id,
        scheme_name=scheme_name,
        page=page,
        page_start=page,
        page_end=page,
        section=section,
        source_url=source_url,
    )


# ---------------------------------------------------------------------------
# Test 1: Context builder creates correct source metadata
# ---------------------------------------------------------------------------
def test_context_builder_creates_correct_source_metadata():
    builder = ContextBuilder()
    chunk1 = create_sample_retrieval_result(
        score=0.88,
        text="A startup recognized by DPIIT is eligible.",
        page=2,
        section="Eligibility",
        document_id="DOC_A",
    )
    chunk2 = create_sample_retrieval_result(
        score=0.75,
        text="Grant of up to Rs. 20 Lakhs for Proof of Concept.",
        page=11,
        section="Benefits",
        document_id="DOC_A",
    )

    context = builder.build_context([chunk1, chunk2])

    assert isinstance(context, RAGContext)
    assert context.total_chunks == 2
    assert len(context.sources) == 2

    # Verify source metadata preservation
    src1 = context.sources[0]
    assert src1.scheme_name == "Startup India Seed Fund Scheme"
    assert src1.document_id == "DOC_A"
    assert src1.page == 2
    assert src1.section == "Eligibility"
    assert "startupindia.gov.in" in src1.source

    src2 = context.sources[1]
    assert src2.page == 11
    assert src2.section == "Benefits"

    # Verify formatted context contains labels and text
    assert "[Source 1]" in context.formatted_context
    assert "[Source 2]" in context.formatted_context
    assert "A startup recognized by DPIIT is eligible." in context.formatted_context
    assert "Grant of up to Rs. 20 Lakhs" in context.formatted_context
    assert "Similarity Score: 0.8800" in context.formatted_context


def test_context_builder_empty_chunks():
    builder = ContextBuilder()
    context = builder.build_context([])
    assert context.total_chunks == 0
    assert len(context.sources) == 0
    assert "No relevant verified documents" in context.formatted_context


# ---------------------------------------------------------------------------
# Test 2: Missing API key is handled safely
# ---------------------------------------------------------------------------
def test_missing_api_key_handled_safely():
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
        # Explicit empty key
        with pytest.raises(MissingAPIKeyError) as exc_info:
            OpenAIClientWrapper(api_key="")
        assert "OPENAI_API_KEY" in str(exc_info.value)
        assert "missing" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test 3: Empty retrieval does NOT call the LLM
# ---------------------------------------------------------------------------
def test_empty_retrieval_does_not_call_llm():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []

    mock_llm = MagicMock(spec=OpenAIClientWrapper)

    generator = RAGAnswerGenerator(retriever=mock_retriever, llm_client=mock_llm)
    result = generator.generate("What is the recipe for cookies?")

    # Verify LLM was NOT called
    mock_llm.generate_response.assert_not_called()

    # Verify safe fallback answer
    assert isinstance(result, GroundedAnswer)
    assert result.grounded is False
    assert result.retrieved_chunks == 0
    assert len(result.sources) == 0
    assert "not contain sufficient information" in result.answer.lower()


# ---------------------------------------------------------------------------
# Test 4: Prompt requires grounded answering
# ---------------------------------------------------------------------------
def test_grounding_prompt_contains_critical_rules():
    instructions = CITIZEN_RAG_SYSTEM_INSTRUCTIONS
    # Verify core grounding tenets
    assert "strictly and solely using the verified government document excerpts" in instructions
    assert "Do NOT invent, assume, or extrapolate" in instructions
    assert "Preserve all numerical values" in instructions
    assert "explicitly state that the available verified documents do not provide enough information" in instructions
    assert "Do NOT use your general pre-trained knowledge" in instructions
    assert "NEVER claim that an application has been submitted, approved, rejected, or verified" in instructions


def test_format_user_prompt():
    prompt = format_user_prompt(
        query="What is the age limit?",
        context="[Source 1]\nIncorporated not more than 2 years ago.",
    )
    assert "Citizen Question: What is the age limit?" in prompt
    assert "Incorporated not more than 2 years ago." in prompt
    assert "Verified Official Government Scheme Documents:" in prompt


# ---------------------------------------------------------------------------
# Test 5: API errors do not expose API keys
# ---------------------------------------------------------------------------
def test_api_error_sanitizes_secret_key():
    secret_key = "sk-proj-supersecretkey1234567890abcdefghijklmnopqrstuvwxyz"
    raw_error = f"Error calling OpenAI API with key {secret_key}: 401 Unauthorized"

    sanitized = sanitize_secret_message(raw_error)
    assert secret_key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized


def test_llm_client_generation_error_masks_key():
    fake_key = "sk-live-abcdef1234567890abcdef"
    mock_openai = MagicMock()
    mock_openai.responses.create.side_effect = Exception(f"Failed with key {fake_key}")

    wrapper = OpenAIClientWrapper.__new__(OpenAIClientWrapper)
    wrapper._api_key = fake_key
    wrapper.model = "gpt-5.6-luna"
    wrapper.client = mock_openai

    with pytest.raises(LLMGenerationError) as exc_info:
        wrapper.generate_response(input_text="hello", instructions="instruction")

    assert fake_key not in str(exc_info.value)
    assert "[REDACTED_API_KEY]" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 6: Structured answer parsing works
# ---------------------------------------------------------------------------
def test_structured_answer_parsing():
    raw_payload = {
        "answer": "Startups recognized by DPIIT within 2 years of incorporation are eligible.",
        "sources": [
            {
                "scheme_name": "Startup India Seed Fund Scheme",
                "document_id": "SISFS_01",
                "page": 2,
                "section": "Eligibility",
                "source": "https://www.startupindia.gov.in",
            }
        ],
        "retrieved_chunks": 1,
        "grounded": True,
    }

    answer_model = GroundedAnswer.model_validate(raw_payload)
    assert answer_model.grounded is True
    assert answer_model.retrieved_chunks == 1
    assert len(answer_model.sources) == 1
    assert answer_model.sources[0].page == 2
    assert answer_model.sources[0].section == "Eligibility"

    dumped = answer_model.model_dump()
    assert dumped["grounded"] is True
    assert dumped["sources"][0]["document_id"] == "SISFS_01"


# ---------------------------------------------------------------------------
# Test 7: Full RAG Answer Generator flow (Mocked LLM)
# ---------------------------------------------------------------------------
def test_rag_answer_generator_success_flow():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        create_sample_retrieval_result(
            score=0.91,
            text="Seed Fund provides up to Rs. 20 Lakhs grant for Proof of Concept.",
            page=11,
            section="Benefits",
        )
    ]

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    mock_llm.generate_response.return_value = LLMResponse(
        content="Under the Seed Fund Scheme, eligible startups can receive up to Rs. 20 Lakhs as a grant for Proof of Concept (Page 11, Benefits).",
        model="gpt-5.6-luna",
        response_id="resp_12345",
    )

    generator = RAGAnswerGenerator(
        retriever=mock_retriever,
        llm_client=mock_llm,
    )

    answer = generator.generate("What grant amount can I get for prototype validation?")

    mock_retriever.retrieve.assert_called_once()
    mock_llm.generate_response.assert_called_once()

    assert answer.grounded is True
    assert answer.retrieved_chunks == 1
    assert len(answer.sources) == 1
    assert answer.sources[0].section == "Benefits"
    assert answer.sources[0].page == 11
    assert "Rs. 20 Lakhs" in answer.answer
