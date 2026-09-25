"""Agent Orchestrator controlling the LLM reasoning and tool execution loop."""
import json
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.agent.state import AgentState
from src.agent.tool_registry import ToolRegistry
from src.agent.prompts import AGENT_ORCHESTRATOR_SYSTEM_INSTRUCTIONS
from src.llm.client import OpenAIClientWrapper, LLMGenerationError
from src.tools.rag_tool import SchemeSearchTool

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Structured response returned by the Agent Orchestrator."""
    answer: str = Field(description="Natural-language grounded answer for the citizen")
    tools_called: List[str] = Field(default_factory=list, description="List of tools invoked in this interaction")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Verified sources gathered by tools")
    is_mock_used: bool = Field(default=False, description="Flag indicating if mock/demo data was referenced")
    iterations: int = Field(default=0, description="Number of agent loop iterations executed")
    quota_limited: bool = Field(default=False, description="True if an API quota limitation prevented live generation")


class AgentOrchestrator:
    """Controls the interaction loop between the OpenAI LLM and registered tools."""

    MAX_AGENT_STEPS: int = 5

    def __init__(
        self,
        llm_client: Optional[OpenAIClientWrapper] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_steps: Optional[int] = None,
        verbose: bool = True,
    ):
        self.llm_client = llm_client
        self.tool_registry = tool_registry or ToolRegistry()
        self.max_steps = max_steps or self.MAX_AGENT_STEPS
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Safe logging utility for agent observability (never outputs secrets)."""
        if self.verbose:
            print(message)
        logger.info(message)

    def run(self, query: str) -> AgentResponse:
        """Execute the agent orchestrator loop for a citizen question.

        Flow:
            1. Initialize conversation state.
            2. Send query + tool definitions to LLM.
            3. If tool calls requested: validate, execute safely in Python, return output to LLM.
            4. Repeat until LLM produces final answer or MAX_AGENT_STEPS is reached.
            5. Return structured AgentResponse.
        """
        clean_query = query.strip()
        if not clean_query:
            return AgentResponse(
                answer="Please enter a question or query regarding government schemes, profile, or application status.",
                iterations=0,
            )

        state = AgentState(query=clean_query, max_iterations=self.max_steps)
        self._log(f"[AGENT] User query received: \"{clean_query}\"")

        # Lazy initialization of LLM client if not injected
        if self.llm_client is None:
            self.llm_client = OpenAIClientWrapper()

        tool_defs = self.tool_registry.get_tool_definitions()
        prev_response_id: Optional[str] = None
        current_input: Any = clean_query

        while not state.has_reached_limit():
            state.current_iteration += 1

            try:
                # Call OpenAI Responses API with tool definitions
                turn_response = self.llm_client.create_agent_turn(
                    input_items=current_input,
                    instructions=AGENT_ORCHESTRATOR_SYSTEM_INSTRUCTIONS,
                    tools=tool_defs,
                    previous_response_id=prev_response_id,
                )
            except LLMGenerationError as e:
                err_str = str(e)
                if "credit_balance_exhausted" in err_str or "insufficient_quota" in err_str:
                    self._log("[AGENT] Notice: OpenAI API quota exhausted (Error 429).")
                    return self._handle_quota_exhausted_fallback(clean_query, state)
                raise

            prev_response_id = turn_response.response_id

            # Case A: Model requested tool calls
            if turn_response.has_tool_calls:
                tool_output_items: List[Dict[str, Any]] = []

                for tool_call in turn_response.tool_calls:
                    t_name = tool_call.name
                    t_args = tool_call.arguments
                    self._log(f"[AGENT] LLM requested tool: {t_name}")

                    # Execute tool safely via registry (rejects unauthorized commands)
                    tool_result = self.tool_registry.execute(tool_name=t_name, arguments=t_args)
                    self._log(f"[TOOL] {t_name} executed")

                    if t_name == "search_government_schemes":
                        count = len(tool_result.get("results", []))
                        self._log(f"[TOOL] Retrieved {count} verified chunks")

                    state.add_step(tool_name=t_name, arguments=t_args, result=tool_result)

                    # Prepare function call output item for next turn
                    tool_output_items.append({
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(tool_result),
                    })

                self._log("[AGENT] Sending tool result to LLM")
                current_input = tool_output_items
                continue

            # Case B: Model returned natural language answer
            if turn_response.content:
                state.final_answer = turn_response.content
                self._log("[AGENT] Final response generated")
                break

        # Check if loop terminated due to iteration limit
        if state.has_reached_limit() and not state.final_answer:
            self._log(f"[AGENT] Reached maximum iteration limit ({self.max_steps}). Terminating loop safely.")
            state.final_answer = (
                "I have gathered information from the relevant tools, but reached the processing limit "
                "before completing the response. Please rephrase or narrow your question."
            )

        return AgentResponse(
            answer=state.final_answer or "No response could be generated.",
            tools_called=state.get_tool_call_names(),
            sources=state.sources,
            is_mock_used=state.is_mock_used,
            iterations=state.current_iteration,
        )

    def _handle_quota_exhausted_fallback(self, query: str, state: AgentState) -> AgentResponse:
        """Handle 429 quota exhaustion safely without fabricating answers.

        When the LLM credit quota is exhausted, this fallback dispatches the appropriate
        tool directly based on the user intent so the citizen can still inspect verified
        schemes, demo profiles, or application status safely.
        """
        q = query.lower()
        tools_called = []
        sources = []
        is_mock = False

        # Scenario A: Multi-tool recommendation (Profile + Schemes)
        if "profile" in q and ("support" in q or "scheme" in q or "relevant" in q or "eligible" in q or "apply" in q):
            profile_tool = self.tool_registry.get("get_citizen_profile")
            rag_tool = self.tool_registry.get("search_government_schemes")
            profile_res = profile_tool.execute(citizen_id="demo-user") if profile_tool else {}
            rag_res = rag_tool.execute(query="Startup India Seed Fund Scheme eligibility criteria", top_k=2) if rag_tool else {}

            tools_called.extend(["get_citizen_profile", "search_government_schemes"])
            is_mock = True
            sources = rag_res.get("results", [])

            p = profile_res.get("profile", {})
            lines = [
                "[OpenAI Quota Notice]: Your OpenAI API key has exhausted its credit quota (Error 429: credit_balance_exhausted).",
                "The Agent Orchestrator executed the relevant tools directly to support your query:\n",
                "[1] Citizen Profile Retrieved (Tool: get_citizen_profile):",
                f"    - Citizen ID: {p.get('citizen_id')} (Name: {p.get('name')})",
                f"    - Age: {p.get('age')} years | State: {p.get('state')} | Category: {p.get('category')}",
                f"    - Occupation: {p.get('occupation')} | Annual Income: Rs {p.get('annual_income', 0):,}",
                f"    - Special Status: {p.get('special_status')}",
                f"    - Note: {profile_res.get('notice')}\n",
                "[2] Relevant Government Scheme Information (Tool: search_government_schemes):",
            ]
            for idx, r in enumerate(sources, start=1):
                lines.append(f"    Clause {idx} ({r['scheme']}, Page {r['page']}, Section: {r['section']}):")
                lines.append(f"      {r['content']}\n")

            return AgentResponse(
                answer="\n".join(lines),
                tools_called=tools_called,
                sources=sources,
                is_mock_used=is_mock,
                iterations=2,
                quota_limited=True,
            )

        # Scenario B: Profile question
        if "profile" in q or "information do you have" in q or "about me" in q:
            profile_tool = self.tool_registry.get("get_citizen_profile")
            if profile_tool:
                profile_res = profile_tool.execute(citizen_id="demo-user")
                p = profile_res.get("profile", {})
                lines = [
                    "[OpenAI Quota Notice]: Your OpenAI API key has exhausted its credit quota (Error 429: credit_balance_exhausted).",
                    "The Agent Orchestrator retrieved your demographic profile directly via `get_citizen_profile`:\n",
                    f"- Citizen ID: {p.get('citizen_id')}",
                    f"- Name: {p.get('name')}",
                    f"- Age: {p.get('age')} years",
                    f"- Gender: {p.get('gender')}",
                    f"- State: {p.get('state')}",
                    f"- Category: {p.get('category')}",
                    f"- Occupation: {p.get('occupation')}",
                    f"- Annual Income: Rs {p.get('annual_income', 0):,}",
                    f"- Special Status: {p.get('special_status')}",
                    f"\n[Transparency Notice]: {profile_res.get('notice')}",
                ]
                return AgentResponse(
                    answer="\n".join(lines),
                    tools_called=["get_citizen_profile"],
                    sources=[],
                    is_mock_used=True,
                    iterations=1,
                    quota_limited=True,
                )

        # Scenario C: Application status question
        if "status" in q or "application" in q or "tracking" in q:
            status_tool = self.tool_registry.get("get_application_status")
            if status_tool:
                status_res = status_tool.execute(application_id="DEMO-001")
                rec = status_res.get("record", {})
                lines = [
                    "[OpenAI Quota Notice]: Your OpenAI API key has exhausted its credit quota (Error 429: credit_balance_exhausted).",
                    "The Agent Orchestrator retrieved your application tracking record directly via `get_application_status`:\n",
                    f"- Application ID: {rec.get('application_id')}",
                    f"- Scheme Name: {rec.get('scheme_name')}",
                    f"- Status: {rec.get('status')}",
                    f"- Submitted On: {rec.get('submission_date')}",
                    f"- Last Updated: {rec.get('last_updated')}",
                    f"- Remarks: {rec.get('remarks')}",
                    f"\n[Transparency Notice]: {status_res.get('notice')}",
                ]
                return AgentResponse(
                    answer="\n".join(lines),
                    tools_called=["get_application_status"],
                    sources=[],
                    is_mock_used=True,
                    iterations=1,
                    quota_limited=True,
                )

        # Scenario D: Scheme search question (RAG tool)
        rag_tool = self.tool_registry.get("search_government_schemes")
        if isinstance(rag_tool, SchemeSearchTool):
            rag_result = rag_tool.execute(query=query, top_k=2)
            results = rag_result.get("results", [])
            if results:
                self._log(f"[FALLBACK] Direct RAG search retrieved {len(results)} verified chunks.")
                answer_lines = [
                    "[OpenAI Quota Notice]: Your OpenAI API key has exhausted its credit quota (Error 429: credit_balance_exhausted).",
                    "The Agent Orchestrator cannot generate live natural language synthesis, but has directly retrieved the authoritative government clauses for your query:\n"
                ]
                for idx, r in enumerate(results, start=1):
                    answer_lines.append(f"[{idx}] {r['scheme']} — Page {r['page']} ({r['section']}):")
                    answer_lines.append(f"    {r['content']}\n")

                return AgentResponse(
                    answer="\n".join(answer_lines),
                    tools_called=["search_government_schemes"],
                    sources=results,
                    is_mock_used=False,
                    iterations=1,
                    quota_limited=True,
                )

        return AgentResponse(
            answer=(
                "[OpenAI Quota Notice]: Your OpenAI API key has exhausted its credit quota (Error 429: credit_balance_exhausted). "
                "The Agent Orchestrator architecture is functioning correctly, but cannot generate live LLM responses until "
                "API credits are added at https://platform.openai.com/settings/organization/billing/."
            ),
            tools_called=state.get_tool_call_names(),
            sources=state.sources,
            is_mock_used=state.is_mock_used,
            iterations=state.current_iteration,
            quota_limited=True,
        )
