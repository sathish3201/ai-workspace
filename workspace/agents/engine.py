
import os

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from workspace.tools.workspace_tools import (
    write_file,
    execute_sql,
    read_data,
)
from workspace.prompts.system import SYSTEM_PROMPT


# Keep one checkpointer and one agent instance for the session.
checkpointer = InMemorySaver()

model = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0,
)

agent = create_agent(
    model=model,
    tools=[
        write_file,
        execute_sql,
        read_data,
    ],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "write_file": True,
                "execute_sql": {
                    "allowed_decisions": ["approve", "reject"],
                },
                "read_data": False,
            },
            description_prefix="Tool execution pending approval",
        ),
    ],
    checkpointer=checkpointer,
)


def run_agent(message: str, thread_id: str = "colab-session"):
    """Start or continue an agent conversation."""
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    return agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )


def resume_agent(thread_id: str, decisions: list[dict]):
    """Resume the interrupted agent using human decisions."""
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    return agent.invoke(
        {"decisions": decisions},
        config=config,
    )
