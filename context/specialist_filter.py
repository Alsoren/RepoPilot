from core.state import CodeAnalysis

CATEGORY_MAP = {
    "security": {"security"},
    "bug": {"bug"},
    "quality": {"quality", "improvement"},
}


def filter_analyses_for_route(
    analyses: list[CodeAnalysis],
    route: str,
) -> list[CodeAnalysis]:
    allowed = CATEGORY_MAP.get(route, set())

    filtered = []

    for analysis in analyses:
        matching_findings = [
            finding
            for finding in analysis.findings
            if finding.category.lower().strip() in allowed
        ]

        if matching_findings:
            filtered.append(
                CodeAnalysis(
                    file_path=analysis.file_path,
                    findings=matching_findings,
                )
            )

    return filtered