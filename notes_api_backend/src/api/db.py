"""
SQLite database utilities for the Notes API.

This module reads the SQLite database file path from the database container's
db_connection.txt file (source of truth) and provides helpers for obtaining
connections and ensuring the required schema exists.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


# IMPORTANT: This path is in a different container workspace, but is available in this
# monorepo-style workspace at runtime in this code-generation environment.
_DB_CONNECTION_TXT_PATH = (
    Path(__file__).resolve().parents[4]
    / "simple-notes-manager-197529-197541"
    / "database"
    / "db_connection.txt"
)


def _utc_now_iso() -> str:
    """Return current UTC time as an ISO-8601 string with 'Z' suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_db_path_from_db_connection_txt(txt: str) -> str:
    """
    Parse the SQLite file path from db_connection.txt contents.

    Expected to contain a line like:
        # File path: /abs/path/to/myapp.db
    """
    for line in txt.splitlines():
        line = line.strip()
        if line.lower().startswith("# file path:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError(
        f"Could not find '# File path:' in {_DB_CONNECTION_TXT_PATH}. "
        "This file is the source of truth for SQLite location."
    )


# PUBLIC_INTERFACE
def get_db_path() -> str:
    """Return the SQLite database file path from the database container's db_connection.txt."""
    if not _DB_CONNECTION_TXT_PATH.exists():
        raise RuntimeError(
            f"Database connection file not found at {_DB_CONNECTION_TXT_PATH}. "
            "Backend must read SQLite path from this file."
        )

    txt = _DB_CONNECTION_TXT_PATH.read_text(encoding="utf-8")
    db_path = _parse_db_path_from_db_connection_txt(txt)

    # Ensure parent directory exists (db file may be created on first run).
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """
    Context-managed sqlite3 connection.

    Ensures connections are always closed, and enables foreign keys.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()


# PUBLIC_INTERFACE
def ensure_schema() -> None:
    """Create the notes table if it doesn't exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


# PUBLIC_INTERFACE
def execute_select(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Execute a SELECT query with parameters and return fetched rows."""
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close()


# PUBLIC_INTERFACE
def execute_select_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    """Execute a SELECT query with parameters and return a single row or None."""
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            return cur.fetchone()
        finally:
            cur.close()


# PUBLIC_INTERFACE
def execute_modify(sql: str, params: tuple = ()) -> int:
    """
    Execute an INSERT/UPDATE/DELETE with parameters.

    Returns:
        int: cursor.lastrowid for INSERTs, or cursor.rowcount otherwise.
    """
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            # lastrowid is meaningful for INSERT; for others, rowcount is useful.
            return int(cur.lastrowid) if cur.lastrowid is not None else int(cur.rowcount)
        finally:
            cur.close()


# PUBLIC_INTERFACE
def utc_now_iso() -> str:
    """Return current UTC time string used for created_at/updated_at fields."""
    return _utc_now_iso()
