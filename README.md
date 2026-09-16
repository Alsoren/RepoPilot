# RepoPilot

**RepoPilot** is an agentic AI-powered repository analysis and code review system built with **Python, LangGraph, LangChain, and Google Gemini**.

Instead of sending an entire repository directly to an LLM, RepoPilot first explores and prioritizes the codebase, selects relevant context under a controlled analysis budget, and routes detected issues to specialized review agents.

A critic agent evaluates the specialist results and selectively retries only the analyses that need improvement. After the analysis is complete, users can interact with the repository through a repo-aware conversational assistant.

---

## Why RepoPilot?

Large repositories introduce several challenges for LLM-based code analysis:

- Sending the entire repository to an LLM is expensive and often exceeds context limits.
- Not every file is equally important.
- A single general-purpose reviewer may perform poorly across different issue categories.
- LLM-generated findings may be vague, inconsistent, or incomplete.
- Repository questions often require inspecting the actual source code rather than relying only on an initial report.

RepoPilot addresses these problems with a structured **multi-agent analysis pipeline**, deterministic context management, repository tools, and a critic-based feedback loop.

---

## Architecture

```text
Repository
    │
    ▼
Repository Preparation
    │
    ▼
Scanner
    │
    ▼
File Prioritizer
    │
    ▼
Explorer Agent
    │
    │  Repository Tools
    │  ├── list_files
    │  ├── read_file
    │  ├── search_code
    │  └── find_references
    │
    ▼
Context Selector
    │
    ▼
Analyzer
    │
    ▼
Router
    │
    ├─────────────┬─────────────┐
    ▼             ▼             ▼
Security Agent   Bug Agent   Quality Agent
    │             │             │
    └─────────────┴─────────────┘
                  │
                  ▼
              Critic Agent
                  │
            ┌─────┴─────┐
            │           │
         Approved     Retry
            │           │
            │     Selected Specialist
            │           │
            │       Critic Again
            │
            ▼
        Report Generator
            │
            ▼
        Repo Session
            │
            ▼
       Repo-Aware Chat
            │
            ▼
         Gradio UI
```

---

## Core Features

### Repository Exploration

RepoPilot uses an Explorer Agent to inspect the repository before deep analysis.

The Explorer can interact with the repository through tools such as:

- `list_files`
- `read_file`
- `search_code`
- `find_references`

This allows the model to inspect the real repository instead of relying only on a pre-generated prompt.

---

### File Prioritization

Before expensive LLM analysis begins, RepoPilot assigns structural priority scores to repository files.

The prioritizer considers signals such as:

- Entry points
- Configuration files
- Important directories
- Code structure
- Functions and classes
- Imports
- File size
- Low-priority/generated directories

These scores act as navigation hints for repository exploration.

---

### Context-Aware File Selection

RepoPilot does not blindly send every source file to the Analyzer.

The **Context Selector** combines structural priority with information discovered during repository exploration and operates under a controlled analysis budget.

Conceptually:

```text
Repository Files
      │
      ▼
Structural Priority
      │
      ▼
Explorer Evidence
      │
      ▼
Context Selector
      │
      ▼
Selected Analysis Context
```

This reduces unnecessary LLM calls and makes the architecture more suitable for larger repositories.

---

### Multi-Agent Code Review

After the initial analysis, RepoPilot routes findings to specialized agents.

#### Security Agent

Focuses on security-related findings and potential vulnerabilities.

#### Bug Agent

Focuses on:

- Logic errors
- Runtime risks
- Incorrect behavior
- Functional defects

#### Quality Agent

Focuses on:

- Maintainability
- Readability
- Duplication
- Code structure
- Design quality

Only relevant findings are passed to each specialist.

---

### Specialist Filtering

RepoPilot prevents every specialist from receiving unrelated findings.

For example:

```text
Security findings ──► Security Agent
Bug findings      ──► Bug Agent
Quality findings  ──► Quality Agent
```

This keeps specialist context focused and reduces unnecessary token usage.

---

## Critic and Selective Retry

Specialist results are evaluated by a dedicated **Critic Agent**.

The Critic checks whether findings are:

- Technically reasonable
- Relevant
- Clearly explained
- Assigned an appropriate severity
- Actionable

If the results are sufficient:

```text
Specialists
    ↓
Critic
    ↓
Approved
    ↓
Report
```

If one specialist produces insufficient results, RepoPilot does not rerun the entire pipeline.

Instead:

```text
Specialists
    ↓
Critic
    ↓
Bug analysis insufficient
    ↓
Retry Bug Agent only
    ↓
Previous Findings
+
Critic Feedback
    ↓
Improved Bug Analysis
    ↓
Critic
```

A retry limit prevents uncontrolled agent loops.

This creates an **evaluator-feedback loop** while avoiding unnecessary specialist executions.

---

## Repository-Aware Chat

After analysis, RepoPilot starts a conversational session for the analyzed repository.

Users can ask questions such as:

```text
What is the main responsibility of this file?

Where is this function used?

Explain the most important bug.

Show me the code related to this finding.

What happens after this method is called?
```

The assistant receives the analysis results as baseline context but can also inspect the repository through its tools when exact source information is required.

This means the chat assistant is not limited to repeating the generated report.

---

## Conversation Memory

RepoPilot uses LangGraph checkpointing to maintain conversational context.

For example:

```text
User:
Analyze Main.java.

RepoPilot:
Main.java is responsible for ...

User:
Which classes use it?

RepoPilot:
...
```

The second question can be interpreted using the previous conversation without requiring the user to repeat the filename.

Repository analysis state and conversational memory are kept as separate concerns.

---

## Repository Tools

Repository tools operate against the repository on disk.

```text
Agent
  │
  ├── list_files()
  ├── read_file()
  ├── search_code()
  └── find_references()
        │
        ▼
Repository
```

The repository itself remains the source of truth for source-code inspection.

Tool access also includes protections such as path validation, ignored directories, file-size limits, and bounded results.

---

## Analysis Output

RepoPilot generates a Markdown code review report containing findings such as:

```markdown
### Improper Input Validation

**Severity:** High

**Description**

User-controlled input reaches a sensitive operation without sufficient validation.

**Suggestion**

Validate and sanitize the input before using it in the operation.
```

The final report combines the approved specialist findings into a structured output.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| LangGraph | Agent workflow and state orchestration |
| LangChain | Agent and tool integration |
| Google Gemini | LLM reasoning and structured analysis |
| Pydantic | Structured agent outputs |
| Gradio | Interactive repository chat UI |
| Git | Repository operations |

---

## Project Structure

The project is organized around separate workflow, agent, tool, context-management, and application layers.

```text
RepoPilot/
│
├── agents/
│   ├── explorer
│   ├── specialists
│   ├── critic
│   └── chat
│
├── agent_tools/
│   └── repository_tools.py
│
├── context/
│   ├── context_selector.py
│   └── specialist_filter.py
│
├── core/
│   └── llm.py
│
├── services/
│   └── repository preparation / scanning
│
├── app.py
├── graph.py
├── state.py
├── session.py
├── ui.py
├── requirements.txt
└── README.md
```

> The exact directory structure may evolve as RepoPilot continues to be refactored.

---

## Getting Started

### 1. Clone RepoPilot

```bash
git clone https://github.com/<your-username>/RepoPilot.git
cd RepoPilot
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

Do not commit the `.env` file to Git.

### 5. Run RepoPilot

```bash
python app.py
```

RepoPilot will prepare the repository, execute the analysis pipeline, generate the report, and start the repository-aware interface.

---

## Design Principles

RepoPilot is built around several design decisions:

**Selective context over brute-force prompting**

Only relevant repository context should reach expensive analysis stages.

**Tools over hallucinated repository knowledge**

When exact source information is required, agents should inspect the repository.

**Specialization over one general reviewer**

Security, bugs, and code quality have different analysis requirements.

**Selective retry over complete reruns**

Only specialists rejected by the Critic should be executed again.

**Deterministic logic where LLM reasoning is unnecessary**

Context budgeting, specialist filtering, retry limits, and state merging are handled by deterministic application logic.

**Repository state and conversation state are separate**

Repository analysis belongs to the application session, while conversation history belongs to the chat/checkpoint layer.

---

## Current Status

RepoPilot currently includes the core V1 architecture:

- Repository scanning
- File prioritization
- Tool-driven repository exploration
- Context-aware file selection
- Structured code analysis
- Finding-based routing
- Specialized review agents
- Specialist context filtering
- Critic evaluation
- Selective feedback-based retries
- Markdown report generation
- Repository-aware chat
- Conversation memory
- Gradio interface

Further work is focused primarily on testing, evaluation, observability, deployment, and portfolio-level polish rather than expanding the core architecture.

---

## Roadmap

Planned improvements include:

- Automated evaluation repositories
- False-positive / false-negative measurement
- Token and latency metrics
- Agent/tool tracing and observability
- Persistent conversation storage
- Docker containerization
- Public deployment
- Improved web interface
- Larger-repository evaluation

---

## Example Workflow

```text
1. User provides a repository
                ↓
2. RepoPilot scans and prioritizes files
                ↓
3. Explorer investigates repository structure
                ↓
4. Context Selector chooses analysis files
                ↓
5. Analyzer detects potential issues
                ↓
6. Router selects relevant specialists
                ↓
7. Specialists perform focused reviews
                ↓
8. Critic evaluates their findings
                ↓
9. Weak specialist results are selectively retried
                ↓
10. RepoPilot generates the final report
                ↓
11. User continues with repository-aware chat
```

---

## Disclaimer

RepoPilot uses large language models for code analysis. Findings should be treated as engineering assistance rather than guaranteed proof of correctness or security.

For security-critical software, results should be validated through appropriate testing, static analysis, and professional security review.

---

## License

Add the project's license here.
