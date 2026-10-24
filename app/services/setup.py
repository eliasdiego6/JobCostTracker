"""Getting the database ready: run at app startup and by the seed/migrate scripts."""

import sqlite3
from pathlib import Path

from app import db
from app.qb import default_account_map
from app.repositories import settings as settings_repo


def seed_account_map(conn: sqlite3.Connection) -> None:
    """First run only: load the connector's starting account map (fake mode has one; real QB doesn't)."""
    defaults = default_account_map()
    if defaults and settings_repo.account_map_is_empty(conn):
        settings_repo.add_account_mappings(conn, defaults)
        conn.commit()


def prepare_database(path: Path) -> None:
    conn = db.connect(path)
    try:
        db.migrate(conn)
        seed_account_map(conn)
    finally:
        conn.close()
