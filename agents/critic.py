from core.state import CriticAnalysis
from core.llm import llm

#kodu görmüyor şimdilik v1
async def analyze_critique(specialist_findings: list):
    critic_agent_llm = llm.with_structured_output(
        CriticAnalysis
    )

    prompt = f"""
You are a strict senior code review critic.

Your job is to evaluate the findings produced by specialist code review agents.

Specialist findings:
{specialist_findings}

Evaluate whether the specialist analysis is sufficiently accurate, relevant, clear, technically reasonable, and actionable.

Check that:
- Findings describe meaningful problems.
- Findings are technically reasonable.
- Severity levels are appropriate.
- Descriptions clearly explain the problems.
- Suggestions provide useful and concrete remediation.
- There are no obvious contradictions or low-quality findings.

Your output must include:

approved:
- Set to true if the specialist analysis is good enough to be included in the final report.
- Set to false only if one or more specialist analyses have significant quality problems that justify another analysis pass.

feedback:
- Explain your overall evaluation.
- If approved is false, clearly explain what is insufficient and what should be improved.
- Make the feedback useful for the specialist agents that will run again.

retry_routes:
- Select only the specialist routes whose analysis needs to be repeated.
- Allowed values are: security, bug, quality.
- Do not include specialists whose findings are already sufficient.
- If approved is true, retry_routes must be empty.
- If approved is false, retry_routes must contain at least one route.

Examples:

If only the security analysis is insufficient:
approved = false
retry_routes = ["security"]

If bug and quality analyses need improvement:
approved = false
retry_routes = ["bug", "quality"]

If all specialist findings are sufficient:
approved = true
retry_routes = []

Do not perform a new code review.
Do not invent additional vulnerabilities, bugs, or quality issues.
Do not rewrite the specialist findings.
Evaluate only the quality of the provided specialist findings.
    """
    return await critic_agent_llm.ainvoke(prompt)
