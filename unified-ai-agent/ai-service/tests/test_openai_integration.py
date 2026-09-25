"""Optional live integration test for OpenAI LLM connection.

This test is skipped automatically when OPENAI_API_KEY is not configured.
"""
import os
import pytest
from src.config.settings import get_settings
from src.llm.client import OpenAIClientWrapper


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not configured. Skipping live OpenAI integration test.",
)
def test_live_openai_responses_call():
    """Manual/CI integration test verifying live connection to OpenAI Responses API."""
    settings = get_settings()
    client = OpenAIClientWrapper(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )

    try:
        response = client.generate_response(
            input_text="State in one short sentence: what is the official capital of India?",
            instructions="Answer briefly and factually.",
        )
        assert response.content
        assert len(response.content) > 0
        assert "Delhi" in response.content or "delhi" in response.content.lower()
    except Exception as e:
        if "insufficient_quota" in str(e) or "credit_balance_exhausted" in str(e):
            pytest.skip(f"Live OpenAI call skipped due to account quota: {e}")
        raise
