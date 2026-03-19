"""APAS Agent Graph — LangGraph workflow connecting orchestrator + specialists.

Flow:
  User Query → Orchestrator (route) → Specialist Agent(s) → Synthesize → Response
"""

import logging
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from agents.orchestrator import route_query, synthesize_responses
from agents.specialist import create_specialist_agent

logger = logging.getLogger(__name__)


# ─── State Schema ───

class AgentState(TypedDict):
    """State passed through the graph."""
    query: str                          # Original user query
    routed_agents: list[str]            # Which specialists to invoke
    agent_responses: dict[str, str]     # scope → response text
    final_response: str                 # Synthesized answer


# ─── Nodes ───

def orchestrator_node(state: AgentState) -> dict:
    """Route the query to appropriate specialist agent(s)."""
    query = state["query"]
    agents = route_query(query)
    logger.info(f"Orchestrator routed to: {agents}")
    return {"routed_agents": agents, "agent_responses": {}}


def specialist_node(state: AgentState) -> dict:
    """Run all routed specialist agents and collect responses."""
    query = state["query"]
    routed = state["routed_agents"]
    responses = dict(state.get("agent_responses", {}))

    for scope in routed:
        logger.info(f"Running {scope} agent...")
        try:
            agent = create_specialist_agent(scope)
            result = agent.invoke({"messages": [HumanMessage(content=query)]})

            # Extract the final AI message content
            ai_messages = [m for m in result["messages"] if hasattr(m, "content") and m.type == "ai"]
            if ai_messages:
                # Get the last AI message (the final answer, not tool calls)
                final_msg = None
                for msg in reversed(ai_messages):
                    if msg.content and not getattr(msg, "tool_calls", None):
                        final_msg = msg
                        break
                if final_msg:
                    responses[scope] = final_msg.content
                else:
                    responses[scope] = ai_messages[-1].content
            else:
                responses[scope] = "Agent did not produce a response."

        except Exception as e:
            logger.error(f"{scope} agent failed: {e}")
            responses[scope] = f"Error: {scope} agent encountered an issue — {str(e)}"

    return {"agent_responses": responses}


def synthesize_node(state: AgentState) -> dict:
    """Merge specialist responses into a unified answer."""
    query = state["query"]
    responses = state["agent_responses"]

    if not responses:
        return {"final_response": "No specialist agents were able to process this query."}

    final = synthesize_responses(query, responses)
    return {"final_response": final}


# ─── Graph Construction ───

def build_graph() -> StateGraph:
    """Build and compile the APAS agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("specialists", specialist_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "specialists")
    graph.add_edge("specialists", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


# ─── Public API ───

_compiled_graph = None


def get_graph():
    """Get or create the compiled graph (singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def ask(query: str) -> str:
    """Run a query through the full APAS agent pipeline.

    Args:
        query: User's question about government scheme appraisal.

    Returns:
        Formatted response with citations.
    """
    graph = get_graph()
    result = graph.invoke({
        "query": query,
        "routed_agents": [],
        "agent_responses": {},
        "final_response": "",
    })
    return result["final_response"]
