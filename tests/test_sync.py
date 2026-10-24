from app import db
from app.qb.base import QBCost, QBJob
from app.repositories import jobs as jobs_repo
from app.repositories import settings as settings_repo
from app.repositories import transactions as txn_repo
from app.services import sync


class StubConnector:
    """A connector whose costs and failures each test controls."""

    def __init__(self, costs=(), invoiced=0.0):
        self.costs = list(costs)
        self.invoiced = invoiced
        self.error = None

    def find_jobs(self, search):
        return []

    def get_job(self, list_id):
        return QBJob(list_id, f"Cust:{list_id}", "Cust")

    def job_costs(self, list_id):
        if self.error:
            raise self.error
        return self.costs

    def job_invoiced(self, list_id):
        return self.invoiced


def cost(account, amount):
    return QBCost("2026-05-01", "Bill", "1", "Vendor", account, "", amount)


def add_job(conn):
    job_id = jobs_repo.insert(conn, {
        "job_number": "T-1", "qb_list_id": "L1", "qb_full_name": "Cust:T-1", "customer": "Cust",
        "created_at": db.now(),
    })
    conn.commit()
    return job_id


def test_costs_land_in_mapped_buckets_and_unmapped_is_misc(conn):
    settings_repo.add_account_mappings(conn, {"Direct Labor": "labor", "Subs": "sub"})
    job_id = add_job(conn)
    qb = StubConnector([cost("direct labor", 100), cost("Subs", 50.5), cost("Permits", 20)], invoiced=300)

    sync.sync_job(conn, qb, job_id)

    job = jobs_repo.get(conn, job_id)
    assert (job["act_labor"], job["act_sub"], job["act_misc"], job["act_material"]) == (100, 50.5, 20, 0)
    assert job["invoiced"] == 300
    assert job["synced_at"] and job["sync_error"] is None
    assert [t["bucket"] for t in txn_repo.for_job(conn, job_id)] == ["labor", "sub", "misc"]


def test_resync_replaces_transactions(conn):
    job_id = add_job(conn)
    qb = StubConnector([cost("A", 10), cost("B", 20)])
    sync.sync_job(conn, qb, job_id)
    qb.costs = [cost("A", 5)]
    sync.sync_job(conn, qb, job_id)
    assert len(txn_repo.for_job(conn, job_id)) == 1
    assert jobs_repo.get(conn, job_id)["act_misc"] == 5


def test_failure_keeps_last_good_numbers_and_records_error(conn):
    job_id = add_job(conn)
    qb = StubConnector([cost("A", 10)])
    sync.sync_job(conn, qb, job_id)

    qb.error = RuntimeError("QuickBooks is not open")
    sync.sync_job(conn, qb, job_id)
    job = jobs_repo.get(conn, job_id)
    assert job["act_misc"] == 10
    assert job["sync_error"] == "QuickBooks is not open"
    assert len(txn_repo.for_job(conn, job_id)) == 1

    qb.error = None
    sync.sync_job(conn, qb, job_id)
    assert jobs_repo.get(conn, job_id)["sync_error"] is None


def test_sync_all_records_last_sync(conn):
    add_job(conn)
    assert sync.sync_all(conn, StubConnector()) == 1
    assert settings_repo.get_meta(conn, "last_sync")
