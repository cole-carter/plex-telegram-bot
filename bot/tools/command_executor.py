"""Safe command execution with security constraints."""

import subprocess
import shlex
from pathlib import Path
from typing import Dict, Any

# Allowed commands (whitelist)
ALLOWED_COMMANDS = [
    "api-call",
    "recycle-bin",
    "ls",
    "find",
    "mv",
    "cp",
    "mkdir",
    "cat",
    "grep",
    "head",
    "tail",
    "file",
    "du",
    "df",
    "stat",
    "dirname",
    "basename",
    "pwd",
    "wc",
    "sort",
    "uniq",
]

# Blocked patterns (blacklist)
BLOCKED_PATTERNS = [
    ".env",  # Never access .env files
    "*.key",  # No key files
    "*.pem",  # No certificate files
    "secrets",  # No secrets files
    "rm ",  # No rm command
    " dd ",  # No disk operations (with spaces to avoid blocking -d flags)
    "mkfs",  # No filesystem formatting
    "chmod 777",  # No insecure permissions
    "curl ",  # No external network calls
    "wget ",  # No external network calls
    "nc ",  # No netcat
    "ssh ",  # No SSH
    "> /dev/",  # No writing to devices
]


def is_command_safe(command: str) -> tuple[bool, str]:
    """
    Check if a command is safe to execute.

    Returns:
        (is_safe, error_message)
    """
    # Check for blocked patterns
    command_lower = command.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in command_lower:
            return False, f"Blocked pattern detected: {pattern}"

    # Extract first word (the command)
    try:
        parts = shlex.split(command)
        if not parts:
            return False, "Empty command"

        first_command = parts[0]

        # Handle paths in command (e.g., ./script or /full/path/to/command)
        command_name = Path(first_command).name

        # Check if command is in whitelist
        if command_name not in ALLOWED_COMMANDS:
            return (
                False,
                f"Command '{command_name}' not allowed. "
                f"Allowed: {', '.join(ALLOWED_COMMANDS)}",
            )

    except ValueError as e:
        return False, f"Invalid command syntax: {e}"

    return True, ""


def execute_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a shell command safely.

    Args:
        command: The command to execute
        timeout: Command timeout in seconds

    Returns:
        dict with keys: success, output, error
    """
    # Check if command is safe
    is_safe, error_msg = is_command_safe(command)
    if not is_safe:
        return {"success": False, "output": "", "error": f"Security violation: {error_msg}"}

    try:
        # Add scripts directory to PATH so api-call and recycle-bin are available
        from bot.config import SCRIPTS_DIR

        env = {"PATH": f"{SCRIPTS_DIR}:/usr/local/bin:/usr/bin:/bin"}

        # Copy over necessary env vars for API authentication
        import os
        for key in [
            "SONARR_API_KEY", "SONARR_URL",
            "RADARR_API_KEY", "RADARR_URL",
            "QBITTORRENT_USER", "QBITTORRENT_PASS", "QBITTORRENT_URL",
            "PLEX_TOKEN", "PLEX_URL",
        ]:
            if key in os.environ:
                env[key] = os.environ[key]

        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

        # Return result
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else "",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Command timed out after {timeout} seconds",
        }

    except Exception as e:
        return {"success": False, "output": "", "error": f"Execution error: {str(e)}"}
