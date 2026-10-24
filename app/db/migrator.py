"""Schema migrations: numbered .sql files in migrations/, applied in order, each exactly once.

The applied version is kept in SQLite's built-in PRAGMA user_version. To change the schema, add
the next file (e.g. 0002_job_status_override.sql). Never edit a migration that has shipped.
"""

import re
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_NAME = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")


def migrations() -> list[tuple[int, Path]]:
    found = []
    for path in MIGRATIONS_DIR.glob("*.sql"):
        m = _NAME.match(path.name)
        if not m:
            raise ValueError(f"Bad migration file name: {path.name} (expected 0001_short_name.sql)")
        found.append((int(m.group(1)), path))
    found.sort()
    versions = [v for v, _ in found]
    if versions != list(range(1, len(versions) + 1)):
        raise ValueError(f"Migration numbers must run 1, 2, 3... with no gaps; found {versions}")
    return found


def latest_version() -> int:
    return len(migrations())


def current_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Apply any pending migrations, each in its own transaction. Returns the versions applied."""
    applied = []
    for version, path in migrations():
        if version <= current_version(conn):
            continue
        sql = path.read_text(encoding="utf-8")
        try:
            conn.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {version};\nCOMMIT;")
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        applied.append(version)
    return applied
