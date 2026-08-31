from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from pathlib import Path
from core.state import RepoPilotState
from context.file_prioritizer import prioritize_files
from context.context_selector import select_analysis_files
from context.specialist_filter import filter_analyses_for_route, CATEGORY_MAP

from services.repository import (
    scan_repository,
    prepare_repository,
)

from services.analyzer import analyze_code
from services.report import generate_markdown_report

from agents.specialists import (
    analyze_security,
    analyze_bugs,
    analyze_quality,
)

from agents.explorer_agent import explorer_agent
from agents.critic import analyze_critique

MAX_RETRIES = 3

def prepare_repository_node(state: RepoPilotState):
    print("\n[Prepare] Repository path preparing...")

    repo_path, is_temporary = prepare_repository(
        state["repo_path"]
    )

    print(
        f"[Prepare] Repository ready: {repo_path}"
    )

    return {
        "repo_path": repo_path,
        "is_temporary_repo": is_temporary,
    }

def scan_repository_node(state: RepoPilotState):

    print("\n[Scanner] Repository preparing...")

    files = scan_repository(
        state["repo_path"]
    )

    print(
        f"[Scanner] {len(files)} code files found."
    )

    return {
        "files": files
    }

def prioritize_files_node(state: RepoPilotState):
    print("\n[Prioritizer] Ranking repository files...")

    prioritized_files = prioritize_files(
        state["files"]
    )

    print("[Prioritizer] Top priority files:")

    for file in prioritized_files[:10]:
        print(
            f"  {file['priority_score']:>5} "
            f"{file['path']}"
        )

    return {
        "prioritized_files": prioritized_files
    }

async def explorer_node(state: RepoPilotState):
    print("\n[Explorer] Repository exploration started...")

    result = await explorer_agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Explore this repository. "
                        "Identify its structure, important source files, "
                        "entry points, important classes and functions."
                    ),
                }
            ],

            # ASIL AKTARIM BURADA
            "repo_path": state["repo_path"],
            "important_files": [],
            "prioritized_files": state["prioritized_files"],
        }
    )

    explorer_result = result["structured_response"]

    important_files = [
        str(Path(path))
        for path in explorer_result.important_files
    ]

    print("\n[Explorer] Important files:")

    for path in important_files:
        print(f"  - {path}")

    return {
        "exploration_summary": explorer_result.summary,
        "important_files": explorer_result.important_files,
    }

def context_selector_node(state: RepoPilotState):
    print("\n[Context Selector] Selecting files for deep analysis...")

    analysis_files = select_analysis_files(
        prioritized_files=state["prioritized_files"],
        important_files=state["important_files"],
        exploration_summary=state.get("exploration_summary", ""),
    )

    print(
        f"[Context Selector] "
        f"{len(analysis_files)} / {len(state['files'])} files selected."
    )

    print("[Context Selector] Selected files:")

    for file in analysis_files:
        print(f"  - {file['path']}")

    return {
        "analysis_files": analysis_files
    }

def analyze_code_node(state: RepoPilotState):
    print("\n[Analyzer] Code analysis started...")

    analyses = []

    files = state["analysis_files"]

    for index, file in enumerate(files, start=1):

        print(
            f"[Analyzer] [{index}/{len(files)}] "
            f"Analyzing: {file['path']}"
        )

        analysis = analyze_code(
            file,
            state["exploration_summary"]
        )

        if analysis is not None:
            analyses.append(analysis)

    return {
        "analyses": analyses
    }

def router_node(state: RepoPilotState):
    print("\n[Router] Classifying findings...")

    routes = set()

    for analysis in state["analyses"]:
        for finding in analysis.findings:
            category = finding.category.lower().strip()
            for route, allowed in CATEGORY_MAP.items():
                if category in allowed:
                    routes.add(route)

    routes = sorted(routes)
    if not routes:
        routes.append("clean")

    print(f"[Router] Routes detected: {routes}")
    return {"routes": routes}

def route_to_specialists(state: RepoPilotState):
    if state["routes"] == ["clean"]:
        return [Send("report_generator", state)]

    sends = []

    for route in state["routes"]:

        filtered = filter_analyses_for_route(state["analyses"], route)

        print(f"[DEBUG] {route} route → {len(filtered)} dosya, "
              f"{sum(len(a.findings) for a in filtered)} finding gönderiliyor "
              f"(toplam {sum(len(a.findings) for a in state['analyses'])} finding vardı)")

        sends.append(
            Send(
                "specialist_agent",
                {
                    "route": route,
                    "analyses": filter_analyses_for_route(state["analyses"], route),
                    "exploration_summary": state["exploration_summary"],
                    "retry_count": state.get("retry_count", 0),
                },
            )
        )
    return sends

async def specialist_agent_node(state):
    route = state["route"]

    if route == "security":
        print("\n[Security Agent] Security analysis started...")
        result = await analyze_security(state)

    elif route == "bug":
        print("\n[Bug Agent] Bug analysis started...")
        result = await analyze_bugs(state)

    elif route == "quality":
        print("\n[Quality Agent] Quality analysis started...")
        result = await analyze_quality(state)

    else:
        return {
            "specialist_findings": [],
            "retry_count": state.get("retry_count", 0)
        }

    return {
        "specialist_findings": result.findings,
        "retry_count": state.get("retry_count", 0)
    }
    
# fan-in korunur
def critic_gate_node(state: RepoPilotState):
    return {}

def should_run_critic(state: RepoPilotState):

    retry_count = state.get("retry_count", 0)
    if state["retry_count"] >= MAX_RETRIES:
        return "report_generator"

    return "analyze_critique"

async def analyze_critique_node(state: RepoPilotState):

    print("\n[critique Agent] analysis started...")

    print("\n[Critic] Reviewing specialist findings...")

    critique = await analyze_critique(
        state["specialist_findings"]
    )

    update = {
        "critic_analysis": critique
    }

    if not critique.approved:
        update["retry_count"] = state["retry_count"] + 1

    return update

def route_after_critic(state: RepoPilotState):
    critique = state["critic_analysis"]
    if critique.approved:
        return "report_generator"

    sends = []
    for route in critique.retry_routes:
        previous_findings = [
            f for f in state["specialist_findings"] if f.agent == route
        ]
        sends.append(
            Send(
                "specialist_agent",
                {
                    "route": route,
                    "analyses": filter_analyses_for_route(state["analyses"], route),
                    "exploration_summary": state["exploration_summary"],
                    "previous_findings": previous_findings,
                    "critic_feedback": critique.feedback,
                    "retry_count": state["retry_count"],
                },
            )
        )
    return sends

def generate_report_node(state: RepoPilotState):
    print("\n[Report] Generating report...")

    report = generate_markdown_report(
        state["specialist_findings"]
    )

    print("\nSpecialist findings:")

    for finding in state["specialist_findings"]:
        print(
            f"[{finding.agent}] "
            f"[{finding.severity}] "
            f"{finding.title}"
        )

    return {
        "report": report
    }

builder = StateGraph(RepoPilotState)

builder.add_node(
    "prepare_repository",
    prepare_repository_node
)

builder.add_node(
    "scanner",
    scan_repository_node
)

builder.add_node(
    "file_prioritizer",
    prioritize_files_node
)

builder.add_node(
    "explorer",
    explorer_node
)

builder.add_node(
    "context_selector",
    context_selector_node
)

builder.add_node(
    "analyzer",
    analyze_code_node
)

builder.add_node(
    "report_generator",
    generate_report_node
)

builder.add_node(
    "router",
    router_node
)

builder.add_node(
    "critic_gate",
    critic_gate_node
)

builder.add_node(
    "analyze_critique",
    analyze_critique_node
)

builder.add_node(
    "specialist_agent",
    specialist_agent_node
)

builder.add_edge(
    START,
    "prepare_repository"
)

builder.add_edge(
    "prepare_repository",
    "scanner"
)

builder.add_edge(
    "scanner",
    "file_prioritizer"
)

builder.add_edge(
    "file_prioritizer",
    "explorer"
)

builder.add_edge(
    "explorer",
    "context_selector"
)

builder.add_edge(
    "context_selector",
    "analyzer"
)

builder.add_edge(
    "analyzer",
    "router"
)

builder.add_conditional_edges(
    "router",
    route_to_specialists
)

builder.add_edge(
    "specialist_agent",
    "critic_gate"
)

builder.add_conditional_edges(
    "critic_gate",
    should_run_critic
)

builder.add_conditional_edges(
    "analyze_critique",
    route_after_critic
)

builder.add_edge(
    "report_generator",
    END
)

graph = builder.compile()