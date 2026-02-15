# Plex Telegram Bot — Development Guide

This file contains instructions for Claude Code (the development assistant) when working on this project.

## Project Overview

This is an AI-powered Telegram bot that manages a home Plex media server. It uses Claude (via Anthropic API) to provide natural language control over Sonarr, Radarr, qBittorrent, and Plex.

## Architecture

- **Agentic design**: Bot agent has CLI access, not rigid function wrappers
- **CLI-first**: Generic `api-call` wrapper for all service APIs
- **Self-documenting**: Agent can update its own docs in `docs/`
- **Secure**: Command whitelist, .env blocking, safe deletion
- **Turn limit**: 12 turns per message (configurable in bot/agent.py)
- **Extended thinking**: Agent uses reasoning tokens to plan before executing
- **Memory architecture**:
  - `MEMORY.md` - Permanent facts (Docker setup, paths, workflows)
  - `TASKS.md` - Active task state (ephemeral, resumable across turn limits)
  - `LEARNINGS.md` - Agent learnings from experiences
  - `API_REFERENCE.md` - API behavior documentation
- **Progress tracking**: Real-time updates as agent executes (implemented)

## Key Files

### Core Bot Files
- `AGENT.md` — Instructions for the bot agent (loaded at runtime)
- `SOUL.md` — Agent personality (optional, for future use)
- `bot/main.py` — Telegram bot entry point (progress tracking, conversation history)
- `bot/agent.py` — Claude API integration (turn limit: 12)
- `bot/config.py` — Configuration management
- `bot/tools/docs_manager.py` — Agent documentation management tool

### Runtime Documentation (Modified by Bot)
- `docs/MEMORY.md` — Permanent system knowledge (Docker, paths, workflows) ⚠️ In .gitignore
- `docs/LEARNINGS.md` — Agent learnings from experiences ⚠️ In .gitignore
- `docs/API_REFERENCE.md` — API behavior and quirks
- `docs/TASKS.md` — Active task state (ephemeral, resumable) ⚠️ In .gitignore

### CLI Tools
- `scripts/api-call` — Generic API wrapper CLI (qbt, sonarr, radarr, plex)
- `scripts/recycle-bin` — Safe file deletion

## Development Workflow

1. Make changes locally in WSL
2. Test locally: `python -m bot.main`
3. Commit and push to GitHub
4. **IMPORTANT**: After every push, provide the user with server update commands (see below)

### After Every Push - Provide These Commands

**ALWAYS** provide these commands to the user after pushing updates:

```bash
# SSH to server (if not already connected)
ssh mermanarchy@192.168.1.14
```

```bash
# Pull updates and restart bot
cd ~/plex-telegram-bot && git pull && sudo systemctl restart plex-bot
```

```bash
# Verify it's running
sudo systemctl status plex-bot
```

## Important Rules

- **Never read .env** — contains secrets, must never be accessed
- Keep AGENT.md focused on bot operations, not development
- Test locally before deploying to server
- File operations won't work locally (need server paths)
- **Runtime docs are in .gitignore**: `docs/MEMORY.md`, `docs/LEARNINGS.md`, `docs/TASKS.md`
  - These files are modified by the bot on the server
  - `git pull` won't overwrite them (protected by .gitignore)
  - Don't commit these files - they're server-specific runtime state

## Docker Architecture

The media server runs in Docker containers defined in `~/arr-stack/docker-compose.yml`:
- **qBittorrent**: Downloads to `/home/mermanarchy/downloads` (system disk)
- **Sonarr/Radarr**: Move completed files to `/mnt/storage/{TV Shows,Movies}` (big storage)
- **Gluetun**: VPN for qBittorrent
- **Prowlarr**: Indexer manager

**Critical detail**: The bot's `docs/MEMORY.md` contains comprehensive Docker architecture documentation including:
- Container path mappings (container paths vs host paths)
- File workflow (download → import → organize)
- Storage locations and capacity

**The bot needs this context** to understand where files are and how they move through the system.

## Deployment

Server: Dell Inspiron 537s at 192.168.1.14
Method: Systemd service (see `systemd/plex-bot.service`)

## Debugging Workflow

When the bot has issues or needs debugging:

### Option 1: User as Bridge (Recommended)
1. SSH to server: `ssh mermanarchy@192.168.1.14`
2. Check systemd logs (full output): `sudo journalctl -u plex-bot -n 200 --no-pager`
3. Or check file logs: `cat ~/plex-telegram-bot/logs/bot.log`
4. Copy/paste relevant log output to Claude Code
5. Claude Code diagnoses and suggests fixes
6. Make fixes locally in WSL (`/home/merman/plex_bot`)
7. Commit and push to GitHub
8. Pull on server: `cd ~/plex-telegram-bot && git pull`
9. Restart service: `sudo systemctl restart plex-bot`
10. Verify: `sudo systemctl status plex-bot`

### Option 2: Claude Code SSH Access (Future)
If debugging becomes frequent, set up SSH keys for direct access.

### Useful Commands
- View live logs: `sudo journalctl -u plex-bot -f`
- Last 200 lines (no truncation): `sudo journalctl -u plex-bot -n 200 --no-pager`
- File logs: `~/plex-telegram-bot/logs/bot.log`
- Service status: `sudo systemctl status plex-bot`
- Restart service: `sudo systemctl restart plex-bot`

## Current Features

### Progress Tracking Messages ✅ Implemented
The bot shows real-time progress as the agent executes tools:
```
Working on your request...
✓ Searched Radarr for "Star Wars"
✓ Checked root folders
⏳ Getting quality profiles...
```

**Implementation**: `bot/main.py` lines 210-237 (progress_callback function)

**Known issue**: Progress updates appear at the end instead of in real-time due to `loop.create_task()` scheduling async edits without awaiting them. All edits queue up and fire when the event loop processes tasks at the end.

### Memory & Task Management ✅ Implemented
- **Conversation history**: Last 10 exchanges (20 messages), 8000 chars per message
- **Task state**: Persisted in TASKS.md for resuming across turn limits
- **Permanent memory**: System facts in MEMORY.md (Docker, paths, workflows)
- **Turn budget**: 12 turns per message with explicit budget management

## Future Improvements

### Scheduled Check-ins
Proactive status updates at 8 AM, 12 PM, 4 PM, and 8 PM Central Time.

**Implementation ideas:**
- Use asyncio scheduled tasks in bot/main.py
- Check qBittorrent, Radarr, Sonarr for status
- Only send message if there's something interesting:
  - Downloads completed (ready to organize)
  - Active downloads with progress
  - Disk space warnings
  - Failed downloads

**Example message:**
```
🕐 4 PM Check-in:
✅ Star Wars: Complete (ready to organize)
⏳ Breaking Bad S05E12: 67% downloaded
📊 2 active torrents, 150 GB free
```

### Fix Progress Tracking Real-time Updates
Currently progress updates appear at the end. Need to await edits or use different approach for true real-time updates.
