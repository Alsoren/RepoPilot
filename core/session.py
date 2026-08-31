# session.py

from dataclasses import dataclass

from core.state import (
    CodeAnalysis,
    SpecialistFinding,
    CriticAnalysis,
)


@dataclass
class RepoSession:
    repo_path: str
    exploration_summary: str
    important_files: list[str]
    analysis_files: list[dict]
    analyses: list[CodeAnalysis]
    specialist_findings: list[SpecialistFinding]
    critic_analysis: CriticAnalysis | None
    report: str


def strip_file_content(files: list[dict]) -> list[dict]:
    return [
        {
            key: value
            for key, value in file.items()
            if key != "content"
        }
        for file in files
    ]


def create_repo_session(result: dict) -> RepoSession:
    return RepoSession(
        repo_path=result["repo_path"],
        exploration_summary=result.get(
            "exploration_summary",
            "",
        ),
        important_files=result.get(
            "important_files",
            [],
        ),
        analysis_files=strip_file_content(
            result.get("analysis_files", [])
        ),
        analyses=result.get(
            "analyses",
            [],
        ),
        specialist_findings=result.get(
            "specialist_findings",
            [],
        ),
        critic_analysis=result.get(
            "critic_analysis",
        ),
        report=result.get(
            "report",
            "",
        ),
    )