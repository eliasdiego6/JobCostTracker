# Job Cost Tracker

Tracks each job's actual costs from QuickBooks Desktop against estimates (labor, material,
subcontractor, direct expenses / misc, and contract price). See [PLAN.md](PLAN.md) for the full plan.

## Run it on your PC (fake QuickBooks data)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
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

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `JCT_QB_MODE` | `fake` | `fake` = sample data; `desktop` = real QuickBooks Desktop (server only, step 3) |
| `JCT_DATA_DIR` | `./data` | Where `jobs.db` lives. On the server, point this outside the code folder |
| `JCT_SYNC_MINUTES` | `30` | How often the server pulls from QuickBooks |
| `JCT_PORT` | `8000` | Web port |

## Layout

```
app/main.py        web API + serves the dashboard
app/calc.py        over / trending / on-track math
app/sync.py        pulls costs from QuickBooks into the database
app/qb/            QuickBooks connectors (fake.py now; desktop connector in step 3)
app/static/        the dashboard (HTML/CSS/JS, no build step)
scripts/seed_demo.py
tests/
```
