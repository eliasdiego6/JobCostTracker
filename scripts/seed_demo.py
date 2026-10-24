"""Load the fake QuickBooks jobs into the database so the dashboard has something to show.

Usage:  python -m scripts.seed_demo
Leaves the last few fake jobs out so you can try "Add job" yourself (e.g. 24-146, 24-150).
"""

from app import config, db
from app.qb.fake import FAKE_JOBS, FakeConnector, _job
from app.repositories import jobs as jobs_repo
from app.services import sync
from app.services.setup import prepare_database

PCT_COMPLETE = {"24-101": 95, "24-108": 50, "24-117": 80, "24-125": 100, "24-134": 35, "24-139": 90}


def main():
    config.load_env_file()
    if config.qb_mode() != "fake":
        raise SystemExit("seed_demo only runs in fake QuickBooks mode (JCT_QB_MODE=fake).")
    prepare_database(config.db_path())
    conn = db.connect(config.db_path())
    for row in FAKE_JOBS[:10]:
        number, _, _, (labor, material, sub, misc), contract, *_ = row
        qb = _job(row)
        if jobs_repo.exists(conn, number, qb.list_id):
            continue
        jobs_repo.insert(conn, {
            "job_number": number, "qb_list_id": qb.list_id, "qb_full_name": qb.full_name, "customer": qb.customer,
            "est_labor": labor, "est_material": material, "est_sub": sub, "est_misc": misc,
            "contract": contract, "pct_complete": PCT_COMPLETE.get(number),
            "created_at": db.now(), "created_by": "Demo",
        })
    conn.commit()
    count = sync.sync_all(conn, FakeConnector())
    conn.close()
    print(f"Seeded and synced {count} demo jobs into {config.db_path()}")


if __name__ == "__main__":
    main()
