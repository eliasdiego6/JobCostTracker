"""Users (name only, no passwords) and their personal view: prefs, starred and hidden jobs."""

import json
import sqlite3


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [{"id": r["id"], "name": r["name"]} for r in conn.execute("SELECT id, name FROM users ORDER BY name")]


def find_by_name(conn: sqlite3.Connection, name: str) -> dict | None:
    row = conn.execute("SELECT id, name FROM users WHERE name = ?", (name,)).fetchone()
    return {"id": row["id"], "name": row["name"]} if row else None


def add(conn: sqlite3.Connection, name: str) -> int:
    return conn.execute("INSERT INTO users (name) VALUES (?)", (name,)).lastrowid


def get_prefs(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute("SELECT prefs FROM users WHERE id = ?", (user_id,)).fetchone()
    return json.loads(row["prefs"]) if row else None


def set_prefs(conn: sqlite3.Connection, user_id: int, prefs: dict) -> None:
    conn.execute("UPDATE users SET prefs = ? WHERE id = ?", (json.dumps(prefs), user_id))


def set_job_flags(conn: sqlite3.Connection, user_id: int, job_id: int, starred: bool | None, hidden: bool | None) -> None:
    conn.execute("INSERT OR IGNORE INTO user_jobs (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
    if starred is not None:
        conn.execute("UPDATE user_jobs SET starred = ? WHERE user_id = ? AND job_id = ?", (int(starred), user_id, job_id))
    if hidden is not None:
        conn.execute("UPDATE user_jobs SET hidden = ? WHERE user_id = ? AND job_id = ?", (int(hidden), user_id, job_id))
