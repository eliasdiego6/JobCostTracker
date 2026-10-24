# Job Cost Tracker

Tracks each job's actual costs from QuickBooks Desktop against estimates (labor, material,
subcontractor, direct expenses / misc, and contract price). See [PLAN.md](PLAN.md) for the full plan.

| Doc | For |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Project rules: QuickBooks one-way data, the three-agent review pipeline, process |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Setting up, running and testing on your PC |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the code is organized and where new features go |
| [docs/CONVENTIONS.md](docs/CONVENTIONS.md) | Code rules and the required log → plan → approve process |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Installing, backing up and updating on the office server |
| [docs/MEMORY.md](docs/MEMORY.md) | Log of features and decisions |
| [prompts/](prompts/) | Every work request, with its plan and approval |

## Run it on your PC (fake QuickBooks data)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m scripts.seed_demo      # loads 10 sample jobs
.\.venv\Scripts\python run.py                    # http://localhost:8000
```

Try adding job **24-146** or **24-150**; they're in the fake QuickBooks data but not yet in the tracker.

## QuickBooks discovery (run on the server)

Read-only look at how jobs, accounts and items are set up in QuickBooks. Needs QuickBooks
Desktop open with the company file, on the same PC.

```powershell
git clone https://github.com/eliasdiego6/JobCostTracker.git
cd JobCostTracker
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m scripts.qb_discover 24-117     # use a real job number
```

The first run makes QuickBooks ask whether to allow "Job Cost Tracker" access. A QB Admin must
answer **Yes, always; allow access even if QuickBooks is not running**. Results go to
`discovery_output\` (ignored by git); `summary.txt` is the short version.

## Tests

```powershell
.\.venv\Scripts\python -m pytest
```

## Settings

Environment variables (or a `.env` file), all listed in [.env.example](.env.example). The main ones:
`JCT_QB_MODE` (`fake` | `desktop`), `JCT_DATA_DIR` (keep outside the code folder on the server),
`JCT_SYNC_MINUTES`, `JCT_PORT`.

## Layout

```
app/main.py          app factory: routers, static files, startup
app/api/             HTTP routes + request schemas (no SQL)
app/services/        business workflows: jobs, notes, users, sync, export
app/domain/          pure budget math and bucket/status vocabulary
app/repositories/    all SQL
app/db/              connection, numbered migrations, backup
app/qb/              QuickBooks connectors: fake.py now, desktop via qbxml.py in step 3
app/scheduler.py     background QB sync
app/static/          dashboard (HTML/CSS + ES modules in js/, no build step)
scripts/             seed_demo, migrate, backup_db, qb_discover
tests/
docs/  prompts/
```
