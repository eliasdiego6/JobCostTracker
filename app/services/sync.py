"""Pull actual costs from QuickBooks into the local database."""

import logging
import sqlite3

from app import config, db
from app.domain.buckets import BUCKETS, UNMAPPED_BUCKET
from app.qb import get_connector
from app.qb.base import Connector
from app.repositories import jobs as jobs_repo
from app.repositories import settings as settings_repo
from app.repositories import transactions as txn_repo

log = logging.getLogger(__name__)


def bucket_for(account: str, mapping: dict[str, str]) -> str:
    return mapping.get(account.lower(), UNMAPPED_BUCKET)


def sync_job(conn: sqlite3.Connection, connector: Connector, job_id: int) -> None:
    job = jobs_repo.get(conn, job_id)
    try:
        costs = connector.job_costs(job["qb_list_id"])
        invoiced = connector.job_invoiced(job["qb_list_id"])
    except Exception as e:  # keep last good numbers, show the error on the job
        log.exception("Sync failed for job %s", job["job_number"])
        jobs_repo.set_sync_error(conn, job_id, str(e))
        conn.commit()
        return

    mapping = settings_repo.account_map(conn)
    totals = dict.fromkeys(BUCKETS, 0.0)
    rows = []
    for c in costs:
        bucket = bucket_for(c.account, mapping)
        totals[bucket] += c.amount
        rows.append({**vars(c), "bucket": bucket})
    txn_repo.replace_for_job(conn, job_id, rows)
    jobs_repo.update_actuals(conn, job_id, totals, invoiced, db.now())
    conn.commit()


def sync_all(conn: sqlite3.Connection, connector: Connector) -> int:
    ids = jobs_repo.all_ids(conn)
    for job_id in ids:
        sync_job(conn, connector, job_id)
    settings_repo.set_meta(conn, "last_sync", db.now())
    conn.commit()
    return len(ids)


def run_sync() -> int:
    """Sync every job using its own connection, so it's safe to run in a worker thread."""
    conn = db.connect(config.db_path())
    try:
        return sync_all(conn, get_connector())
    finally:
        conn.close()
