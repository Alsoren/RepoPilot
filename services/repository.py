import os
import stat
import shutil
import subprocess
import tempfile
from pathlib import Path

MAX_FILE_SIZE = 100_000  # yaklaşık 100 KB

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
}

def prepare_repository(repo_source: str) -> tuple[str, bool]:
    repo_source = repo_source.strip().rstrip("/")

    if repo_source.startswith(("https://github.com/", "http://github.com/")):
        temp_dir = tempfile.mkdtemp(prefix="repopilot_")

        branch = None
        clone_url = repo_source

        # /tree/<branch>[/<subpath>]  veya  /blob/<branch>/<file>
        for marker in ("/tree/", "/blob/"):
            if marker in repo_source:
                repo_part, rest = repo_source.split(marker, 1)
                # Branch adını ilk "/" öncesine kadar al.
                # Not: branch adında "/" varsa (örn. "feature/x") bu
                # yöntem yanlış sonuç verebilir — GitHub URL'si bunu
                # tek başına ayırt edemez.
                branch = rest.split("/", 1)[0]
                clone_url = repo_part
                break

        if not clone_url.endswith(".git"):
            clone_url += ".git"

        command = ["git", "clone", "--depth", "1"]
        if branch:
            command.extend(["--branch", branch])
        command.extend([clone_url, temp_dir])

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Git clone failed:\n{error.stderr}") from error

        return temp_dir, True

    repo_path = Path(repo_source)

    if not repo_path.exists():
        raise ValueError(f"Repository not found: {repo_source}")

    if not repo_path.is_dir():
        raise ValueError("Repository path must be a directory.")

    return str(repo_path), False


def cleanup_repository(
    repo_path: str,
    is_temporary_repo: bool
):
    if not is_temporary_repo:
        return

    repo = Path(repo_path)

    print("\n[Cleanup] Removing temporary repository...")

    def remove_readonly(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    try:
        shutil.rmtree(
            repo,
            onexc=remove_readonly
        )

        print(
            "[Cleanup] Temporary repository completely removed."
        )

    except Exception as error:
        print(
            f"[Cleanup] Failed to remove repository: {error}"
        )

def scan_repository(repo_path: str):
    repo = Path(repo_path)

    files = []

    for file_path in repo.rglob("*"):
        if not file_path.is_file():
            continue

        if any(part in IGNORED_DIRECTORIES for part in file_path.parts):
            continue

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        if file_path.stat().st_size > MAX_FILE_SIZE:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if not content.strip():
            continue

        files.append(
            {
                "path": str(file_path.relative_to(repo)),
                "language": SUPPORTED_EXTENSIONS[extension],
                "content": content,
            }
        )

    return files