"""Pull actual costs from QuickBooks into the local database."""

import logging
import sqlite3

from app import db
from app.qb.base import Connector

log = logging.getLogger(__name__)


def bucket_for(account: str, mapping: dict[str, str]) -> str:
    return mapping.get(account.lower(), "misc")


def sync_job(conn: sqlite3.Connection, connector: Connector, job_id: int) -> None:
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    try:
        costs = connector.job_costs(job["qb_list_id"])
        invoiced = connector.job_invoiced(job["qb_list_id"])
    except Exception as e:  # keep last good numbers, show the error on the job
        log.exception("Sync failed for job %s", job["job_number"])
        conn.execute("UPDATE jobs SET sync_error = ? WHERE id = ?", (str(e), job_id))
        conn.commit()
        return

    mapping = db.account_map(conn)
    totals = dict.fromkeys(db.BUCKETS, 0.0)
    conn.execute("DELETE FROM transactions WHERE job_id = ?", (job_id,))
    for c in costs:
        bucket = bucket_for(c.account, mapping)
        totals[bucket] += c.amount
        conn.execute(
            "INSERT INTO transactions (job_id, txn_date, txn_type, ref, name, account, memo, amount, bucket) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, c.txn_date, c.txn_type, c.ref, c.name, c.account, c.memo, c.amount, bucket),
        )
    conn.execute(
        "UPDATE jobs SET act_labor = ?, act_material = ?, act_sub = ?, act_misc = ?, "
        "invoiced = ?, synced_at = ?, sync_error = NULL WHERE id = ?",
        (
            round(totals["labor"], 2),
            round(totals["material"], 2),
            round(totals["sub"], 2),
            round(totals["misc"], 2),
            invoiced,
            db.now(),
            job_id,
        ),
    )
    conn.commit()


def sync_all(conn: sqlite3.Connection, connector: Connector) -> int:
    ids = [r["id"] for r in conn.execute("SELECT id FROM jobs")]
    for job_id in ids:
        sync_job(conn, connector, job_id)
    db.set_meta(conn, "last_sync", db.now())
    conn.commit()
    return len(ids)
