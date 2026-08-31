import re
from pathlib import Path


ENTRY_POINT_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "main.java",
    "application.java",
    "index.js",
    "index.ts",
    "index.tsx",
    "main.js",
    "main.ts",
}


CONFIG_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}


IMPORTANT_DIRECTORIES = {
    "src",
    "app",
    "core",
    "service",
    "services",
    "api",
    "controller",
    "controllers",
    "repository",
    "repositories",
    "domain",
    "models",
}


LOW_PRIORITY_DIRECTORIES = {
    "test",
    "tests",
    "docs",
    "examples",
    "example",
    "generated",
    "vendor",
    "dist",
    "build",
    "migrations",
}


def _count_functions(content: str) -> int:
    patterns = [
        # Python
        r"\bdef\s+\w+\s*\(",

        # JavaScript / TypeScript
        r"\bfunction\s+\w+\s*\(",

        # Java / C# / C++ style methods
        r"\b(?:public|private|protected)?\s*"
        r"[\w<>\[\], ?]+\s+\w+\s*\([^;]*\)\s*\{",
    ]

    return sum(
        len(re.findall(pattern, content))
        for pattern in patterns
    )


def _count_classes(content: str) -> int:
    return len(
        re.findall(
            r"\bclass\s+\w+",
            content
        )
    )


def _count_imports(content: str) -> int:
    patterns = [
        # Python / Java / JS imports
        r"^\s*import\s+",

        # Python from x import y
        r"^\s*from\s+\S+\s+import\s+",

        # C / C++
        r'^\s*#include\s*[<"]',

        # CommonJS
        r"^\s*(?:const|let|var)?\s*\w*\s*=?\s*require\s*\(",
    ]

    return sum(
        len(
            re.findall(
                pattern,
                content,
                flags=re.MULTILINE
            )
        )
        for pattern in patterns
    )


def calculate_file_priority(file: dict) -> float:
    path = Path(file["path"])
    file_name = path.name.lower()

    path_parts = {
        part.lower()
        for part in path.parts
    }

    content = file.get("content", "")

    score = 0.0

    # 1. Entry points
    if file_name in ENTRY_POINT_NAMES:
        score += 20

    # 2. Configuration / dependency files
    if file_name in CONFIG_FILES:
        score += 12

    # 3. Important architectural directories
    important_dir_hits = len(
        path_parts & IMPORTANT_DIRECTORIES
    )

    score += min(
        important_dir_hits * 3,
        9
    )

    # 4. Lower-value directories
    low_priority_hits = len(
        path_parts & LOW_PRIORITY_DIRECTORIES
    )

    score -= min(
        low_priority_hits * 5,
        15
    )

    # 5. Function density
    function_count = _count_functions(content)

    score += min(
        function_count * 1.5,
        12
    )

    # 6. Class density
    class_count = _count_classes(content)

    score += min(
        class_count * 2.5,
        10
    )

    # 7. Dependency / import density
    import_count = _count_imports(content)

    score += min(
        import_count * 0.75,
        8
    )

    # 8. Code volume
    line_count = len(content.splitlines())

    if 20 <= line_count <= 400:
        score += 4

    elif 400 < line_count <= 800:
        score += 1

    elif line_count > 800:
        score -= 4

    # 9. Very small / trivial files
    if line_count < 10:
        score -= 5

    return round(score, 2)


def prioritize_files(
    files: list[dict]
) -> list[dict]:

    prioritized_files = []

    for file in files:
        priority_score = calculate_file_priority(file)

        prioritized_files.append(
            {
                **file,
                "priority_score": priority_score,
            }
        )

    return sorted(
        prioritized_files,
        key=lambda file: file["priority_score"],
        reverse=True
    )