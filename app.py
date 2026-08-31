import warnings
warnings.filterwarnings("ignore")
from ui import create_ui
import asyncio
from core.session import create_repo_session
from services.repository import cleanup_repository
from workflow.graph import graph
from dotenv import load_dotenv
from agents.chat_agent import create_chat_agent

load_dotenv()


async def main():

    initial_state = {
        "repo_path": "https://github.com/Alsoren/SENG272-HW1",
        "is_temporary_repo": False,

        "files": [],
        "analyses": [],

        "exploration_summary": "",
        "prioritized_files": [],
        "important_files": [],

        "analysis_files": [],
        "routes": [],
        "specialist_findings": [],
        "critic_analysis": [],
        "retry_count": 0,
        "report": "",
    }

    result = None

    try:
        result = await graph.ainvoke(initial_state)

        print(
            "Detected routes:",
            result["routes"]
        )

        with open(
            "report.md",
            "w",
            encoding="utf-8"
        ) as report_file:
            report_file.write(
                result["report"]
            )

        print("\nRepoPilot analysis completed.")
        print("Report saved to report.md")

        session = create_repo_session(result)
        chat_agent = create_chat_agent(session)
        demo = create_ui(
            session=session,
            chat_agent=chat_agent,
        )

        demo.launch()

    finally:
        if result is not None:
            cleanup_repository(
                result["repo_path"],
                result.get(
                    "is_temporary_repo",
                    False
                )
            )


if __name__ == "__main__":
    asyncio.run(main())