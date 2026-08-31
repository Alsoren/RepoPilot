import os
from core.state import ChatState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from agent_tools.repository_tools import (
    list_files,
    read_file,
    search_code,
    find_references,
)


def build_system_prompt(
    report: str,
    exploration_summary: str,
) -> str:
    return f"""
You are RepoPilot's assistant for this repository.

RepoPilot has already completed a code analysis of this repository.

Use the existing repository analysis as your primary context.
Do not repeat the entire analysis unnecessarily.

If the user's question cannot be answered reliably from the existing
analysis, use the repository tools to inspect the real source code.

Repository tools available:
- list_files
- read_file
- search_code
- find_references

Never invent files, source code, findings, or repository relationships.

Repository overview:

{exploration_summary}

Analysis report:

{report}
"""

def create_chat_agent(session):
    chat_llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    checkpointer = InMemorySaver()

    return create_agent(
        model=chat_llm,
        tools=[
            list_files,
            read_file,
            search_code,
            find_references,
        ],
        system_prompt=build_system_prompt(
            session.report,
            session.exploration_summary,
        ),
        state_schema=ChatState,
        checkpointer=checkpointer,
    )