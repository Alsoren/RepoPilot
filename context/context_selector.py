# context/context_selector.py
from pathlib import Path

MAX_ANALYSIS_TOKENS = 40_000
SYSTEM_PROMPT_BUFFER = 300  # şablon + talimat metni için sabit pay


def normalize_path(path: str) -> str:
    return str(Path(path))


def estimate_tokens(content: str) -> int:
    """
    Basit token tahmini.
    Ortalama olarak 1 token ≈ 4 karakter varsayıyoruz.
    Bu kesin tokenizer değildir ama deterministic budget için yeterlidir.
    """
    if not content:
        return 0
    return max(1, len(content) // 4)


def select_analysis_files(
    prioritized_files: list[dict],
    important_files: list[str],
    exploration_summary: str = "",
) -> list[dict]:
    overhead = estimate_tokens(exploration_summary) + SYSTEM_PROMPT_BUFFER

    def file_cost(file: dict) -> int:
        return estimate_tokens(file.get("content", "")) + overhead

    normalized_important = {
        normalize_path(path) for path in important_files
    }
    by_path = {
        normalize_path(file["path"]): file
        for file in prioritized_files
    }

    selected_files: list[dict] = []
    used_tokens = 0

    # 1. High-priority first pass: Explorer'ın kanıtla önemli bulduğu
    #    dosyalar önce denenir. "Garanti" değil, öncelik — bütçeyi
    #    aşan çok büyük bir dosya yine de elenebilir.
    first_pass = sorted(
        (by_path[p] for p in normalized_important if p in by_path),
        key=lambda f: f.get("priority_score", 0),
        reverse=True,
    )

    for file in first_pass:
        cost = file_cost(file)
        if used_tokens + cost > MAX_ANALYSIS_TOKENS:
            continue
        selected_files.append({**file, "context_score": file.get("priority_score", 0)})
        used_tokens += cost

    # 2. Kalan bütçe: priority_score / token yoğunluğuna göre greedy doldur.
    remaining = [
        file for file in prioritized_files
        if normalize_path(file["path"]) not in normalized_important
    ]

    remaining.sort(
        key=lambda f: f.get("priority_score", 0) / file_cost(f),
        reverse=True,
    )

    for file in remaining:
        cost = file_cost(file)
        if used_tokens + cost > MAX_ANALYSIS_TOKENS:
            continue
        selected_files.append({**file, "context_score": file.get("priority_score", 0)})
        used_tokens += cost

    return selected_files