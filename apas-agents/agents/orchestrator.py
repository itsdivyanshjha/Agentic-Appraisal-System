"""Orchestrator — routes queries to specialist agents and synthesizes responses."""

import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, ORCHESTRATOR_MODEL
from prompts.system_prompts import ORCHESTRATOR_PROMPT, SYNTHESIZER_PROMPT

logger = logging.getLogger(__name__)


def create_orchestrator_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=ORCHESTRATOR_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0.0,
    )


def route_query(query: str) -> list[str]:
    """Determine which specialist agent(s) should handle this query.

    Returns a list of scope names: ["compliance"], ["fiscal", "sector"], etc.
    """
    llm = create_orchestrator_llm()

    messages = [
        SystemMessage(content=ORCHESTRATOR_PROMPT),
        HumanMessage(content=query),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Parse JSON response
    try:
        # Handle markdown fences
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(l for l in lines if not l.strip().startswith("```"))

        result = json.loads(raw)
        agents = result.get("agents", [])

        # Validate agent names
        valid = {"compliance", "fiscal", "sector"}
        agents = [a for a in agents if a in valid]

        if not agents:
            reason = result.get("reason", "no agents selected")
            logger.warning(f"Orchestrator returned no agents: {reason}")
            # Fallback: route to compliance (most general)
            return ["compliance"]

        logger.info(f"Routing to: {agents}")
        return agents

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse orchestrator response: {e}. Raw: {raw}")
        # Fallback: route to compliance
        return ["compliance"]


def synthesize_responses(query: str, agent_responses: dict[str, str]) -> str:
    """Merge responses from multiple specialist agents into a unified answer.

    Args:
        query: The original user query.
        agent_responses: Dict mapping scope name to agent's response text.

    Returns:
        Synthesized response string.
    """
    # If only one agent responded, return its response directly
    if len(agent_responses) == 1:
        scope, response = next(iter(agent_responses.items()))
        return response

    llm = create_orchestrator_llm()

    # Build context from all agent responses
    agent_texts = []
    for scope, response in agent_responses.items():
        agent_texts.append(f"=== {scope.upper()} AGENT RESPONSE ===\n{response}")

    combined = "\n\n".join(agent_texts)

    messages = [
        SystemMessage(content=SYNTHESIZER_PROMPT),
        HumanMessage(content=f"User query: {query}\n\nSpecialist responses:\n\n{combined}"),
    ]

    response = llm.invoke(messages)
    return response.content
