"""Documentation management for agent self-updating."""

from pathlib import Path
from typing import Dict, Any, List


# Top-level files the agent can read/write
_READABLE_TOP_LEVEL = ["MEMORY.md", "REFERENCE.md", "TASKS.md", "SOUL.md"]
_WRITABLE_TOP_LEVEL = ["MEMORY.md", "TASKS.md", "SOUL.md"]


def _is_valid_doc(file: str, writable: bool = False) -> bool:
    """Check if a file path is a valid agent doc."""
    # Top-level docs
    allowed = _WRITABLE_TOP_LEVEL if writable else _READABLE_TOP_LEVEL
    if file in allowed:
        return True

    # Skill files (readable and writable) — block path traversal
    if file.startswith("skills/") and file.endswith(".md") and ".." not in file:
        return True

    return False


def _resolve_doc_path(file: str) -> Path:
    """Resolve a doc filename to its path in the docs directory."""
    from bot.config import DOCS_DIR

    return DOCS_DIR / file


def list_skills() -> List[Dict]:
    """Scan docs/skills/ and return list of {name, description, filename} for each skill."""
    from bot.config import DOCS_DIR
    skills_dir = DOCS_DIR / "skills"
    if not skills_dir.exists():
        return []

    skills = []
    for skill_file in sorted(skills_dir.glob("*.md")):
        name = ""
        description = ""
        try:
            content = skill_file.read_text()
            for line in content.split("\n")[:5]:
                if line.startswith("<!-- name:"):
                    name = line.replace("<!-- name:", "").replace("-->", "").strip()
                elif line.startswith("<!-- description:"):
                    description = line.replace("<!-- description:", "").replace("-->", "").strip()
        except Exception:
            continue

        if name and description:
            skills.append({
                "name": name,
                "description": description,
                "filename": f"skills/{skill_file.name}",
            })

    return skills


def read_docs(file: str) -> Dict[str, Any]:
    """
    Read an agent documentation file.

    Args:
        file: Name of the docs file (e.g. 'MEMORY.md', 'skills/sonarr.md')

    Returns:
        dict with keys: success, content, error
    """
    if not _is_valid_doc(file, writable=False):
        available = ", ".join(_READABLE_TOP_LEVEL) + ", skills/<name>.md"
        return {
            "success": False,
            "content": "",
            "error": f"Cannot read '{file}'. Available: {available}",
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
        file: Name of the docs file (e.g. 'MEMORY.md', 'skills/sonarr.md')
        content: Content to write
        mode: 'append' or 'replace'

    Returns:
        dict with keys: success, message, error
    """
    if not _is_valid_doc(file, writable=True):
        available = ", ".join(_WRITABLE_TOP_LEVEL) + ", skills/<name>.md"
        return {
            "success": False,
            "message": "",
            "error": f"Cannot write to '{file}'. Writable: {available}",
        }

    if mode not in ["append", "replace"]:
        return {
            "success": False,
            "message": "",
            "error": f"Invalid mode '{mode}'. Use 'append' or 'replace'",
        }

    try:
        file_path = _resolve_doc_path(file)

        # Ensure parent directory exists (for skills/)
        file_path.parent.mkdir(parents=True, exist_ok=True)

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
    return _READABLE_TOP_LEVEL
