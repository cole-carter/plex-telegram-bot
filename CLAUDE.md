# Plex Telegram Bot — Development Guide

This file contains instructions for Claude Code (the development assistant) when working on this project.

## Project Overview

This is an AI-powered Telegram bot that manages a home Plex media server. It uses Claude (via Anthropic API) to provide natural language control over Sonarr, Radarr, qBittorrent, and Plex.

## Architecture

- **Agentic design**: Bot agent has CLI access, not rigid function wrappers
- **CLI-first**: Generic `api-call` wrapper for all service APIs
- **Self-documenting**: Agent can update its own docs in `docs/`
- **Secure**: Command whitelist, .env blocking, safe deletion

## Key Files

- `AGENT.md` — Instructions for the bot agent (loaded at runtime)
- `SOUL.md` — Agent personality (optional, for future use)
- `bot/main.py` — Telegram bot entry point
- `bot/agent.py` — Claude API integration
- `bot/config.py` — Configuration management
- `scripts/api-call` — Generic API wrapper CLI
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

# Pull updates and restart bot
cd ~/plex-telegram-bot && git pull && sudo systemctl restart plex-bot

# Verify it's running
sudo systemctl status plex-bot
```

## Important Rules

- **Never read .env** — contains secrets, must never be accessed
- Keep AGENT.md focused on bot operations, not development
- Test locally before deploying to server
- File operations won't work locally (need server paths)

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

### Progress Tracking Messages
Edit a single message to show real-time progress as the agent works:
```
Working on your request...
✓ Action 1/4: Searched Radarr for "Star Wars"
✓ Action 2/4: Checked root folders
⏳ Action 3/4: Getting quality profiles...
```

Keep the final message showing all completed actions.
