
from pprint import pprint
from langgraph.types import Command
from configs import Settings
from workspace.agents.engine import agent

WORKSPACE = Settings.BACKEND_DIR
THREAD_ID = "hitl-engine-test-001"

# Resume the interrupted agent and approve the pending tool call.
approved_result = agent.invoke(
    Command(
        resume={
            "decisions": [
                {"type": "approve"}
            ]
        }
    ),
    config={
        "configurable": {
            "thread_id": THREAD_ID
        }
    },
)

print("Result:")
pprint(approved_result)

target = WORKSPACE / "test_output" / "hello.txt"

print("\nFile exists:", target.exists())

if target.exists():
    print("File content:", target.read_text(encoding="utf-8"))
