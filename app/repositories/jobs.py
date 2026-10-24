import sqlite3

from app.domain.buckets import BUCKETS

ESTIMATE_FIELDS = (*(f"est_{b}" for b in BUCKETS), "contract", "pct_complete")


def get(conn: sqlite3.Connection, job_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()


def all_ids(conn: sqlite3.Connection) -> list[int]:
    return [r["id"] for r in conn.execute("SELECT id FROM jobs")]


def list_for_user(conn: sqlite3.Connection, user_id: int | None) -> list[sqlite3.Row]:
    """Every job, plus this user's star/hide flags as u_starred / u_hidden."""
    return conn.execute(
        "SELECT j.*, COALESCE(u.starred, 0) AS u_starred, COALESCE(u.hidden, 0) AS u_hidden "
        "FROM jobs j LEFT JOIN user_jobs u ON u.job_id = j.id AND u.user_id = ? "
        "ORDER BY j.job_number",
        (user_id,),
    ).fetchall()


def exists(conn: sqlite3.Connection, job_number: str, qb_list_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM jobs WHERE job_number = ? OR qb_list_id = ?", (job_number, qb_list_id))
    return row.fetchone() is not None


def insert(conn: sqlite3.Connection, fields: dict) -> int:
    cols = ", ".join(fields)
    marks = ", ".join("?" for _ in fields)
    cur = conn.execute(f"INSERT INTO jobs ({cols}) VALUES ({marks})", tuple(fields.values()))
    return cur.lastrowid


def update_estimates(conn: sqlite3.Connection, job_id: int, estimates: dict) -> None:
    fields = {k: estimates[k] for k in ESTIMATE_FIELDS}
    sets = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE jobs SET {sets} WHERE id = ?", (*fields.values(), job_id))


def update_actuals(conn: sqlite3.Connection, job_id: int, totals: dict[str, float], invoiced: float, synced_at: str) -> None:
    sets = ", ".join(f"act_{b} = ?" for b in BUCKETS)
    conn.execute(
        f"UPDATE jobs SET {sets}, invoiced = ?, synced_at = ?, sync_error = NULL WHERE id = ?",
        (*(round(totals[b], 2) for b in BUCKETS), invoiced, synced_at, job_id),
    )


def set_sync_error(conn: sqlite3.Connection, job_id: int, error: str) -> None:
    conn.execute("UPDATE jobs SET sync_error = ? WHERE id = ?", (error, job_id))


def delete(conn: sqlite3.Connection, job_id: int) -> None:
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
