"""Load the fake QuickBooks jobs into the database so the dashboard has something to show.

Usage:  python -m scripts.seed_demo
Leaves the last few fake jobs out so you can try "Add job" yourself (e.g. 24-146, 24-150).
"""

from app import config, db, sync
from app.main import _seed_account_map
from app.qb.fake import FAKE_JOBS, FakeConnector, _job

PCT_COMPLETE = {"24-101": 95, "24-108": 50, "24-117": 80, "24-125": 100, "24-134": 35, "24-139": 90}


def main():
    conn = db.connect(config.db_path())
    db.init(conn)
    _seed_account_map(conn)
    for row in FAKE_JOBS[:10]:
        number, _, _, (labor, material, sub, misc), contract, *_ = row
        qb = _job(row)
        conn.execute(
            "INSERT OR IGNORE INTO jobs (job_number, qb_list_id, qb_full_name, customer, est_labor, est_material, "
            "est_sub, est_misc, contract, pct_complete, created_at, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Demo')",
            (number, qb.list_id, qb.full_name, qb.customer, labor, material, sub, misc, contract,
             PCT_COMPLETE.get(number), db.now()),
        )
    conn.commit()
    count = sync.sync_all(conn, FakeConnector())
    print(f"Seeded and synced {count} demo jobs into {config.db_path()}")


if __name__ == "__main__":
    main()
