import gradio as gr
import uuid


def create_ui(session, chat_agent):

    thread_id = str(uuid.uuid4())

    async def chat(message, history):
        result = await chat_agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ],
                "repo_path": session.repo_path,
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )

        return result["messages"][-1].content

    return gr.ChatInterface(
        fn=chat,
        title="RepoPilot",
        description="Ask questions about the analyzed repository.",
    )