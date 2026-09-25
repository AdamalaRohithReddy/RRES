"""Base tool abstraction for Agent Orchestrator."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """Abstract base class representing an executable agent tool."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description explaining what the tool does and when the LLM should invoke it."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema defining the expected input arguments."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool logic and return structured results."""
        pass

    def to_openai_tool(self) -> Dict[str, Any]:
        """Format tool definition for OpenAI Responses / function tool parameter specifications."""
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
