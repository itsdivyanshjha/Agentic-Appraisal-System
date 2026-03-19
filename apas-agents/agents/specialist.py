"""Specialist agent factory — creates ReAct agents with scoped retrieval tools."""

import logging

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, AGENT_MODEL
from tools.retrieval import create_search_rules_tool, create_search_documents_tool
from prompts.system_prompts import COMPLIANCE_PROMPT, FISCAL_PROMPT, SECTOR_PROMPT

logger = logging.getLogger(__name__)

AGENT_PROMPTS = {
    "compliance": COMPLIANCE_PROMPT,
    "fiscal": FISCAL_PROMPT,
    "sector": SECTOR_PROMPT,
}


def create_specialist_agent(scope: str):
    """Create a ReAct agent for the given scope (compliance/fiscal/sector).

    Each agent gets:
    - A scoped system prompt defining its expertise
    - search_rules tool (queries primary collection)
    - search_documents tool (queries secondary collection)
    - LLM via OpenRouter
    """
    if scope not in AGENT_PROMPTS:
        raise ValueError(f"Unknown scope: {scope}. Must be one of: {list(AGENT_PROMPTS.keys())}")

    llm = ChatOpenAI(
        model=AGENT_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0.1,
    )

    tools = [
        create_search_rules_tool(scope),
        create_search_documents_tool(scope),
    ]

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=AGENT_PROMPTS[scope],
    )

    logger.info(f"Created {scope} agent with model={AGENT_MODEL}")
    return agent
