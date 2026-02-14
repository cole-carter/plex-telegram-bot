# Plex Telegram Bot 🤖

An AI-powered Telegram bot that manages your Plex media server through natural language. Built with Claude AI, it controls Sonarr (TV), Radarr (Movies), qBittorrent (downloads), and Plex (library management).

## Features

- 🎬 **Natural Language Control** - Just chat with the bot to manage your media
- 📺 **TV Show Management** - Request shows, check episodes, trigger downloads via Sonarr
- 🎥 **Movie Management** - Add movies, search library via Radarr
- 📥 **Download Management** - Add magnet links, monitor progress via qBittorrent
- 📚 **Library Organization** - Automatically organize files with Plex naming conventions
- 🧠 **Self-Learning** - Agent remembers patterns and improves over time
- 🔒 **Secure** - Restricted to your Telegram user ID only

## Architecture

```
User (Telegram) → Bot (Python) → Claude API (Haiku)
                                → Sonarr API (TV)
                                → Radarr API (Movies)
                                → qBittorrent API (Torrents)
                                → Plex API (Library)
                                → Filesystem (Organization)
```

### Agentic Design

This bot follows an **agentic-first** approach:
- Agent has CLI access to services via `api-call` wrapper
- Agent can read and update its own documentation
- Agent composes solutions using standard Unix tools
- No rigid function wrappers - full flexibility

## Prerequisites

- Python 3.10 or higher
- Access to:
  - Telegram (for bot creation)
  - Anthropic API (for Claude)
  - Sonarr, Radarr, qBittorrent, Plex instances

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/plex-telegram-bot.git
cd plex-telegram-bot
```

### 2. Install Dependencies

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Get API Keys

#### Telegram Bot Token
1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token

#### Your Telegram User ID
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your user ID

#### Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com/settings/keys)
2. Create a new API key
3. Copy it

#### Service API Keys
- **Sonarr**: Settings → General → API Key
- **Radarr**: Settings → General → API Key
- **qBittorrent**: Your web UI username/password
- **Plex**: [Finding your Plex token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit with your favorite editor
nano .env
```

Fill in all the values from the API keys you collected.

### 5. Make Scripts Executable

```bash
chmod +x scripts/api-call scripts/recycle-bin
```

### 6. Test the Bot

```bash
# Run locally
python -m bot.main
```

Send a message to your bot on Telegram to test it!

## Usage

### Example Conversations

**Request TV Show:**
```
You: Get me Breaking Bad season 5
Bot: Found Breaking Bad in Sonarr. Triggering search for all 16 episodes from season 5.
     Sonarr will download them automatically when indexers find them.
```

**Add Magnet Link:**
```
You: (paste magnet link)
Bot: What should I download this as? Is it a movie or TV show? What's the title?
You: Season 3 of Young Royals
Bot: Started downloading Young Royals Season 3. Ask me 'what's downloading?' to check progress.
```

**Check Downloads:**
```
You: What's downloading?
Bot: Active downloads:
     1. Young Royals S03 - 45% complete, ETA 15 minutes
     2. Some Movie 2024 - 89% complete, ETA 3 minutes
```

**Library Status:**
```
You: Do I have The Office?
Bot: Yes! You have The Office (2005) in your library with 9 seasons and 201 episodes.
```

**Organize Files:**
```
You: Check downloads folder and organize anything ready
Bot: Found 3 completed downloads. Organizing...
     ✓ Young Royals S03E01 → TV Shows library
     ✓ Young Royals S03E02 → TV Shows library
     ✓ Young Royals S03E03 → TV Shows library
     Plex is scanning now.
```

## Deployment

### Option 1: Systemd Service (Recommended)

```bash
# Copy to server
scp -r plex-telegram-bot user@192.168.1.14:~/

# On server, create service file
sudo nano /etc/systemd/system/plex-bot.service
```

```ini
[Unit]
Description=Plex Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/mermanarchy/plex-telegram-bot
ExecStart=/usr/bin/python3 -m bot.main
Restart=always
RestartSec=10
User=mermanarchy
EnvironmentFile=/home/mermanarchy/plex-telegram-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable plex-bot
sudo systemctl start plex-bot

# Check status
sudo systemctl status plex-bot

# View logs
sudo journalctl -u plex-bot -f
```

### Option 2: Docker Compose

Add to your existing `docker-compose.yml`:

```yaml
plex-bot:
  build: ./plex-telegram-bot
  container_name: plex-bot
  restart: unless-stopped
  env_file:
    - ./plex-telegram-bot/.env
  volumes:
    - /mnt/storage:/mnt/storage
    - /home/mermanarchy/downloads:/downloads
    - /home/mermanarchy/recycle-bin:/recycle-bin
  network_mode: host
```

## Project Structure

```
plex_bot/
├── CLAUDE.md                  # Agent instructions (you control)
├── bot/
│   ├── main.py               # Telegram bot entry point
│   ├── agent.py              # Claude API integration
│   ├── config.py             # Configuration management
│   └── tools/
│       ├── command_executor.py  # Safe command execution
│       └── docs_manager.py      # Agent self-documentation
├── scripts/
│   ├── api-call              # Generic API wrapper CLI
│   └── recycle-bin           # Safe file deletion
├── docs/                      # Agent can read/write these
│   ├── MEMORY.md
│   ├── LEARNINGS.md
│   └── API_REFERENCE.md
├── requirements.txt
├── .env.example
└── README.md
```

## Security

- ✅ Bot only responds to your Telegram user ID
- ✅ API keys stored in `.env`, never committed to git
- ✅ Agent cannot read `.env` or secret files
- ✅ Destructive commands blocked (`rm`, `dd`, etc.)
- ✅ Safe deletion via recycle bin
- ✅ Command whitelist (only approved commands allowed)

## Agentic Best Practices

This project demonstrates several agentic design principles:

1. **Give capabilities, not procedures** - Agent has shell access, not rigid functions
2. **Provide context, not code** - API docs in CLAUDE.md, agent composes calls
3. **Enable self-improvement** - Agent can update its own documentation
4. **Trust boundaries over trust tokens** - Security via isolation, not hiding keys
5. **Smooth the onboarding ramp** - Clear setup with `.env.example`

## Troubleshooting

### Bot doesn't respond
- Check bot is running: `systemctl status plex-bot`
- Check logs: `journalctl -u plex-bot -f`
- Verify `TELEGRAM_USER_ID` in `.env` matches yours

### API calls fail
- Verify service URLs are correct and accessible
- Check API keys are valid
- Test manually: `./scripts/api-call sonarr GET /system/status`

### Commands blocked
- Check security rules in `bot/tools/command_executor.py`
- Agent may be trying to access blocked files/commands
- Review logs for security violations

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Claude AI](https://anthropic.com/claude) by Anthropic
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library
- Inspired by the agentic design principles of [OpenClaw](https://github.com/openclaw/openclaw)

## Support

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/yourusername/plex-telegram-bot/issues)
- Documentation: See CLAUDE.md for agent behavior
- API Docs: Check docs/ folder for agent learnings
