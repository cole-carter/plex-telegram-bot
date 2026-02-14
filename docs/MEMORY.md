## System Information

**Environment:** WSL2 (Windows Subsystem for Linux 2) on Windows

**Key Paths:**
- Project root: `/home/merman/plex_bot/`
- Bot code: `/home/merman/plex_bot/bot/`
- Documentation: `/home/merman/plex_bot/docs/`
- Logs: `/home/merman/plex_bot/logs/`
- Scripts: `/home/merman/plex_bot/scripts/`
- Home directory: `/home/merman/`

**Project Structure:**
```
/home/merman/plex_bot/
├── bot/
│   ├── agent.py (AI agent logic)
│   ├── main.py (Telegram bot main)
│   ├── config.py (configuration)
│   └── tools/ (tool implementations)
├── docs/
│   ├── MEMORY.md (system info)
│   ├── LEARNINGS.md (learnings)
│   └── API_REFERENCE.md (API docs)
├── logs/ (application logs)
├── scripts/ (utility scripts)
├── systemd/ (systemd service files)
├── CLAUDE.md (agent instructions)
├── README.md (project documentation)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

**Windows Integration:**
- Windows C: drive mounted at `/mnt/c/`
- WSL filesystem at `/`
- Total disk space: ~1TB (782GB used, 171GB available)

**Other Projects in /home/merman/:**
- stacker
- scoundrel
- telarus
- me (personal projects)
- dev (development files)
