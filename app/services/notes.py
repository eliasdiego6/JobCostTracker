import sqlite3

from app import db
from app.repositories import notes as notes_repo
from app.services.jobs import get_row


def add(conn: sqlite3.Connection, job_id: int, body: str, author: str | None) -> int:
    get_row(conn, job_id)
    note_id = notes_repo.add(conn, job_id, author, body.strip(), db.now())
    conn.commit()
    return note_id


def delete(conn: sqlite3.Connection, note_id: int) -> None:
    notes_repo.delete(conn, note_id)
    conn.commit()
