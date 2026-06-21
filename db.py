from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import aiosqlite

import asyncpg

from config import POSTGRES_DSN, SQLITE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    chi_score REAL,
    vector TEXT,
    tags TEXT,
    compressed TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS services_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chi_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id INTEGER,
    score REAL NOT NULL,
    channel TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meqlog_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload TEXT,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db() -> None:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(SQLITE_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def save_clip(content: str, chi_score: float | None = None, vector: Any = None, tags: list[str] | None = None, compressed: str | None = None) -> dict[str, Any]:
    await init_db()
    created_at = _now()
    vector_json = json.dumps(vector) if vector is not None else None
    tags_json = json.dumps(tags or [])
    async with aiosqlite.connect(SQLITE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO clips (content, chi_score, vector, tags, compressed, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (content, chi_score, vector_json, tags_json, compressed, created_at),
        )
        await db.commit()
        clip_id = cursor.lastrowid
    await _save_clip_postgres(content, chi_score, vector_json, tags_json, compressed, created_at)
    return {"id": clip_id, "content": content, "chi_score": chi_score, "vector": vector, "tags": tags or [], "compressed": compressed, "created_at": created_at}


async def get_clips(limit: int = 50, offset: int = 0, search: str | None = None) -> list[dict[str, Any]]:
    await init_db()
    query = "SELECT id, content, chi_score, vector, tags, compressed, created_at FROM clips"
    params: list[Any] = []
    if search:
        query += " WHERE content LIKE ? OR tags LIKE ?"
        term = f"%{search}%"
        params.extend([term, term])
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    async with aiosqlite.connect(SQLITE_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(query, params)
    return [_row_to_clip(row) for row in rows]


async def check_postgres_connection() -> bool:
    if not POSTGRES_DSN:
        return False

    conn: asyncpg.Connection | None = None
    try:
        conn = await asyncpg.connect(POSTGRES_DSN)
        await conn.execute("SELECT 1")
        return True
    except Exception:
        return False
    finally:
        if conn is not None:
            await conn.close()


async def sync_to_postgres() -> None:
    """Backward-compatible no-op health check for the default PostgreSQL DSN.

    Clipboard writes are mirrored in ``_save_clip_postgres``.  This periodic
    task only verifies the configured default DSN so older imports keep working
    without implying that a batch sync is happening.
    """
    await check_postgres_connection()


async def sync_loop(interval_seconds: int = 300) -> None:
    while True:
        await check_postgres_connection()
        await asyncio.sleep(interval_seconds)


async def _save_clip_postgres(*args: Any) -> None:
    if not POSTGRES_DSN:
        return

    conn: asyncpg.Connection | None = None
    try:
        conn = await asyncpg.connect(POSTGRES_DSN)
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clips (
                id SERIAL PRIMARY KEY, content TEXT NOT NULL, chi_score DOUBLE PRECISION,
                vector TEXT, tags TEXT, compressed TEXT, created_at TEXT NOT NULL
            )
            """
        )
        await conn.execute(
            "INSERT INTO clips (content, chi_score, vector, tags, compressed, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            *args,
        )
    except Exception:
        return
    finally:
        if conn is not None:
            await conn.close()


def _row_to_clip(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "content": row["content"],
        "chi_score": row["chi_score"],
        "vector": json.loads(row["vector"]) if row["vector"] else None,
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "compressed": row["compressed"],
        "created_at": row["created_at"],
    }
