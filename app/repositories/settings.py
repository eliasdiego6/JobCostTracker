"""App-wide settings stored in the database: the account -> bucket map and key/value meta."""

import sqlite3


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def account_map(conn: sqlite3.Connection) -> dict[str, str]:
    """Lower-cased account name -> bucket."""
    return {r["account"].lower(): r["bucket"] for r in conn.execute("SELECT * FROM account_map")}


def account_map_is_empty(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT 1 FROM account_map").fetchone() is None


def add_account_mappings(conn: sqlite3.Connection, mapping: dict[str, str]) -> None:
    conn.executemany("INSERT INTO account_map (account, bucket) VALUES (?, ?)", mapping.items())
