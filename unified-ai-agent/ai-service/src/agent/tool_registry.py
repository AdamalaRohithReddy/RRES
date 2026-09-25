"""Tool Registry managing available tools, validation, and safe execution."""
import logging
from typing import Dict, Any, List, Optional
from src.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when tool execution fails or an unauthorized tool is requested."""
    pass


class ToolRegistry:
    """Registry maintaining authorized tools and executing them with strict safety boundaries."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new authorized tool in the registry."""
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Tool must inherit from BaseTool, got {type(tool).__name__}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a registered tool by name."""
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        """Check if a tool name is registered in the registry."""
        return name in self._tools

    def list_tool_names(self) -> List[str]:
        """Return names of all currently registered tools."""
        return list(self._tools.keys())

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Export all registered tools in OpenAI Responses function tool schema format."""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def execute(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Safely execute a registered tool with provided arguments.

        CRITICAL SECURITY RULES:
        1. Only tools explicitly registered in `self._tools` may be executed.
        2. Arbitrary code, shell, or database execution attempts are rejected immediately.
        3. Exceptions inside tools are trapped and returned as structured error payloads.
        """
        clean_name = (tool_name or "").strip()
        args = arguments or {}

        # Rule 1 & 2: Authorize tool name
        if clean_name not in self._tools:
            return {
                "status": "error",
                "tool": clean_name,
                "error_type": "UNAUTHORIZED_TOOL",
                "message": (
                    f"Access Denied: Tool '{clean_name}' is not an authorized registered tool. "
                    f"Available tools are: {', '.join(self.list_tool_names())}"
                ),
            }

        target_tool = self._tools[clean_name]

        try:
            result = target_tool.execute(**args)
            return result
        except TypeError as te:
            return {
                "status": "error",
                "tool": clean_name,
                "error_type": "INVALID_ARGUMENTS",
                "message": f"Invalid arguments provided to tool '{clean_name}': {str(te)}",
            }
        except Exception as e:
            return {
                "status": "error",
                "tool": clean_name,
                "error_type": "EXECUTION_FAILURE",
                "message": f"Error executing tool '{clean_name}': {str(e)}",
            }
