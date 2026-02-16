"""Documentation management for agent self-updating."""

from pathlib import Path
from typing import Dict, Any, List

# Files the agent can read
AGENT_READABLE_DOCS = ["MEMORY.md", "REFERENCE.md", "TASKS.md", "SOUL.md"]

# Files the agent can write (REFERENCE.md is read-only, developer-maintained)
AGENT_WRITABLE_DOCS = ["MEMORY.md", "TASKS.md", "SOUL.md"]

def _resolve_doc_path(file: str) -> Path:
    """Resolve a doc filename to its path in the docs directory."""
    from bot.config import DOCS_DIR

    return DOCS_DIR / file


def read_docs(file: str) -> Dict[str, Any]:
    """
    Read an agent documentation file.

    Args:
        file: Name of the docs file (MEMORY.md, REFERENCE.md, or TASKS.md)

    Returns:
        dict with keys: success, content, error
    """
    if file not in AGENT_READABLE_DOCS:
        return {
            "success": False,
            "content": "",
            "error": f"Cannot read '{file}'. Available files: {', '.join(AGENT_READABLE_DOCS)}",
        }

    try:
        file_path = _resolve_doc_path(file)

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
            "error": f"Cannot write to '{file}'. Writable files: {', '.join(AGENT_WRITABLE_DOCS)}",
        }

    if mode not in ["append", "replace"]:
        return {
            "success": False,
            "message": "",
            "error": f"Invalid mode '{mode}'. Use 'append' or 'replace'",
        }

    try:
        file_path = _resolve_doc_path(file)

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
    """Return list of docs files the agent can read."""
    return AGENT_READABLE_DOCS
