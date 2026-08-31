import operator
from typing import Annotated ,List, TypedDict
from pydantic import BaseModel, Field
from langchain.agents import AgentState

class Finding(BaseModel):
    category: str = Field(
        description="Issue category such as bug, security, quality, or improvement"
    )

    severity: str = Field(
        description="Severity level: low, medium, high, or critical"
    )

    title: str = Field(
        description="Short title of the finding"
    )

    description: str = Field(
        description="Clear explanation of the issue"
    )

    suggestion: str = Field(
        description="Recommended fix or improvement"
    )


class CodeAnalysis(BaseModel):
    file_path: str

    findings: List[Finding]

class SpecialistFinding(BaseModel):
    agent: str
    severity: str
    title: str
    description: str
    suggestion: str


class SpecialistAnalysis(BaseModel):
    findings: list[SpecialistFinding]

class CriticAnalysis(BaseModel):
    approved: bool
    feedback: str
    retry_routes: list[str] = Field(
        default_factory=list,
        description=(
            "List of specialist routes that must be re-run because their findings "
            "were insufficient, unclear, inaccurate, or not actionable enough. "
            "Allowed values: security, bug, quality. "
            "Must be empty when approved is true."
        )
    )

# Reducer
def merge_specialist_findings(
    existing: list[SpecialistFinding],
    new: list[SpecialistFinding]
):
    if not existing:
        return new

    if not new:
        return existing

    new_agents = {
        finding.agent
        for finding in new
    }

    remaining_findings = [
        finding
        for finding in existing
        if finding.agent not in new_agents
    ]

    return remaining_findings + new

def keep_max_retry(current: int, new: int) -> int:
    return max(current, new)

class RepoPilotState(TypedDict):
    repo_path: str
    is_temporary_repo: bool

    # Repository
    files: list[dict]
    prioritized_files: list[dict]

    # Exploration
    exploration_summary: str
    important_files: list[str]

    # Context selection
    analysis_files: list[dict]

    # Analysis
    analyses: list[CodeAnalysis]
    routes: list[str]

    # Specialists
    specialist_findings: Annotated[
        list[SpecialistFinding],
        merge_specialist_findings
    ]

    # Critic
    critic_analysis: CriticAnalysis
    retry_count: Annotated[
        int,
        keep_max_retry
    ]

    # Output
    report: str

# Explorer agent state
class ExplorerState(AgentState):
    repo_path: str
    prioritized_files: list[dict]      # -> priority_ranked_files (heuristic, input)
    important_files: list[str]         # -> explorer_findings (semantic, output)

# Chat agent state
class ChatState(AgentState):
    repo_path: str