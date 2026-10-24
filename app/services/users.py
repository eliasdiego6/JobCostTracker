import sqlite3

from app.repositories import users as users_repo
from app.services.errors import NotFound


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return users_repo.list_all(conn)


def get_or_create(conn: sqlite3.Connection, name: str) -> dict:
    """Names are case-insensitive: "alice" signs in as the existing "Alice"."""
    name = name.strip()
    user = users_repo.find_by_name(conn, name)
    if not user:
        user = {"id": users_repo.add(conn, name), "name": name}
        conn.commit()
    return user


def get_prefs(conn: sqlite3.Connection, user_id: int) -> dict:
    prefs = users_repo.get_prefs(conn, user_id)
    if prefs is None:
        raise NotFound("User not found")
    return prefs


def save_prefs(conn: sqlite3.Connection, user_id: int, prefs: dict) -> dict:
    users_repo.set_prefs(conn, user_id, prefs)
    conn.commit()
    return prefs


def set_job_flags(conn: sqlite3.Connection, user_id: int, job_id: int,
                  starred: bool | None = None, hidden: bool | None = None) -> None:
    users_repo.set_job_flags(conn, user_id, job_id, starred, hidden)
    conn.commit()
