"""Web server: JSON API + the dashboard page. Run with `python run.py`."""

import asyncio
import contextlib
import io
import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import calc, config, db, export, sync
from app.qb import get_connector

log = logging.getLogger(__name__)
STATIC = config.ROOT / "app" / "static"


def open_db():
    conn = db.connect(config.db_path())
    try:
        yield conn
    finally:
        conn.close()


def _seed_account_map(conn) -> None:
    if config.qb_mode() != "fake" or conn.execute("SELECT 1 FROM account_map").fetchone():
        return
    from app.qb.fake import DEFAULT_ACCOUNT_MAP

    conn.executemany("INSERT INTO account_map VALUES (?, ?)", DEFAULT_ACCOUNT_MAP.items())
    conn.commit()


def run_sync() -> int:
    conn = db.connect(config.db_path())
    try:
        return sync.sync_all(conn, get_connector())
    finally:
        conn.close()


async def sync_loop():
    while True:
        try:
            await asyncio.to_thread(run_sync)
        except Exception:
            log.exception("Scheduled sync failed")
        await asyncio.sleep(config.sync_minutes() * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = db.connect(config.db_path())
    db.init(conn)
    _seed_account_map(conn)
    conn.close()
    task = asyncio.create_task(sync_loop())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Job Cost Tracker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


# ---------- users ----------


class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)


@app.get("/api/users")
def list_users(conn=Depends(open_db)):
    return [{"id": r["id"], "name": r["name"]} for r in conn.execute("SELECT id, name FROM users ORDER BY name")]


@app.post("/api/users")
def add_user(body: UserIn, conn=Depends(open_db)):
    name = body.name.strip()
    row = conn.execute("SELECT id, name FROM users WHERE name = ?", (name,)).fetchone()
    if not row:
        cur = conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        row = {"id": cur.lastrowid, "name": name}
    return {"id": row["id"], "name": row["name"]}


@app.get("/api/users/{user_id}/prefs")
def get_prefs(user_id: int, conn=Depends(open_db)):
    row = conn.execute("SELECT prefs FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(404, "User not found")
    return json.loads(row["prefs"])


@app.put("/api/users/{user_id}/prefs")
def save_prefs(user_id: int, prefs: dict, conn=Depends(open_db)):
    conn.execute("UPDATE users SET prefs = ? WHERE id = ?", (json.dumps(prefs), user_id))
    conn.commit()
    return prefs


class UserJobIn(BaseModel):
    starred: bool | None = None
    hidden: bool | None = None


@app.put("/api/users/{user_id}/jobs/{job_id}")
def set_user_job(user_id: int, job_id: int, body: UserJobIn, conn=Depends(open_db)):
    conn.execute("INSERT OR IGNORE INTO user_jobs (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
    if body.starred is not None:
        conn.execute("UPDATE user_jobs SET starred = ? WHERE user_id = ? AND job_id = ?", (int(body.starred), user_id, job_id))
    if body.hidden is not None:
        conn.execute("UPDATE user_jobs SET hidden = ? WHERE user_id = ? AND job_id = ?", (int(body.hidden), user_id, job_id))
    conn.commit()
    return {"ok": True}


# ---------- jobs ----------


def job_view(row, starred=False, hidden=False) -> dict:
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


def list_job_views(conn, user_id: int | None) -> list[dict]:
    rows = conn.execute(
        "SELECT j.*, COALESCE(u.starred, 0) AS u_starred, COALESCE(u.hidden, 0) AS u_hidden "
        "FROM jobs j LEFT JOIN user_jobs u ON u.job_id = j.id AND u.user_id = ? "
        "ORDER BY j.job_number",
        (user_id,),
    )
    return [job_view(r, r["u_starred"], r["u_hidden"]) for r in rows]


@app.get("/api/jobs")
def list_jobs(user_id: int | None = None, conn=Depends(open_db)):
    return {"jobs": list_job_views(conn, user_id), "last_sync": db.get_meta(conn, "last_sync")}


def get_job_row(conn, job_id: int):
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Job not found")
    return row


@app.get("/api/jobs/{job_id}")
def job_detail(job_id: int, conn=Depends(open_db)):
    row = get_job_row(conn, job_id)
    txns = conn.execute("SELECT * FROM transactions WHERE job_id = ? ORDER BY txn_date", (job_id,))
    notes = conn.execute("SELECT * FROM notes WHERE job_id = ? ORDER BY created_at DESC, id DESC", (job_id,))
    return {
        **job_view(row),
        "transactions": [dict(t) for t in txns],
        "notes": [dict(n) for n in notes],
    }


@app.get("/api/qb/search")
def qb_search(q: str = Query(min_length=1)):
    return [vars(j) for j in get_connector().find_jobs(q)]


class Estimates(BaseModel):
    est_labor: float = Field(ge=0)
    est_material: float = Field(ge=0)
    est_sub: float = Field(ge=0)
    est_misc: float = Field(ge=0)
    contract: float = Field(ge=0)
    pct_complete: float | None = Field(default=None, ge=0, le=100)


class JobIn(Estimates):
    job_number: str = Field(min_length=1, max_length=30)
    qb_list_id: str
    created_by: str | None = None


@app.post("/api/jobs")
def add_job(body: JobIn, conn=Depends(open_db)):
    connector = get_connector()
    qb_job = connector.get_job(body.qb_list_id)
    if not qb_job:
        raise HTTPException(404, "That job was not found in QuickBooks")
    number = body.job_number.strip()
    if conn.execute("SELECT 1 FROM jobs WHERE job_number = ? OR qb_list_id = ?", (number, qb_job.list_id)).fetchone():
        raise HTTPException(409, f"Job {number} is already in the tracker")
    cur = conn.execute(
        "INSERT INTO jobs (job_number, qb_list_id, qb_full_name, customer, est_labor, est_material, est_sub, "
        "est_misc, contract, pct_complete, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            number, qb_job.list_id, qb_job.full_name, qb_job.customer,
            body.est_labor, body.est_material, body.est_sub, body.est_misc,
            body.contract, body.pct_complete, db.now(), body.created_by,
        ),
    )
    conn.commit()
    sync.sync_job(conn, connector, cur.lastrowid)
    return job_view(get_job_row(conn, cur.lastrowid))


@app.put("/api/jobs/{job_id}")
def update_job(job_id: int, body: Estimates, conn=Depends(open_db)):
    get_job_row(conn, job_id)
    conn.execute(
        "UPDATE jobs SET est_labor = ?, est_material = ?, est_sub = ?, est_misc = ?, contract = ?, "
        "pct_complete = ? WHERE id = ?",
        (body.est_labor, body.est_material, body.est_sub, body.est_misc, body.contract, body.pct_complete, job_id),
    )
    conn.commit()
    return job_view(get_job_row(conn, job_id))


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, conn=Depends(open_db)):
    get_job_row(conn, job_id)
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    return {"ok": True}


class NoteIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    author: str | None = None


@app.post("/api/jobs/{job_id}/notes")
def add_note(job_id: int, note: NoteIn, conn=Depends(open_db)):
    get_job_row(conn, job_id)
    conn.execute(
        "INSERT INTO notes (job_id, author, body, created_at) VALUES (?, ?, ?, ?)",
        (job_id, note.author, note.body.strip(), db.now()),
    )
    conn.commit()
    return {"ok": True}


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, conn=Depends(open_db)):
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    return {"ok": True}


# ---------- sync & export ----------


@app.post("/api/sync")
async def sync_now():
    count = await asyncio.to_thread(run_sync)
    return {"synced": count}


@app.get("/api/export.xlsx")
def export_xlsx(user_id: int | None = None, include_hidden: bool = False, conn=Depends(open_db)):
    jobs = [j for j in list_job_views(conn, user_id) if include_hidden or not j["hidden"]]
    data = export.jobs_workbook(jobs)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="job-costs.xlsx"'},
    )
