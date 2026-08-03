from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import DB_PATH, RUNTIME_DIR


def _connect() -> sqlite3.Connection:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                mode TEXT NOT NULL CHECK(mode IN ('daily','practice')),
                date_key TEXT NOT NULL,
                question_ids TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed')),
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user_date
            ON quiz_sessions(user_name, date_key, mode);

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                question_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                selected_id TEXT NOT NULL,
                correct_id TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                response_ms INTEGER NOT NULL DEFAULT 0,
                answered_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES quiz_sessions(id),
                UNIQUE(session_id, question_id)
            );

            CREATE INDEX IF NOT EXISTS idx_attempts_user
            ON attempts(user_name, answered_at);
            """
        )


def create_session(
    user_name: str,
    mode: str,
    date_key: str,
    question_ids: list[str],
    created_at: str,
) -> str:
    session_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO quiz_sessions
            (id, user_name, mode, date_key, question_ids, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?)
            """,
            (session_id, user_name, mode, date_key, json.dumps(question_ids), created_at),
        )
    return session_id


def get_daily_session(user_name: str, date_key: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM quiz_sessions
            WHERE user_name = ? AND date_key = ? AND mode = 'daily'
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_name, date_key),
        ).fetchone()
    return _session_dict(row) if row else None


def get_session(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM quiz_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return _session_dict(row) if row else None


def _session_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["question_ids"] = json.loads(item["question_ids"])
    return item


def get_attempts_for_session(session_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM attempts WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_user_attempts(user_name: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM attempts WHERE user_name = ? ORDER BY answered_at",
            (user_name,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_user_sessions(user_name: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM quiz_sessions WHERE user_name = ? ORDER BY created_at",
            (user_name,),
        ).fetchall()
    return [_session_dict(row) for row in rows]


def save_attempt(
    *,
    session_id: str,
    user_name: str,
    question_id: str,
    topic: str,
    difficulty: str,
    selected_id: str,
    correct_id: str,
    response_ms: int,
    answered_at: str,
) -> bool:
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO attempts (
                    session_id, user_name, question_id, topic, difficulty,
                    selected_id, correct_id, is_correct, response_ms, answered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, user_name, question_id, topic, difficulty,
                    selected_id, correct_id, int(selected_id == correct_id),
                    max(0, response_ms), answered_at,
                ),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def mark_completed(session_id: str, completed_at: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE quiz_sessions
            SET status = 'completed', completed_at = COALESCE(completed_at, ?)
            WHERE id = ?
            """,
            (completed_at, session_id),
        )
