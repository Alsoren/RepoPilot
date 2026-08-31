from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
}

MAX_TOOL_FILE_SIZE = 100_000
MAX_RESULTS = 50


def resolve_repo_path(
    repo_path: str,
    relative_path: str,
) -> Path | None:

    repo_root = Path(repo_path).resolve()
    target = (repo_root / relative_path).resolve()

    try:
        target.relative_to(repo_root)
    except ValueError:
        return None

    return target


@tool
def list_files(
    state: Annotated[dict, InjectedState]
) -> list[dict]:
    """
    List repository files.

    If prioritized_files are available in the agent state,
    return them ordered by priority score.

    Otherwise, fall back to scanning the repository from disk.
    """

    prioritized_files = state.get(
        "prioritized_files",
        []
    )

    if prioritized_files:
        sorted_files = sorted(
            prioritized_files,
            key=lambda file: file.get(
                "priority_score",
                0
            ),
            reverse=True,
        )

        return [
            {
                "path": file["path"],
                "priority_score": file.get(
                    "priority_score",
                    0
                ),
            }
            for file in sorted_files[:MAX_RESULTS]
        ]

    repo_root = Path(
        state["repo_path"]
    ).resolve()

    results = []

    for path in repo_root.rglob("*"):

        if not path.is_file():
            continue

        relative_path = path.relative_to(
            repo_root
        )

        if any(
            part in IGNORED_DIRECTORIES
            for part in relative_path.parts
        ):
            continue

        results.append(
            {
                "path": str(relative_path),
                "priority_score": 0,
            }
        )

        if len(results) >= MAX_RESULTS:
            break

    return results


@tool
def read_file(
    state: Annotated[dict, InjectedState],
    file_path: str,
) -> str:
    """
    Read a source file from the repository.
    """

    repo_path = state["repo_path"]

    target = resolve_repo_path(
        repo_path,
        file_path,
    )

    if target is None:
        return "Invalid file path."

    if not target.is_file():
        return f"File not found: {file_path}"

    if target.stat().st_size > MAX_TOOL_FILE_SIZE:
        return f"File too large: {file_path}"

    try:
        return target.read_text(
            encoding="utf-8",
            errors="replace",
        )

    except OSError as error:
        return f"Unable to read file: {error}"


@tool
def search_code(
    state: Annotated[dict, InjectedState],
    query: str,
) -> list[str]:
    """
    Search for text across repository files.
    """

    repo_root = Path(state["repo_path"]).resolve()

    matches = []
    query_lower = query.lower()

    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(repo_root)

        if any(
            part in IGNORED_DIRECTORIES
            for part in relative_path.parts
        ):
            continue

        try:
            if path.stat().st_size > MAX_TOOL_FILE_SIZE:
                continue

            content = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except OSError:
            continue

        if query_lower in content.lower():
            matches.append(str(relative_path))

        if len(matches) >= MAX_RESULTS:
            break

    return matches


@tool
def find_references(
    state: Annotated[dict, InjectedState],
    symbol: str,
) -> list[str]:
    """
    Find repository files containing a symbol.
    """

    repo_root = Path(state["repo_path"]).resolve()

    references = []

    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(repo_root)

        if any(
            part in IGNORED_DIRECTORIES
            for part in relative_path.parts
        ):
            continue

        try:
            if path.stat().st_size > MAX_TOOL_FILE_SIZE:
                continue

            content = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except OSError:
            continue

        if symbol in content:
            references.append(str(relative_path))

        if len(references) >= MAX_RESULTS:
            break

    return references