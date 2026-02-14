"""Documentation management for agent self-updating."""

from pathlib import Path
from typing import Dict, Any, List

# Files the agent can read and write
AGENT_WRITABLE_DOCS = ["MEMORY.md", "LEARNINGS.md", "API_REFERENCE.md"]


def read_docs(file: str) -> Dict[str, Any]:
    """
    Read an agent documentation file.

    Args:
        file: Name of the docs file (MEMORY.md, LEARNINGS.md, or API_REFERENCE.md)

    Returns:
        dict with keys: success, content, error
    """
    if file not in AGENT_WRITABLE_DOCS:
        return {
            "success": False,
            "content": "",
            "error": f"Cannot read '{file}'. Allowed files: {', '.join(AGENT_WRITABLE_DOCS)}",
        }

    try:
        from bot.config import DOCS_DIR

        file_path = DOCS_DIR / file

        if not file_path.exists():
            return {
                "success": False,
                "content": "",
                "error": f"File does not exist: {file}",
            }

        content = file_path.read_text()
        return {"success": True, "content": content, "error": ""}

    except Exception as e:
        return {"success": False, "content": "", "error": f"Error reading file: {str(e)}"}


def update_docs(file: str, content: str, mode: str = "append") -> Dict[str, Any]:
    """
    Update an agent documentation file.

    Args:
        file: Name of the docs file
        content: Content to write
        mode: 'append' or 'replace'

    Returns:
        dict with keys: success, message, error
    """
    if file not in AGENT_WRITABLE_DOCS:
        return {
            "success": False,
            "message": "",
            "error": f"Cannot write to '{file}'. Allowed files: {', '.join(AGENT_WRITABLE_DOCS)}",
        }

    if mode not in ["append", "replace"]:
        return {
            "success": False,
            "message": "",
            "error": f"Invalid mode '{mode}'. Use 'append' or 'replace'",
        }

    try:
        from bot.config import DOCS_DIR

        file_path = DOCS_DIR / file

        if mode == "append":
            # Append to existing content
            existing = file_path.read_text() if file_path.exists() else ""
            new_content = existing + "\n\n" + content
        else:
            # Replace entire file
            new_content = content

        file_path.write_text(new_content)

        return {
            "success": True,
            "message": f"Updated {file} ({mode} mode)",
            "error": "",
        }

    except Exception as e:
        return {
            "success": False,
            "message": "",
            "error": f"Error writing file: {str(e)}",
        }


def list_available_docs() -> List[str]:
    """Return list of docs files the agent can access."""
    return AGENT_WRITABLE_DOCS
