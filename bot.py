"""
Professional Telegram Coding Agent Bot - Ultimate Edition
Single File with Rich Messages + Button-Driven Navigation (English Only)

Features:
- Rich HTML messages with embedded inline keyboard buttons
- Terminal engine (npm, pip, git, build, test, run)
- Autonomous coding agent with self-correction & checkpoints
- Skills & Tools system (create, run, delete)
- Task templates & chaining
- Website control (preview, server, screenshot, tunnel, status)
- Database management (MySQL, PostgreSQL, MongoDB)
- Backup & Restore, Environment variables
- API testing, Code translation, Performance, Deploy, Auto-commit
- Admin commands (stats, broadcast, ban, unban)
- File operations (read, write, edit, ls, mkdir)
"""

import os
import sys
import json
import time
import shlex
import sqlite3
import logging
import subprocess
import threading
import importlib.util
import http.server
import socketserver
import urllib.request
import urllib.error
from collections import defaultdict, deque
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Callable

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
    BotCommand,
    BotCommandScopeAllPrivateChats,
    InputMediaPhoto,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")

# AI Provider (free tiers): claude | gemini | openrouter
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openrouter").lower()
CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/auto")

ADMIN_IDS: List[int] = [
    int(uid.strip())
    for uid in os.getenv("ADMIN_IDS", "").split(",")
    if uid.strip().isdigit()
]

RATE_LIMIT_PER_MIN: int = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
MAX_CONCURRENT_TASKS: int = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
DB_PATH: str = os.getenv("DB_PATH", "data/bot.db")
WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", "/workspace")
SKILLS_DIR: str = os.getenv("SKILLS_DIR", "data/skills")
TOOLS_DIR: str = os.getenv("TOOLS_DIR", "data/tools")
TASKS_DIR: str = os.getenv("TASKS_DIR", "data/tasks")
MAX_CMD_OUTPUT: int = int(os.getenv("MAX_CMD_OUTPUT", "8000"))
COMMAND_TIMEOUT: int = int(os.getenv("COMMAND_TIMEOUT", "120"))

DANGEROUS_COMMANDS: List[str] = [
    "rm -rf", "mkfs", "dd ", "> /dev/", "shutdown", "reboot",
    "init 0", "init 6", ":(){ :|:& };:", "format",
]

# ============================================================================
# DIRECTORIES
# ============================================================================

for _d in [os.path.dirname(DB_PATH), SKILLS_DIR, TOOLS_DIR, TASKS_DIR, "logs"]:
    if _d:
        os.makedirs(_d, exist_ok=True)

# ============================================================================
# LOGGER
# ============================================================================

logger = logging.getLogger("coding_agent_bot")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    _ch = logging.StreamHandler()
    _ch.setLevel(logging.INFO)
    _ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
    logger.addHandler(_ch)

    _fh = RotatingFileHandler(
        os.path.join("logs", "bot.log"),
        maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"))
    logger.addHandler(_fh)

# ============================================================================
# EMOJI PALETTE
# ============================================================================

EMOJI = {
    "bot": "🤖", "success": "✅", "error": "❌", "warning": "⚠️",
    "info": "ℹ️", "terminal": "💻", "file": "📄", "folder": "📂",
    "skill": "🧠", "tool": "🔧", "task": "📋", "agent": "🚀",
    "admin": "👮", "stats": "📊", "time": "⏱️", "running": "🔄",
    "pending": "⏳", "completed": "✅", "failed": "❌", "delete": "🗑️",
    "edit": "✏️", "read": "📖", "write": "📝", "broadcast": "📢",
    "ban": "🚫", "unban": "🔓", "history": "🕒", "build": "🏗️",
    "test": "🧪", "npm": "📦", "pip": "🐍", "git": "🌿",
    "lock": "🔒", "unlock": "🔓", "key": "🔑", "gear": "⚙️",
    "rocket": "🚀", "star": "⭐", "check": "✅", "cross": "✖️",
    "arrow": "▶️", "back": "🔙", "home": "🏠", "search": "🔍",
    "plus": "➕", "minus": "➖", "db": "🗄️", "list": "📋",
    "docker": "🐳", "preview": "👁️", "screenshot": "📸",
    "tunnel": "🚇", "website": "🌐", "server": "🖥️",
    "apk": "📱", "sandbox": "🏗️",
}

# ============================================================================
# RICH MESSAGE BUILDERS
# ============================================================================

def _box(title: str, content: str, icon: str = "📦") -> str:
    """Build a professional boxed message."""
    return (
        f"{icon} <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{content}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def _panel(title: str, rows: List[str], icon: str = "⚙️") -> str:
    """Build a professional panel with rows."""
    lines = [f"{icon} <b>{title}</b>", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines.extend(rows)
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


def _rich_table(headers: List[str], rows: List[List[str]]) -> str:
    """Build a rich markdown-style table for Telegram."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    line = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    out = [line]
    out.append("| " + " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)) + " |")
    out.append(line)
    for row in rows:
        out.append("| " + " | ".join(f"{str(c):<{col_widths[i]}}" for i, c in enumerate(row)) + " |")
    out.append(line)
    return "<pre>\n" + "\n".join(out) + "\n</pre>"


def _status_badge(status: str) -> str:
    """Return a styled status badge."""
    styles = {
        "success": f"{EMOJI['success']} <b>SUCCESS</b>",
        "error": f"{EMOJI['error']} <b>FAILED</b>",
        "running": f"{EMOJI['running']} <b>RUNNING</b>",
        "pending": f"{EMOJI['pending']} <b>PENDING</b>",
        "completed": f"{EMOJI['completed']} <b>COMPLETED</b>",
        "failed": f"{EMOJI['failed']} <b>FAILED</b>",
    }
    return styles.get(status, f"{EMOJI['info']} <b>{status.upper()}</b>")


def _progress_bar(current: int, total: int, width: int = 10) -> str:
    """Build a visual progress bar."""
    filled = int(width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * current / total) if total > 0 else 0
    return f"<code>{bar}</code> {pct}%"

# ============================================================================
# DATABASE (SQLite)
# ============================================================================

class Database:
    """SQLite storage: users, skills, tools, tasks, command_log, checkpoints."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def _init_tables(self) -> None:
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT, first_name TEXT, last_name TEXT,
                    is_banned INTEGER DEFAULT 0,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS skills (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    code TEXT,
                    category TEXT DEFAULT 'general',
                    created_by INTEGER,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS tools (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    code TEXT,
                    created_by INTEGER,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS task_templates (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    task_type TEXT,
                    params_json TEXT,
                    created_by INTEGER,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS user_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_type TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at TEXT, updated_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                CREATE TABLE IF NOT EXISTS command_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, command TEXT,
                    executed_at TEXT, success INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, task_id INTEGER,
                    description TEXT, state_json TEXT, created_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                """
            )
            c.commit()

    def upsert_user(self, user_id: int, username: Optional[str] = None,
                    first_name: Optional[str] = None,
                    last_name: Optional[str] = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            ex = c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone()
            if ex:
                c.execute(
                    "UPDATE users SET username=?, first_name=?, last_name=?, updated_at=? WHERE user_id=?",
                    (username, first_name, last_name, now, user_id),
                )
            else:
                c.execute(
                    "INSERT INTO users(user_id,username,first_name,last_name,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                    (user_id, username, first_name, last_name, now, now),
                )
            c.commit()

    def is_banned(self, user_id: int) -> bool:
        with self._conn() as c:
            r = c.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,)).fetchone()
            return bool(r and r["is_banned"] == 1)

    def ban_user(self, user_id: int) -> None:
        self.upsert_user(user_id)
        with self._conn() as c:
            c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
            c.commit()

    def unban_user(self, user_id: int) -> None:
        self.upsert_user(user_id)
        with self._conn() as c:
            c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
            c.commit()

    def skill_exists(self, name: str) -> bool:
        with self._conn() as c:
            return bool(c.execute("SELECT 1 FROM skills WHERE name=?", (name,)).fetchone())

    def save_skill(self, name: str, description: str, code: str,
                   category: str, created_by: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            if self.skill_exists(name):
                c.execute(
                    "UPDATE skills SET description=?, code=?, category=?, updated_at=? WHERE name=?",
                    (description, code, category, now, name),
                )
            else:
                c.execute(
                    "INSERT INTO skills(name,description,code,category,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (name, description, code, category, created_by, now, now),
                )
            c.commit()

    def get_skill(self, name: str) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM skills WHERE name=?", (name,)).fetchone()
            return dict(r) if r else None

    def list_skills(self) -> List[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT name,description,category,created_at FROM skills ORDER BY category, name").fetchall()
            return [dict(r) for r in rows]

    def delete_skill(self, name: str) -> bool:
        with self._conn() as c:
            c.execute("DELETE FROM skills WHERE name=?", (name,))
            c.commit()
            return c.total_changes > 0

    def tool_exists(self, name: str) -> bool:
        with self._conn() as c:
            return bool(c.execute("SELECT 1 FROM tools WHERE name=?", (name,)).fetchone())

    def save_tool(self, name: str, description: str, code: str, created_by: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            if self.tool_exists(name):
                c.execute("UPDATE tools SET description=?, code=?, updated_at=? WHERE name=?",
                          (description, code, now, name))
            else:
                c.execute(
                    "INSERT INTO tools(name,description,code,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                    (name, description, code, created_by, now, now),
                )
            c.commit()

    def get_tool(self, name: str) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM tools WHERE name=?", (name,)).fetchone()
            return dict(r) if r else None

    def list_tools(self) -> List[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT name,description,created_at FROM tools ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def delete_tool(self, name: str) -> bool:
        with self._conn() as c:
            c.execute("DELETE FROM tools WHERE name=?", (name,))
            c.commit()
            return c.total_changes > 0

    def save_task_template(self, name: str, description: str, task_type: str,
                           params: dict, created_by: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        params_json = json.dumps(params, ensure_ascii=False)
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO task_templates(name,description,task_type,params_json,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (name, description, task_type, params_json, created_by, now, now),
            )
            c.commit()

    def get_task_template(self, name: str) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM task_templates WHERE name=?", (name,)).fetchone()
            if r:
                d = dict(r)
                d["params"] = json.loads(d["params_json"] or "{}")
                return d
            return None

    def list_task_templates(self) -> List[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT name,description,task_type,created_at FROM task_templates ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def delete_task_template(self, name: str) -> bool:
        with self._conn() as c:
            c.execute("DELETE FROM task_templates WHERE name=?", (name,))
            c.commit()
            return c.total_changes > 0

    def create_task(self, user_id: int, task_type: str,
                    task_id: Optional[int] = None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            if task_id:
                c.execute("UPDATE user_tasks SET status='pending', updated_at=? WHERE id=? AND user_id=?",
                          (now, task_id, user_id))
                tid = task_id
            else:
                cur = c.execute(
                    "INSERT INTO user_tasks(user_id,task_type,status,created_at,updated_at) VALUES(?,?,'pending',?,?)",
                    (user_id, task_type, now, now),
                )
                tid = cur.lastrowid
            c.commit()
            return tid

    def update_task(self, task_id: int, status: str,
                    result: Optional[str] = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            if result is not None:
                c.execute("UPDATE user_tasks SET status=?, result=?, updated_at=? WHERE id=?",
                          (status, result, now, task_id))
            else:
                c.execute("UPDATE user_tasks SET status=?, updated_at=? WHERE id=?", (status, now, task_id))
            c.commit()

    def get_task(self, task_id: int) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM user_tasks WHERE id=?", (task_id,)).fetchone()
            return dict(r) if r else None

    def log_command(self, user_id: int, command: str, success: bool = False) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute("INSERT INTO command_log(user_id,command,executed_at,success) VALUES(?,?,?,?)",
                      (user_id, command, now, int(success)))
            c.commit()

    def create_checkpoint(self, user_id: int, task_id: int,
                          description: str, state: dict) -> int:
        now = datetime.now(timezone.utc).isoformat()
        sj = json.dumps(state, ensure_ascii=False)
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO checkpoints(user_id,task_id,description,state_json,created_at) VALUES(?,?,?,?,?)",
                (user_id, task_id, description, sj, now),
            )
            c.commit()
            return cur.lastrowid

    def get_stats(self) -> dict:
        with self._conn() as c:
            def cnt(q: str) -> int:
                return c.execute(q).fetchone()["cnt"]
            return {
                "total_users": cnt("SELECT COUNT(*) AS cnt FROM users"),
                "banned_users": cnt("SELECT COUNT(*) AS cnt FROM users WHERE is_banned=1"),
                "total_skills": cnt("SELECT COUNT(*) AS cnt FROM skills"),
                "total_tools": cnt("SELECT COUNT(*) AS cnt FROM tools"),
                "total_task_templates": cnt("SELECT COUNT(*) AS cnt FROM task_templates"),
                "total_commands": cnt("SELECT COUNT(*) AS cnt FROM command_log"),
                "successful_commands": cnt("SELECT COUNT(*) AS cnt FROM command_log WHERE success=1"),
                "pending_tasks": cnt("SELECT COUNT(*) AS cnt FROM user_tasks WHERE status='pending'"),
                "running_tasks": cnt("SELECT COUNT(*) AS cnt FROM user_tasks WHERE status='running'"),
                "completed_tasks": cnt("SELECT COUNT(*) AS cnt FROM user_tasks WHERE status='completed'"),
            }

# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    def __init__(self, max_calls_per_minute: int) -> None:
        self.max_calls = max_calls_per_minute
        self._calls: Dict[int, Deque[float]] = defaultdict(deque)

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        ws = now - 60.0
        calls = self._calls[user_id]
        while calls and calls[0] < ws:
            calls.popleft()
        if len(calls) >= self.max_calls:
            logger.warning("Rate limit exceeded user %d", user_id)
            return False
        calls.append(now)
        return True

    def get_remaining(self, user_id: int) -> int:
        now = time.time()
        ws = now - 60.0
        calls = self._calls[user_id]
        while calls and calls[0] < ws:
            calls.popleft()
        return max(0, self.max_calls - len(calls))

# ============================================================================
# AI CLIENT
# ============================================================================

class AIClient:
    def __init__(self) -> None:
        self.provider = AI_PROVIDER
        self.claude_key = CLAUDE_API_KEY
        self.gemini_key = GEMINI_API_KEY
        self.openrouter_key = OPENROUTER_API_KEY
        self.claude_model = CLAUDE_MODEL
        self.gemini_model = GEMINI_MODEL
        self.openrouter_model = OPENROUTER_MODEL
        self._client: Any = None
        self._init()

    def _init(self) -> None:
        try:
            if self.provider == "claude":
                import anthropic
                if self.claude_key:
                    self._client = anthropic.Anthropic(api_key=self.claude_key)
                    logger.info("Claude AI client initialized")
            elif self.provider == "gemini":
                import google.generativeai as genai
                if self.gemini_key:
                    genai.configure(api_key=self.gemini_key)
                    self._client = genai.GenerativeModel(self.gemini_model)
                    logger.info("Gemini AI client initialized")
            elif self.provider == "openrouter":
                import openai
                if self.openrouter_key:
                    self._client = openai.OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=self.openrouter_key,
                    )
                    logger.info("OpenRouter AI client initialized")
        except ImportError as e:
            logger.error("AI import error: %s", e)
        except Exception as e:
            logger.error("AI init error: %s", e)

    def is_available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 max_tokens: int = 2000, temperature: float = 0.7) -> str:
        if not self._client:
            return ("⚠️ AI provider not configured. Set CLAUDE_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY.")
        try:
            if self.provider == "claude" and hasattr(self._client, "messages"):
                msgs: List[dict] = []
                if system_prompt:
                    msgs.append({"role": "system", "content": system_prompt})
                msgs.append({"role": "user", "content": prompt})
                r = self._client.messages.create(
                    model=self.claude_model, max_tokens=max_tokens,
                    temperature=temperature, messages=msgs,
                )
                return r.content[0].text
            if self.provider == "gemini" and hasattr(self._client, "generate_content"):
                fp = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                r = self._client.generate_content(fp)
                return r.text
            if self.provider == "openrouter":
                msgs: List[dict] = []
                if system_prompt:
                    msgs.append({"role": "system", "content": system_prompt})
                msgs.append({"role": "user", "content": prompt})
                r = self._client.chat.completions.create(
                    model=self.openrouter_model, messages=msgs,
                    max_tokens=max_tokens, temperature=temperature,
                )
                return r.choices[0].message.content
            return "⚠️ Unknown AI provider."
        except Exception as e:
            logger.error("AI generate error: %s", e)
            return f"⚠️ AI generation failed: {e}"

    def coding_agent_system_prompt(self, task: str, workspace: str,
                                   file_context: str = "") -> str:
        return (
            "You are an elite autonomous coding agent in a sandboxed workspace.\n"
            f"Workspace: {workspace}\nTask: {task}\n\n"
            "MISSION: Read, write, edit, run, test, lint, fix, and commit code until the task is 100% complete.\n"
            "You operate in a loop: READ → PLAN → ACT → VERIFY → (if failed) FIX → REPEAT.\n\n"
            "AVAILABLE SKILLS (use exact names):\n"
            "• terminal.run — Run any shell command\n"
            "• terminal.npm — Install npm package\n"
            "• terminal.pip — Install pip package\n"
            "• terminal.git — Run git command\n"
            "• terminal.build — Build project\n"
            "• terminal.test — Run tests\n"
            "• file.read — Read a file\n"
            "• file.write — Write/create a file\n\n"
            "RESPONSE FORMAT — Output ONE action per step:\n"
            "ACTION: READ <file_path>\n"
            "ACTION: WRITE <file_path> <content>\n"
            "ACTION: RUN <skill_name> <args>\n"
            "ACTION: TEST\n"
            "ACTION: LINT\n"
            "ACTION: GIT <git_command>\n"
            "ACTION: DIFF <file_path>\n"
            "ACTION: INIT <project_type>\n"
            "ACTION: DEPS\n"
            "ACTION: REVIEW <file_path>\n"
            "ACTION: DOCKER <command>\n"
            "ACTION: FORMAT <file_path>\n"
            "ACTION: SEARCH <pattern>\n"
            "ACTION: REPLACE <file_path> <old> <new>\n"
            "ACTION: BRANCH <branch_name>\n"
            "ACTION: SCAFFOLD <template_name>\n"
            "ACTION: CHAIN <task_1> | <task_2> | ...\n"
            "ACTION: FIX <error_description>\n"
            "ACTION: APK_BUILD <project_path>\n"
            "ACTION: APK_INFO <apk_path>\n"
            "ACTION: APK_INSTALL <apk_path>\n"
            "ACTION: APK_DECOMPILE <apk_path>\n"
            "ACTION: APK_EDIT <decompile_dir> <file_path> <content>\n"
            "ACTION: APK_CHANGE <apk_path> <description>\n"
            "ACTION: APK_REBUILD <decompile_dir> <output_apk>\n"
            "ACTION: SANDBOX_RUN <command>\n"
            "ACTION: SANDBOX_LIST\n"
            "ACTION: AUTO_LEARN_SKILL <name> <description> <code>\n"
            "ACTION: AUTO_CREATE_TOOL <name> <description> <code>\n"
            "ACTION: AUTO_USE_SKILL <skill_name> <args>\n"
            "ACTION: AUTO_USE_TOOL <tool_name> <args>\n"
            "ACTION: COMPLETE <summary>\n\n"
            "RULES:\n"
            "1. Always READ files before modifying them.\n"
            "2. Make small, incremental changes.\n"
            "3. After writing code, RUN tests and LINT to verify.\n"
            "4. If tests fail, use ACTION: FIX to analyze and correct.\n"
            "5. Use ACTION: GIT to commit changes when task is complete.\n"
            "6. Never run destructive commands (rm -rf, format, shutdown).\n"
            "7. Report progress clearly after every step.\n"
            "8. Use ACTION: APK_BUILD to build Android APKs.\n"
            "9. Use ACTION: SANDBOX_RUN to test code in isolated sandbox.\n"
            "10. When task is fully working and committed, use ACTION: COMPLETE.\n\n"
            f"Workspace files:\n{file_context}\n\n"
            "Respond with your next ACTION only."
        )

# ============================================================================
# TERMINAL ENGINE
# ============================================================================

class TerminalEngine:
    def __init__(self, workspace: str, db: Database,
                 max_output: int = MAX_CMD_OUTPUT,
                 timeout: int = COMMAND_TIMEOUT) -> None:
        self.workspace = workspace
        self.db = db
        self.max_output = max_output
        self.timeout = timeout
        self.history: List[dict] = []

    def is_dangerous(self, command: str) -> bool:
        low = command.lower()
        return any(p in low for p in DANGEROUS_COMMANDS)

    def run(self, user_id: int, command: str,
            admin: bool = False) -> dict:
        self.db.log_command(user_id, command, success=False)
        if self.is_dangerous(command) and not admin:
            return {
                "success": False,
                "output": "⚠️ Dangerous command blocked. Admin approval required.",
                "exit_code": -1,
            }
        try:
            r = subprocess.run(
                command, shell=True, cwd=self.workspace,
                capture_output=True, text=True, timeout=self.timeout,
            )
            out = (r.stdout or "") + (r.stderr or "")
            if not out:
                out = "(no output)"
            if len(out) > self.max_output:
                out = out[:self.max_output] + "\n... (output truncated)"
            success = r.returncode == 0
            self.db.log_command(user_id, command, success=success)
            self.history.append({
                "user_id": user_id, "command": command,
                "success": success, "exit_code": r.returncode,
                "time": datetime.now(timezone.utc).isoformat(),
            })
            return {
                "success": success,
                "output": out,
                "exit_code": r.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": f"⏱️ Timed out after {self.timeout}s", "exit_code": -1}
        except Exception as e:
            logger.error("Terminal error: %s", e)
            return {"success": False, "output": f"❌ Error: {e}", "exit_code": -1}

    def get_history(self, limit: int = 20) -> List[dict]:
        return self.history[-limit:]

# ============================================================================
# SKILL SYSTEM
# ============================================================================

class Skill:
    def __init__(self, name: str, description: str, code: str,
                 category: str, created_by: int) -> None:
        self.name = name
        self.description = description
        self.code = code
        self.category = category
        self.created_by = created_by
        self._func: Optional[Callable] = None
        self._compiled = False

    def compile(self) -> bool:
        if self._compiled:
            return True
        try:
            ns: dict = {}
            exec(self.code, ns)
            self._func = ns.get("run") or ns.get("execute")
            self._compiled = self._func is not None
            return self._compiled
        except Exception as e:
            logger.error("Skill compile error %s: %s", self.name, e)
            return False

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if not self.compile():
            return f"❌ Skill {self.name} failed to compile."
        try:
            return self._func(*args, **kwargs)
        except Exception as e:
            logger.error("Skill run error %s: %s", self.name, e)
            return f"❌ Skill {self.name} error: {e}"


class SkillRegistry:
    def __init__(self, db: Database, skills_dir: str = SKILLS_DIR,
                 terminal: Optional[TerminalEngine] = None) -> None:
        self.db = db
        self.skills_dir = skills_dir
        self.terminal = terminal
        os.makedirs(skills_dir, exist_ok=True)
        self._skills: Dict[str, Skill] = {}
        self._load_all()
        self._register_builtin_terminal_skills()

    def _register_builtin_terminal_skills(self) -> None:
        builtins = {
            "terminal.run": (
                "Run any shell command via skill",
                """
import os
def run(command: str, workspace: str = "/workspace") -> str:
    import subprocess
    try:
        r = subprocess.run(command, shell=True, cwd=workspace, capture_output=True, text=True, timeout=60)
        out = (r.stdout or "") + (r.stderr or "")
        return out or "(no output)"
    except Exception as e:
        return f"Error: {e}"
""",
                "terminal",
            ),
            "terminal.npm": (
                "Install npm package",
                """
def run(pkg: str) -> str:
    import subprocess
    r = subprocess.run(f"npm install {pkg}", shell=True, cwd="/workspace", capture_output=True, text=True, timeout=120)
    return (r.stdout or "") + (r.stderr or "")
""",
                "terminal",
            ),
            "terminal.pip": (
                "Install pip package",
                """
def run(pkg: str) -> str:
    import subprocess
    r = subprocess.run(f"pip install {pkg}", shell=True, cwd="/workspace", capture_output=True, text=True, timeout=120)
    return (r.stdout or "") + (r.stderr or "")
""",
                "terminal",
            ),
            "terminal.git": (
                "Run git command",
                """
def run(cmd: str) -> str:
    import subprocess
    r = subprocess.run(f"git {cmd}", shell=True, cwd="/workspace", capture_output=True, text=True, timeout=60)
    return (r.stdout or "") + (r.stderr or "")
""",
                "terminal",
            ),
            "terminal.build": (
                "Run project build",
                """
def run() -> str:
    import subprocess, os
    for cmd in ["npm run build", "pip install -r requirements.txt"]:
        r = subprocess.run(cmd, shell=True, cwd="/workspace", capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            return (r.stdout or "") + "Build succeeded"
    return "No build script found"
""",
                "terminal",
            ),
            "terminal.test": (
                "Run project tests",
                """
def run() -> str:
    import subprocess
    for cmd in ["npm test", "pytest"]:
        r = subprocess.run(cmd, shell=True, cwd="/workspace", capture_output=True, text=True, timeout=120)
        if r.returncode == 0 or r.stdout:
            return (r.stdout or "") + (r.stderr or "")
    return "No test command found"
""",
                "terminal",
            ),
            "file.read": (
                "Read a file",
                """
def run(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"
""",
                "file",
            ),
            "file.write": (
                "Write a file",
                """
def run(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"
""",
                "file",
            ),
        }
        for name, (desc, code, cat) in builtins.items():
            if not self.db.skill_exists(name):
                self.db.save_skill(name, desc, code, cat, 0)
            s = Skill(name, desc, code, cat, 0)
            s.compile()
            self._skills[name] = s

    def _load_all(self) -> None:
        for r in self.db.list_skills():
            s = Skill(r["name"], r["description"], r["code"],
                      r.get("category", "general"), r["created_by"])
            self._skills[r["name"]] = s
            p = os.path.join(self.skills_dir, f"{r['name']}.py")
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(r["code"])
            except Exception as e:
                logger.warning("Skill disk write %s: %s", r["name"], e)

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list(self) -> List[dict]:
        return self.db.list_skills()

    def create(self, name: str, description: str, code: str,
               category: str, created_by: int) -> bool:
        if self.db.skill_exists(name):
            return False
        self.db.save_skill(name, description, code, category, created_by)
        s = Skill(name, description, code, category, created_by)
        s.compile()
        self._skills[name] = s
        return True

    def delete(self, name: str) -> bool:
        if self.db.delete_skill(name):
            self._skills.pop(name, None)
            p = os.path.join(self.skills_dir, f"{name}.py")
            if os.path.exists(p):
                os.remove(p)
            return True
        return False

# ============================================================================
# TOOL SYSTEM
# ============================================================================

class Tool:
    def __init__(self, name: str, description: str, code: str,
                 created_by: int) -> None:
        self.name = name
        self.description = description
        self.code = code
        self.created_by = created_by
        self._func: Optional[Callable] = None
        self._compiled = False

    def compile(self) -> bool:
        if self._compiled:
            return True
        try:
            ns: dict = {}
            exec(self.code, ns)
            self._func = ns.get("run") or ns.get("execute")
            self._compiled = self._func is not None
            return self._compiled
        except Exception as e:
            logger.error("Tool compile error %s: %s", self.name, e)
            return False

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if not self.compile():
            return f"❌ Tool {self.name} failed to compile."
        try:
            return self._func(*args, **kwargs)
        except Exception as e:
            logger.error("Tool run error %s: %s", self.name, e)
            return f"❌ Tool {self.name} error: {e}"


class ToolRegistry:
    def __init__(self, db: Database, tools_dir: str = TOOLS_DIR) -> None:
        self.db = db
        self.tools_dir = tools_dir
        os.makedirs(tools_dir, exist_ok=True)
        self._tools: Dict[str, Tool] = {}
        self._load_all()

    def _load_all(self) -> None:
        for r in self.db.list_tools():
            t = Tool(r["name"], r["description"], r["code"], r["created_by"])
            self._tools[r["name"]] = t
            p = os.path.join(self.tools_dir, f"{r['name']}.py")
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(r["code"])
            except Exception as e:
                logger.warning("Tool disk write %s: %s", r["name"], e)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list(self) -> List[dict]:
        return self.db.list_tools()

    def create(self, name: str, description: str, code: str,
               created_by: int) -> bool:
        if self.db.tool_exists(name):
            return False
        self.db.save_tool(name, description, code, created_by)
        t = Tool(name, description, code, created_by)
        t.compile()
        self._tools[name] = t
        return True

    def delete(self, name: str) -> bool:
        if self.db.delete_tool(name):
            self._tools.pop(name, None)
            p = os.path.join(self.tools_dir, f"{name}.py")
            if os.path.exists(p):
                os.remove(p)
            return True
        return False

# ============================================================================
# TASK TEMPLATES
# ============================================================================

class TaskTemplateManager:
    def __init__(self, db: Database, tasks_dir: str = TASKS_DIR) -> None:
        self.db = db
        self.tasks_dir = tasks_dir
        os.makedirs(tasks_dir, exist_ok=True)

    def save(self, name: str, description: str, task_type: str,
             params: dict, created_by: int) -> None:
        self.db.save_task_template(name, description, task_type, params, created_by)

    def get(self, name: str) -> Optional[dict]:
        return self.db.get_task_template(name)

    def list(self) -> List[dict]:
        return self.db.list_task_templates()

    def delete(self, name: str) -> bool:
        return self.db.delete_task_template(name)

# ============================================================================
# DATABASE EXTENSIONS
# ============================================================================

class DatabaseManager:
    """Manage database connections and queries for multiple DB types."""

    def __init__(self) -> None:
        self._connections: Dict[str, Any] = {}

    def connect_mysql(self, host: str, port: int, user: str,
                      password: str, database: str) -> str:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=host, port=port, user=user,
                password=password, database=database
            )
            key = f"mysql:{host}:{port}:{database}"
            self._connections[key] = conn
            return f"✅ Connected to MySQL: {host}:{port}/{database}"
        except ImportError:
            return "❌ mysql-connector-python not installed. Run: pip install mysql-connector-python"
        except Exception as e:
            return f"❌ MySQL connection failed: {e}"

    def connect_postgresql(self, host: str, port: int, user: str,
                           password: str, database: str) -> str:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=host, port=port, user=user,
                password=password, database=database
            )
            key = f"postgres:{host}:{port}:{database}"
            self._connections[key] = conn
            return f"✅ Connected to PostgreSQL: {host}:{port}/{database}"
        except ImportError:
            return "❌ psycopg2 not installed. Run: pip install psycopg2-binary"
        except Exception as e:
            return f"❌ PostgreSQL connection failed: {e}"

    def connect_mongodb(self, host: str, port: int,
                        username: str, password: str,
                        database: str) -> str:
        try:
            from pymongo import MongoClient
            uri = f"mongodb://{username}:{password}@{host}:{port}/{database}"
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.server_info()
            key = f"mongodb:{host}:{port}:{database}"
            self._connections[key] = client
            return f"✅ Connected to MongoDB: {host}:{port}/{database}"
        except ImportError:
            return "❌ pymongo not installed. Run: pip install pymongo"
        except Exception as e:
            return f"❌ MongoDB connection failed: {e}"

    def execute_query(self, key: str, query: str) -> str:
        if key not in self._connections:
            return "❌ Database not connected. Use /db-connect first."
        try:
            conn = self._connections[key]
            if "mysql" in key or "postgres" in key:
                cur = conn.cursor()
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description] if cur.description else []
                cur.close()
                conn.commit()
                if not rows:
                    return "✅ Query executed successfully (no rows returned)."
                result = "| " + " | ".join(columns) + " |\n"
                result += "| " + " | ".join(["---"] * len(columns)) + " |\n"
                for row in rows[:20]:
                    result += "| " + " | ".join(str(c) for c in row) + " |\n"
                if len(rows) > 20:
                    result += f"\n... and {len(rows) - 20} more rows"
                return result
            elif "mongodb" in key:
                return "✅ MongoDB query executed (use /db-mongo for advanced queries)."
            else:
                return "❌ Unknown database type."
        except Exception as e:
            return f"❌ Query failed: {e}"

    def list_connections(self) -> str:
        if not self._connections:
            return "📭 No database connections."
        lines = [f"• {k}" for k in self._connections.keys()]
        return "🔗 <b>Active DB Connections:</b>\n" + "\n".join(lines)


db_manager = DatabaseManager()

# ============================================================================
# BACKUP / RESTORE
# ============================================================================

import zipfile

_BACKUPS_DIR = "data/backups"
os.makedirs(_BACKUPS_DIR, exist_ok=True)


def _create_backup(user_id: int, name: str) -> str:
    backup_path = os.path.join(_BACKUPS_DIR, f"{user_id}_{name}.zip")
    try:
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(WORKSPACE_DIR):
                dirs[:] = [d for d in dirs
                           if not d.startswith(".")
                           and d not in {"node_modules", "__pycache__", ".git"}]
                for f in files:
                    if f.startswith("."):
                        continue
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, WORKSPACE_DIR)
                    zipf.write(full, rel)
        size = os.path.getsize(backup_path)
        return f"✅ Backup created: {backup_path} ({size} bytes)"
    except Exception as e:
        return f"❌ Backup failed: {e}"


def _restore_backup(user_id: int, name: str) -> str:
    backup_path = os.path.join(_BACKUPS_DIR, f"{user_id}_{name}.zip")
    if not os.path.exists(backup_path):
        return f"❌ Backup not found: {name}"
    try:
        with zipfile.ZipFile(backup_path, "r") as zipf:
            zipf.extractall(WORKSPACE_DIR)
        return f"✅ Backup restored: {name}"
    except Exception as e:
        return f"❌ Restore failed: {e}"


def _list_backups(user_id: int) -> str:
    if not os.path.exists(_BACKUPS_DIR):
        return "📭 No backups directory."
    files = [f for f in os.listdir(_BACKUPS_DIR)
             if f.startswith(f"{user_id}_") and f.endswith(".zip")]
    if not files:
        return "📭 No backups found."
    lines = [f"• {f}" for f in sorted(files)]
    return "💾 <b>Available Backups:</b>\n" + "\n".join(lines)

# ============================================================================
# ENVIRONMENT VARIABLE MANAGEMENT
# ============================================================================

_ENV_FILE = os.path.join(WORKSPACE_DIR, ".env")
os.makedirs(os.path.dirname(_ENV_FILE), exist_ok=True)


def _env_set(key: str, value: str) -> str:
    try:
        lines = []
        if os.path.exists(_ENV_FILE):
            with open(_ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"{key}={value}\n")
        with open(_ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return f"✅ Environment variable set: {key}={value}"
    except Exception as e:
        return f"❌ Failed to set env var: {e}"


def _env_get(key: str) -> str:
    if not os.path.exists(_ENV_FILE):
        return "❌ .env file not found."
    with open(_ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith(f"{key}="):
                return line.strip().split("=", 1)[1]
    return f"❌ Environment variable not found: {key}"


def _env_list() -> str:
    if not os.path.exists(_ENV_FILE):
        return "📭 No .env file found."
    with open(_ENV_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    if not lines:
        return "📭 No environment variables defined."
    return "🔧 <b>Environment Variables:</b>\n" + "\n".join(lines)

# ============================================================================
# API TESTING
# ============================================================================

def _api_test(url: str, method: str = "GET",
              headers: Optional[dict] = None,
              body: Optional[str] = None) -> str:
    try:
        req = urllib.request.Request(url, method=method, data=body.encode() if body else None)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            resp_headers = dict(resp.headers)
            content = resp.read().decode("utf-8", errors="replace")
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            result = f"✅ API Test: {method} {url}\n"
            result += f"<b>Status:</b> {status}\n"
            result += f"<b>Content-Type:</b> {resp_headers.get('Content-Type', 'Unknown')}\n"
            result += f"<b>Response:</b>\n<pre>{content}</pre>"
            return result
    except urllib.error.HTTPError as e:
        return f"❌ API Error {e.code}: {e.reason}\nURL: {url}"
    except Exception as e:
        return f"❌ API Test failed: {e}"

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

import psutil


def _get_performance() -> str:
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(WORKSPACE_DIR)
        result = f"🖥️ <b>System Performance</b>\n\n"
        result += f"<b>CPU Usage:</b> {cpu}%\n"
        result += f"<b>Memory:</b> {mem.percent}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)\n"
        result += f"<b>Disk:</b> {disk.percent}% ({disk.used // (1024**2)}GB / {disk.total // (1024**2)}GB)\n"
        result += f"<b>Boot Time:</b> {datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}"
        return result
    except Exception as e:
        return f"❌ Performance check failed: {e}"


# ============================================================================
# AUTO-DEPLOYMENT
# ============================================================================

def _auto_deploy(project_type: str) -> str:
    try:
        if project_type in ("npm", "node", "express", "react"):
            res = terminal_run_cmd("npm install && npm run build 2>&1", admin=True)
            return f"🚀 <b>Deploy: {project_type}</b>\n\n{res['output']}"
        elif project_type in ("python", "flask", "fastapi"):
            res = terminal_run_cmd("pip install -r requirements.txt 2>&1", admin=True)
            return f"🚀 <b>Deploy: {project_type}</b>\n\n{res['output']}"
        else:
            return f"❌ Unknown project type: {project_type}"
    except Exception as e:
        return f"❌ Deploy failed: {e}"


def terminal_run_cmd(cmd: str, admin: bool = False) -> dict:
    temp_db = Database(db_path=DB_PATH)
    term = TerminalEngine(workspace=WORKSPACE_DIR, db=temp_db)
    return term.run(0, cmd, admin=admin)

# ============================================================================
# GLOBAL STATE
# ============================================================================

_active_tasks: Dict[int, int] = {}
_editing_file: Dict[int, str] = {}
_creating_skill: Dict[int, str] = {}
_creating_tool: Dict[int, str] = {}
_waiting_confirm: Dict[int, dict] = {}
_skill_create_step: Dict[int, str] = {}
_skill_create_data: Dict[int, dict] = {}
_tool_create_step: Dict[int, str] = {}
_tool_create_data: Dict[int, dict] = {}
_website_servers: Dict[int, dict] = {}
_website_previews: Dict[int, str] = {}

# ============================================================================
# HELPERS
# ============================================================================

def _safe_path(path: str) -> str:
    safe = os.path.normpath(path)
    if safe.startswith("..") or os.path.isabs(safe):
        safe = os.path.basename(path)
    return os.path.join(WORKSPACE_DIR, safe)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _gather_workspace_context() -> str:
    try:
        entries: List[str] = []
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            dirs[:] = [d for d in dirs
                       if not d.startswith(".")
                       and d not in {"node_modules", "__pycache__", ".git"}]
            for f in files:
                if f.startswith("."):
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, WORKSPACE_DIR)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                entries.append(f"{rel} ({size} bytes)")
        if not entries:
            return "(workspace is empty)"
        return "\n".join(entries[:100])
    except Exception as e:
        logger.error("Workspace context error: %s", e)
        return "(could not read workspace)"

# ============================================================================
# KEYBOARD BUILDERS - All features as buttons
# ============================================================================

def _main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 File Operations", callback_data="menu_files"),
            InlineKeyboardButton("💻 Terminal", callback_data="menu_terminal"),
        ],
        [
            InlineKeyboardButton("🤖 Agent", callback_data="menu_agent"),
            InlineKeyboardButton("🧠 Skills", callback_data="menu_skills"),
        ],
        [
            InlineKeyboardButton("🔧 Tools", callback_data="menu_tools"),
            InlineKeyboardButton("📋 Tasks", callback_data="menu_tasks"),
        ],
        [
            InlineKeyboardButton("🌐 Website", callback_data="menu_website"),
            InlineKeyboardButton("🗄️ Database", callback_data="menu_database"),
        ],
        [
            InlineKeyboardButton("💾 Backup", callback_data="menu_backup"),
            InlineKeyboardButton("🖥️ Env", callback_data="menu_env"),
        ],
        [
            InlineKeyboardButton("🔍 API / Translate", callback_data="menu_api"),
            InlineKeyboardButton("👮 Admin", callback_data="menu_admin"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="menu_help"),
            InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
        ],
    ])


def _files_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Read File", callback_data="file_read_prompt"),
            InlineKeyboardButton("✏️ Write File", callback_data="file_write_prompt"),
        ],
        [
            InlineKeyboardButton("📝 Edit File", callback_data="file_edit_prompt"),
            InlineKeyboardButton("📂 List Dir", callback_data="file_ls_prompt"),
        ],
        [
            InlineKeyboardButton("📁 Mkdir", callback_data="file_mkdir_prompt"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ])


def _terminal_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Run Command", callback_data="term_run_prompt"),
            InlineKeyboardButton("📦 npm Install", callback_data="term_npm_prompt"),
        ],
        [
            InlineKeyboardButton("🐍 pip Install", callback_data="term_pip_prompt"),
            InlineKeyboardButton("🌿 Git", callback_data="term_git_prompt"),
        ],
        [
            InlineKeyboardButton("🏗️ Build", callback_data="term_build"),
            InlineKeyboardButton("🧪 Test", callback_data="term_test"),
        ],
        [
            InlineKeyboardButton("🕒 History", callback_data="term_history"),
            InlineKeyboardButton("📂 List Dir", callback_data="term_ls"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
    ])


def _agent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Start Agent", callback_data="agent_run_prompt"),
            InlineKeyboardButton("📊 Status", callback_data="menu_agent_status"),
        ],
        [
            InlineKeyboardButton("⛔ Cancel", callback_data="agent_cancel_prompt"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ])


def _skills_keyboard(skills: List[dict]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for s in skills[:10]:
        row.append(InlineKeyboardButton(f"🧠 {s['name']}", callback_data=f"skill_run:{s['name']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton("➕ Create Skill", callback_data="skill_create_prompt"),
        InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
    ])
    return InlineKeyboardMarkup(buttons)


def _tools_keyboard(tools: List[dict]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(f"🔧 {t['name']}", callback_data=f"tool_run:{t['name']}")] for t in tools[:10]]
    buttons.append([
        InlineKeyboardButton("➕ Create Tool", callback_data="tool_create_prompt"),
        InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
    ])
    return InlineKeyboardMarkup(buttons)


def _tasks_keyboard(tasks: List[dict]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(f"📋 {t['name']}", callback_data=f"task_run:{t['name']}")] for t in tasks[:10]]
    buttons.append([
        InlineKeyboardButton("💾 Save Task", callback_data="task_save_prompt"),
        InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
    ])
    return InlineKeyboardMarkup(buttons)


def _website_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👁️ Preview", callback_data="web_preview_prompt"),
            InlineKeyboardButton("🖥️ Start Server", callback_data="web_server_start_prompt"),
        ],
        [
            InlineKeyboardButton("⛔ Stop Server", callback_data="web_server_stop"),
            InlineKeyboardButton("📊 Server Status", callback_data="web_server_status"),
        ],
        [
            InlineKeyboardButton("📸 Screenshot", callback_data="web_screenshot_prompt"),
            InlineKeyboardButton("🚇 Tunnel", callback_data="web_tunnel_prompt"),
        ],
        [
            InlineKeyboardButton("🌐 Website Status", callback_data="web_status_prompt"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ])


def _database_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Connect DB", callback_data="db_connect_prompt"),
            InlineKeyboardButton("🔍 DB Query", callback_data="db_query_prompt"),
        ],
        [
            InlineKeyboardButton("📋 List Connections", callback_data="db_list"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ])


def _backup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Create Backup", callback_data="backup_create_prompt"),
            InlineKeyboardButton("🔄 Restore", callback_data="backup_restore_prompt"),
        ],
        [
            InlineKeyboardButton("📋 List Backups", callback_data="backup_list"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ])


def _env_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ Set Var", callback_data="env_set_prompt"),
            InlineKeyboardButton("🔍 Get Var", callback_data="env_get_prompt"),
        ],
        [
            InlineKeyboardButton("📋 List Vars", callback_data="env_list"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ])


def _api_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 API Test", callback_data="api_test_prompt"),
            InlineKeyboardButton("🔄 Translate Code", callback_data="translate_prompt"),
        ],
        [
            InlineKeyboardButton("🖥️ Performance", callback_data="performance_run"),
            InlineKeyboardButton("🚀 Deploy", callback_data="deploy_prompt"),
        ],
        [
            InlineKeyboardButton("💾 Auto Commit", callback_data="auto_commit_prompt"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ],
    ])


def _admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_prompt"),
        ],
        [
            InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_prompt"),
            InlineKeyboardButton("🔓 Unban User", callback_data="admin_unban_prompt"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
    ])


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_set:en"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
    ])


def _confirm_keyboard(action: str, payload: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{action}:{payload}"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirm_cancel"),
        ]
    ])


def _skill_create_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="menu_skills")]
    ])


def _tool_create_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="menu_tools")]
    ])

# ============================================================================
# RICH MESSAGE CONTENT
# ============================================================================

WELCOME_MESSAGE: str = (
    f"{EMOJI['bot']} <b>Professional Coding Agent Bot</b>\n"
    f"{EMOJI['gear']} <i>Ultimate Edition — Autonomous Coding Assistant</i>\n\n"
    "Welcome to your professional coding environment on Telegram.\n\n"
    f"{EMOJI['star']} <b>Capabilities:</b>\n"
    "• 📁 Professional file operations\n"
    "• 💻 Full terminal engine with skill integration\n"
    "• 🧠 Learnable skills & custom tools\n"
    "• 📋 Reusable task templates\n"
    "• 🤖 Autonomous AI coding agent\n"
    "• 👮 Administrative controls\n"
    "• 🌐 Website control & preview\n"
    "• 🗄️ Database management (MySQL/PostgreSQL/MongoDB)\n"
    "• 💾 Backup & restore\n"
    "\nSelect a module below to begin:"
)

HELP_MESSAGE: str = (
    f"{EMOJI['info']} <b>Professional Coding Agent Bot — Help Center</b>\n\n"
    f"{EMOJI['terminal']} <b>Terminal Engine:</b>\n"
    "/run <cmd> — Execute shell command\n"
    "/npm <pkg> — Install npm package\n"
    "/pip <pkg> — Install pip package\n"
    "/git <cmd> — Run git command\n"
    "/build — Build project\n"
    "/test — Run tests\n"
    "/history — Command history\n"
    "/ls [path] — List directory\n"
    "/mkdir <path> — Create directory\n\n"
    f"{EMOJI['skill']} <b>Skills System:</b>\n"
    "/skill list — List all skills\n"
    "/skill run <name> [args] — Execute skill\n"
    "/skill create <name> — Create new skill\n"
    "/skill delete <name> — Remove skill\n"
    "/skill info <name> — Skill details\n"
    "/auto-learn-skill <name> <desc> <code> — Auto learn skill\n"
    "/auto-create-tool <name> <desc> <code> — Auto create tool\n"
    "/auto-use-skill <name> <args> — Auto use skill\n"
    "/auto-use-tool <name> <args> — Auto use tool\n"
    "/push-repo <url> [msg] — Push to remote repo\n\n"
    f"{EMOJI['tool']} <b>Tools System:</b>\n"
    "/tool list — List all tools\n"
    "/tool run <name> [args] — Execute tool\n"
    "/tool create <name> — Create custom tool\n"
    "/tool delete <name> — Remove tool\n\n"
    f"{EMOJI['task']} <b>Task Templates:</b>\n"
    "/task save <name> — Save task template\n"
    "/task list — List saved tasks\n"
    "/task run <name> — Run saved task\n"
    "/task delete <name> — Remove template\n\n"
    f"{EMOJI['agent']} <b>Autonomous Agent:</b>\n"
    "/agent <task> — Start autonomous coding\n"
    "/status — Check agent progress\n"
    "/cancel — Cancel active task\n\n"
    f"{EMOJI['website']} <b>Website Control:</b>\n"
    "/preview <port> — Start website preview server\n"
    "/server-start <port> — Start preview server\n"
    "/server-stop — Stop preview server\n"
    "/server-status — Check server status\n"
    "/screenshot <url> — Capture website screenshot\n"
    "/tunnel <port> — Expose local server via tunnel\n"
    "/website-status <url> — Check website status\n\n"
    f"{EMOJI['db']} <b>Database:</b>\n"
    "/db-connect <type> <host> <port> <user> <pass> <db>\n"
    "/db-query <key> <sql>\n"
    "/db-list — List database connections\n\n"
    f"{EMOJI['plus']} <b>Backup & Restore:</b>\n"
    "/backup [name] — Create workspace backup\n"
    "/restore <name> — Restore a backup\n"
    "/backup-list — List available backups\n\n"
    f"{EMOJI['server']} <b>Environment Variables:</b>\n"
    "/env-set KEY=VALUE — Set env variable\n"
    "/env-get KEY — Get env variable\n"
    "/env-list — List all env variables\n\n"
    f"{EMOJI['search']} <b>API & Code Tools:</b>\n"
    "/api-test <url> [method] [body] — Test API endpoint\n"
    "/translate <from> <to> <file> — Translate code\n"
    "/performance — System performance metrics\n"
    "/deploy <type> — Auto deploy project\n"
    "/auto-commit [msg] — Auto commit changes\n\n"
    f"{EMOJI['file']} <b>File Operations:</b>\n"
    "/read <path> — Read file\n"
    "/write <path> <content> — Write file\n"
    "/edit <path> — Interactive edit\n\n"
    f"{EMOJI['stats']} <b>Project Tools:</b>\n"
    "/diff <path> — Git diff for file\n"
    "/lint — Run linter on project\n"
    "/deps — Show dependencies\n"
    "/init <type> — Scaffold project (npm/python)\n"
    "/review <path> — AI code review\n"
    "/docker <cmd> — Docker operations\n"
    "/format <path> — Format code file\n"
    "/search <pattern> — Search pattern in files\n"
    "/replace <path> <old> <new> — Replace string in file\n"
    "/branch <name> — Git branch operations\n"
    "/scaffold <template> — Scaffold project template\n"
    "/chain <tasks> — Chain multiple agent tasks\n"
    "/apk-build <path> — Build Android APK\n"
    "/apk-info <path> — Get APK info\n"
    "/apk-install <path> — Install APK\n"
    "/apk-decompile <path> — Decompile APK\n"
    "/apk-edit <dir> <file> <content> — Edit decompiled APK\n"
    "/apk-change <path> <desc> — Record APK change\n"
    "/apk-rebuild <dir> <output> — Rebuild APK\n"
    "/sandbox-run <cmd> — Run in sandbox\n"
    "/sandbox-list — List sandboxes\n\n"
    f"{EMOJI['admin']} <b>Admin Commands:</b>\n"
    "/stats — Bot statistics\n"
    "/broadcast <msg> — Broadcast to all users\n"
    "/ban <user_id> — Ban user\n"
    "/unban <user_id> — Unban user\n"
)

# ============================================================================
# HANDLERS
# ============================================================================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db: Database = context.bot_data["db"]
    db.upsert_user(user.id, user.username, user.first_name, user.last_name)
    logger.info("User %d started", user.id)

    await context.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help center"),
        BotCommand("run", "Run terminal command"),
        BotCommand("agent", "Autonomous coding agent"),
        BotCommand("skill", "Manage skills"),
        BotCommand("tool", "Manage tools"),
        BotCommand("task", "Manage task templates"),
        BotCommand("stats", "Bot statistics (admin)"),
        BotCommand("diff", "Show git diff for file"),
        BotCommand("lint", "Run linter on project"),
        BotCommand("deps", "Show project dependencies"),
        BotCommand("init", "Scaffold new project"),
        BotCommand("review", "AI code review for file"),
        BotCommand("docker", "Docker operations"),
        BotCommand("format", "Format code file"),
        BotCommand("search", "Search pattern in files"),
        BotCommand("replace", "Replace string in file"),
        BotCommand("branch", "Git branch operations"),
        BotCommand("scaffold", "Scaffold project template"),
        BotCommand("chain", "Chain multiple agent tasks"),
        BotCommand("apk-build", "Build Android APK"),
        BotCommand("apk-info", "Get APK info"),
        BotCommand("apk-install", "Install APK"),
        BotCommand("apk-decompile", "Decompile APK"),
        BotCommand("apk-edit", "Edit decompiled APK"),
        BotCommand("apk-change", "Record APK change"),
        BotCommand("apk-rebuild", "Rebuild APK"),
        BotCommand("sandbox-run", "Run in sandbox"),
        BotCommand("sandbox-list", "List sandboxes"),
        BotCommand("skill-export", "Export skill to JSON"),
        BotCommand("skill-import", "Import skill from JSON"),
        BotCommand("auto-learn-skill", "Auto learn skill"),
        BotCommand("auto-create-tool", "Auto create tool"),
        BotCommand("auto-use-skill", "Auto use skill"),
        BotCommand("auto-use-tool", "Auto use tool"),
        BotCommand("push-repo", "Push to remote repo"),
        BotCommand("preview", "Start website preview server"),
        BotCommand("server-start", "Start preview server"),
        BotCommand("server-stop", "Stop preview server"),
        BotCommand("server-status", "Check server status"),
        BotCommand("screenshot", "Capture website screenshot"),
        BotCommand("tunnel", "Expose local server via tunnel"),
        BotCommand("website-status", "Check website status"),
        BotCommand("lang", "Set language (en/my)"),
        BotCommand("db-connect", "Connect to database"),
        BotCommand("db-query", "Run database query"),
        BotCommand("db-list", "List DB connections"),
        BotCommand("backup", "Create backup"),
        BotCommand("restore", "Restore backup"),
        BotCommand("backup-list", "List backups"),
        BotCommand("env-set", "Set env variable"),
        BotCommand("env-get", "Get env variable"),
        BotCommand("env-list", "List env variables"),
        BotCommand("api-test", "Test API endpoint"),
        BotCommand("translate", "Translate code"),
        BotCommand("performance", "System performance"),
        BotCommand("deploy", "Auto deploy project"),
        BotCommand("auto-commit", "Auto commit changes"),
    ], scope=BotCommandScopeAllPrivateChats())

    await update.effective_message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=_main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        HELP_MESSAGE,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
        ]),
        parse_mode=ParseMode.HTML,
    )


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("🔒 Admin access required.", parse_mode=ParseMode.HTML)
        return
    db: Database = context.bot_data["db"]
    s = db.get_stats()
    rows = [
        [f"{EMOJI['info']} Users", str(s["total_users"]), f"{EMOJI['ban']} Banned", str(s["banned_users"])],
        [f"{EMOJI['skill']} Skills", str(s["total_skills"]), f"{EMOJI['tool']} Tools", str(s["total_tools"])],
        [f"{EMOJI['task']} Templates", str(s["total_task_templates"]), f"{EMOJI['terminal']} Commands", str(s["total_commands"])],
        [f"{EMOJI['check']} Successful", str(s["successful_commands"]), f"{EMOJI['pending']} Pending", str(s["pending_tasks"])],
        [f"{EMOJI['running']} Running", str(s["running_tasks"]), f"{EMOJI['completed']} Completed", str(s["completed_tasks"])],
    ]
    table = _rich_table(["Metric", "Value", "Metric", "Value"], rows)
    await update.effective_message.reply_text(
        f"{EMOJI['stats']} <b>Bot Statistics Dashboard</b>\n\n{table}",
        parse_mode=ParseMode.HTML,
    )


async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("🔒 Admin access required.", parse_mode=ParseMode.HTML)
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /broadcast <message>", parse_mode=ParseMode.HTML)
        return
    text = " ".join(context.args)
    db: Database = context.bot_data["db"]
    import sqlite3 as _sq
    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row
    rows = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
    conn.close()
    sent = failed = 0
    for row in rows:
        try:
            await context.bot.send_message(
                chat_id=row["user_id"],
                text=f"📢 <b>Broadcast Message</b>\n\n{text}",
                parse_mode=ParseMode.HTML,
            )
            sent += 1
        except Exception as e:
            logger.warning("Broadcast fail %d: %s", row["user_id"], e)
            failed += 1
    await update.effective_message.reply_text(
        f"📢 <b>Broadcast Complete</b>\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )


async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("🔒 Admin access required.", parse_mode=ParseMode.HTML)
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /ban <user_id>", parse_mode=ParseMode.HTML)
        return
    try:
        tid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ Invalid user ID.", parse_mode=ParseMode.HTML)
        return
    db: Database = context.bot_data["db"]
    db.upsert_user(tid)
    db.ban_user(tid)
    await update.effective_message.reply_text(f"🚫 User {tid} banned.", parse_mode=ParseMode.HTML)


async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("🔒 Admin access required.", parse_mode=ParseMode.HTML)
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /unban <user_id>", parse_mode=ParseMode.HTML)
        return
    try:
        tid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ Invalid user ID.", parse_mode=ParseMode.HTML)
        return
    db: Database = context.bot_data["db"]
    db.upsert_user(tid)
    db.unban_user(tid)
    await update.effective_message.reply_text(f"🔓 User {tid} unbanned.", parse_mode=ParseMode.HTML)

# -------------------- Terminal --------------------

async def run_cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db: Database = context.bot_data["db"]
    rl: RateLimiter = context.bot_data["rate_limiter"]
    term: TerminalEngine = context.bot_data["terminal"]
    if not rl.is_allowed(user.id):
        await update.effective_message.reply_text(
            f"⏳ Rate limit exceeded. ({rl.get_remaining(user.id)} calls remaining)",
            parse_mode=ParseMode.HTML,
        )
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /run <command>", parse_mode=ParseMode.HTML)
        return
    cmd = " ".join(context.args)
    res = term.run(user.id, cmd, admin=(user.id in ADMIN_IDS))
    emoji = EMOJI['success'] if res["success"] else EMOJI['error']
    rows = [["Command", cmd], ["Exit Code", str(res["exit_code"])], ["Status", "Success" if res["success"] else "Failed"]]
    table = _rich_table(["Field", "Value"], rows)
    await update.effective_message.reply_text(
        f"{emoji} <b>Terminal Result</b>\n\n{table}\n\n<b>Output:</b>\n<pre>{res['output']}</pre>",
        parse_mode=ParseMode.HTML,
    )


async def npm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /npm <package>", parse_mode=ParseMode.HTML)
        return
    context.args = [f"npm install {context.args[0]}"]
    await run_cmd_handler(update, context)


async def pip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /pip <package>", parse_mode=ParseMode.HTML)
        return
    context.args = [f"pip install {context.args[0]}"]
    await run_cmd_handler(update, context)


async def git_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /git <command>", parse_mode=ParseMode.HTML)
        return
    context.args = ["git " + " ".join(context.args)]
    await run_cmd_handler(update, context)


async def build_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.args = ["npm run build 2>&1 || pip install -r requirements.txt 2>&1 || echo 'No build script found'"]
    await run_cmd_handler(update, context)


async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.args = ["npm test 2>&1 || pytest 2>&1 || echo 'No test script found'"]
    await run_cmd_handler(update, context)


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    term: TerminalEngine = context.bot_data["terminal"]
    hist = term.get_history(15)
    if not hist:
        await update.effective_message.reply_text("🕒 No command history.", parse_mode=ParseMode.HTML)
        return
    rows = [[h["command"], EMOJI['success'] if h["success"] else EMOJI['error'], str(h["exit_code"])] for h in hist]
    table = _rich_table(["Command", "Status", "Exit"], rows)
    await update.effective_message.reply_text(
        f"{EMOJI['history']} <b>Recent Command History</b>\n\n{table}",
        parse_mode=ParseMode.HTML,
    )


async def ls_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    path = context.args[0] if context.args else "."
    sp = _safe_path(path)
    try:
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ Not found: {path}", parse_mode=ParseMode.HTML)
            return
        entries = sorted(os.listdir(sp))
        if not entries:
            await update.effective_message.reply_text(f"📂 {path} is empty.", parse_mode=ParseMode.HTML)
            return
        rows = [[e, "File" if os.path.isfile(os.path.join(sp, e)) else "Dir"] for e in entries[:50]]
        table = _rich_table(["Name", "Type"], rows)
        await update.effective_message.reply_text(
            f"📂 <b>{path}</b>\n\n{table}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await update.effective_message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)


async def mkdir_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /mkdir <path>", parse_mode=ParseMode.HTML)
        return
    sp = _safe_path(context.args[0])
    try:
        os.makedirs(sp, exist_ok=True)
        await update.effective_message.reply_text(f"✅ Created: {context.args[0]}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.effective_message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)

# -------------------- File ops --------------------

async def read_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /read <path>", parse_mode=ParseMode.HTML)
        return
    sp = _safe_path(context.args[0])
    try:
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ Not found: {context.args[0]}", parse_mode=ParseMode.HTML)
            return
        if os.path.isdir(sp):
            await update.effective_message.reply_text(f"📂 {context.args[0]} is a directory.", parse_mode=ParseMode.HTML)
            return
        with open(sp, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 3500:
            content = content[:3500] + "\n... (truncated)"
        await update.effective_message.reply_text(
            f"📖 <b>{context.args[0]}</b>\n\n<pre>{content}</pre>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error("Read error: %s", e)
        await update.effective_message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)


async def write_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: /write <path> <content>", parse_mode=ParseMode.HTML)
        return
    sp = _safe_path(context.args[0])
    content = " ".join(context.args[1:])
    try:
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        with open(sp, "w", encoding="utf-8") as f:
            f.write(content)
        await update.effective_message.reply_text(
            f"✅ Written: {context.args[0]}\n({len(content)} bytes)"
        )
    except Exception as e:
        logger.error("Write error: %s", e)
        await update.effective_message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)


async def edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /edit <path>", parse_mode=ParseMode.HTML)
        return
    fp = context.args[0]
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Read", callback_data=f"edit_read:{fp}"),
            InlineKeyboardButton("✏️ Write", callback_data=f"edit_write:{fp}"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")],
    ])
    await update.effective_message.reply_text(
        f"📝 <b>Edit File</b>\n<code>{fp}</code>\nChoose an action:",
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )

# -------------------- Callback (Rich Menus) --------------------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q:
        return
    await q.answer()
    data = q.data or ""
    user = update.effective_user
    uid = user.id if user else 0

    # ===== MAIN MENU =====
    if data == "menu_main":
        await q.edit_message_text(
            WELCOME_MESSAGE,
            reply_markup=_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== FILE MENU =====
    if data == "menu_files":
        await q.edit_message_text(
            f"{EMOJI['file']} <b>File Operations</b>\n\nChoose an action below:",
            reply_markup=_files_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "file_read_prompt":
        await q.edit_message_text(
            f"{EMOJI['read']} <b>Read File</b>\n\nSend the file path you want to read:",
            reply_markup=ForceReply(selective=True),
            parse_mode=ParseMode.HTML,
        )
        _waiting_confirm[uid] = {"action": "file_read"}
        return

    if data == "file_write_prompt":
        await q.edit_message_text(
            f"{EMOJI['write']} <b>Write File</b>\n\nSend: <code>/write &lt;path&gt; &lt;content&gt;</code>",
            reply_markup=_files_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "file_edit_prompt":
        await q.edit_message_text(
            f"{EMOJI['edit']} <b>Edit File</b>\n\nSend: <code>/edit &lt;path&gt;</code>",
            reply_markup=_files_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "file_ls_prompt":
        await q.edit_message_text(
            f"{EMOJI['folder']} <b>List Directory</b>\n\nSend: <code>/ls [path]</code>",
            reply_markup=_files_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "file_mkdir_prompt":
        await q.edit_message_text(
            f"{EMOJI['plus']} <b>Make Directory</b>\n\nSend: <code>/mkdir &lt;path&gt;</code>",
            reply_markup=_files_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== TERMINAL MENU =====
    if data == "menu_terminal":
        await q.edit_message_text(
            f"{EMOJI['terminal']} <b>Terminal Engine</b>\n\nChoose a command category:",
            reply_markup=_terminal_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "term_run_prompt":
        await q.edit_message_text(
            f"{EMOJI['arrow']} <b>Run Command</b>\n\nSend your terminal command now:",
            reply_markup=ForceReply(selective=True),
            parse_mode=ParseMode.HTML,
        )
        _waiting_confirm[uid] = {"action": "term_run"}
        return

    if data == "term_npm_prompt":
        await q.edit_message_text(
            f"{EMOJI['npm']} <b>npm Install</b>\n\nSend: <code>/npm &lt;package&gt;</code>",
            reply_markup=_terminal_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "term_pip_prompt":
        await q.edit_message_text(
            f"{EMOJI['pip']} <b>pip Install</b>\n\nSend: <code>/pip &lt;package&gt;</code>",
            reply_markup=_terminal_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "term_git_prompt":
        await q.edit_message_text(
            f"{EMOJI['git']} <b>Git</b>\n\nSend: <code>/git &lt;command&gt;</code>",
            reply_markup=_terminal_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "term_build":
        context.args = ["npm run build 2>&1 || pip install -r requirements.txt 2>&1 || echo 'No build script found'"]
        await run_cmd_handler(update, context)
        return

    if data == "term_test":
        context.args = ["npm test 2>&1 || pytest 2>&1 || echo 'No test script found'"]
        await run_cmd_handler(update, context)
        return

    if data == "term_history":
        term: TerminalEngine = context.bot_data["terminal"]
        hist = term.get_history(15)
        if not hist:
            await q.edit_message_text(f"{EMOJI['history']} No history.", parse_mode=ParseMode.HTML)
            return
        rows = [[h["command"], EMOJI['success'] if h["success"] else EMOJI['error'], str(h["exit_code"])] for h in hist]
        table = _rich_table(["Command", "Status", "Exit"], rows)
        await q.edit_message_text(
            f"{EMOJI['history']} <b>Command History</b>\n\n{table}",
            reply_markup=_terminal_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "term_ls":
        entries = sorted(os.listdir(WORKSPACE_DIR))[:50]
        rows = [[e, "File" if os.path.isfile(os.path.join(WORKSPACE_DIR, e)) else "Dir"] for e in entries]
        table = _rich_table(["Name", "Type"], rows)
        await q.edit_message_text(
            f"{EMOJI['folder']} <b>{WORKSPACE_DIR}</b>\n\n{table}",
            reply_markup=_terminal_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== AGENT MENU =====
    if data == "menu_agent":
        await q.edit_message_text(
            f"{EMOJI['agent']} <b>Autonomous Agent</b>\n\n"
            "Use /agent <task description> to start an autonomous coding task.\n\n"
            "The agent will:\n"
            "• Read existing files\n"
            "• Plan and write code\n"
            "• Run tests and fix errors\n"
            "• Report progress step by step",
            reply_markup=_agent_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "agent_run_prompt":
        await q.edit_message_text(
            f"{EMOJI['arrow']} <b>Start Agent Task</b>\n\n"
            "Send: <code>/agent &lt;task description&gt;</code>",
            reply_markup=_agent_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "agent_cancel_prompt":
        await q.edit_message_text(
            f"{EMOJI['cross']} <b>Cancel Task</b>\n\nSend: <code>/cancel</code>",
            reply_markup=_agent_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "menu_agent_status":
        db: Database = context.bot_data["db"]
        tid = _active_tasks.get(uid)
        if not tid:
            await q.edit_message_text(
                f"{EMOJI['info']} No active task.",
                reply_markup=_agent_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return
        task = db.get_task(tid)
        if not task:
            await q.edit_message_text(f"{EMOJI['error']} Task not found.", parse_mode=ParseMode.HTML)
            return
        emo = {"pending": EMOJI['pending'], "running": EMOJI['running'],
               "completed": EMOJI['completed'], "failed": EMOJI['failed']}.get(task["status"], EMOJI['info'])
        msg = (
            f"{emo} <b>Task Status</b>\n\n"
            f"<b>ID:</b> {tid}\n"
            f"<b>Type:</b> {task['task_type']}\n"
            f"<b>Status:</b> {_status_badge(task['status'])}\n"
            f"<b>Created:</b> {task['created_at']}\n"
        )
        if task.get("result"):
            msg += f"\n<b>Result:</b>\n{task['result'][:1200]}"
        await q.edit_message_text(msg, parse_mode=ParseMode.HTML)
        return

    # ===== SKILLS MENU =====
    if data == "menu_skills":
        reg: SkillRegistry = context.bot_data["skills"]
        skills = reg.list()
        if not skills:
            await q.edit_message_text(
                f"{EMOJI['skill']} No skills available.",
                reply_markup=_main_menu_keyboard(),
            )
            return
        await q.edit_message_text(
            f"{EMOJI['skill']} <b>Skills Library</b>\n\nClick a skill to execute it:",
            reply_markup=_skills_keyboard(skills),
            parse_mode=ParseMode.HTML,
        )
        return

    if data.startswith("skill_run:"):
        name = data.split(":", 1)[1]
        reg: SkillRegistry = context.bot_data["skills"]
        s = reg.get(name)
        if not s:
            await q.edit_message_text(f"{EMOJI['error']} Skill not found.", parse_mode=ParseMode.HTML)
            return
        result = s.run()
        await q.edit_message_text(
            f"{EMOJI['skill']} <b>Skill: {name}</b>\n"
            f"{EMOJI['info']} {s.description}\n\n"
            f"<pre>{result[:2500]}</pre>",
            reply_markup=_skills_keyboard(reg.list()),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "skill_create_prompt":
        await q.edit_message_text(
            f"{EMOJI['plus']} <b>Create New Skill</b>\n\n"
            "Send: <code>/skill create &lt;name&gt;</code>",
            reply_markup=_skill_create_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== TOOLS MENU =====
    if data == "menu_tools":
        reg: ToolRegistry = context.bot_data["tools"]
        tools = reg.list()
        if not tools:
            await q.edit_message_text(
                f"{EMOJI['tool']} No tools available.",
                reply_markup=_main_menu_keyboard(),
            )
            return
        buttons = [[InlineKeyboardButton(f"🔧 {t['name']}", callback_data=f"tool_run:{t['name']}")] for t in tools[:10]]
        buttons.append([
            InlineKeyboardButton("➕ Create Tool", callback_data="tool_create_prompt"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ])
        await q.edit_message_text(
            f"{EMOJI['tool']} <b>Tools Library</b>\n\nClick a tool to execute it:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
        )
        return

    if data.startswith("tool_run:"):
        name = data.split(":", 1)[1]
        reg: ToolRegistry = context.bot_data["tools"]
        t = reg.get(name)
        if not t:
            await q.edit_message_text(f"{EMOJI['error']} Tool not found.", parse_mode=ParseMode.HTML)
            return
        result = t.run()
        await q.edit_message_text(
            f"{EMOJI['tool']} <b>Tool: {name}</b>\n"
            f"{EMOJI['info']} {t.description}\n\n"
            f"<pre>{result[:2500]}</pre>",
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "tool_create_prompt":
        await q.edit_message_text(
            f"{EMOJI['plus']} <b>Create Tool</b>\n\n"
            "Send: <code>/tool create &lt;name&gt;</code>",
            reply_markup=_tool_create_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== TASKS MENU =====
    if data == "menu_tasks":
        tm: TaskTemplateManager = context.bot_data["task_manager"]
        tasks = tm.list()
        if not tasks:
            await q.edit_message_text(
                f"{EMOJI['task']} No task templates.",
                reply_markup=_main_menu_keyboard(),
            )
            return
        buttons = [[InlineKeyboardButton(f"📋 {t['name']}", callback_data=f"task_run:{t['name']}")] for t in tasks[:10]]
        buttons.append([
            InlineKeyboardButton("💾 Save Task", callback_data="task_save_prompt"),
            InlineKeyboardButton("🔙 Back", callback_data="menu_main"),
        ])
        await q.edit_message_text(
            f"{EMOJI['task']} <b>Task Templates</b>\n\nClick a template to run it:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
        )
        return

    if data.startswith("task_run:"):
        name = data.split(":", 1)[1]
        tm: TaskTemplateManager = context.bot_data["task_manager"]
        tpl = tm.get(name)
        if not tpl:
            await q.edit_message_text(f"{EMOJI['error']} Template not found.", parse_mode=ParseMode.HTML)
            return
        await q.edit_message_text(
            f"{EMOJI['agent']} <b>Running Template</b>\n\n"
            f"<b>{name}</b>\n"
            f"Type: {tpl['task_type']}\n"
            f"Description: {tpl['description']}\n\n"
            f"{EMOJI['running']} Executing...",
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "task_save_prompt":
        await q.edit_message_text(
            f"{EMOJI['plus']} <b>Save Task</b>\n\nSend: <code>/task save &lt;name&gt;</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_tasks")]]),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== WEBSITE MENU =====
    if data == "menu_website":
        await q.edit_message_text(
            f"{EMOJI['website']} <b>Website Control</b>\n\nChoose an action:",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "web_preview_prompt":
        await q.edit_message_text(
            f"{EMOJI['preview']} <b>Preview Website</b>\n\nSend: <code>/preview &lt;port&gt;</code>",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "web_server_start_prompt":
        await q.edit_message_text(
            f"{EMOJI['server']} <b>Start Server</b>\n\nSend: <code>/server-start &lt;port&gt;</code>",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "web_server_stop":
        if uid not in _website_servers:
            await q.edit_message_text(
                f"{EMOJI['error']} No server running.",
                reply_markup=_website_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return
        server_info = _website_servers.pop(uid)
        try:
            server_info["process"].terminate()
        except Exception:
            pass
        await q.edit_message_text(
            f"{EMOJI['server']} <b>Server Stopped</b>\n\n"
            f"<b>Port:</b> {server_info['port']}\n"
            f"<b>URL was:</b> {server_info['url']}",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "web_server_status":
        if uid not in _website_servers:
            await q.edit_message_text(
                f"{EMOJI['error']} No server running.",
                reply_markup=_website_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return
        info = _website_servers[uid]
        await q.edit_message_text(
            f"{EMOJI['server']} <b>Server Status</b>\n\n"
            f"<b>URL:</b> {info['url']}\n"
            f"<b>Port:</b> {info['port']}\n"
            f"<b>Directory:</b> {info['directory']}\n"
            f"<b>Started:</b> {info['started_at']}",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "web_screenshot_prompt":
        await q.edit_message_text(
            f"{EMOJI['screenshot']} <b>Screenshot</b>\n\nSend: <code>/screenshot &lt;url&gt;</code>",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "web_tunnel_prompt":
        await q.edit_message_text(
            f"{EMOJI['tunnel']} <b>Tunnel</b>\n\nSend: <code>/tunnel &lt;port&gt;</code>",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "web_status_prompt":
        await q.edit_message_text(
            f"{EMOJI['website']} <b>Website Status</b>\n\nSend: <code>/website-status &lt;url&gt;</code>",
            reply_markup=_website_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== DATABASE MENU =====
    if data == "menu_database":
        await q.edit_message_text(
            f"{EMOJI['db']} <b>Database</b>\n\nChoose an action:",
            reply_markup=_database_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "db_connect_prompt":
        await q.edit_message_text(
            f"{EMOJI['info']} <b>Connect DB</b>\n\nSend: <code>/db-connect &lt;type&gt; <host> <port> <user> <password> <database></code>",
            reply_markup=_database_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "db_query_prompt":
        await q.edit_message_text(
            f"{EMOJI['search']} <b>DB Query</b>\n\nSend: <code>/db-query &lt;connection_key&gt; &lt;sql_query&gt;</code>",
            reply_markup=_database_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "db_list":
        result = db_manager.list_connections()
        await q.edit_message_text(result, parse_mode=ParseMode.HTML)
        return

    # ===== BACKUP MENU =====
    if data == "menu_backup":
        await q.edit_message_text(
            f"{EMOJI['plus']} <b>Backup & Restore</b>\n\nChoose an action:",
            reply_markup=_backup_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "backup_create_prompt":
        await q.edit_message_text(
            f"{EMOJI['plus']} <b>Create Backup</b>\n\nSend: <code>/backup [name]</code>",
            reply_markup=_backup_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "backup_restore_prompt":
        await q.edit_message_text(
            f"{EMOJI['cross']} <b>Restore</b>\n\nSend: <code>/restore &lt;backup_name&gt;</code>",
            reply_markup=_backup_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "backup_list":
        result = _list_backups(uid)
        await q.edit_message_text(result, parse_mode=ParseMode.HTML)
        return

    # ===== ENV MENU =====
    if data == "menu_env":
        await q.edit_message_text(
            f"{EMOJI['server']} <b>Environment</b>\n\nChoose an action:",
            reply_markup=_env_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "env_set_prompt":
        await q.edit_message_text(
            f"{EMOJI['plus']} <b>Set Env Var</b>\n\nSend: <code>/env-set KEY=VALUE</code>",
            reply_markup=_env_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "env_get_prompt":
        await q.edit_message_text(
            f"{EMOJI['search']} <b>Get Env Var</b>\n\nSend: <code>/env-get KEY</code>",
            reply_markup=_env_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "env_list":
        result = _env_list()
        await q.edit_message_text(result, parse_mode=ParseMode.HTML)
        return

    # ===== API MENU =====
    if data == "menu_api":
        await q.edit_message_text(
            f"{EMOJI['search']} <b>API & Code Tools</b>\n\nChoose an action:",
            reply_markup=_api_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "api_test_prompt":
        await q.edit_message_text(
            f"{EMOJI['search']} <b>API Test</b>\n\nSend: <code>/api-test &lt;url&gt; [method] [body]</code>",
            reply_markup=_api_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "translate_prompt":
        await q.edit_message_text(
            f"{EMOJI['info']} <b>Translate Code</b>\n\nSend: <code>/translate &lt;from_lang&gt; &lt;to_lang&gt; &lt;file_path&gt;</code>",
            reply_markup=_api_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "performance_run":
        result = _get_performance()
        await q.edit_message_text(result, parse_mode=ParseMode.HTML)
        return

    if data == "deploy_prompt":
        await q.edit_message_text(
            f"{EMOJI['rocket']} <b>Deploy</b>\n\nSend: <code>/deploy &lt;type&gt;</code>",
            reply_markup=_api_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "auto_commit_prompt":
        await q.edit_message_text(
            f"{EMOJI['success']} <b>Auto Commit</b>\n\nSend: <code>/auto-commit [message]</code>",
            reply_markup=_api_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== ADMIN MENU =====
    if data == "menu_admin":
        await q.edit_message_text(
            f"{EMOJI['admin']} <b>Admin Panel</b>\n\nChoose an action:",
            reply_markup=_admin_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "admin_broadcast_prompt":
        await q.edit_message_text(
            f"{EMOJI['broadcast']} <b>Broadcast</b>\n\nSend: <code>/broadcast &lt;message&gt;</code>",
            reply_markup=_admin_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "admin_ban_prompt":
        await q.edit_message_text(
            f"{EMOJI['ban']} <b>Ban User</b>\n\nSend: <code>/ban &lt;user_id&gt;</code>",
            reply_markup=_admin_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "admin_unban_prompt":
        await q.edit_message_text(
            f"{EMOJI['unban']} <b>Unban User</b>\n\nSend: <code>/unban &lt;user_id&gt;</code>",
            reply_markup=_admin_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== LANGUAGE MENU =====
    if data == "menu_lang":
        await q.edit_message_text(
            f"{EMOJI['info']} <b>Language</b>\n\nChoose your preferred language:",
            reply_markup=_lang_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data.startswith("lang_set:"):
        lang = data.split(":", 1)[1]
        if uid and lang in ("en", "my"):
            _user_lang[uid] = lang
            lang_name = "English" if lang == "en" else "Burmese"
            await q.edit_message_text(
                f"{EMOJI['success']} Language set to: {lang_name}",
                reply_markup=_main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        return

    if data == "menu_stats":
        db: Database = context.bot_data["db"]
        s = db.get_stats()
        rows = [
            [f"{EMOJI['info']} Users", str(s["total_users"]), f"{EMOJI['ban']} Banned", str(s["banned_users"])],
            [f"{EMOJI['skill']} Skills", str(s["total_skills"]), f"{EMOJI['tool']} Tools", str(s["total_tools"])],
            [f"{EMOJI['terminal']} Commands", str(s["total_commands"]), f"{EMOJI['pending']} Pending", str(s["pending_tasks"])],
        ]
        table = _rich_table(["Metric", "Value", "Metric", "Value"], rows)
        await q.edit_message_text(
            f"{EMOJI['stats']} <b>Statistics Dashboard</b>\n\n{table}",
            reply_markup=_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "menu_help":
        await q.edit_message_text(
            HELP_MESSAGE,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]),
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== EDIT CANCEL =====
    if data == "edit_cancel":
        await q.edit_message_text(f"{EMOJI['cross']} Edit cancelled.", parse_mode=ParseMode.HTML)
        return

    # ===== EDIT READ/WRITE CALLBACKS =====
    if data.startswith("edit_read:"):
        fp = data.split(":", 1)[1]
        sp = _safe_path(fp)
        try:
            with open(sp, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 3500:
                content = content[:3500] + "\n... (truncated)"
            await q.edit_message_text(
                f"{EMOJI['read']} <b>{fp}</b>\n\n<pre>{content}</pre>",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await q.edit_message_text(f"{EMOJI['error']} {e}", parse_mode=ParseMode.HTML)
        return

    if data.startswith("edit_write:"):
        fp = data.split(":", 1)[1]
        _editing_file[uid] = fp
        await q.edit_message_text(
            f"{EMOJI['write']} <b>Write Mode</b>\n\n"
            f"Send the new content for <code>{fp}</code> in your next message.",
            parse_mode=ParseMode.HTML,
        )
        return

    # ===== CONFIRM CALLBACKS =====
    if data.startswith("confirm:"):
        parts = data.split(":")
        action = parts[1]
        payload = parts[2] if len(parts) > 2 else ""
        if action == "cancel":
            _waiting_confirm.pop(uid, None)
            await q.edit_message_text(f"{EMOJI['cross']} Cancelled.", parse_mode=ParseMode.HTML)
            return
        _waiting_confirm.pop(uid, None)
        await q.edit_message_text(f"{EMOJI['check']} Confirmed: {action} {payload}", parse_mode=ParseMode.HTML)
        return

    if data == "confirm_cancel":
        _waiting_confirm.pop(uid, None)
        await q.edit_message_text(f"{EMOJI['cross']} Cancelled.", parse_mode=ParseMode.HTML)
        return

    logger.warning("Unknown callback: %s", data)


# Remaining handlers (skills, tools, tasks, agent, website, db, backup, env, api)

async def skill_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reg: SkillRegistry = context.bot_data["skills"]
    skills = reg.list()
    if not skills:
        await update.effective_message.reply_text("🧠 No skills available.", parse_mode=ParseMode.HTML)
        return
    lines = [f"• <b>{s['name']}</b> [{s.get('category','general')}] — {s['description']}" for s in skills]
    await update.effective_message.reply_text(
        f"{EMOJI['skill']} <b>Skills Library</b>\n\n" + "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )


async def skill_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /skill info <name>", parse_mode=ParseMode.HTML)
        return
    reg: SkillRegistry = context.bot_data["skills"]
    s = reg.get(context.args[0])
    if not s:
        await update.effective_message.reply_text("❌ Skill not found.", parse_mode=ParseMode.HTML)
        return
    await update.effective_message.reply_text(
        f"{EMOJI['skill']} <b>{s.name}</b> [{s.category}]\n{EMOJI['info']} {s.description}\n\n<code>{s.code[:1500]}</code>",
        parse_mode=ParseMode.HTML,
    )


async def skill_create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.effective_message.reply_text("Usage: /skill create <name>", parse_mode=ParseMode.HTML)
        return
    name = context.args[0]
    _skill_create_step[update.effective_user.id] = "desc"
    _skill_create_data[update.effective_user.id] = {"name": name}
    await update.effective_message.reply_text(
        f"{EMOJI['plus']} <b>Create Skill: {name}</b>\n\nStep 2/3: Send the skill description:",
        parse_mode=ParseMode.HTML,
    )


async def skill_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /skill delete <name>", parse_mode=ParseMode.HTML)
        return
    reg: SkillRegistry = context.bot_data["skills"]
    if reg.delete(context.args[0]):
        await update.effective_message.reply_text(f"🗑️ Deleted skill: {context.args[0]}", parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text("❌ Skill not found.", parse_mode=ParseMode.HTML)


async def skill_run_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.effective_message.reply_text("Usage: /skill run <name> [args...]", parse_mode=ParseMode.HTML)
        return
    name = context.args[0]
    args = context.args[1:]
    reg: SkillRegistry = context.bot_data["skills"]
    s = reg.get(name)
    if not s:
        await update.effective_message.reply_text("❌ Skill not found.", parse_mode=ParseMode.HTML)
        return
    result = s.run(*args)
    await update.effective_message.reply_text(
        f"{EMOJI['skill']} <b>Skill Result: {name}</b>\n<pre>{result}</pre>",
        parse_mode=ParseMode.HTML,
    )


async def tool_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reg: ToolRegistry = context.bot_data["tools"]
    tools = reg.list()
    if not tools:
        await update.effective_message.reply_text("🔧 No tools available.", parse_mode=ParseMode.HTML)
        return
    lines = [f"• <b>{t['name']}</b> — {t['description']}" for t in tools]
    await update.effective_message.reply_text(
        f"{EMOJI['tool']} <b>Tools Library</b>\n\n" + "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )


async def tool_create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.effective_message.reply_text("Usage: /tool create <name>", parse_mode=ParseMode.HTML)
        return
    name = context.args[0]
    _tool_create_step[update.effective_user.id] = "desc"
    _tool_create_data[update.effective_user.id] = {"name": name}
    await update.effective_message.reply_text(
        f"{EMOJI['plus']} <b>Create Tool: {name}</b>\n\nStep 2/3: Send the tool description:",
        parse_mode=ParseMode.HTML,
    )


async def tool_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /tool delete <name>", parse_mode=ParseMode.HTML)
        return
    reg: ToolRegistry = context.bot_data["tools"]
    if reg.delete(context.args[0]):
        await update.effective_message.reply_text(f"🗑️ Deleted tool: {context.args[0]}", parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text("❌ Tool not found.", parse_mode=ParseMode.HTML)


async def tool_run_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.effective_message.reply_text("Usage: /tool run <name> [args...]", parse_mode=ParseMode.HTML)
        return
    name = context.args[0]
    args = context.args[1:]
    reg: ToolRegistry = context.bot_data["tools"]
    t = reg.get(name)
    if not t:
        await update.effective_message.reply_text("❌ Tool not found.", parse_mode=ParseMode.HTML)
        return
    result = t.run(*args)
    await update.effective_message.reply_text(
        f"{EMOJI['tool']} <b>Tool Result: {name}</b>\n<pre>{result}</pre>",
        parse_mode=ParseMode.HTML,
    )


async def task_save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.effective_message.reply_text("Usage: /task save <name>", parse_mode=ParseMode.HTML)
        return
    name = context.args[0]
    user = update.effective_user
    tm: TaskTemplateManager = context.bot_data["task_manager"]
    tid = _active_tasks.get(user.id)
    if not tid:
        await update.effective_message.reply_text("ℹ️ No active task to save.", parse_mode=ParseMode.HTML)
        return
    db: Database = context.bot_data["db"]
    task = db.get_task(tid)
    if not task:
        await update.effective_message.reply_text("❌ Task not found.", parse_mode=ParseMode.HTML)
        return
    tm.save(name, task["task_type"], task["task_type"], {"task": task["task_type"]}, user.id)
    await update.effective_message.reply_text(f"💾 Task template saved: {name}", parse_mode=ParseMode.HTML)


async def task_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tm: TaskTemplateManager = context.bot_data["task_manager"]
    tasks = tm.list()
    if not tasks:
        await update.effective_message.reply_text("📋 No task templates.", parse_mode=ParseMode.HTML)
        return
    lines = [f"• <b>{t['name']}</b> — {t['description']} ({t['task_type']})" for t in tasks]
    await update.effective_message.reply_text(
        f"{EMOJI['task']} <b>Task Templates</b>\n\n" + "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )


async def task_run_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /task run <name>", parse_mode=ParseMode.HTML)
        return
    name = context.args[0]
    tm: TaskTemplateManager = context.bot_data["task_manager"]
    tpl = tm.get(name)
    if not tpl:
        await update.effective_message.reply_text("❌ Template not found.", parse_mode=ParseMode.HTML)
        return
    user = update.effective_user
    db: Database = context.bot_data["db"]
    ai: AIClient = context.bot_data["ai"]
    if not ai.is_available():
        await update.effective_message.reply_text("⚠️ AI provider not configured.", parse_mode=ParseMode.HTML)
        return
    tid = db.create_task(user.id, f"template:{name}")
    db.update_task(tid, "running")
    _active_tasks[user.id] = tid
    await update.effective_message.reply_text(
        f"🚀 Running template <b>{name}</b> (task {tid})...", parse_mode=ParseMode.HTML,
    )
    await _run_agent_loop(context, user.id, tid, tpl["description"])


async def task_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Usage: /task delete <name>", parse_mode=ParseMode.HTML)
        return
    tm: TaskTemplateManager = context.bot_data["task_manager"]
    if tm.delete(context.args[0]):
        await update.effective_message.reply_text(f"🗑️ Deleted template: {context.args[0]}", parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text("❌ Template not found.", parse_mode=ParseMode.HTML)
# ============================================================================
# AGENT - Multi-Step with Self-Correction
# ============================================================================

ACT_READ = "READ"
ACT_WRITE = "WRITE"
ACT_RUN = "RUN"
ACT_TEST = "TEST"
ACT_FIX = "FIX"
ACT_COMPLETE = "COMPLETE"
ACT_GIT = "GIT"
ACT_DIFF = "DIFF"
ACT_LINT = "LINT"
ACT_INIT = "INIT"
ACT_DEPS = "DEPS"
ACT_REVIEW = "REVIEW"
ACT_DOCKER = "DOCKER"
ACT_FORMAT = "FORMAT"
ACT_SEARCH = "SEARCH"
ACT_REPLACE = "REPLACE"
ACT_BRANCH = "BRANCH"
ACT_SCAFFOLD = "SCAFFOLD"
ACT_CHAIN = "CHAIN"
ACT_PREVIEW = "PREVIEW"
ACT_SERVER_START = "SERVER_START"
ACT_SERVER_STOP = "SERVER_STOP"
ACT_SERVER_STATUS = "SERVER_STATUS"
ACT_SCREENSHOT = "SCREENSHOT"
ACT_TUNNEL = "TUNNEL"
ACT_WEBSITE_STATUS = "WEBSITE_STATUS"
ACT_DB_QUERY = "DB_QUERY"
ACT_API_TEST = "API_TEST"
ACT_CODE_TRANSLATE = "CODE_TRANSLATE"
ACT_BACKUP = "BACKUP"
ACT_RESTORE = "RESTORE"
ACT_ENV_SET = "ENV_SET"
ACT_DEPLOY = "DEPLOY"
ACT_PERFORMANCE = "PERFORMANCE"
ACT_AUTO_COMMIT = "AUTO_COMMIT"
ACT_APK_BUILD = "APK_BUILD"
ACT_APK_INFO = "APK_INFO"
ACT_APK_INSTALL = "APK_INSTALL"
ACT_SANDBOX_RUN = "SANDBOX_RUN"
ACT_SANDBOX_LIST = "SANDBOX_LIST"

MAX_AGENT_ITERATIONS: int = 25


def _parse_agent_actions(response: str) -> List[dict]:
    actions = []
    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("ACTION:"):
            payload = line[len("ACTION:"):].strip()
            if payload.startswith(ACT_READ):
                actions.append({"type": ACT_READ, "payload": payload[len(ACT_READ):].strip()})
            elif payload.startswith(ACT_WRITE):
                rest = payload[len(ACT_WRITE):].strip()
                parts = rest.split(" ", 1)
                actions.append({"type": ACT_WRITE, "payload": parts[0] if parts else "", "content": parts[1] if len(parts) > 1 else ""})
            elif payload.startswith(ACT_RUN):
                actions.append({"type": ACT_RUN, "payload": payload[len(ACT_RUN):].strip()})
            elif payload.startswith(ACT_TEST):
                actions.append({"type": ACT_TEST, "payload": ""})
            elif payload.startswith(ACT_FIX):
                actions.append({"type": ACT_FIX, "payload": payload[len(ACT_FIX):].strip()})
            elif payload.startswith(ACT_COMPLETE):
                actions.append({"type": ACT_COMPLETE, "payload": payload[len(ACT_COMPLETE):].strip()})
            elif payload.startswith(ACT_GIT):
                actions.append({"type": ACT_GIT, "payload": payload[len(ACT_GIT):].strip()})
            elif payload.startswith(ACT_DIFF):
                actions.append({"type": ACT_DIFF, "payload": payload[len(ACT_DIFF):].strip()})
            elif payload.startswith(ACT_LINT):
                actions.append({"type": ACT_LINT, "payload": ""})
            elif payload.startswith(ACT_INIT):
                actions.append({"type": ACT_INIT, "payload": payload[len(ACT_INIT):].strip()})
            elif payload.startswith(ACT_DEPS):
                actions.append({"type": ACT_DEPS, "payload": ""})
            elif payload.startswith(ACT_REVIEW):
                actions.append({"type": ACT_REVIEW, "payload": payload[len(ACT_REVIEW):].strip()})
            elif payload.startswith(ACT_DOCKER):
                actions.append({"type": ACT_DOCKER, "payload": payload[len(ACT_DOCKER):].strip()})
            elif payload.startswith(ACT_FORMAT):
                actions.append({"type": ACT_FORMAT, "payload": payload[len(ACT_FORMAT):].strip()})
            elif payload.startswith(ACT_SEARCH):
                actions.append({"type": ACT_SEARCH, "payload": payload[len(ACT_SEARCH):].strip()})
            elif payload.startswith(ACT_REPLACE):
                actions.append({"type": ACT_REPLACE, "payload": payload[len(ACT_REPLACE):].strip()})
            elif payload.startswith(ACT_BRANCH):
                actions.append({"type": ACT_BRANCH, "payload": payload[len(ACT_BRANCH):].strip()})
            elif payload.startswith(ACT_SCAFFOLD):
                actions.append({"type": ACT_SCAFFOLD, "payload": payload[len(ACT_SCAFFOLD):].strip()})
            elif payload.startswith(ACT_CHAIN):
                actions.append({"type": ACT_CHAIN, "payload": payload[len(ACT_CHAIN):].strip()})
            elif payload.startswith(ACT_PREVIEW):
                actions.append({"type": ACT_PREVIEW, "payload": payload[len(ACT_PREVIEW):].strip()})
            elif payload.startswith(ACT_SERVER_START):
                actions.append({"type": ACT_SERVER_START, "payload": payload[len(ACT_SERVER_START):].strip()})
            elif payload.startswith(ACT_SERVER_STOP):
                actions.append({"type": ACT_SERVER_STOP, "payload": payload[len(ACT_SERVER_STOP):].strip()})
            elif payload.startswith(ACT_SERVER_STATUS):
                actions.append({"type": ACT_SERVER_STATUS, "payload": payload[len(ACT_SERVER_STATUS):].strip()})
            elif payload.startswith(ACT_SCREENSHOT):
                actions.append({"type": ACT_SCREENSHOT, "payload": payload[len(ACT_SCREENSHOT):].strip()})
            elif payload.startswith(ACT_TUNNEL):
                actions.append({"type": ACT_TUNNEL, "payload": payload[len(ACT_TUNNEL):].strip()})
            elif payload.startswith(ACT_WEBSITE_STATUS):
                actions.append({"type": ACT_WEBSITE_STATUS, "payload": payload[len(ACT_WEBSITE_STATUS):].strip()})
            elif payload.startswith(ACT_DB_QUERY):
                actions.append({"type": ACT_DB_QUERY, "payload": payload[len(ACT_DB_QUERY):].strip()})
            elif payload.startswith(ACT_API_TEST):
                actions.append({"type": ACT_API_TEST, "payload": payload[len(ACT_API_TEST):].strip()})
            elif payload.startswith(ACT_CODE_TRANSLATE):
                actions.append({"type": ACT_CODE_TRANSLATE, "payload": payload[len(ACT_CODE_TRANSLATE):].strip()})
            elif payload.startswith(ACT_BACKUP):
                actions.append({"type": ACT_BACKUP, "payload": payload[len(ACT_BACKUP):].strip()})
            elif payload.startswith(ACT_RESTORE):
                actions.append({"type": ACT_RESTORE, "payload": payload[len(ACT_RESTORE):].strip()})
            elif payload.startswith(ACT_ENV_SET):
                actions.append({"type": ACT_ENV_SET, "payload": payload[len(ACT_ENV_SET):].strip()})
            elif payload.startswith(ACT_DEPLOY):
                actions.append({"type": ACT_DEPLOY, "payload": payload[len(ACT_DEPLOY):].strip()})
            elif payload.startswith(ACT_PERFORMANCE):
                actions.append({"type": ACT_PERFORMANCE, "payload": ""})
            elif payload.startswith(ACT_AUTO_COMMIT):
                actions.append({"type": ACT_AUTO_COMMIT, "payload": payload[len(ACT_AUTO_COMMIT):].strip()})
            elif payload.startswith(ACT_APK_BUILD):
                actions.append({"type": ACT_APK_BUILD, "payload": payload[len(ACT_APK_BUILD):].strip()})
            elif payload.startswith(ACT_APK_INFO):
                actions.append({"type": ACT_APK_INFO, "payload": payload[len(ACT_APK_INFO):].strip()})
            elif payload.startswith(ACT_APK_INSTALL):
                actions.append({"type": ACT_APK_INSTALL, "payload": payload[len(ACT_APK_INSTALL):].strip()})
            elif payload.startswith(ACT_SANDBOX_RUN):
                actions.append({"type": ACT_SANDBOX_RUN, "payload": payload[len(ACT_SANDBOX_RUN):].strip()})
            elif payload.startswith(ACT_SANDBOX_LIST):
                actions.append({"type": ACT_SANDBOX_LIST, "payload": payload[len(ACT_SANDBOX_LIST):].strip()})
    return actions


async def _execute_agent_action(action: dict, user_id: int, db: Database,
                                 skills: SkillRegistry, terminal: TerminalEngine,
                                 ai: AIClient, workspace: str) -> dict:
    act_type = action["type"]
    payload = action.get("payload", "")

    try:
        if act_type == ACT_READ:
            file_path = payload
            sp = _safe_path(file_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ File not found: {file_path}", "action_type": act_type}
            if os.path.isdir(sp):
                return {"success": False, "output": f"❌ {file_path} is a directory", "action_type": act_type}
            with open(sp, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 4000:
                content = content[:4000] + "\n... (truncated)"
            return {"success": True, "output": f"📖 <b>{file_path}</b>\n\n<pre>{content}</pre>", "action_type": act_type}

        if act_type == ACT_WRITE:
            file_path = payload
            content = action.get("content", "")
            sp = _safe_path(file_path)
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            with open(sp, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "output": f"✅ Written: {file_path} ({len(content)} bytes)", "action_type": act_type}

        if act_type == ACT_RUN:
            parts = payload.split(" ", 1)
            skill_name = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            s = skills.get(skill_name)
            if not s:
                return {"success": False, "output": f"❌ Skill '{skill_name}' not found.", "action_type": act_type}
            result = s.run(args) if args else s.run()
            return {"success": True, "output": f"🔧 <b>Skill {skill_name}</b>\n<pre>{result}</pre>", "action_type": act_type}

        if act_type == ACT_TEST:
            res = terminal.run(user_id, "npm test 2>&1 || pytest 2>&1 || echo 'No test framework found'", admin=(user_id in ADMIN_IDS))
            return {"success": res["success"], "output": f"🧪 <b>Test Results</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_LINT:
            res = terminal.run(user_id, "npx eslint . 2>&1 || python -m pylint . 2>&1 || echo 'No linter configured'", admin=(user_id in ADMIN_IDS))
            return {"success": res["success"], "output": f"🔍 <b>Lint Results</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_GIT:
            git_cmd = payload if payload else "status"
            res = terminal.run(user_id, f"git {git_cmd}", admin=(user_id in ADMIN_IDS))
            return {"success": res["success"], "output": f"🌿 <b>Git {git_cmd}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_DIFF:
            file_path = payload
            res = terminal.run(user_id, f"git diff -- {file_path}", admin=(user_id in ADMIN_IDS))
            if not res["output"].strip() or res["output"] == "(no output)":
                res["output"] = "No changes detected or not a git repo."
            return {"success": True, "output": f"📊 <b>Diff: {file_path}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_INIT:
            project_type = payload.lower() if payload else "auto"
            if project_type in ("npm", "node", "javascript", "auto"):
                res1 = terminal.run(user_id, "npm init -y", admin=(user_id in ADMIN_IDS))
                res2 = terminal.run(user_id, "git init", admin=(user_id in ADMIN_IDS))
                return {"success": res1["success"] and res2["success"], "output": f"📦 <b>Init npm+git</b>\n\n{res1['output']}\n\n{res2['output']}", "action_type": act_type}
            if project_type in ("python", "py"):
                res1 = terminal.run(user_id, "python3 -m venv venv 2>&1 || echo 'venv exists'", admin=(user_id in ADMIN_IDS))
                res2 = terminal.run(user_id, "git init", admin=(user_id in ADMIN_IDS))
                return {"success": True, "output": f"🐍 <b>Init Python+git</b>\n\n{res1['output']}\n\n{res2['output']}", "action_type": act_type}
            return {"success": False, "output": f"❌ Unknown project type: {project_type}. Use: npm, python", "action_type": act_type}

        if act_type == ACT_DEPS:
            res1 = terminal.run(user_id, "cat package.json 2>&1 || echo 'No package.json'", admin=(user_id in ADMIN_IDS))
            res2 = terminal.run(user_id, "cat requirements.txt 2>&1 || echo 'No requirements.txt'", admin=(user_id in ADMIN_IDS))
            return {"success": True, "output": f"📚 <b>Dependencies</b>\n\n<b>package.json:</b>\n<pre>{res1['output']}</pre>\n\n<b>requirements.txt:</b>\n<pre>{res2['output']}</pre>", "action_type": act_type}

        if act_type == ACT_REVIEW:
            file_path = payload
            sp = _safe_path(file_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ File not found: {file_path}", "action_type": act_type}
            with open(sp, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 4000:
                content = content[:4000] + "\n... (truncated)"
            review_prompt = (
                f"Review this code for bugs, security issues, and improvements:\n\n"
                f"File: {file_path}\n\n{content}\n\n"
                "Provide a concise review with: 1) Issues found, 2) Suggestions, 3) Rating (1-10)."
            )
            review_resp = ai.generate(prompt=review_prompt, system_prompt="You are a senior code reviewer. Be concise and actionable.", max_tokens=1500, temperature=0.3)
            return {"success": True, "output": f"🔍 <b>Code Review: {file_path}</b>\n\n{review_resp}", "action_type": act_type}

        if act_type == ACT_DOCKER:
            docker_cmd = payload if payload else "ps"
            res = terminal.run(user_id, f"docker {docker_cmd}", admin=(user_id in ADMIN_IDS))
            return {"success": res["success"], "output": f"🐳 <b>Docker {docker_cmd}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_FORMAT:
            file_path = payload
            sp = _safe_path(file_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ File not found: {file_path}", "action_type": act_type}
            if file_path.endswith((".js", ".ts", ".jsx", ".tsx", ".json", ".css", ".html", ".md")):
                res = terminal.run(user_id, f"npx prettier --write {file_path} 2>&1 || echo 'Prettier not available'", admin=(user_id in ADMIN_IDS))
            elif file_path.endswith(".py"):
                res = terminal.run(user_id, f"python3 -m black {file_path} 2>&1 || echo 'Black not available'", admin=(user_id in ADMIN_IDS))
            else:
                res = {"success": False, "output": "❌ No formatter configured for this file type.", "exit_code": -1}
            return {"success": res["success"], "output": f"🎨 <b>Format: {file_path}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_SEARCH:
            pattern = payload
            res = terminal.run(user_id, f"grep -rn '{pattern}' . --include='*.py' --include='*.js' --include='*.ts' --include='*.html' --include='*.css' 2>/dev/null | head -50", admin=(user_id in ADMIN_IDS))
            if not res["output"].strip():
                res["output"] = "No matches found."
            return {"success": True, "output": f"🔍 <b>Search: '{pattern}'</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_REPLACE:
            parts = payload.split(" ", 2)
            if len(parts) < 3:
                return {"success": False, "output": f"❌ Usage: REPLACE <file_path> <old_string> <new_string>", "action_type": act_type}
            file_path = parts[0]
            old_str = parts[1]
            new_str = parts[2]
            sp = _safe_path(file_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ File not found: {file_path}", "action_type": act_type}
            with open(sp, "r", encoding="utf-8") as f:
                content = f.read()
            count = content.count(old_str)
            if count == 0:
                return {"success": False, "output": f"❌ String '{old_str}' not found in {file_path}", "action_type": act_type}
            new_content = content.replace(old_str, new_str)
            with open(sp, "w", encoding="utf-8") as f:
                f.write(new_content)
            return {"success": True, "output": f"🔄 <b>Replace in {file_path}</b>\nReplaced {count} occurrence(s).", "action_type": act_type}

        if act_type == ACT_BRANCH:
            branch_name = payload
            if not branch_name:
                res = terminal.run(user_id, "git branch", admin=(user_id in ADMIN_IDS))
                return {"success": True, "output": f"🌿 <b>Branches</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}
            res = terminal.run(user_id, f"git checkout -b {branch_name}", admin=(user_id in ADMIN_IDS))
            return {"success": res["success"], "output": f"🌿 <b>Branch: {branch_name}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_SCAFFOLD:
            template = payload.lower() if payload else "express"
            if template == "express":
                files = {
                    "package.json": json.dumps({"name": "my-app", "version": "1.0.0", "scripts": {"start": "node index.js", "dev": "nodemon index.js"}, "dependencies": {"express": "^4.18.2"}}, indent=2),
                    "index.js": "const express = require('express');\nconst app = express();\nconst PORT = process.env.PORT || 3000;\n\napp.get('/', (req, res) => res.json({ status: 'ok' }));\napp.get('/health', (req, res) => res.json({ status: 'healthy' }));\n\napp.listen(PORT, () => console.log(`Server running on port ${PORT}`));\n",
                    ".gitignore": "node_modules/\n.env\n",
                    "README.md": "# My Express App\n\n## Endpoints\n- GET /\n- GET /health\n",
                }
            elif template == "react":
                files = {
                    "package.json": json.dumps({"name": "my-react-app", "version": "1.0.0", "scripts": {"start": "react-scripts start", "build": "react-scripts build"}, "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}, indent=2),
                    "src/App.js": "import React from 'react';\nfunction App() { return <h1>Hello React</h1>; }\nexport default App;\n",
                    "src/index.js": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nReactDOM.createRoot(document.getElementById('root')).render(<App />);\n",
                    "public/index.html": "<!DOCTYPE html><html><head><title>React App</title></head><body><div id=\"root\"></div></body></html>\n",
                    ".gitignore": "node_modules/\nbuild/\n.env\n",
                }
            elif template == "flask":
                files = {
                    "requirements.txt": "flask==3.0.0\n",
                    "app.py": "from flask import Flask, jsonify\napp = Flask(__name__)\n\n@app.route('/')\ndef index(): return jsonify({'status': 'ok'})\n\n@app.route('/health')\ndef health(): return jsonify({'status': 'healthy'})\n\nif __name__ == '__main__': app.run(debug=True)\n",
                    ".gitignore": "venv/\n__pycache__/\n.env\n",
                    "README.md": "# Flask App\n\n## Endpoints\n- GET /\n- GET /health\n",
                }
            elif template == "fastapi":
                files = {
                    "requirements.txt": "fastapi==0.104.0\nuvicorn==0.24.0\n",
                    "main.py": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef index(): return {'status': 'ok'}\n\n@app.get('/health')\ndef health(): return {'status': 'healthy'}\n",
                    ".gitignore": "venv/\n__pycache__/\n.env\n",
                    "README.md": "# FastAPI App\n\n## Endpoints\n- GET /\n- GET /health\n",
                }
            else:
                return {"success": False, "output": f"❌ Unknown template: {template}. Use: express, react, flask, fastapi", "action_type": act_type}
            written = []
            for path, content in files.items():
                sp = _safe_path(path)
                os.makedirs(os.path.dirname(sp), exist_ok=True)
                with open(sp, "w", encoding="utf-8") as f:
                    f.write(content)
                written.append(path)
            terminal.run(user.id, "git init", admin=(user_id in ADMIN_IDS))
            return {"success": True, "output": f"📦 <b>Scaffold: {template}</b>\n\n" + "\n".join(f"✅ {w}" for w in written) + "\n\n🌿 Git initialized.", "action_type": act_type}

        if act_type == ACT_CHAIN:
            tasks = [t.strip() for t in payload.split("|") if t.strip()]
            if not tasks:
                return {"success": False, "output": f"❌ Usage: CHAIN <task_1> | <task_2> | ...", "action_type": act_type}
            context_data = {"chain_tasks": tasks, "chain_index": 0, "chain_user": user_id, "chain_task_id": task_id}
            db.create_checkpoint(user_id, task_id, f"chain start: {len(tasks)} tasks", {"chain": context_data})
            first_task = tasks[0]
            return {"success": True, "output": f"⛓️ <b>Task Chain Started</b>\nTotal tasks: {len(tasks)}\nCurrent: 1/{len(tasks)} - {first_task}\n\nUse /agent '{first_task}' to begin.", "action_type": act_type}

        if act_type == ACT_PREVIEW:
            port_str = payload.strip() if payload else "8000"
            try:
                port = int(port_str)
            except ValueError:
                port = 8000

            def start_server():
                handler = http.server.SimpleHTTPRequestHandler
                with socketserver.TCPServer(("", port), handler) as httpd:
                    httpd.serve_forever()

            if user.id in _website_servers:
                old = _website_servers[user.id]
                try:
                    old["process"].terminate()
                except Exception:
                    pass

            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()

            _website_servers[user.id] = {
                "port": port, "process": server_thread, "directory": WORKSPACE_DIR,
                "url": f"http://localhost:{port}",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

            return {"success": True, "output": f"{EMOJI['preview']} <b>Website Preview Started</b>\n<b>URL:</b> http://localhost:{port}\n<b>Directory:</b> {WORKSPACE_DIR}\nUse /server-status to check, /server-stop to stop.", "action_type": act_type}

        if act_type == ACT_SERVER_START:
            return await _execute_agent_action({"type": ACT_PREVIEW, "payload": payload}, user_id, db, skills, terminal, ai, workspace)

        if act_type == ACT_SERVER_STOP:
            if user.id not in _website_servers:
                return {"success": False, "output": f"{EMOJI['error']} No server running.", "action_type": act_type}
            server_info = _website_servers.pop(user.id)
            return {"success": True, "output": f"{EMOJI['server']} <b>Server Stopped</b>\n<b>Port:</b> {server_info['port']}\n<b>URL was:</b> {server_info['url']}", "action_type": act_type}

        if act_type == ACT_SERVER_STATUS:
            if user.id not in _website_servers:
                return {"success": False, "output": f"{EMOJI['error']} No server running.", "action_type": act_type}
            info = _website_servers[user.id]
            return {"success": True, "output": f"{EMOJI['server']} <b>Server Status</b>\n<b>URL:</b> {info['url']}\n<b>Port:</b> {info['port']}\n<b>Directory:</b> {info['directory']}\n<b>Started:</b> {info['started_at']}", "action_type": act_type}

        if act_type == ACT_SCREENSHOT:
            url = payload if payload else (_website_servers.get(user.id, {}).get("url", ""))
            if not url:
                return {"success": False, "output": f"{EMOJI['error']} No URL specified and no server running.", "action_type": act_type}
            import subprocess
            try:
                result = subprocess.run(
                    f"python3 -c \"from PIL import ImageGrab; img = ImageGrab.grab(); img.save('/tmp/screenshot.png')\" 2>&1",
                    shell=True, capture_output=True, text=True, timeout=10,
                )
                if os.path.exists("/tmp/screenshot.png"):
                    return {"success": True, "output": f"{EMOJI['screenshot']} <b>Screenshot Captured</b>\n<b>URL:</b> {url}\nScreenshot saved to /tmp/screenshot.png", "action_type": act_type}
                else:
                    return {"success": False, "output": f"{EMOJI['error']} Screenshot tool not available.\nInstall: pip install pillow", "action_type": act_type}
            except Exception as e:
                return {"success": False, "output": f"{EMOJI['error']} Screenshot failed: {e}", "action_type": act_type}

        if act_type == ACT_TUNNEL:
            port_str = payload.strip() if payload else "8000"
            try:
                port = int(port_str)
            except ValueError:
                port = 8000
            result = terminal.run(user_id, f"npx localtunnel --port {port} 2>&1 || echo 'Localtunnel not available. Install: npm install -g localtunnel'", admin=(user_id in ADMIN_IDS))
            return {"success": True, "output": f"{EMOJI['tunnel']} <b>Tunnel Request</b>\n<b>Port:</b> {port}\n<b>Result:</b>\n<pre>{result['output']}</pre>", "action_type": act_type}

        if act_type == ACT_WEBSITE_STATUS:
            url = payload if payload else (_website_servers.get(user.id, {}).get("url", ""))
            if not url:
                return {"success": False, "output": f"{EMOJI['error']} No URL specified and no server running.", "action_type": act_type}
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    status = resp.status
                    headers = dict(resp.headers)
                return {"success": True, "output": f"{EMOJI['website']} <b>Website Status: {url}</b>\n<b>HTTP Status:</b> {status}\n<b>Server:</b> {headers.get('Server', 'Unknown')}\n<b>Content-Type:</b> {headers.get('Content-Type', 'Unknown')}", "action_type": act_type}
            except Exception as e:
                return {"success": False, "output": f"{EMOJI['error']} Website check failed: {url}\nError: {e}", "action_type": act_type}

        if act_type == ACT_DB_QUERY:
            parts = payload.split(" ", 1)
            if len(parts) < 2:
                return {"success": False, "output": f"❌ Usage: DB_QUERY <connection_key> <query>", "action_type": act_type}
            conn_key = parts[0]
            query = parts[1]
            result = db_manager.execute_query(conn_key, query)
            return {"success": True, "output": f"🗄️ <b>DB Query: {conn_key}</b>\n\n{result}", "action_type": act_type}

        if act_type == ACT_API_TEST:
            parts = payload.split(" ", 2)
            url = parts[0] if parts else ""
            method = parts[1] if len(parts) > 1 else "GET"
            body = parts[2] if len(parts) > 2 else None
            if not url:
                return {"success": False, "output": f"❌ Usage: API_TEST <url> [method] [body]", "action_type": act_type}
            result = _api_test(url, method=method, body=body)
            return {"success": True, "output": f"🔗 <b>API Test</b>\n\n{result}", "action_type": act_type}

        if act_type == ACT_CODE_TRANSLATE:
            parts = payload.split(" ", 2)
            if len(parts) < 3:
                return {"success": False, "output": f"❌ Usage: CODE_TRANSLATE <from_lang> <to_lang> <file_path>", "action_type": act_type}
            from_lang, to_lang, file_path = parts[0], parts[1], parts[2]
            sp = _safe_path(file_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ File not found: {file_path}", "action_type": act_type}
            with open(sp, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"
            translate_prompt = (
                f"Translate this code from {from_lang} to {to_lang}:\n\n"
                f"File: {file_path}\n\n{content}\n\n"
                "Provide the translated code with brief comments explaining changes."
            )
            translate_resp = ai.generate(prompt=translate_prompt, system_prompt="You are an expert polyglot programmer. Translate code accurately.", max_tokens=2000, temperature=0.3)
            return {"success": True, "output": f"🔄 <b>Code Translation: {from_lang} → {to_lang}</b>\n<b>File:</b> {file_path}\n\n{translate_resp}", "action_type": act_type}

        if act_type == ACT_BACKUP:
            name = payload if payload else "backup"
            result = _create_backup(user_id, name)
            return {"success": "✅" in result, "output": result, "action_type": act_type}

        if act_type == ACT_RESTORE:
            name = payload if payload else "backup"
            result = _restore_backup(user_id, name)
            return {"success": "✅" in result, "output": result, "action_type": act_type}

        if act_type == ACT_ENV_SET:
            if "=" not in payload:
                return {"success": False, "output": f"❌ Usage: ENV_SET KEY=VALUE", "action_type": act_type}
            key, value = payload.split("=", 1)
            result = _env_set(key.strip(), value.strip())
            return {"success": "✅" in result, "output": result, "action_type": act_type}

        if act_type == ACT_DEPLOY:
            result = _auto_deploy(payload if payload else "auto")
            return {"success": "✅" in result or "🚀" in result, "output": result, "action_type": act_type}

        if act_type == ACT_PERFORMANCE:
            result = _get_performance()
            return {"success": True, "output": result, "action_type": act_type}

        if act_type == ACT_AUTO_COMMIT:
            msg = payload if payload else "Auto-commit by Coding Agent"
            res_add = terminal.run(user_id, "git add .", admin=(user_id in ADMIN_IDS))
            res_commit = terminal.run(user_id, f'git commit -m "{msg}"', admin=(user_id in ADMIN_IDS))
            return {"success": res_commit["success"], "output": f"💾 <b>Auto-Commit</b>\n\n<b>Add:</b>\n<pre>{res_add['output']}</pre>\n\n<b>Commit:</b>\n<pre>{res_commit['output']}</pre>", "action_type": act_type}

        if act_type == ACT_APK_BUILD:
            # payload: <project_path>
            project_path = payload if payload else WORKSPACE_DIR
            sp = _safe_path(project_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ Project path not found: {project_path}", "action_type": act_type}
            # Check for gradlew or build.gradle
            gradlew = os.path.join(sp, "gradlew")
            build_gradle = os.path.join(sp, "build.gradle")
            build_gradle_kts = os.path.join(sp, "build.gradle.kts")
            if os.path.exists(gradlew):
                res = terminal.run(user_id, f"cd {sp} && ./gradlew assembleDebug", admin=(user_id in ADMIN_IDS), timeout=300)
            elif os.path.exists(build_gradle) or os.path.exists(build_gradle_kts):
                res = terminal.run(user_id, f"cd {sp} && gradle assembleDebug", admin=(user_id in ADMIN_IDS), timeout=300)
            else:
                return {"success": False, "output": f"❌ No Android project found at {project_path} (no gradlew or build.gradle)", "action_type": act_type}
            # Find APK
            apk_path = ""
            for root, dirs, files in os.walk(sp):
                for f in files:
                    if f.endswith("-debug.apk"):
                        apk_path = os.path.join(root, f)
                        break
                if apk_path:
                    break
            if apk_path:
                res["output"] += f"\n\n📱 APK built: {apk_path}\nSize: {os.path.getsize(apk_path)} bytes"
            return {"success": res["success"], "output": f"📱 <b>APK Build: {project_path}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_APK_INFO:
            # payload: <apk_path>
            apk_path = payload if payload else ""
            if not apk_path:
                return {"success": False, "output": f"❌ Usage: APK_INFO <apk_path>", "action_type": act_type}
            sp = _safe_path(apk_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ APK not found: {apk_path}", "action_type": act_type}
            # Try aapt
            res = terminal.run(user_id, f"aapt dump badging {sp}", admin=(user_id in ADMIN_IDS))
            if not res["output"].strip() or "not found" in res["output"].lower():
                # Try reading APK as zip
                import zipfile
                try:
                    with zipfile.ZipFile(sp, 'r') as z:
                        manifest = z.read("AndroidManifest.xml").decode('utf-8', errors='replace')[:2000]
                        res["output"] = f"APK Size: {os.path.getsize(sp)} bytes\n\nManifest (raw):\n{manifest}"
                except Exception as e:
                    res["output"] = f"❌ Cannot read APK: {e}"
            return {"success": True, "output": f"📱 <b>APK Info: {apk_path}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_APK_INSTALL:
            # payload: <apk_path>
            apk_path = payload if payload else ""
            if not apk_path:
                return {"success": False, "output": f"❌ Usage: APK_INSTALL <apk_path>", "action_type": act_type}
            sp = _safe_path(apk_path)
            if not os.path.exists(sp):
                return {"success": False, "output": f"❌ APK not found: {apk_path}", "action_type": act_type}
            res = terminal.run(user_id, f"adb install {sp}", admin=(user_id in ADMIN_IDS))
            return {"success": res["success"], "output": f"📱 <b>APK Install: {apk_path}</b>\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_SANDBOX_RUN:
            # payload: <command>
            command = payload if payload else ""
            if not command:
                return {"success": False, "output": f"❌ Usage: SANDBOX_RUN <command>", "action_type": act_type}
            # Run in sandbox (isolated subprocess with restrictions)
            import tempfile
            sandbox_dir = os.path.join(WORKSPACE_DIR, ".sandbox")
            os.makedirs(sandbox_dir, exist_ok=True)
            sandbox_id = f"sandbox_{int(time.time())}"
            sandbox_path = os.path.join(sandbox_dir, sandbox_id)
            os.makedirs(sandbox_path, exist_ok=True)
            try:
                res = terminal.run(user_id, f"cd {sandbox_path} && {command}", admin=(user_id in ADMIN_IDS), timeout=60)
            except Exception as e:
                res = {"success": False, "output": f"❌ Sandbox error: {e}", "exit_code": -1}
            # Cleanup
            try:
                import shutil
                shutil.rmtree(sandbox_path, ignore_errors=True)
            except Exception:
                pass
            return {"success": res["success"], "output": f"🏗️ <b>Sandbox Run</b>\n<b>Command:</b> {command}\n\n<pre>{res['output']}</pre>", "action_type": act_type}

        if act_type == ACT_SANDBOX_LIST:
            # List active sandboxes
            sandbox_dir = os.path.join(WORKSPACE_DIR, ".sandbox")
            if not os.path.exists(sandbox_dir):
                return {"success": True, "output": f"🏗️ <b>Sandboxes</b>\n\nNo active sandboxes.", "action_type": act_type}
            sandboxes = []
            for d in os.listdir(sandbox_dir):
                dpath = os.path.join(sandbox_dir, d)
                if os.path.isdir(dpath):
                    try:
                        mtime = os.path.getmtime(dpath)
                        sandboxes.append((d, mtime))
                    except Exception:
                        pass
            sandboxes.sort(key=lambda x: x[1], reverse=True)
            lines = [f"• {name}" for name, _ in sandboxes[:20]]
            return {"success": True, "output": f"🏗️ <b>Active Sandboxes</b>\n\n" + "\n".join(lines) if lines else "No active sandboxes.", "action_type": act_type}

        if act_type == ACT_COMPLETE:
            return {"success": True, "output": f"✅ <b>Task Complete</b>\n{payload}", "action_type": act_type}

        return {"success": False, "output": f"❌ Unknown action type: {act_type}", "action_type": act_type}

    except Exception as e:
        logger.error("Agent action error: %s", e)
        return {"success": False, "output": f"❌ Action error: {e}", "action_type": act_type}


async def _rollback_to_checkpoint(context: ContextTypes.DEFAULT_TYPE, user_id: int, task_id: int) -> None:
    db: Database = context.bot_data["db"]
    checkpoint = db.get_latest_checkpoint(task_id)
    if not checkpoint:
        return
    state = checkpoint.get("state", {})
    files_state = state.get("files", {})
    for file_path, content in files_state.items():
        try:
            sp = _safe_path(file_path)
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            with open(sp, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.warning("Rollback file write failed %s: %s", file_path, e)
    db.update_task(task_id, "running", result=f"Rolled back to checkpoint: {checkpoint['description']}")


async def _run_agent_loop(context: ContextTypes.DEFAULT_TYPE, user_id: int, task_id: int, task_desc: str, is_chain: bool = False, chain_state: Optional[dict] = None) -> None:
    db: Database = context.bot_data["db"]
    ai: AIClient = context.bot_data["ai"]
    skills: SkillRegistry = context.bot_data["skills"]
    terminal: TerminalEngine = context.bot_data["terminal"]

    iteration = 0
    consecutive_failures = 0
    max_failures = 3
    files_snapshot: Dict[str, str] = {}

    while iteration < MAX_AGENT_ITERATIONS:
        iteration += 1
        ctx = _gather_workspace_context()
        system_prompt = ai.coding_agent_system_prompt(task_desc, WORKSPACE_DIR, ctx)

        failure_context = ""
        if consecutive_failures > 0:
            failure_context = (
                f"\n\n⚠️ PREVIOUS FAILURES ({consecutive_failures}x): "
                f"The last {consecutive_failures} action(s) failed. "
                f"Analyze errors carefully and use ACTION: FIX to correct.\n"
            )

        prompt = (
            f"Iteration {iteration}/{MAX_AGENT_ITERATIONS}. Task: {task_desc}\n"
            f"{failure_context}"
            "Decide your next ACTION. "
            "If you have enough information and code is working, use ACTION: COMPLETE.\n"
        )

        resp = ai.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=2000, temperature=0.3)
        actions = _parse_agent_actions(resp)

        if not actions:
            consecutive_failures += 1
            await context.bot.send_message(
                chat_id=user_id,
                text=(f"{EMOJI['warning']} <b>Agent Iteration {iteration}</b> (task {task_id})\nNo valid action parsed. Retrying...\n<i>{resp[:300]}</i>"),
                parse_mode=ParseMode.HTML,
            )
            if consecutive_failures >= max_failures:
                await _rollback_to_checkpoint(context, user_id, task_id)
                consecutive_failures = 0
            continue

        action = actions[0]
        act_type = action["type"]

        action_labels = {
            ACT_READ: f"{EMOJI['read']} READ", ACT_WRITE: f"{EMOJI['write']} WRITE",
            ACT_RUN: f"{EMOJI['terminal']} RUN", ACT_TEST: f"{EMOJI['test']} TEST",
            ACT_LINT: f"{EMOJI['info']} LINT", ACT_GIT: f"{EMOJI['git']} GIT",
            ACT_DIFF: f"{EMOJI['stats']} DIFF", ACT_INIT: f"{EMOJI['plus']} INIT",
            ACT_DEPS: f"{EMOJI['list']} DEPS", ACT_REVIEW: f"{EMOJI['info']} REVIEW",
            ACT_DOCKER: f"{EMOJI['docker']} DOCKER", ACT_FORMAT: f"{EMOJI['info']} FORMAT",
            ACT_SEARCH: f"{EMOJI['search']} SEARCH", ACT_REPLACE: f"{EMOJI['cross']} REPLACE",
            ACT_BRANCH: f"{EMOJI['git']} BRANCH", ACT_SCAFFOLD: f"{EMOJI['plus']} SCAFFOLD",
            ACT_CHAIN: f"{EMOJI['rocket']} CHAIN", ACT_FIX: f"{EMOJI['warning']} FIX",
            ACT_PREVIEW: f"{EMOJI['preview']} PREVIEW", ACT_SERVER_START: f"{EMOJI['server']} SERVER_START",
            ACT_SERVER_STOP: f"{EMOJI['server']} SERVER_STOP", ACT_SERVER_STATUS: f"{EMOJI['server']} SERVER_STATUS",
            ACT_SCREENSHOT: f"{EMOJI['screenshot']} SCREENSHOT", ACT_TUNNEL: f"{EMOJI['tunnel']} TUNNEL",
            ACT_WEBSITE_STATUS: f"{EMOJI['website']} WEBSITE_STATUS", ACT_DB_QUERY: f"{EMOJI['db']} DB_QUERY",
            ACT_API_TEST: f"{EMOJI['search']} API_TEST", ACT_CODE_TRANSLATE: f"{EMOJI['info']} TRANSLATE",
            ACT_BACKUP: f"{EMOJI['plus']} BACKUP", ACT_RESTORE: f"{EMOJI['cross']} RESTORE",
            ACT_ENV_SET: f"{EMOJI['info']} ENV_SET", ACT_DEPLOY: f"{EMOJI['rocket']} DEPLOY",
            ACT_PERFORMANCE: f"{EMOJI['server']} PERFORMANCE", ACT_AUTO_COMMIT: f"{EMOJI['success']} AUTO_COMMIT",
            ACT_APK_BUILD: f"{EMOJI['apk']} APK_BUILD", ACT_APK_INFO: f"{EMOJI['apk']} APK_INFO",
            ACT_APK_INSTALL: f"{EMOJI['apk']} APK_INSTALL", ACT_SANDBOX_RUN: f"{EMOJI['sandbox']} SANDBOX_RUN",
            ACT_SANDBOX_LIST: f"{EMOJI['sandbox']} SANDBOX_LIST",
            ACT_COMPLETE: f"{EMOJI['success']} COMPLETE",
        }
        label = action_labels.get(act_type, f"{EMOJI['info']} {act_type}")

        if act_type == ACT_WRITE:
            action_payload = action.get("payload", "")
            if action_payload:
                sp = _safe_path(action_payload)
                if os.path.exists(sp):
                    try:
                        with open(sp, "r", encoding="utf-8") as f:
                            files_snapshot[action_payload] = f.read()
                    except Exception:
                        pass
            db.create_checkpoint(user_id, task_id, f"pre-write iteration {iteration}", {"files": files_snapshot, "step": iteration})

        result = await _execute_agent_action(action, user_id, db, skills, terminal, ai, WORKSPACE_DIR)

        if act_type == ACT_WRITE and result["success"]:
            sp = _safe_path(action.get("payload", ""))
            if os.path.exists(sp):
                try:
                    with open(sp, "r", encoding="utf-8") as f:
                        files_snapshot[action.get("payload", "")] = f.read()
                except Exception:
                    pass
            db.create_checkpoint(user_id, task_id, f"post-write iteration {iteration}", {"files": files_snapshot, "step": iteration})

        if result["success"]:
            consecutive_failures = 0
            await context.bot.send_message(
                chat_id=user_id,
                text=(f"{label} <b>Iteration {iteration}</b> (task {task_id})\n{result['output'][:2000]}"),
                parse_mode=ParseMode.HTML,
            )
        else:
            consecutive_failures += 1
            await context.bot.send_message(
                chat_id=user_id,
                text=(f"{EMOJI['error']} <b>Iteration {iteration} FAILED</b> (task {task_id})\n{result['output'][:1500]}\nConsecutive failures: {consecutive_failures}/{max_failures}"),
                parse_mode=ParseMode.HTML,
            )
            if consecutive_failures >= max_failures:
                await context.bot.send_message(chat_id=user_id, text=(f"{EMOJI['warning']} <b>Triggering rollback...</b>\nRolling back to last checkpoint."), parse_mode=ParseMode.HTML)
                await _rollback_to_checkpoint(context, user_id, task_id)
                consecutive_failures = 0
                continue

        if act_type == ACT_COMPLETE:
            db.update_task(task_id, "completed", result=result["output"])
            if is_chain and chain_state:
                chain_state["completed"].append(task_desc)
                chain_state["results"].append(result["output"])
                chain_state["index"] += 1
                db.create_checkpoint(user_id, task_id, f"chain step {chain_state['index']} complete", {"chain_state": chain_state})
                if chain_state["index"] < len(chain_state["tasks"]):
                    next_task = chain_state["tasks"][chain_state["index"]]
                    next_tid = db.create_task(user.id, f"chain:{next_task[:30]}")
                    db.update_task(next_tid, "running")
                    _active_tasks[user.id] = next_tid
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(f"{EMOJI['rocket']} <b>Chain Next Task</b>\n\n<b>Chain ID:</b> {task_id}\n<b>Progress:</b> {chain_state['index'] + 1}/{len(chain_state['tasks'])}\n<b>Next:</b> {next_task}\n\n{EMOJI['running']} Executing..."),
                        parse_mode=ParseMode.HTML,
                    )
                    await _run_agent_loop(context, user_id, next_tid, next_task, is_chain=True, chain_state=chain_state)
                    return
                else:
                    db.update_task(task_id, "completed", result=f"Chain complete. {len(chain_state['tasks'])} tasks executed.")
                    _active_tasks.pop(user_id, None)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(f"{EMOJI['success']} <b>Task Chain Complete!</b>\n\n<b>Chain ID:</b> {task_id}\n<b>Tasks completed:</b> {len(chain_state['tasks'])}\n<b>Results:</b>\n" + "\n".join(f"{i+1}. {r[:200]}" for i, r in enumerate(chain_state["results"]))),
                        parse_mode=ParseMode.HTML,
                    )
                    return
            _active_tasks.pop(user_id, None)
            await context.bot.send_message(
                chat_id=user_id,
                text=(f"{EMOJI['success']} <b>Agent Task Complete!</b> (task {task_id})\n{result['output'][:2000]}"),
                parse_mode=ParseMode.HTML,
            )
            return

    db.update_task(task_id, "completed", result=f"Reached max iterations ({MAX_AGENT_ITERATIONS}). Task may need manual review.")
    _active_tasks.pop(user_id, None)
    await context.bot.send_message(
        chat_id=user_id,
        text=(f"{EMOJI['warning']} <b>Max iterations reached.</b> (task {task_id})\nThe agent stopped after {MAX_AGENT_ITERATIONS} iterations.\nUse /status to review results."),
        parse_mode=ParseMode.HTML,
    )


async def agent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db: Database = context.bot_data["db"]
    ai: AIClient = context.bot_data["ai"]
    if not ai.is_available():
        await update.effective_message.reply_text("⚠️ AI provider not configured.\nSet CLAUDE_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY.", parse_mode=ParseMode.HTML)
        return
    if user.id in _active_tasks:
        await update.effective_message.reply_text("⏳ Active task exists. Use /status or /cancel.", parse_mode=ParseMode.HTML)
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /agent <task description>", parse_mode=ParseMode.HTML)
        return
    desc = " ".join(context.args)
    tid = db.create_task(user.id, "coding_agent")
    db.update_task(tid, "running")
    _active_tasks[user.id] = tid
    db.create_checkpoint(user.id, tid, "started", {"task": desc, "step": 0})
    await update.effective_message.reply_text(
        f"{EMOJI['agent']} <b>Agent Started</b>\n\n<b>Task ID:</b> {tid}\n<b>Task:</b> {desc}\n{EMOJI['running']} Working autonomously...\nMax iterations: {MAX_AGENT_ITERATIONS}\nUse /status to check progress.",
        parse_mode=ParseMode.HTML,
    )
    await _run_agent_loop(context, user.id, tid, desc)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db: Database = context.bot_data["db"]
    tid = _active_tasks.get(user.id)
    if not tid:
        await update.effective_message.reply_text("ℹ️ No active task.", parse_mode=ParseMode.HTML)
        return
    task = db.get_task(tid)
    if not task:
        await update.effective_message.reply_text("❌ Task not found.", parse_mode=ParseMode.HTML)
        return
    emo = {"pending": EMOJI['pending'], "running": EMOJI['running'], "completed": EMOJI['completed'], "failed": EMOJI['failed']}.get(task["status"], EMOJI['info'])
    msg = (f"{emo} <b>Task Status</b>\n\n<b>ID:</b> {tid}\n<b>Type:</b> {task['task_type']}\n<b>Status:</b> {_status_badge(task['status'])}\n<b>Created:</b> {task['created_at']}\n")
    if task.get("result"):
        msg += f"\n<b>Result:</b>\n{task['result'][:1500]}"
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    tid = _active_tasks.pop(user.id, None)
    if not tid:
        await update.effective_message.reply_text("ℹ️ No active task.", parse_mode=ParseMode.HTML)
        return
    db: Database = context.bot_data["db"]
    db.update_task(tid, "failed", result="Cancelled by user.")
    await update.effective_message.reply_text(f"⛔ Task {tid} cancelled.", parse_mode=ParseMode.HTML)

# Remaining text message handler and application builder
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    uid = user.id
    text = update.effective_message.text or ""

    # Force reply: terminal command
    if uid in _waiting_confirm and _waiting_confirm[uid].get("action") == "term_run":
        _waiting_confirm.pop(uid, None)
        db: Database = context.bot_data["db"]
        rl: RateLimiter = context.bot_data["rate_limiter"]
        term: TerminalEngine = context.bot_data["terminal"]
        if not rl.is_allowed(uid):
            await update.effective_message.reply_text(
                f"⏳ Rate limit exceeded. ({rl.get_remaining(uid)} left)",
                parse_mode=ParseMode.HTML,
            )
            return
        res = term.run(uid, text, admin=(uid in ADMIN_IDS))
        emoji = EMOJI['success'] if res["success"] else EMOJI['error']
        await update.effective_message.reply_text(
            f"{emoji} <b>Terminal Result</b>\n<code>{text}</code>\nExit: {res['exit_code']}\n\n<pre>{res['output'][:3000]}</pre>",
            parse_mode=ParseMode.HTML,
        )
        return

    # Force reply: file read
    if uid in _waiting_confirm and _waiting_confirm[uid].get("action") == "file_read":
        _waiting_confirm.pop(uid, None)
        sp = _safe_path(text)
        try:
            if not os.path.exists(sp):
                await update.effective_message.reply_text(f"❌ Not found: {text}", parse_mode=ParseMode.HTML)
                return
            with open(sp, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 3500:
                content = content[:3500] + "\n... (truncated)"
            await update.effective_message.reply_text(
                f"📖 <b>{text}</b>\n\n<pre>{content}</pre>",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await update.effective_message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)
        return

    # Creating skill
    if uid in _skill_create_step:
        step = _skill_create_step[uid]
        data = _skill_create_data[uid]
        if step == "desc":
            data["description"] = text
            _skill_create_step[uid] = "code"
            await update.effective_message.reply_text(
                f"{EMOJI['plus']} <b>Create Skill: {data['name']}</b>\n\nStep 3/3: Send the Python code (define `run` function):",
                parse_mode=ParseMode.HTML,
            )
            return
        if step == "code":
            data["code"] = text
            reg: SkillRegistry = context.bot_data["skills"]
            if reg.create(data["name"], data["description"], data["code"], "general", uid):
                await update.effective_message.reply_text(f"{EMOJI['success']} Skill created: {data['name']}", parse_mode=ParseMode.HTML)
            else:
                await update.effective_message.reply_text(f"❌ Skill already exists: {data['name']}", parse_mode=ParseMode.HTML)
            _skill_create_step.pop(uid, None)
            _skill_create_data.pop(uid, None)
            return

    # Creating tool
    if uid in _tool_create_step:
        step = _tool_create_step[uid]
        data = _tool_create_data[uid]
        if step == "desc":
            data["description"] = text
            _tool_create_step[uid] = "code"
            await update.effective_message.reply_text(
                f"{EMOJI['plus']} <b>Create Tool: {data['name']}</b>\n\nStep 3/3: Send the Python code (define `run` function):",
                parse_mode=ParseMode.HTML,
            )
            return
        if step == "code":
            data["code"] = text
            reg: ToolRegistry = context.bot_data["tools"]
            if reg.create(data["name"], data["description"], data["code"], uid):
                await update.effective_message.reply_text(f"{EMOJI['success']} Tool created: {data['name']}", parse_mode=ParseMode.HTML)
            else:
                await update.effective_message.reply_text(f"❌ Tool already exists: {data['name']}", parse_mode=ParseMode.HTML)
            _tool_create_step.pop(uid, None)
            _tool_create_data.pop(uid, None)
            return

    # Editing file
    if uid in _editing_file:
        fp = _editing_file.pop(uid)
        sp = _safe_path(fp)
        try:
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            with open(sp, "w", encoding="utf-8") as f:
                f.write(text)
            await update.effective_message.reply_text(f"✅ Written: {fp} ({len(text)} bytes)", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)
        return

    await update.effective_message.reply_text(
        "ℹ️ Use /help for commands, or /agent <task> for autonomous coding.",
        parse_mode=ParseMode.HTML,
    )

# ============================================================================
# APPLICATION BUILDER
# ============================================================================

def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db"] = Database(db_path=DB_PATH)
    app.bot_data["rate_limiter"] = RateLimiter(max_calls_per_minute=RATE_LIMIT_PER_MIN)
    app.bot_data["ai"] = AIClient()
    app.bot_data["terminal"] = TerminalEngine(workspace=WORKSPACE_DIR, db=app.bot_data["db"])
    app.bot_data["skills"] = SkillRegistry(db=app.bot_data["db"], skills_dir=SKILLS_DIR, terminal=app.bot_data["terminal"])
    app.bot_data["tools"] = ToolRegistry(db=app.bot_data["db"], tools_dir=TOOLS_DIR)
    app.bot_data["task_manager"] = TaskTemplateManager(db=app.bot_data["db"], tasks_dir=TASKS_DIR)

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    app.add_handler(CommandHandler("ban", ban_handler))
    app.add_handler(CommandHandler("unban", unban_handler))
    app.add_handler(CommandHandler("run", run_cmd_handler))
    app.add_handler(CommandHandler("npm", npm_handler))
    app.add_handler(CommandHandler("pip", pip_handler))
    app.add_handler(CommandHandler("git", git_handler))
    app.add_handler(CommandHandler("build", build_handler))
    app.add_handler(CommandHandler("test", test_handler))
    app.add_handler(CommandHandler("history", history_handler))
    app.add_handler(CommandHandler("ls", ls_handler))
    app.add_handler(CommandHandler("mkdir", mkdir_handler))
    app.add_handler(CommandHandler("read", read_handler))
    app.add_handler(CommandHandler("write", write_handler))
    app.add_handler(CommandHandler("edit", edit_handler))
    app.add_handler(CommandHandler("agent", agent_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("cancel", cancel_handler))
    app.add_handler(CommandHandler("skill", lambda u, c: _skill_dispatch(u, c)))
    app.add_handler(CommandHandler("tool", lambda u, c: _tool_dispatch(u, c)))
    app.add_handler(CommandHandler("task", lambda u, c: _task_dispatch(u, c)))
    app.add_handler(CommandHandler("preview", lambda u, c: _website_dispatch(u, c, "preview")))
    app.add_handler(CommandHandler("server-start", lambda u, c: _website_dispatch(u, c, "server-start")))
    app.add_handler(CommandHandler("server-stop", lambda u, c: _website_dispatch(u, c, "server-stop")))
    app.add_handler(CommandHandler("server-status", lambda u, c: _website_dispatch(u, c, "server-status")))
    app.add_handler(CommandHandler("screenshot", lambda u, c: _website_dispatch(u, c, "screenshot")))
    app.add_handler(CommandHandler("tunnel", lambda u, c: _website_dispatch(u, c, "tunnel")))
    app.add_handler(CommandHandler("website-status", lambda u, c: _website_dispatch(u, c, "website-status")))
    app.add_handler(CommandHandler("db-connect", lambda u, c: _db_dispatch(u, c, "connect")))
    app.add_handler(CommandHandler("db-query", lambda u, c: _db_dispatch(u, c, "query")))
    app.add_handler(CommandHandler("db-list", lambda u, c: _db_dispatch(u, c, "list")))
    app.add_handler(CommandHandler("backup", lambda u, c: _backup_dispatch(u, c, "create")))
    app.add_handler(CommandHandler("restore", lambda u, c: _backup_dispatch(u, c, "restore")))
    app.add_handler(CommandHandler("backup-list", lambda u, c: _backup_dispatch(u, c, "list")))
    app.add_handler(CommandHandler("env-set", lambda u, c: _env_dispatch(u, c, "set")))
    app.add_handler(CommandHandler("env-get", lambda u, c: _env_dispatch(u, c, "get")))
    app.add_handler(CommandHandler("env-list", lambda u, c: _env_dispatch(u, c, "list")))
    app.add_handler(CommandHandler("api-test", lambda u, c: _api_dispatch(u, c, "test")))
    app.add_handler(CommandHandler("translate", lambda u, c: _api_dispatch(u, c, "translate")))
    app.add_handler(CommandHandler("performance", lambda u, c: _api_dispatch(u, c, "performance")))
    app.add_handler(CommandHandler("deploy", lambda u, c: _api_dispatch(u, c, "deploy")))
    app.add_handler(CommandHandler("auto-commit", lambda u, c: _api_dispatch(u, c, "auto-commit")))
    app.add_handler(CommandHandler("diff", lambda u, c: _code_dispatch(u, c, "diff")))
    app.add_handler(CommandHandler("lint", lambda u, c: _code_dispatch(u, c, "lint")))
    app.add_handler(CommandHandler("deps", lambda u, c: _code_dispatch(u, c, "deps")))
    app.add_handler(CommandHandler("init", lambda u, c: _code_dispatch(u, c, "init")))
    app.add_handler(CommandHandler("review", lambda u, c: _code_dispatch(u, c, "review")))
    app.add_handler(CommandHandler("docker", lambda u, c: _code_dispatch(u, c, "docker")))
    app.add_handler(CommandHandler("format", lambda u, c: _code_dispatch(u, c, "format")))
    app.add_handler(CommandHandler("search", lambda u, c: _code_dispatch(u, c, "search")))
    app.add_handler(CommandHandler("replace", lambda u, c: _code_dispatch(u, c, "replace")))
    app.add_handler(CommandHandler("branch", lambda u, c: _code_dispatch(u, c, "branch")))
    app.add_handler(CommandHandler("scaffold", lambda u, c: _code_dispatch(u, c, "scaffold")))
    app.add_handler(CommandHandler("chain", lambda u, c: _code_dispatch(u, c, "chain")))
    app.add_handler(CommandHandler("apk-build", lambda u, c: _code_dispatch(u, c, "apk-build")))
    app.add_handler(CommandHandler("apk-info", lambda u, c: _code_dispatch(u, c, "apk-info")))
    app.add_handler(CommandHandler("apk-install", lambda u, c: _code_dispatch(u, c, "apk-install")))
    app.add_handler(CommandHandler("sandbox-run", lambda u, c: _code_dispatch(u, c, "sandbox-run")))
    app.add_handler(CommandHandler("sandbox-list", lambda u, c: _code_dispatch(u, c, "sandbox-list")))
    app.add_handler(CommandHandler("apk-decompile", lambda u, c: _code_dispatch(u, c, "apk-decompile")))
    app.add_handler(CommandHandler("apk-edit", lambda u, c: _code_dispatch(u, c, "apk-edit")))
    app.add_handler(CommandHandler("apk-change", lambda u, c: _code_dispatch(u, c, "apk-change")))
    app.add_handler(CommandHandler("apk-rebuild", lambda u, c: _code_dispatch(u, c, "apk-rebuild")))

    app.add_handler(CommandHandler("auto-learn-skill", lambda u, c: _code_dispatch(u, c, "auto-learn-skill")))
    app.add_handler(CommandHandler("auto-create-tool", lambda u, c: _code_dispatch(u, c, "auto-create-tool")))
    app.add_handler(CommandHandler("auto-use-skill", lambda u, c: _code_dispatch(u, c, "auto-use-skill")))
    app.add_handler(CommandHandler("auto-use-tool", lambda u, c: _code_dispatch(u, c, "auto-use-tool")))
    app.add_handler(CommandHandler("push-repo", lambda u, c: _code_dispatch(u, c, "push-repo")))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    logger.info("Application built.")
    return app


# Sub-dispatchers for simplified command registration

async def _skill_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("🧠 Skills: /skill list | /skill run <name> | /skill create <name> | /skill delete <name> | /skill info <name>", parse_mode=ParseMode.HTML)
        return
    sub = args[0].lower()
    context.args = args[1:]
    dispatch = {"list": skill_list_handler, "run": skill_run_handler, "create": skill_create_handler, "delete": skill_delete_handler, "info": skill_info_handler}
    h = dispatch.get(sub)
    if h:
        await h(update, context)
    else:
        await update.effective_message.reply_text("❌ Unknown skill subcommand.", parse_mode=ParseMode.HTML)


async def _tool_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("🔧 Tools: /tool list | /tool run <name> | /tool create <name> | /tool delete <name>", parse_mode=ParseMode.HTML)
        return
    sub = args[0].lower()
    context.args = args[1:]
    dispatch = {"list": tool_list_handler, "run": tool_run_handler, "create": tool_create_handler, "delete": tool_delete_handler}
    h = dispatch.get(sub)
    if h:
        await h(update, context)
    else:
        await update.effective_message.reply_text("❌ Unknown tool subcommand.", parse_mode=ParseMode.HTML)


async def _task_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("📋 Tasks: /task save <name> | /task list | /task run <name> | /task delete <name>", parse_mode=ParseMode.HTML)
        return
    sub = args[0].lower()
    context.args = args[1:]
    dispatch = {"save": task_save_handler, "list": task_list_handler, "run": task_run_handler, "delete": task_delete_handler}
    h = dispatch.get(sub)
    if h:
        await h(update, context)
    else:
        await update.effective_message.reply_text("❌ Unknown task subcommand.", parse_mode=ParseMode.HTML)


async def _website_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE, sub: str) -> None:
    user = update.effective_user
    if not user:
        return
    term: TerminalEngine = context.bot_data["terminal"]
    if sub == "preview":
        port_str = context.args[0] if context.args else "8000"
        try:
            port = int(port_str)
        except ValueError:
            port = 8000

        def start_server():
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", port), handler) as httpd:
                httpd.serve_forever()

        if user.id in _website_servers:
            old = _website_servers[user.id]
            try:
                old["process"].terminate()
            except Exception:
                pass

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        _website_servers[user.id] = {"port": port, "process": server_thread, "directory": WORKSPACE_DIR, "url": f"http://localhost:{port}", "started_at": datetime.now(timezone.utc).isoformat()}
        await update.effective_message.reply_text(
            f"{EMOJI['preview']} <b>Website Preview Started</b>\n\n<b>URL:</b> http://localhost:{port}\n<b>Directory:</b> {WORKSPACE_DIR}\n<b>Port:</b> {port}\n\nUse /server-status to check, /server-stop to stop.",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "server-stop":
        if user.id not in _website_servers:
            await update.effective_message.reply_text(f"{EMOJI['error']} No server running.", parse_mode=ParseMode.HTML)
            return
        server_info = _website_servers.pop(user.id)
        try:
            server_info["process"].terminate()
        except Exception:
            pass
        await update.effective_message.reply_text(
            f"{EMOJI['server']} <b>Server Stopped</b>\n\n<b>Port:</b> {server_info['port']}\n<b>URL was:</b> {server_info['url']}",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "server-status":
        if user.id not in _website_servers:
            await update.effective_message.reply_text(f"{EMOJI['error']} No server running.\nUse /preview <port> to start one.", parse_mode=ParseMode.HTML)
            return
        info = _website_servers[user.id]
        await update.effective_message.reply_text(
            f"{EMOJI['server']} <b>Server Status</b>\n\n<b>URL:</b> {info['url']}\n<b>Port:</b> {info['port']}\n<b>Directory:</b> {info['directory']}\n<b>Started:</b> {info['started_at']}",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "screenshot":
        url = context.args[0] if context.args else _website_servers.get(user.id, {}).get("url", "")
        if not url:
            await update.effective_message.reply_text(f"{EMOJI['error']} No URL specified.\nUsage: /screenshot <url>\nOr start a server first with /preview", parse_mode=ParseMode.HTML)
            return
        import subprocess
        try:
            result = subprocess.run(f"python3 -c \"from PIL import ImageGrab; img = ImageGrab.grab(); img.save('/tmp/screenshot_{user.id}.png')\" 2>&1", shell=True, capture_output=True, text=True, timeout=10)
            screenshot_path = f"/tmp/screenshot_{user.id}.png"
            if os.path.exists(screenshot_path):
                await update.effective_message.reply_photo(photo=open(screenshot_path, "rb"), caption=f"{EMOJI['screenshot']} <b>Screenshot Captured</b>\n<b>URL:</b> {url}", parse_mode=ParseMode.HTML)
            else:
                await update.effective_message.reply_text(f"{EMOJI['error']} Screenshot tool not available.\nInstall: pip install pillow", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.effective_message.reply_text(f"{EMOJI['error']} Screenshot failed: {e}", parse_mode=ParseMode.HTML)
    elif sub == "tunnel":
        port_str = context.args[0] if context.args else "8000"
        try:
            port = int(port_str)
        except ValueError:
            port = 8000
        result = term.run(user.id, f"npx localtunnel --port {port} 2>&1 || echo 'Localtunnel not available. Install: npm install -g localtunnel'", admin=(user.id in ADMIN_IDS))
        await update.effective_message.reply_text(
            f"{EMOJI['tunnel']} <b>Tunnel Request</b>\n\n<b>Port:</b> {port}\n<b>Result:</b>\n<pre>{result['output']}</pre>",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "website-status":
        url = context.args[0] if context.args else _website_servers.get(user.id, {}).get("url", "")
        if not url:
            await update.effective_message.reply_text(f"{EMOJI['error']} No URL specified.\nUsage: /website-status <url>\nOr start a server first with /preview", parse_mode=ParseMode.HTML)
            return
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                headers = dict(resp.headers)
            await update.effective_message.reply_text(
                f"{EMOJI['website']} <b>Website Status: {url}</b>\n\n<b>HTTP Status:</b> {status}\n<b>Server:</b> {headers.get('Server', 'Unknown')}\n<b>Content-Type:</b> {headers.get('Content-Type', 'Unknown')}",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await update.effective_message.reply_text(f"{EMOJI['error']} Website check failed: {url}\nError: {e}", parse_mode=ParseMode.HTML)


async def _db_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE, sub: str) -> None:
    user = update.effective_user
    if not user:
        return
    if sub == "connect":
        if not context.args:
            await update.effective_message.reply_text("🗄️ <b>Database Connect</b>\n\nUsage: /db-connect <type> <host> <port> <user> <password> <database>\nTypes: mysql, postgres, mongodb\nExample: /db-connect mysql localhost 3306 root mypass mydb", parse_mode=ParseMode.HTML)
            return
        db_type = context.args[0].lower()
        if len(context.args) < 6:
            await update.effective_message.reply_text("❌ Missing arguments.\nUsage: /db-connect <type> <host> <port> <user> <password> <database>", parse_mode=ParseMode.HTML)
            return
        host = context.args[1]
        try:
            port = int(context.args[2])
        except ValueError:
            await update.effective_message.reply_text("❌ Invalid port number.", parse_mode=ParseMode.HTML)
            return
        db_user = context.args[3]
        password = context.args[4]
        database = context.args[5]
        if db_type == "mysql":
            result = db_manager.connect_mysql(host, port, db_user, password, database)
        elif db_type == "postgres":
            result = db_manager.connect_postgresql(host, port, db_user, password, database)
        elif db_type == "mongodb":
            result = db_manager.connect_mongodb(host, port, db_user, password, database)
        else:
            result = f"❌ Unknown database type: {db_type}\nSupported: mysql, postgres, mongodb"
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "query":
        if len(context.args) < 2:
            await update.effective_message.reply_text("🗄️ <b>Database Query</b>\n\nUsage: /db-query <connection_key> <sql_query>\nExample: /db-query mysql:localhost:3306:mydb 'SELECT * FROM users'", parse_mode=ParseMode.HTML)
            return
        conn_key = context.args[0]
        query = " ".join(context.args[1:])
        result = db_manager.execute_query(conn_key, query)
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "list":
        result = db_manager.list_connections()
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


async def _backup_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE, sub: str) -> None:
    user = update.effective_user
    if not user:
        return
    if sub == "create":
        name = context.args[0] if context.args else "backup"
        result = _create_backup(user.id, name)
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "restore":
        if not context.args:
            await update.effective_message.reply_text("Usage: /restore <backup_name>\nUse /backup-list to see available backups.", parse_mode=ParseMode.HTML)
            return
        name = context.args[0]
        result = _restore_backup(user.id, name)
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "list":
        result = _list_backups(user.id)
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


async def _env_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE, sub: str) -> None:
    if sub == "set":
        if len(context.args) < 1 or "=" not in context.args[0]:
            await update.effective_message.reply_text("Usage: /env-set KEY=VALUE\nExample: /env-set NODE_ENV=production", parse_mode=ParseMode.HTML)
            return
        key, value = context.args[0].split("=", 1)
        result = _env_set(key.strip(), value.strip())
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "get":
        if not context.args:
            await update.effective_message.reply_text("Usage: /env-get KEY", parse_mode=ParseMode.HTML)
            return
        result = _env_get(context.args[0])
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "list":
        result = _env_list()
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


async def _api_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE, sub: str) -> None:
    if sub == "test":
        if not context.args:
            await update.effective_message.reply_text("Usage: /api-test <url> [method] [body]\nExample: /api-test https://api.example.com/users GET", parse_mode=ParseMode.HTML)
            return
        url = context.args[0]
        method = context.args[1] if len(context.args) > 1 else "GET"
        body = context.args[2] if len(context.args) > 2 else None
        result = _api_test(url, method=method, body=body)
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "translate":
        if len(context.args) < 3:
            await update.effective_message.reply_text("Usage: /translate <from_lang> <to_lang> <file_path>\nExample: /translate python javascript app.py", parse_mode=ParseMode.HTML)
            return
        from_lang = context.args[0]
        to_lang = context.args[1]
        file_path = context.args[2]
        sp = _safe_path(file_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ File not found: {file_path}", parse_mode=ParseMode.HTML)
            return
        with open(sp, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"
        ai: AIClient = context.bot_data["ai"]
        if not ai.is_available():
            await update.effective_message.reply_text("⚠️ AI provider not configured.", parse_mode=ParseMode.HTML)
            return
        translate_prompt = (f"Translate this code from {from_lang} to {to_lang}:\n\nFile: {file_path}\n\n{content}\n\nProvide the translated code with brief comments explaining changes.")
        translate_resp = ai.generate(prompt=translate_prompt, system_prompt="You are an expert polyglot programmer. Translate code accurately.", max_tokens=2000, temperature=0.3)
        await update.effective_message.reply_text(
            f"🔄 <b>Code Translation: {from_lang} → {to_lang}</b>\n<b>File:</b> {file_path}\n\n{translate_resp}",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "performance":
        result = _get_performance()
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "deploy":
        if not context.args:
            await update.effective_message.reply_text("Usage: /deploy <type>\nTypes: npm, python, flask, fastapi", parse_mode=ParseMode.HTML)
            return
        project_type = context.args[0].lower()
        result = _auto_deploy(project_type)
        await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    elif sub == "auto-commit":
        user = update.effective_user
        if not user:
            return
        msg = " ".join(context.args) if context.args else "Auto-commit by Coding Agent"
        res_add = context.bot_data["terminal"].run(user.id, "git add .", admin=(user.id in ADMIN_IDS))
        res_commit = context.bot_data["terminal"].run(user.id, f'git commit -m "{msg}"', admin=(user.id in ADMIN_IDS))
        await update.effective_message.reply_text(
            f"💾 <b>Auto-Commit</b>\n\n<b>Add:</b>\n<pre>{res_add['output']}</pre>\n\n<b>Commit:</b>\n<pre>{res_commit['output']}</pre>",
            parse_mode=ParseMode.HTML,
        )


async def _code_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE, sub: str) -> None:
    user = update.effective_user
    if not user:
        return
    term: TerminalEngine = context.bot_data["terminal"]
    if sub == "diff":
        if not context.args:
            await update.effective_message.reply_text("Usage: /diff <file_path>", parse_mode=ParseMode.HTML)
            return
        file_path = context.args[0]
        res = term.run(user.id, f"git diff -- {file_path}", admin=(user.id in ADMIN_IDS))
        if not res["output"].strip() or res["output"] == "(no output)":
            res["output"] = "No changes detected or not a git repo."
        await update.effective_message.reply_text(f"{EMOJI['stats']} <b>Diff: {file_path}</b>\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "lint":
        if not rl_allowed(context, user.id):
            return
        res = term.run(user.id, "npx eslint . 2>&1 || python -m pylint . 2>&1 || echo 'No linter configured'", admin=(user.id in ADMIN_IDS))
        await update.effective_message.reply_text(f"{EMOJI['info']} <b>Lint Results</b>\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "deps":
        res1 = term.run(user.id, "cat package.json 2>&1 || echo 'No package.json'", admin=(user.id in ADMIN_IDS))
        res2 = term.run(user.id, "cat requirements.txt 2>&1 || echo 'No requirements.txt'", admin=(user.id in ADMIN_IDS))
        await update.effective_message.reply_text(f"{EMOJI['list']} <b>Dependencies</b>\n\n<b>package.json:</b>\n<pre>{res1['output']}</pre>\n\n<b>requirements.txt:</b>\n<pre>{res2['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "init":
        if not context.args:
            await update.effective_message.reply_text("Usage: /init <type>\nTypes: npm, python", parse_mode=ParseMode.HTML)
            return
        project_type = context.args[0].lower()
        if project_type in ("npm", "node", "javascript"):
            res1 = term.run(user.id, "npm init -y", admin=(user.id in ADMIN_IDS))
            res2 = term.run(user.id, "git init", admin=(user.id in ADMIN_IDS))
            await update.effective_message.reply_text(f"{EMOJI['plus']} <b>Init npm+git</b>\n\n<b>npm init:</b>\n<pre>{res1['output']}</pre>\n\n<b>git init:</b>\n<pre>{res2['output']}</pre>", parse_mode=ParseMode.HTML)
        elif project_type in ("python", "py"):
            res1 = term.run(user.id, "python3 -m venv venv 2>&1 || echo 'venv exists'", admin=(user.id in ADMIN_IDS))
            res2 = term.run(user.id, "git init", admin=(user.id in ADMIN_IDS))
            await update.effective_message.reply_text(f"{EMOJI['plus']} <b>Init Python+git</b>\n\n<b>venv:</b>\n<pre>{res1['output']}</pre>\n\n<b>git init:</b>\n<pre>{res2['output']}</pre>", parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(f"❌ Unknown project type: {project_type}\nTypes: npm, python", parse_mode=ParseMode.HTML)
    elif sub == "review":
        if not context.args:
            await update.effective_message.reply_text("Usage: /review <file_path>", parse_mode=ParseMode.HTML)
            return
        file_path = context.args[0]
        sp = _safe_path(file_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ File not found: {file_path}", parse_mode=ParseMode.HTML)
            return
        with open(sp, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 4000:
            content = content[:4000] + "\n... (truncated)"
        ai: AIClient = context.bot_data["ai"]
        if not ai.is_available():
            await update.effective_message.reply_text("⚠️ AI provider not configured.", parse_mode=ParseMode.HTML)
            return
        review_prompt = (f"Review this code for bugs, security issues, and improvements:\n\nFile: {file_path}\n\n{content}\n\nProvide a concise review with: 1) Issues found, 2) Suggestions, 3) Rating (1-10).")
        review_resp = ai.generate(prompt=review_prompt, system_prompt="You are a senior code reviewer. Be concise and actionable.", max_tokens=1500, temperature=0.3)
        await update.effective_message.reply_text(
            f"{EMOJI['info']} <b>Code Review: {file_path}</b>\n\n{review_resp}",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "docker":
        if not context.args:
            await update.effective_message.reply_text("Usage: /docker <command>\nExamples: /docker ps, /docker build -t myapp ., /docker run -p 3000:3000 myapp", parse_mode=ParseMode.HTML)
            return
        cmd = " ".join(context.args)
        res = term.run(user.id, f"docker {cmd}", admin=(user.id in ADMIN_IDS))
        emoji = EMOJI['success'] if res["success"] else EMOJI['error']
        await update.effective_message.reply_text(f"{emoji} <b>Docker {cmd}</b>\nExit: {res['exit_code']}\n\n<pre>{res['output'][:3000]}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "format":
        if not context.args:
            await update.effective_message.reply_text("Usage: /format <file_path>", parse_mode=ParseMode.HTML)
            return
        file_path = context.args[0]
        sp = _safe_path(file_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ File not found: {file_path}", parse_mode=ParseMode.HTML)
            return
        if file_path.endswith((".js", ".ts", ".jsx", ".tsx", ".json", ".css", ".html", ".md")):
            res = term.run(user.id, f"npx prettier --write {file_path} 2>&1 || echo 'Prettier not available'", admin=(user.id in ADMIN_IDS))
        elif file_path.endswith(".py"):
            res = term.run(user.id, f"python3 -m black {file_path} 2>&1 || echo 'Black not available'", admin=(user.id in ADMIN_IDS))
        else:
            await update.effective_message.reply_text(f"❌ No formatter for: {file_path}\nSupported: .js, .ts, .jsx, .tsx, .json, .css, .html, .md, .py", parse_mode=ParseMode.HTML)
            return
        await update.effective_message.reply_text(f"{EMOJI['info']} <b>Format: {file_path}</b>\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "search":
        if not context.args:
            await update.effective_message.reply_text("Usage: /search <pattern>", parse_mode=ParseMode.HTML)
            return
        pattern = " ".join(context.args)
        res = term.run(user.id, f"grep -rn '{pattern}' . --include='*.py' --include='*.js' --include='*.ts' --include='*.html' --include='*.css' --include='*.json' 2>/dev/null | head -50", admin=(user.id in ADMIN_IDS))
        if not res["output"].strip():
            res["output"] = "No matches found."
        await update.effective_message.reply_text(f"{EMOJI['search']} <b>Search: '{pattern}'</b>\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "replace":
        if len(context.args) < 3:
            await update.effective_message.reply_text("Usage: /replace <file_path> <old_string> <new_string>", parse_mode=ParseMode.HTML)
            return
        file_path = context.args[0]
        old_str = context.args[1]
        new_str = context.args[2]
        sp = _safe_path(file_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ File not found: {file_path}", parse_mode=ParseMode.HTML)
            return
        with open(sp, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(old_str)
        if count == 0:
            await update.effective_message.reply_text(f"❌ String not found: '{old_str}' in {file_path}", parse_mode=ParseMode.HTML)
            return
        new_content = content.replace(old_str, new_str)
        with open(sp, "w", encoding="utf-8") as f:
            f.write(new_content)
        await update.effective_message.reply_text(f"{EMOJI['cross']} <b>Replace in {file_path}</b>\nReplaced {count} occurrence(s).", parse_mode=ParseMode.HTML)
    elif sub == "branch":
        if not context.args:
            res = term.run(user.id, "git branch", admin=(user.id in ADMIN_IDS))
            await update.effective_message.reply_text(f"{EMOJI['git']} <b>Git Branches</b>\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
            return
        branch_name = context.args[0]
        res = term.run(user.id, f"git checkout -b {branch_name}", admin=(user.id in ADMIN_IDS))
        emoji = EMOJI['success'] if res["success"] else EMOJI['error']
        await update.effective_message.reply_text(f"{emoji} <b>Branch: {branch_name}</b>\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "scaffold":
        if not context.args:
            await update.effective_message.reply_text("Usage: /scaffold <template>\nTemplates: express, react, flask, fastapi", parse_mode=ParseMode.HTML)
            return
        template = context.args[0].lower()
        if template == "express":
            files = {
                "package.json": json.dumps({"name": "my-app", "version": "1.0.0", "scripts": {"start": "node index.js", "dev": "nodemon index.js"}, "dependencies": {"express": "^4.18.2"}}, indent=2),
                "index.js": "const express = require('express');\nconst app = express();\nconst PORT = process.env.PORT || 3000;\n\napp.get('/', (req, res) => res.json({ status: 'ok' }));\napp.get('/health', (req, res) => res.json({ status: 'healthy' }));\n\napp.listen(PORT, () => console.log(`Server running on port ${PORT}`));\n",
                ".gitignore": "node_modules/\n.env\n",
                "README.md": "# My Express App\n\n## Endpoints\n- GET /\n- GET /health\n",
            }
        elif template == "react":
            files = {
                "package.json": json.dumps({"name": "my-react-app", "version": "1.0.0", "scripts": {"start": "react-scripts start", "build": "react-scripts build"}, "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}, indent=2),
                "src/App.js": "import React from 'react';\nfunction App() { return <h1>Hello React</h1>; }\nexport default App;\n",
                "src/index.js": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nReactDOM.createRoot(document.getElementById('root')).render(<App />);\n",
                "public/index.html": "<!DOCTYPE html><html><head><title>React App</title></head><body><div id=\"root\"></div></body></html>\n",
                ".gitignore": "node_modules/\nbuild/\n.env\n",
            }
        elif template == "flask":
            files = {
                "requirements.txt": "flask==3.0.0\n",
                "app.py": "from flask import Flask, jsonify\napp = Flask(__name__)\n\n@app.route('/')\ndef index(): return jsonify({'status': 'ok'})\n\n@app.route('/health')\ndef health(): return jsonify({'status': 'healthy'})\n\nif __name__ == '__main__': app.run(debug=True)\n",
                ".gitignore": "venv/\n__pycache__/\n.env\n",
                "README.md": "# Flask App\n\n## Endpoints\n- GET /\n- GET /health\n",
            }
        elif template == "fastapi":
            files = {
                "requirements.txt": "fastapi==0.104.0\nuvicorn==0.24.0\n",
                "main.py": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef index(): return {'status': 'ok'}\n\n@app.get('/health')\ndef health(): return {'status': 'healthy'}\n",
                ".gitignore": "venv/\n__pycache__/\n.env\n",
                "README.md": "# FastAPI App\n\n## Endpoints\n- GET /\n- GET /health\n",
            }
        else:
            await update.effective_message.reply_text(f"❌ Unknown template: {template}\nUse: express, react, flask, fastapi", parse_mode=ParseMode.HTML)
            return
        written = []
        for path, content in files.items():
            sp = _safe_path(path)
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            with open(sp, "w", encoding="utf-8") as f:
                f.write(content)
            written.append(path)
        term.run(user.id, "git init", admin=(user.id in ADMIN_IDS))
        await update.effective_message.reply_text(
            f"{EMOJI['plus']} <b>Scaffold: {template}</b>\n\n" + "\n".join(f"✅ {w}" for w in written) + "\n\n🌿 Git initialized.",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "chain":
        if not context.args:
            await update.effective_message.reply_text("Usage: /chain <task_1> | <task_2> | <task_3>\nExample: /chain Create Express API | Add health endpoint | Write tests", parse_mode=ParseMode.HTML)
            return
        tasks = [t.strip() for t in " ".join(context.args).split("|") if t.strip()]
        if not tasks:
            await update.effective_message.reply_text("❌ No tasks provided.", parse_mode=ParseMode.HTML)
            return
        db: Database = context.bot_data["db"]
        ai: AIClient = context.bot_data["ai"]
        if not ai.is_available():
            await update.effective_message.reply_text("⚠️ AI provider not configured.", parse_mode=ParseMode.HTML)
            return
        tid = db.create_task(user.id, "task_chain")
        db.update_task(tid, "running")
        chain_state = {"tasks": tasks, "index": 0, "completed": [], "results": []}
        db.create_checkpoint(user_id=user.id, task_id=tid, description="Chain initialized", state=chain_state)
        _active_tasks[user.id] = tid
        first_task = tasks[0]
        await update.effective_message.reply_text(
            f"{EMOJI['rocket']} <b>Task Chain Started</b>\n\n<b>Chain ID:</b> {tid}\n<b>Total tasks:</b> {len(tasks)}\n<b>Current:</b> 1/{len(tasks)} - {first_task}\n\n{EMOJI['running']} Executing...",
            parse_mode=ParseMode.HTML,
        )
        await _run_agent_loop(context, user.id, tid, first_task, is_chain=True, chain_state=chain_state)

    elif sub == "apk-build":
        if not context.args:
            await update.effective_message.reply_text("Usage: /apk-build <project_path>\nExample: /apk-build ./my-android-app", parse_mode=ParseMode.HTML)
            return
        project_path = context.args[0]
        sp = _safe_path(project_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ Project not found: {project_path}", parse_mode=ParseMode.HTML)
            return
        gradlew = os.path.join(sp, "gradlew")
        build_gradle = os.path.join(sp, "build.gradle")
        build_gradle_kts = os.path.join(sp, "build.gradle.kts")
        if os.path.exists(gradlew):
            res = term.run(user.id, f"cd {sp} && ./gradlew assembleDebug", admin=(user.id in ADMIN_IDS), timeout=300)
        elif os.path.exists(build_gradle) or os.path.exists(build_gradle_kts):
            res = term.run(user.id, f"cd {sp} && gradle assembleDebug", admin=(user.id in ADMIN_IDS), timeout=300)
        else:
            await update.effective_message.reply_text(f"❌ No Android project found at {project_path} (no gradlew or build.gradle)", parse_mode=ParseMode.HTML)
            return
        apk_path = ""
        for root, dirs, files in os.walk(sp):
            for f in files:
                if f.endswith("-debug.apk"):
                    apk_path = os.path.join(root, f)
                    break
            if apk_path:
                break
        if apk_path:
            res["output"] += f"\n\n📱 APK built: {apk_path}\nSize: {os.path.getsize(apk_path)} bytes"
        emoji = EMOJI['success'] if res["success"] else EMOJI['error']
        await update.effective_message.reply_text(
            f"{emoji} <b>APK Build: {project_path}</b>\n\n<pre>{res['output']}</pre>",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "apk-info":
        if not context.args:
            await update.effective_message.reply_text("Usage: /apk-info <apk_path>", parse_mode=ParseMode.HTML)
            return
        apk_path = context.args[0]
        sp = _safe_path(apk_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ APK not found: {apk_path}", parse_mode=ParseMode.HTML)
            return
        res = term.run(user.id, f"aapt dump badging {sp}", admin=(user.id in ADMIN_IDS))
        if not res["output"].strip() or "not found" in res["output"].lower():
            import zipfile
            try:
                with zipfile.ZipFile(sp, 'r') as z:
                    manifest = z.read("AndroidManifest.xml").decode('utf-8', errors='replace')[:2000]
                    res["output"] = f"APK Size: {os.path.getsize(sp)} bytes\n\nManifest (raw):\n{manifest}"
            except Exception as e:
                res["output"] = f"❌ Cannot read APK: {e}"
        await update.effective_message.reply_text(f"{EMOJI['apk']} <b>APK Info: {apk_path}</b>\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "apk-install":
        if not context.args:
            await update.effective_message.reply_text("Usage: /apk-install <apk_path>", parse_mode=ParseMode.HTML)
            return
        apk_path = context.args[0]
        sp = _safe_path(apk_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ APK not found: {apk_path}", parse_mode=ParseMode.HTML)
            return
        res = term.run(user.id, f"adb install {sp}", admin=(user.id in ADMIN_IDS))
        emoji = EMOJI['success'] if res["success"] else EMOJI['error']
        await update.effective_message.reply_text(
            f"{emoji} <b>APK Install: {apk_path}</b>\n\n<pre>{res['output']}</pre>",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "sandbox-run":
        if not context.args:
            await update.effective_message.reply_text("Usage: /sandbox-run <command>", parse_mode=ParseMode.HTML)
            return
        command = " ".join(context.args)
        import tempfile
        sandbox_dir = os.path.join(WORKSPACE_DIR, ".sandbox")
        os.makedirs(sandbox_dir, exist_ok=True)
        sandbox_id = f"sandbox_{int(time.time())}"
        sandbox_path = os.path.join(sandbox_dir, sandbox_id)
        os.makedirs(sandbox_path, exist_ok=True)
        try:
            res = term.run(user.id, f"cd {sandbox_path} && {command}", admin=(user.id in ADMIN_IDS), timeout=60)
        except Exception as e:
            res = {"success": False, "output": f"❌ Sandbox error: {e}", "exit_code": -1}
        try:
            import shutil
            shutil.rmtree(sandbox_path, ignore_errors=True)
        except Exception:
            pass
        emoji = EMOJI['success'] if res["success"] else EMOJI['error']
        await update.effective_message.reply_text(
            f"{emoji} <b>Sandbox Run</b>\n<b>Command:</b> {command}\n\n<pre>{res['output']}</pre>",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "sandbox-list":
        sandbox_dir = os.path.join(WORKSPACE_DIR, ".sandbox")
        if not os.path.exists(sandbox_dir):
            await update.effective_message.reply_text(f"{EMOJI['sandbox']} <b>Sandboxes</b>\n\nNo active sandboxes.", parse_mode=ParseMode.HTML)
            return
        sandboxes = []
        for d in os.listdir(sandbox_dir):
            dpath = os.path.join(sandbox_dir, d)
            if os.path.isdir(dpath):
                try:
                    mtime = os.path.getmtime(dpath)
                    sandboxes.append((d, mtime))
                except Exception:
                    pass
        sandboxes.sort(key=lambda x: x[1], reverse=True)
        lines = [f"• {name}" for name, _ in sandboxes[:20]]
        await update.effective_message.reply_text(
            f"{EMOJI['sandbox']} <b>Active Sandboxes</b>\n\n" + "\n".join(lines) if lines else "No active sandboxes.",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "apk-decompile":
        if not context.args:
            await update.effective_message.reply_text("Usage: /apk-decompile <apk_path>", parse_mode=ParseMode.HTML)
            return
        apk_path = context.args[0]
        sp = _safe_path(apk_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ APK not found: {apk_path}", parse_mode=ParseMode.HTML)
            return
        decompile_dir = os.path.join(WORKSPACE_DIR, ".apk_decompile", os.path.splitext(os.path.basename(apk_path))[0])
        os.makedirs(decompile_dir, exist_ok=True)
        res = term.run(user.id, f"apktool d {sp} -o {decompile_dir} -f", admin=(user.id in ADMIN_IDS), timeout=120)
        if not res["success"] or "not found" in res["output"].lower():
            import zipfile
            try:
                with zipfile.ZipFile(sp, 'r') as z:
                    z.extractall(decompile_dir)
                res["output"] = f"Extracted APK contents to {decompile_dir}\nFiles: {len(os.listdir(decompile_dir))}"
            except Exception as e:
                res["output"] = f"❌ Cannot decompile APK: {e}"
        await update.effective_message.reply_text(f"{EMOJI['apk']} <b>APK Decompile: {apk_path}</b>\nOutput: {decompile_dir}\n\n<pre>{res['output']}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "apk-edit":
        if len(context.args) < 3:
            await update.effective_message.reply_text("Usage: /apk-edit <decompile_dir> <file_path> <content>", parse_mode=ParseMode.HTML)
            return
        decompile_dir = context.args[0]
        file_path = context.args[1]
        new_content = context.args[2]
        sp = _safe_path(os.path.join(decompile_dir, file_path))
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ File not found in decompiled APK: {file_path}", parse_mode=ParseMode.HTML)
            return
        try:
            with open(sp, "w", encoding="utf-8") as f:
                f.write(new_content)
            await update.effective_message.reply_text(f"✅ Edited: {file_path} in {decompile_dir}\nSize: {len(new_content)} bytes", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Edit failed: {e}", parse_mode=ParseMode.HTML)
    elif sub == "apk-change":
        if len(context.args) < 2:
            await update.effective_message.reply_text("Usage: /apk-change <apk_path> <description>", parse_mode=ParseMode.HTML)
            return
        apk_path = context.args[0]
        change_desc = context.args[1]
        sp = _safe_path(apk_path)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ APK not found: {apk_path}", parse_mode=ParseMode.HTML)
            return
        change_log = os.path.join(WORKSPACE_DIR, ".apk_changes.txt")
        with open(change_log, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} | {apk_path} | {change_desc}\n")
        await update.effective_message.reply_text(f"✅ Change recorded: {change_desc}\nAPK: {apk_path}\nUse /apk-rebuild to apply changes.", parse_mode=ParseMode.HTML)
    elif sub == "apk-rebuild":
        if len(context.args) < 2:
            await update.effective_message.reply_text("Usage: /apk-rebuild <decompile_dir> <output_apk_path>", parse_mode=ParseMode.HTML)
            return
        decompile_dir = context.args[0]
        output_apk = context.args[1]
        sp = _safe_path(decompile_dir)
        if not os.path.exists(sp):
            await update.effective_message.reply_text(f"❌ Decompile dir not found: {decompile_dir}", parse_mode=ParseMode.HTML)
            return
        res = term.run(user.id, f"apktool b {sp} -o {output_apk}", admin=(user.id in ADMIN_IDS), timeout=120)
        emoji = EMOJI['success'] if res["success"] else EMOJI['error']
        await update.effective_message.reply_text(
            f"{emoji} <b>APK Rebuild: {output_apk}</b>\n\n<pre>{res['output']}</pre>",
            parse_mode=ParseMode.HTML,
        )
    elif sub == "auto-learn-skill":
        if len(context.args) < 3:
            await update.effective_message.reply_text("Usage: /auto-learn-skill <name> <description> <code>", parse_mode=ParseMode.HTML)
            return
        name = context.args[0]
        description = context.args[1]
        code = context.args[2]
        reg: SkillRegistry = context.bot_data["skills"]
        if reg.create(name, description, code, "auto_learned", user.id):
            await update.effective_message.reply_text(f"{EMOJI['skill']} <b>Auto-Learned Skill: {name}</b>\nDescription: {description}", parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(f"❌ Skill already exists: {name}", parse_mode=ParseMode.HTML)
    elif sub == "auto-create-tool":
        if len(context.args) < 3:
            await update.effective_message.reply_text("Usage: /auto-create-tool <name> <description> <code>", parse_mode=ParseMode.HTML)
            return
        name = context.args[0]
        description = context.args[1]
        code = context.args[2]
        reg: ToolRegistry = context.bot_data["tools"]
        if reg.create(name, description, code, user.id):
            await update.effective_message.reply_text(f"{EMOJI['tool']} <b>Auto-Created Tool: {name}</b>\nDescription: {description}", parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(f"❌ Tool already exists: {name}", parse_mode=ParseMode.HTML)
    elif sub == "auto-use-skill":
        if not context.args:
            await update.effective_message.reply_text("Usage: /auto-use-skill <skill_name> [args...]", parse_mode=ParseMode.HTML)
            return
        skill_name = context.args[0]
        args = context.args[1:]
        reg: SkillRegistry = context.bot_data["skills"]
        s = reg.get(skill_name)
        if not s:
            await update.effective_message.reply_text(f"❌ Skill not found: {skill_name}", parse_mode=ParseMode.HTML)
            return
        result = s.run(*args) if args else s.run()
        await update.effective_message.reply_text(f"{EMOJI['skill']} <b>Auto-Used Skill: {skill_name}</b>\n\n<pre>{result}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "auto-use-tool":
        if not context.args:
            await update.effective_message.reply_text("Usage: /auto-use-tool <tool_name> [args...]", parse_mode=ParseMode.HTML)
            return
        tool_name = context.args[0]
        args = context.args[1:]
        reg: ToolRegistry = context.bot_data["tools"]
        t = reg.get(tool_name)
        if not t:
            await update.effective_message.reply_text(f"❌ Tool not found: {tool_name}", parse_mode=ParseMode.HTML)
            return
        result = t.run(*args) if args else t.run()
        await update.effective_message.reply_text(f"{EMOJI['tool']} <b>Auto-Used Tool: {tool_name}</b>\n\n<pre>{result}</pre>", parse_mode=ParseMode.HTML)
    elif sub == "push-repo":
        if not context.args:
            await update.effective_message.reply_text("Usage: /push-repo <remote_url> [commit_msg]\nExample: /push-repo https://github.com/user/repo.git \"Auto commit\"", parse_mode=ParseMode.HTML)
            return
        remote_url = context.args[0]
        commit_msg = " ".join(context.args[1:]) if len(context.args) > 1 else "Auto commit from Coding Agent Bot"
        res_add = term.run(user.id, "git add .", admin=(user.id in ADMIN_IDS))
        res_commit = term.run(user.id, f'git commit -m "{commit_msg}"', admin=(user.id in ADMIN_IDS))
        res_remote = term.run(user.id, f"git remote add origin {remote_url} 2>/dev/null || true", admin=(user.id in ADMIN_IDS))
        res_push = term.run(user.id, "git push -u origin HEAD", admin=(user.id in ADMIN_IDS), timeout=120)
        await update.effective_message.reply_text(
            f"{EMOJI['rocket']} <b>Push to Repo</b>\n\n"
            f"<b>Add:</b>\n<pre>{res_add['output']}</pre>\n"
            f"<b>Commit:</b>\n<pre>{res_commit['output']}</pre>\n"
            f"<b>Remote:</b>\n<pre>{res_remote['output']}</pre>\n"
            f"<b>Push:</b>\n<pre>{res_push['output']}</pre>",
            parse_mode=ParseMode.HTML,
        )


def rl_allowed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    rl: RateLimiter = context.bot_data["rate_limiter"]
    if not rl.is_allowed(user_id):
        import asyncio
        # Can't send message here easily, just return False
        return False
    return True


def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set.")
        return
    app = build_application()
    logger.info("Starting Professional Coding Agent Bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
