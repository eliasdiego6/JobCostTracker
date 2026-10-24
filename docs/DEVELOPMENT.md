# Development

Everything below runs on any Windows PC in **fake QuickBooks mode**. QuickBooks isn't needed.

## First-time setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
copy .env.example .env          # optional; the defaults already use fake mode and .\data
```

## Run

```powershell
.\.venv\Scripts\python -m scripts.seed_demo      # 10 sample jobs (safe to re-run)
.\.venv\Scripts\python run.py                    # http://localhost:8000
```

Try **+ Add job** with **24-146** or **24-150**. They're in the fake QuickBooks data but not yet in the tracker.

Auto-reload while editing: `.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`.
Interactive API docs: http://localhost:8000/docs.

Start over: stop the server and delete `data\jobs.db` (and the `-wal`/`-shm` files next to it).

## Test

```powershell
.\.venv\Scripts\python -m pytest            # all tests
.\.venv\Scripts\python -m pytest tests/test_calc.py -q
```

Tests use a temporary database each time and never read `.env`.

## Database tools

```powershell
.\.venv\Scripts\python -m scripts.migrate       # apply pending migrations (the app also does this on start)
.\.venv\Scripts\python -m scripts.backup_db     # copy to <data dir>\backups, keep newest 30
```

## Settings

All settings are environment variables, documented in [.env.example](../.env.example). `run.py` and the
scripts also read a `.env` file in the project root; real environment variables win.

## Where things are

See [ARCHITECTURE.md](ARCHITECTURE.md) for layers and where new code goes, and
[CONVENTIONS.md](CONVENTIONS.md) for the rules and the required plan → approve → log process.
