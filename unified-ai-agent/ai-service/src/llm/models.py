"""Data models for LLM interactions."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Encapsulates the response returned by a single LLM completion."""
    content: str = Field(description="Generated text content")
    model: str = Field(description="Model identifier that produced the completion")
    response_id: Optional[str] = Field(default=None, description="OpenAI response ID if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")


class ToolCallRequest(BaseModel):
    """Represents a structured tool execution call requested by the LLM."""
    call_id: str = Field(description="Unique call ID assigned by OpenAI Responses API")
    name: str = Field(description="Name of the function/tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Parsed arguments for the tool call")


class AgentTurnResponse(BaseModel):
    """Encapsulates an agent turn output: either tool calls or final natural language answer."""
    content: Optional[str] = Field(default=None, description="Natural language output text (if generated)")
    tool_calls: List[ToolCallRequest] = Field(default_factory=list, description="Tool calls requested in this turn")
    model: str = Field(description="Model identifier")
    response_id: Optional[str] = Field(default=None, description="Response ID from OpenAI Responses API")

    @property
    def has_tool_calls(self) -> bool:
        """True if the model requested one or more tool calls."""
        return len(self.tool_calls) > 0
