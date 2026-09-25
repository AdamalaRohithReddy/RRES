"""State management for the Agent Orchestrator."""
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    """Represents a single tool invocation step executed by the agent."""
    step_number: int = Field(description="Step sequence number")
    tool_name: str = Field(description="Name of the tool called")
    tool_arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    tool_result: Dict[str, Any] = Field(default_factory=dict, description="Result returned by tool execution")
    timestamp: float = Field(default_factory=time.time, description="Epoch timestamp of step execution")


class AgentState(BaseModel):
    """Tracks conversation context, tool executions, and turn limits for an agent session."""
    query: str = Field(description="Original citizen user query")
    steps: List[AgentStep] = Field(default_factory=list, description="Sequence of tool execution steps")
    current_iteration: int = Field(default=0, description="Number of LLM reasoning turns executed")
    max_iterations: int = Field(default=5, description="Maximum allowed agent turns before loop termination")
    final_answer: Optional[str] = Field(default=None, description="Final natural-language response generated")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Verified sources gathered by tools")
    is_mock_used: bool = Field(default=False, description="Flag indicating if any mock tool data was referenced")

    def has_reached_limit(self) -> bool:
        """Check if maximum allowed agent iterations have been exhausted."""
        return self.current_iteration >= self.max_iterations

    def add_step(self, tool_name: str, arguments: Dict[str, Any], result: Dict[str, Any]) -> AgentStep:
        """Record a completed tool execution step."""
        step = AgentStep(
            step_number=len(self.steps) + 1,
            tool_name=tool_name,
            tool_arguments=arguments,
            tool_result=result,
        )
        self.steps.append(step)

        # Track sources if RAG tool was called
        if tool_name == "search_government_schemes" and isinstance(result, dict):
            for res in result.get("results", []):
                self.sources.append(res)

        # Track mock data usage
        if result.get("is_mock"):
            self.is_mock_used = True

        return step

    def get_tool_call_names(self) -> List[str]:
        """Return list of all tool names executed in this interaction."""
        return [s.tool_name for s in self.steps]
