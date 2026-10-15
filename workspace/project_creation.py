
import sys
from pathlib import Path

# Locate project root
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Make configs package importable
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

print(PROJECT_DIR)
from configs import Settings

WORKSPACE= Settings.BACKEND_DIR

# ROOT = Path("/content/ai-workspace")
# WORKSPACE = ROOT / "workspace"

for folder in [
    WORKSPACE / "agents",
    WORKSPACE / "tools",
    WORKSPACE / "prompts",
    WORKSPACE / "utils",
    WORKSPACE / "database",
    WORKSPACE / "api",
    WORKSPACE / "rag",
    WORKSPACE / "tests/unit/hitl",
    WORKSPACE / "tests/integration",

]:
    folder.mkdir(parents=True, exist_ok=True)

for path in [
    WORKSPACE / "__init__.py",
    WORKSPACE / "agents" / "__init__.py",
    WORKSPACE / "tools" / "__init__.py",
    WORKSPACE / "utils" / "__init__.py",
    WORKSPACE / "database" / "__init__.py",
    WORKSPACE / "api" / "__init__.py",
    WORKSPACE / "rag" / "__init__.py",
    WORKSPACE / "prompts" / "__init__.py",
    WORKSPACE / "api" / "main.py",
    WORKSPACE / 'requirements.txt'
]:
    path.touch(exist_ok=True)


print("Workspace engine directories created.")
