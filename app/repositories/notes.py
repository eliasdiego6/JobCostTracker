import sqlite3


def for_job(conn: sqlite3.Connection, job_id: int) -> list[dict]:
    rows = conn.execute("SELECT * FROM notes WHERE job_id = ? ORDER BY created_at DESC, id DESC", (job_id,))
    return [dict(r) for r in rows]


def add(conn: sqlite3.Connection, job_id: int, author: str | None, body: str, created_at: str) -> int:
    cur = conn.execute(
        "INSERT INTO notes (job_id, author, body, created_at) VALUES (?, ?, ?, ?)",
        (job_id, author, body, created_at),
    )
    return cur.lastrowid


def delete(conn: sqlite3.Connection, note_id: int) -> None:
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
