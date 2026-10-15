import sys
from pathlib import Path

# Locate project root
PROJECT_DIR = Path(__file__).resolve().parents[2]

# Make configs package importable
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

print(PROJECT_DIR)
from configs import Settings

WORKSPACE_ROOT= Settings.BACKEND_DIR

import sqlite3
from pathlib import Path

from langchain.tools import tool

# WORKSPACE_ROOT = Path("/content/ai-workspace/workspace").resolve()
DATABASE_PATH = WORKSPACE_ROOT / "database" / "workspace.db"

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def safe_workspace_path(path: str) -> Path:
    """Prevent workspace tools from accessing paths outside the workspace."""
    target = (WORKSPACE_ROOT / path).resolve()

    if not target.is_relative_to(WORKSPACE_ROOT):
        raise ValueError("Access outside the workspace is not allowed.")

    return target


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file inside the workspace. Requires approval."""
    target = safe_workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return f"File written successfully: {target.relative_to(WORKSPACE_ROOT)}"


@tool
def read_data(path: str) -> str:
    """Read a UTF-8 text file from inside the workspace. No approval required."""
    target = safe_workspace_path(path)

    if not target.is_file():
        return f"File not found: {path}"

    return target.read_text(encoding="utf-8")


@tool
def execute_sql(query: str) -> str:
    """Execute SQL against the workspace SQLite database. Requires approval."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(query)

        if cursor.description:
            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchmany(50)

            return str({
                "columns": columns,
                "rows": rows,
            })

        return f"SQL executed successfully. Rows affected: {cursor.rowcount}"
