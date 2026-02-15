# Blackbeard 🏴‍☠️

AI-powered Telegram bot that manages a home Plex media server through natural language. Uses Claude AI to control Sonarr (TV), Radarr (Movies), qBittorrent (downloads), and Plex (library).

## Architecture

```
User (Telegram) → Blackbeard (Orchestrator/Sonnet 4.5)
                      → execute_command → Executor (Haiku 4.5) → summarized result
                      → read_docs / update_docs → MEMORY.md, TASKS.md
```

### Design Principles

- **Agentic-first**: Agent has CLI access via `api-call` wrapper, not rigid function wrappers
- **Orchestrator/Executor**: Sonnet plans and acts, Haiku summarizes command output
- **Self-documenting**: Agent reads REFERENCE.md, writes to MEMORY.md and TASKS.md
- **Rules-first prompt**: 3 mandatory rules at top of system prompt (always execute, always fetch fresh, always verify)
- **Procedural memory**: Tool calls and results embedded in conversation history

## Project Structure

```
blackbeard/
├── AGENT.md                    # System prompt (loaded at runtime)
├── SOUL.md                     # Agent personality
├── CLAUDE.md                   # Dev assistant instructions (gitignored)
├── bot/
│   ├── main.py                 # Telegram entry point
│   ├── agent.py                # Claude API integration (BlackbeardAgent)
│   ├── config.py               # Configuration
│   └── tools/
│       ├── command_executor.py  # Safe command execution (whitelist)
│       ├── docs_manager.py      # Agent doc read/write
│       └── executor.py          # Haiku output processing
├── docs/
│   ├── REFERENCE.md             # API docs + system architecture (git-tracked, read-only)
│   ├── MEMORY.md                # Agent's discovered knowledge (gitignored)
│   └── TASKS.md                 # Active task state (gitignored)
├── scripts/
│   ├── api-call                 # Generic API wrapper (sonarr, radarr, qbt, plex)
│   └── recycle-bin              # Safe file deletion
├── systemd/
│   └── blackbeard.service       # Systemd service file
├── requirements.txt
└── .env                         # Secrets (gitignored)
```

## Setup

### Prerequisites

- Python 3.10+
- Telegram bot token (via @BotFather)
- Anthropic API key
- Running instances of Sonarr, Radarr, qBittorrent, Plex

### Install

```bash
git clone https://github.com/cole-carter/Blackbeard.git
cd blackbeard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x scripts/api-call scripts/recycle-bin
cp .env.example .env  # Edit with your keys
python -m bot.main
```

### Deploy (Systemd)

```bash
sudo cp systemd/blackbeard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blackbeard
sudo systemctl start blackbeard
```

### Update

```bash
cd ~/blackbeard && git pull && sudo systemctl restart blackbeard
```

## Usage

Just chat naturally:

- "Get me Breaking Bad season 5"
- "What's downloading?"
- "Do I have The Office?"
- "Check disk space"
- Send a magnet link and tell it what it is

## Security

- Bot only responds to allowlisted Telegram user IDs
- Command whitelist (only approved commands execute)
- `.env` and secret files blocked from agent access
- `rm` blocked — uses `recycle-bin` instead
- No network tools (`curl`, `wget`) — uses `api-call` wrapper

## Acknowledgments

- [Claude AI](https://anthropic.com) by Anthropic
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Inspired by [OpenClaw](https://docs.openclaw.ai/)
