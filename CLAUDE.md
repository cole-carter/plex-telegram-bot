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
4. On server: `git pull && sudo systemctl restart plex-bot`

## Important Rules

- **Never read .env** — contains secrets, must never be accessed
- Keep AGENT.md focused on bot operations, not development
- Test locally before deploying to server
- File operations won't work locally (need server paths)

## Deployment

Server: Dell Inspiron 537s at 192.168.1.14
Method: Systemd service (see `systemd/plex-bot.service`)
