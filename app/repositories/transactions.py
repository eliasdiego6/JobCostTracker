"""The QuickBooks transaction lines behind each job's actuals, replaced on every sync."""

import sqlite3

COLUMNS = ("txn_date", "txn_type", "ref", "name", "account", "memo", "amount", "bucket")


def for_job(conn: sqlite3.Connection, job_id: int) -> list[dict]:
    rows = conn.execute("SELECT * FROM transactions WHERE job_id = ? ORDER BY txn_date", (job_id,))
    return [dict(r) for r in rows]


def replace_for_job(conn: sqlite3.Connection, job_id: int, rows: list[dict]) -> None:
    conn.execute("DELETE FROM transactions WHERE job_id = ?", (job_id,))
    conn.executemany(
        f"INSERT INTO transactions (job_id, {', '.join(COLUMNS)}) VALUES (?, {', '.join('?' for _ in COLUMNS)})",
        [(job_id, *(r[c] for c in COLUMNS)) for r in rows],
    )
