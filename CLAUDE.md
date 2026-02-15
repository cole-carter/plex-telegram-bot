# Blackbeard — Development Guide

Instructions for Claude Code (the development assistant) when working on this project.

## Project Overview

AI-powered Telegram bot ("Blackbeard") that manages a home Plex media server. Uses Claude (Anthropic API) for natural language control of Sonarr, Radarr, qBittorrent, and Plex.

## Architecture

- **Agentic design**: Bot agent has CLI access via `execute_command`, not rigid function wrappers
- **Orchestrator/Executor**: Sonnet orchestrates, Haiku summarizes command outputs
- **Self-documenting**: Agent reads `REFERENCE.md`, writes to `MEMORY.md` and `TASKS.md`
- **Turn limit**: 12 turns per message with turn counter injection and save-state trigger at turn 10
- **Tool history**: Agent's tool calls and results are embedded in conversation history for procedural memory

## Key Files

### Core
- `AGENT.md` — System prompt for bot agent (loaded at runtime)
- `SOUL.md` — Agent personality (appended to system prompt)
- `bot/main.py` — Telegram bot entry point (progress tracking, conversation history)
- `bot/agent.py` — Claude API integration (tool definitions, turn loop)
- `bot/config.py` — Configuration management
- `bot/tools/command_executor.py` — Safe command execution with whitelist
- `bot/tools/docs_manager.py` — Agent doc read/write management
- `bot/tools/executor.py` — Haiku-powered output processing

### Documentation

| File | Tracked | Owner | Purpose |
|------|---------|-------|---------|
| `AGENT.md` | git | Developer | System prompt — behavioral rules, tools, workflows |
| `SOUL.md` | git | Developer | Personality and tone |
| `docs/REFERENCE.md` | git | Developer | API docs, Docker architecture, storage details |
| `docs/MEMORY.md` | .gitignore | Agent | Discovered knowledge, user preferences |
| `docs/TASKS.md` | .gitignore | Agent | Active task state (ephemeral) |

### Scripts
- `scripts/api-call` — Generic API wrapper (qbt, sonarr, radarr, plex)
- `scripts/recycle-bin` — Safe file deletion

## Development Workflow

1. Make changes locally in WSL (`/home/merman/blackbeard/`)
2. Test locally: `python -m bot.main`
3. Commit and push to GitHub
4. **After every push**, provide the user with server update commands:

```bash
# On server (ssh mermanarchy@192.168.1.14)
cd ~/blackbeard && git pull && sudo systemctl restart blackbeard
```

```bash
# Verify
sudo systemctl status blackbeard
```

## Important Rules

- **Never read .env** — contains secrets
- Keep AGENT.md focused on agent behavior, not development
- `docs/MEMORY.md` and `docs/TASKS.md` are in .gitignore — they're agent runtime state on the server, not development artifacts
- `docs/REFERENCE.md` IS git-tracked — agent can read it but not write to it

## Debugging

1. SSH to server: `ssh mermanarchy@192.168.1.14`
2. Check logs: `sudo journalctl -u blackbeard -n 200 --no-pager`
3. File logs: `cat ~/blackbeard/logs/bot.log`
4. Copy relevant output to Claude Code for diagnosis
5. Fix locally, commit, push, pull on server, restart

## Server

- **Host:** Dell Inspiron 537s at 192.168.1.14
- **OS:** Ubuntu 24.04
- **Service:** systemd (`blackbeard.service`)
- **Docker stack:** `~/arr-stack/docker-compose.yml` (qBittorrent, Sonarr, Radarr, Prowlarr behind Gluetun VPN)
- **Storage:** MergerFS pool at `/mnt/storage/` (1TB SSD + 2TB HDD)
