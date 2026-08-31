from core.state import CodeAnalysis
from core.llm import llm

def analyze_code(
    file: dict,
    exploration_summary: str
):
    structured_llm = llm.with_structured_output(CodeAnalysis)

    prompt = f"""
You are a professional code reviewer.

You are analyzing one file from a larger software repository.

Repository context:
{exploration_summary}

File:
{file["path"]}

Language:
{file["language"]}

Code:
{file["content"]}

Analyze this file while considering the repository context above.

Identify meaningful issues.

Possible categories:
- bug
- security
- quality
- improvement

Severity must be one of:
- low
- medium
- high
- critical

Do not invent issues.
Only report problems that are actually relevant.

Use the repository context to better understand the role of this file,
but base findings on the actual source code.
"""

    try:
        result = structured_llm.invoke(prompt)
        return result

    except Exception as error:
        print(f"Analysis failed for {file['path']}: {error}")
        return None