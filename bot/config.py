"""Configuration management for Blackbeard."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
AGENT_MD_PATH = PROJECT_ROOT / "AGENT.md"
SOUL_MD_PATH = PROJECT_ROOT / "docs" / "SOUL.md"
MEMORY_MD_PATH = PROJECT_ROOT / "docs" / "MEMORY.md"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("TELEGRAM_USER_ID", "").split(",")
    if uid.strip()
]

# Anthropic API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# AI Models (role-based configuration)
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "claude-sonnet-4-5-20250929")
EXECUTOR_MODEL = os.getenv("EXECUTOR_MODEL", "claude-haiku-4-5-20251001")

# Token limits for executor
MAX_EXECUTOR_INPUT_TOKENS = int(os.getenv("MAX_EXECUTOR_INPUT_TOKENS", "50000"))
MAX_EXECUTOR_OUTPUT_TOKENS = int(os.getenv("MAX_EXECUTOR_OUTPUT_TOKENS", "4000"))

# Service URLs (for reference, actual API calls use api-call script)
SONARR_URL = os.getenv("SONARR_URL", "http://192.168.1.14:8989")
RADARR_URL = os.getenv("RADARR_URL", "http://192.168.1.14:7878")
QBITTORRENT_URL = os.getenv("QBITTORRENT_URL", "http://192.168.1.14:8080")
PLEX_URL = os.getenv("PLEX_URL", "http://192.168.1.14:32400")

# File paths
MEDIA_ROOT = Path("/mnt/storage")
DOWNLOADS_DIR = Path("/home/mermanarchy/downloads")
RECYCLE_BIN = Path("/home/mermanarchy/recycle-bin")


def validate_config():
    """Validate that required configuration is present."""
    errors = []

    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN not set")

    if not ALLOWED_USER_IDS:
        errors.append("TELEGRAM_USER_ID not set")

    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not set")

    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file")
        return False

    return True
