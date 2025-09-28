from typing import List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path
from services.contracts.models import Conversation, Message

DB_PATH = Path(__file__).parent.parent / 'app' / 'db.sqlite3'

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conv_id TEXT,
    role TEXT,
    content TEXT,
    tool_name TEXT,
    created_at TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)

init_db()

def create_conversation() -> Conversation:
    import uuid
    now = datetime.utcnow().isoformat()
    conv_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at) VALUES (?, ?)",
            (conv_id, now)
        )
    return Conversation(id=conv_id, created_at=now)

def add_message(conv_id: str, role: str, content: str, tool_name: Optional[str] = None) -> Message:
    import uuid
    now = datetime.utcnow().isoformat()
    msg_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (id, conv_id, role, content, tool_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, conv_id, role, content, tool_name, now)
        )
    return Message(role=role, content=content, tool_name=tool_name, created_at=now)

def list_messages(conv_id: str, limit: int = 50) -> List[Message]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, tool_name, created_at FROM messages WHERE conv_id = ? ORDER BY created_at ASC LIMIT ?",
            (conv_id, limit)
        ).fetchall()
    return [Message(**dict(row)) for row in rows]
