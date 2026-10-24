"""Adding, editing, viewing and deleting tracked jobs."""

import sqlite3

from app import db
from app.domain import calc
from app.qb.base import Connector
from app.repositories import jobs as jobs_repo
from app.repositories import notes as notes_repo
from app.repositories import settings as settings_repo
from app.repositories import transactions as txn_repo
from app.services import sync
from app.services.errors import Conflict, NotFound


def job_view(row, starred=False, hidden=False) -> dict:
    """A jobs row -> what the dashboard shows for one job card."""
    return {
        "id": row["id"],
        "job_number": row["job_number"],
        "name": row["qb_full_name"].split(":")[-1],
        "qb_full_name": row["qb_full_name"],
        "customer": row["customer"],
        "pct_complete": row["pct_complete"],
        "synced_at": row["synced_at"],
        "sync_error": row["sync_error"],
        "created_at": row["created_at"],
        "created_by": row["created_by"],
        "starred": bool(starred),
        "hidden": bool(hidden),
        **calc.summarize(row),
    }


def get_row(conn: sqlite3.Connection, job_id: int) -> sqlite3.Row:
    row = jobs_repo.get(conn, job_id)
    if not row:
        raise NotFound("Job not found")
    return row


def list_views(conn: sqlite3.Connection, user_id: int | None) -> list[dict]:
    return [job_view(r, r["u_starred"], r["u_hidden"]) for r in jobs_repo.list_for_user(conn, user_id)]


def dashboard(conn: sqlite3.Connection, user_id: int | None) -> dict:
    return {"jobs": list_views(conn, user_id), "last_sync": settings_repo.get_meta(conn, "last_sync")}


def detail(conn: sqlite3.Connection, job_id: int) -> dict:
    return {
        **job_view(get_row(conn, job_id)),
        "transactions": txn_repo.for_job(conn, job_id),
        "notes": notes_repo.for_job(conn, job_id),
    }


def add(conn: sqlite3.Connection, connector: Connector, job_number: str, qb_list_id: str,
        estimates: dict, created_by: str | None) -> dict:
    """Link a QuickBooks Customer:Job to the tracker with its estimates, then pull its actuals."""
    qb_job = connector.get_job(qb_list_id)
    if not qb_job:
        raise NotFound("That job was not found in QuickBooks")
    number = job_number.strip()
    if jobs_repo.exists(conn, number, qb_job.list_id):
        raise Conflict(f"Job {number} is already in the tracker")
    job_id = jobs_repo.insert(conn, {
        "job_number": number,
        "qb_list_id": qb_job.list_id,
        "qb_full_name": qb_job.full_name,
        "customer": qb_job.customer,
        **{k: estimates[k] for k in jobs_repo.ESTIMATE_FIELDS},
        "created_at": db.now(),
        "created_by": created_by,
    })
    conn.commit()
    sync.sync_job(conn, connector, job_id)
    return job_view(get_row(conn, job_id))


def update_estimates(conn: sqlite3.Connection, job_id: int, estimates: dict) -> dict:
    get_row(conn, job_id)
    jobs_repo.update_estimates(conn, job_id, estimates)
    conn.commit()
    return job_view(get_row(conn, job_id))


def delete(conn: sqlite3.Connection, job_id: int) -> None:
    """Removes the job for everyone (notes and transactions cascade). Never touches QuickBooks."""
    get_row(conn, job_id)
    jobs_repo.delete(conn, job_id)
    conn.commit()
