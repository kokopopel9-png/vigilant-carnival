# Professional Telegram Coding Agent Bot — Setup Guide

## Overview

A complete, single-file Telegram Coding Agent Bot with button-driven navigation, rich HTML messages, and 57+ commands across 17 feature modules.

**File:** `bot.py` (~200KB, single Python file)  
**Language:** English only  
**Telegram:** python-telegram-bot v21+ (InlineKeyboard, ForceReply, BotCommand scope)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required for `python-telegram-bot` |
| pip | Latest | Python package manager |
| Telegram Bot Token | From @BotFather | Get your token |
| AI API Key | Optional | Claude, Gemini, or OpenRouter (free tiers) |

---

## Step 1: Get Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name and username for your bot
4. Copy the **Bot Token** (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

---

## Step 2: Clone / Prepare Files

```bash
# Ensure you have these files in your project folder:
# bot.py              - Main bot (single file, ~200KB)
# requirements.txt    - Python dependencies
# .env.example        - Environment template
```

---

## Step 3: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt contents:**
```text
python-telegram-bot==21.4
python-dotenv==1.0.1

# Optional AI provider SDKs (install only the one you use):
# anthropic==0.32.0        # Claude
# google-generativeai==0.8.0  # Gemini
# openai==1.50.0           # OpenRouter
```

Optional AI providers (choose one):
```bash
pip install anthropic        # For Claude
pip install google-generativeai  # For Gemini
pip install openai           # For OpenRouter
```

Optional system packages (for full features):
```bash
# For PostgreSQL
pip install psycopg2-binary

# For MySQL
pip install mysql-connector-python

# For MongoDB
pip install pymongo

# For system performance monitoring
pip install psutil

# For screenshot capture
pip install pillow
```

---

## Step 4: Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
nano .env   # or use any text editor
```

**.env.example:**
```ini
# ===== REQUIRED =====
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=your_bot_username

# ===== AI PROVIDER (choose one, free tiers) =====
AI_PROVIDER=openrouter   # claude | gemini | openrouter
CLAUDE_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# AI Models
CLAUDE_MODEL=claude-3-haiku-20240307
GEMINI_MODEL=gemini-1.5-flash
OPENROUTER_MODEL=openrouter/auto

# ===== ADMIN USER IDs (comma-separated) =====
# Get your user ID from @userinfobot on Telegram
ADMIN_IDS=123456789

# ===== LIMITS =====
RATE_LIMIT_PER_MIN=30
MAX_CONCURRENT_TASKS=3
COMMAND_TIMEOUT=120
MAX_CMD_OUTPUT=8000

# ===== PATHS =====
DB_PATH=data/bot.db
WORKSPACE_DIR=/workspace
SKILLS_DIR=data/skills
TOOLS_DIR=data/tools
TASKS_DIR=data/tasks
```

---

## Step 5: Run the Bot

```bash
# Make sure you're in the project directory
cd /path/to/your/bot

# Activate virtual environment
source venv/bin/activate   # Linux/Mac

# Run the bot
python bot.py
```

You should see:
```
INFO     | Starting Professional Coding Agent Bot...
```

---

## Step 6: Test in Telegram

1. Open Telegram and find your bot by username
2. Send `/start`
3. You'll see the **Main Menu** with buttons:
   - 📁 File Operations
   - 💻 Terminal
   - 🤖 Agent
   - 🧠 Skills
   - 🔧 Tools
   - 📋 Tasks
   - 🌐 Website
   - 🗄️ Database
   - 💾 Backup
   - 🖥️ Env
   - 🔍 API / Translate
   - 👮 Admin
   - ℹ️ Help
   - 📊 Stats

4. Tap any button to explore features.

---

## Feature Modules

| Module | Buttons | Commands |
|--------|---------|----------|
| **File Operations** | Read, Write, Edit, List Dir, Mkdir | /read, /write, /edit, /ls, /mkdir |
| **Terminal** | Run, npm, pip, git, Build, Test, History, List Dir | /run, /npm, /pip, /git, /build, /test, /history, /ls, /mkdir |
| **Agent** | Start Agent, Status, Cancel | /agent, /status, /cancel |
| **Skills** | List skills, Run skill, Create skill | /skill list, /skill run, /skill create, /skill delete, /skill info |
| **Tools** | List tools, Run tool, Create tool, Delete tool | /tool list, /tool run, /tool create, /tool delete |
| **Tasks** | List templates, Run template, Save task, Delete task | /task save, /task list, /task run, /task delete |
| **Website** | Preview, Start Server, Stop Server, Status, Screenshot, Tunnel, Website Status | /preview, /server-start, /server-stop, /server-status, /screenshot, /tunnel, /website-status |
| **Database** | Connect DB, DB Query, List Connections | /db-connect, /db-query, /db-list |
| **Backup** | Create Backup, Restore, List Backups | /backup, /restore, /backup-list |
| **Env** | Set Var, Get Var, List Vars | /env-set, /env-get, /env-list |
| **API** | API Test, Translate Code, Performance, Deploy, Auto Commit | /api-test, /translate, /performance, /deploy, /auto-commit |
| **Admin** | Stats, Broadcast, Ban User, Unban User | /stats, /broadcast, /ban, /unban |
| **Code** | Diff, Lint, Deps, Init, Review, Docker, Format, Search, Replace, Branch, Scaffold, Chain | /diff, /lint, /deps, /init, /review, /docker, /format, /search, /replace, /branch, /scaffold, /chain |

---

## File Structure

```
your-bot-folder/
├── bot.py              # Main bot (single file, all features)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template (copy to .env)
├── .env                # Your configuration (create this)
├── data/               # Auto-created
│   ├── bot.db          # SQLite database
│   ├── skills/         # User skills
│   ├── tools/          # User tools
│   ├── tasks/          # Task templates
│   └── backups/        # Backup files
└── logs/               # Auto-created
    └── bot.log         # Rotating log file
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `BOT_TOKEN not set` | Check `.env` file has `BOT_TOKEN=your_token` |
| `python-telegram-bot not found` | Run `pip install -r requirements.txt` |
| Bot doesn't respond | Check bot token is correct, bot is not blocked by you |
| AI features not working | Set `CLAUDE_API_KEY`, `GEMINI_API_KEY`, or `OPENROUTER_API_KEY` in `.env` |
| Terminal commands fail | Ensure workspace directory exists and has permissions |
| Database connection fails | Install required driver: `pip install psycopg2-binary` (PostgreSQL), `mysql-connector-python` (MySQL), `pymongo` (MongoDB) |

---

## Security Notes

- **Never share your BOT_TOKEN**
- **Never commit `.env` to version control**
- Admin IDs restrict `/stats`, `/broadcast`, `/ban`, `/unban` to specific users
- Dangerous commands (`rm -rf`, `shutdown`, `format`, etc.) are blocked for non-admins
- All commands run in the `WORKSPACE_DIR` sandbox

---

## Support

- Get bot token: @BotFather on Telegram
- Get user ID: @userinfobot on Telegram
- Report issues: https://github.com/Kilo-Org/kilocode/issues

---

**Built with python-telegram-bot v21+** | **Single file architecture** | **Button-driven UI** | **English only**