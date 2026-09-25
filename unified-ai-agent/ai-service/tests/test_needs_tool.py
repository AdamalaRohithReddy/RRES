"""Unit tests for Milestone 6 Need Detection Tool."""
import pytest
from src.tools.need_tool import NeedDetectionTool
from src.agent.tool_registry import ToolRegistry


def test_need_tool_metadata():
    """Verify tool naming, description, and schema."""
    tool = NeedDetectionTool()
    assert tool.name == "detect_citizen_needs"
    assert "problem description" in tool.description.lower()
    assert "hardship" in tool.description.lower()

    schema = tool.parameters_schema
    assert schema["type"] == "object"
    assert "text" in schema["properties"]
    assert "text" in schema["required"]


def test_need_tool_execution_success():
    """Verify tool execution on a multi-need sentence returns expected structured dict."""
    tool = NeedDetectionTool()
    result = tool.execute(text="I lost my job and cannot pay school fees for my daughter.")

    assert isinstance(result, dict)
    assert result["total_needs"] >= 2
    categories = [n["category"] for n in result["needs"]]
    assert "employment" in categories
    assert "education" in categories
    assert "disclaimer" in result
    assert "does NOT determine eligibility" in result["disclaimer"]
    assert "employment" in result["suggested_scheme_queries"]
    assert "education" in result["suggested_scheme_queries"]


def test_need_tool_execution_ambiguous():
    """Verify tool execution on ambiguous request returns clarification prompts and NO scheme queries."""
    tool = NeedDetectionTool()
    result = tool.execute(text="I need help for my family.")

    assert result["is_ambiguous"] is True
    assert result["total_needs"] == 1
    assert result["needs"][0]["category"] == "unknown_ambiguous"
    assert len(result["clarification_prompts"]) > 0
    assert result["suggested_scheme_queries"] == {}


def test_need_tool_registered_in_tool_registry():
    """Verify NeedDetectionTool registers cleanly in ToolRegistry."""
    registry = ToolRegistry()
    tool = NeedDetectionTool()
    registry.register(tool)

    retrieved = registry.get("detect_citizen_needs")
    assert retrieved is tool
    assert "detect_citizen_needs" in [t["name"] for t in registry.get_tool_definitions()]
