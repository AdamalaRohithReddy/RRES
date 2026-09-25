"""OpenAI Client Abstraction using the Responses API."""
import json
import re
from typing import Optional, List, Dict, Any, Union
from openai import OpenAI, OpenAIError

from src.llm.models import LLMResponse, ToolCallRequest, AgentTurnResponse
from src.config.settings import get_settings


class LLMClientError(Exception):
    """Base exception for LLM client operations."""
    pass


class MissingAPIKeyError(LLMClientError):
    """Raised when the OpenAI API key is missing or not configured."""
    pass


class LLMGenerationError(LLMClientError):
    """Raised when an error occurs during text generation."""
    pass


def sanitize_secret_message(message: str) -> str:
    """Mask any potential API key tokens from exception messages."""
    return re.sub(r"sk-[a-zA-Z0-9_\-]{10,}", "[REDACTED_API_KEY]", str(message))


class OpenAIClientWrapper:
    """Encapsulates interaction with the official OpenAI Python SDK Responses API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model or "gpt-5.6-luna"

        if not self._api_key or not self._api_key.strip():
            raise MissingAPIKeyError(
                "OpenAI API key is missing. Please configure OPENAI_API_KEY in your .env file or environment."
            )

        try:
            self.client = OpenAI(api_key=self._api_key)
        except Exception as e:
            raise LLMClientError(f"Failed to initialize OpenAI client: {sanitize_secret_message(str(e))}") from None

    def generate_response(
        self,
        input_text: str,
        instructions: str,
    ) -> LLMResponse:
        """Call the OpenAI Responses API to generate a grounded response (Milestone 2 flow).

        Args:
            input_text: The user prompt containing the question and retrieved context.
            instructions: Developer/system instructions guiding the model's behavior.

        Returns:
            LLMResponse containing the output text and completion metadata.
        """
        if not input_text or not input_text.strip():
            raise ValueError("Input text cannot be empty.")

        try:
            # Calling the official OpenAI Responses API without temperature
            response = self.client.responses.create(
                model=self.model,
                input=input_text,
                instructions=instructions,
            )

            # Extract generated content from Responses API object
            output_content = ""
            if hasattr(response, "output_text") and response.output_text:
                output_content = response.output_text
            elif hasattr(response, "output"):
                # Fallback to traversing response output items if present
                for item in response.output:
                    if getattr(item, "type", None) == "message":
                        for content_part in getattr(item, "content", []):
                            if getattr(content_part, "type", None) == "text":
                                output_content += getattr(content_part, "text", "")

            response_id = getattr(response, "id", None)
            return LLMResponse(
                content=output_content.strip(),
                model=self.model,
                response_id=response_id,
            )
        except OpenAIError as e:
            sanitized_err = sanitize_secret_message(str(e))
            raise LLMGenerationError(f"OpenAI API error during response generation: {sanitized_err}") from None
        except Exception as e:
            sanitized_err = sanitize_secret_message(str(e))
            raise LLMGenerationError(f"Unexpected error during LLM generation: {sanitized_err}") from None

    def create_agent_turn(
        self,
        input_items: Union[str, List[Any]],
        instructions: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        previous_response_id: Optional[str] = None,
    ) -> AgentTurnResponse:
        """Execute a turn in an agent orchestrator loop using the Responses API (Milestone 3).

        Args:
            input_items: User prompt string or list of input items / tool call outputs.
            instructions: Agent system instructions.
            tools: List of authorized tool definitions in OpenAI function schema format.
            previous_response_id: Chained response ID for multi-turn conversation state.

        Returns:
            AgentTurnResponse containing requested tool calls or final natural language answer.
        """
        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "input": input_items,
                "instructions": instructions,
            }
            if tools:
                kwargs["tools"] = tools
            if previous_response_id:
                kwargs["previous_response_id"] = previous_response_id

            # Calling the official OpenAI Responses API without temperature
            response = self.client.responses.create(**kwargs)

            # Extract tool calls and text content
            tool_calls: List[ToolCallRequest] = []
            output_content = ""

            if hasattr(response, "output") and response.output:
                for item in response.output:
                    item_type = getattr(item, "type", None)
                    if item_type == "function_call":
                        raw_args = getattr(item, "arguments", "{}")
                        if isinstance(raw_args, str):
                            try:
                                parsed_args = json.loads(raw_args)
                            except Exception:
                                parsed_args = {"raw": raw_args}
                        elif isinstance(raw_args, dict):
                            parsed_args = raw_args
                        else:
                            parsed_args = {}

                        call_id = getattr(item, "call_id", None) or getattr(item, "id", "")
                        tool_calls.append(
                            ToolCallRequest(
                                call_id=call_id,
                                name=getattr(item, "name", ""),
                                arguments=parsed_args,
                            )
                        )
                    elif item_type == "message":
                        for part in getattr(item, "content", []):
                            if getattr(part, "type", None) == "text":
                                output_content += getattr(part, "text", "")

            if not output_content and hasattr(response, "output_text") and response.output_text:
                output_content = response.output_text

            return AgentTurnResponse(
                content=output_content.strip() if output_content else None,
                tool_calls=tool_calls,
                model=self.model,
                response_id=getattr(response, "id", None),
            )
        except OpenAIError as e:
            sanitized_err = sanitize_secret_message(str(e))
            raise LLMGenerationError(f"OpenAI API error during agent turn: {sanitized_err}") from None
        except Exception as e:
            sanitized_err = sanitize_secret_message(str(e))
            raise LLMGenerationError(f"Unexpected error during agent turn: {sanitized_err}") from None
