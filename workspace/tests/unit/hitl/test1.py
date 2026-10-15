from configs import Settings
WORKSPACE = Settings.BACKEND_DIR

from workspace.agents.engine import run_agent
THREAD_ID = "hitl-engine-test-001"
if (WORKSPACE / "test_output" / "hello.txt").exists():
    (WORKSPACE / "test_output" / "hello.txt").unlink()
result = run_agent(
    message=(
        "Use the write_file tool to create "
        "test_output/hello.txt with the exact content "
        "Hello from the HITL engine. "
        "Do not claim it was created unless the tool runs."
    ),
    thread_id=THREAD_ID,
)

print("Interrupts:", result.get("__interrupt__", []))
print("File exists before approval:",
      (WORKSPACE / "test_output" / "hello.txt").exists())
