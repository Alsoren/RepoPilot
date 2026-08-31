import os
from core.state import ExplorerState
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from pydantic import BaseModel, Field

from agent_tools.repository_tools import (
    list_files,
    read_file,
    search_code,
    find_references,
)


load_dotenv()

explorer_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

explorer_tools = [
    list_files,
    read_file,
    search_code,
    find_references,
]

class ExplorerResult(BaseModel):
    summary: str = Field(
        description="Concise summary of the repository structure and important relationships."
    )

    important_files: list[str] = Field(
        description=(
            "Exact repository-relative paths of files that are important "
            "for deeper code analysis."
        )
    )

explorer_agent = create_agent(
    model=explorer_llm,
    tools=explorer_tools,
    state_schema=ExplorerState,
    response_format=ExplorerResult,
    system_prompt="""
You are the repository exploration agent of RepoPilot.

Your job is to explore a software repository and gather useful context
before deeper code analysis is performed.

You have access to repository tools:

- list_files: inspect the repository file structure
- read_file: read a specific source file
- search_code: search for text across the repository
- find_references: find files referencing a symbol

You must use repository tools to inspect the repository before producing
the final exploration summary.

Start by using list_files to inspect the prioritized repository structure.
Then use read_file, search_code, and find_references selectively based on
what you discover.

Focus on understanding:
- repository structure
- important source files
- entry points
- important classes and functions
- dependencies between files
- areas that may require deeper analysis

Repository files may include priority scores.

Use priority scores as navigation hints when deciding which files
to inspect first.

Prefer higher-priority files when starting repository exploration,
because they are more likely to be structurally important.

However:
- A high priority score does not mean that a file contains a bug,
  vulnerability, or quality issue.
- Priority scores are heuristic signals, not evidence.
- Do not ignore lower-priority files.
- Inspect lower-priority files whenever dependencies, references,
  or repository relationships make them relevant.
- Base your conclusions on information obtained through repository tools,
  not on priority scores alone.

Do not invent repository information.
Base your conclusions only on information obtained from the available tools.
"""
)