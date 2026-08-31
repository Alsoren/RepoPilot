from core.state import SpecialistAnalysis
from core.llm import llm

async def analyze_security(state: dict):
    previous_findings = state.get(
        "previous_findings",
        []
    )

    critic_feedback = state.get(
        "critic_feedback",
        ""
    )

    specialist_llm = llm.with_structured_output(
        SpecialistAnalysis
    )

    prompt = f"""
You are a security-focused code reviewer.

Repository context:
{state.get("exploration_summary", "")}

Review the repository analysis below.

Analyses:
{state["analyses"]}

Previous security findings:
{previous_findings}

Critic feedback:
{critic_feedback}

Identify only meaningful security issues and vulnerabilities.

If previous findings and critic feedback are provided,
improve the previous security analysis based on the critic feedback.

If they are empty, perform the initial security analysis normally.

Use the repository context to understand the role of files,
important components, entry points, and relationships between files.

However, do not treat the repository context itself as proof of a vulnerability.
Base security findings on the available code analysis evidence.

Focus on issues such as:
- insecure memory handling
- injection risks
- unsafe input handling
- authentication or authorization problems
- insecure cryptographic practices
- sensitive data exposure
- other meaningful security vulnerabilities

For every finding:
- agent must be "security"
- severity must be low, medium, high, or critical
- provide a concise title
- clearly explain the security risk
- provide a concrete remediation suggestion

Do not report non-security issues.
Do not invent vulnerabilities.
Do not repeat weak or irrelevant findings just to produce output.
"""

    return await specialist_llm.ainvoke(prompt)


async def analyze_bugs(state: dict):
    previous_findings = state.get(
        "previous_findings",
        []
    )

    critic_feedback = state.get(
        "critic_feedback",
        ""
    )

    specialist_llm = llm.with_structured_output(
        SpecialistAnalysis
    )

    prompt = f"""
You are a bug-focused code reviewer.

Repository context:
{state.get("exploration_summary", "")}

Review the repository analysis below.

Analyses:
{state["analyses"]}

Previous bug findings:
{previous_findings}

Critic feedback:
{critic_feedback}

Identify only meaningful bugs, incorrect logic,
runtime risks, and functional defects.

If previous findings and critic feedback are provided,
improve the previous analysis based on the critic feedback.

If they are empty, perform the initial bug analysis normally.

Use the repository context to understand the role of files,
important components, entry points, and relationships between files.

However, do not treat the repository context itself as proof of a bug.
Base bug findings on the available code analysis evidence.

For every finding:
- agent must be "bug"
- severity must be low, medium, high, or critical
- provide a concise title
- explain the issue
- provide a concrete suggestion

Do not report unrelated issues.
Do not invent bugs.
Do not repeat weak or irrelevant findings just to produce output.
"""

    return await specialist_llm.ainvoke(prompt)


async def analyze_quality(state: dict):
    previous_findings = state.get(
        "previous_findings",
        []
    )

    critic_feedback = state.get(
        "critic_feedback",
        ""
    )

    specialist_llm = llm.with_structured_output(
        SpecialistAnalysis
    )

    prompt = f"""
You are a code quality reviewer.

Repository context:
{state.get("exploration_summary", "")}

Review the repository analysis below.

Analyses:
{state["analyses"]}

Previous quality findings:
{previous_findings}

Critic feedback:
{critic_feedback}

Identify meaningful maintainability, readability,
duplication, design, and code quality problems.

If previous findings and critic feedback are provided,
improve the previous quality analysis based on the critic feedback.

If they are empty, perform the initial quality analysis normally.

Use the repository context to understand the role of files,
important components, entry points, responsibilities,
and relationships between files.

However, do not treat the repository context itself as proof of a
code quality problem. Base findings on the available code analysis evidence.

Focus on issues such as:
- poor readability
- unnecessary complexity
- duplicated logic
- weak code structure
- maintainability problems
- unclear naming or responsibilities
- design issues that make the code harder to modify or understand

For every finding:
- agent must be "quality"
- severity must be low, medium, high, or critical
- provide a concise title
- clearly explain why the issue affects code quality
- provide a concrete improvement suggestion

Do not report unrelated bugs or security vulnerabilities.
Do not invent problems.
Do not repeat weak or cosmetic findings just to produce output.
"""

    return await specialist_llm.ainvoke(prompt)