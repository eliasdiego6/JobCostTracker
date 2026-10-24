# Architecture

Job Cost Tracker is one Python process on the office server. It serves the dashboard and a JSON API
to browsers on the LAN, and syncs actual costs from QuickBooks Desktop into a local SQLite file on a
timer. There are no logins, no build step and no external services. That fits an internal tool used
by a handful of PMs on one network.

```
 Browser (Edge/Chrome on the LAN)
   │  static HTML/CSS/JS (app/static)  +  fetch /api/...
   ▼
 FastAPI app (app/main.py) ───────────── background sync loop (app/scheduler.py)
   │                                         │ every JCT_SYNC_MINUTES
   ▼                                         ▼
 api/routes ──► services ──► repositories ──► SQLite (JCT_DATA_DIR/jobs.db)
                   │   │
                   │   └──► domain (pure budget math)
                   └──────► qb.Connector ──► fake data  |  QuickBooks Desktop (qbXML over COM)
```

## Layers

| Layer | Folder | Does | Must not |
|---|---|---|---|
| API | `app/api/` | Validate requests (`schemas.py`), map URLs to service calls, inject the DB connection and QB connector (`deps.py`) | Contain SQL or business rules |
| Services | `app/services/` | Business workflows: add/edit/delete jobs, notes, users, sync, export. **Own the commit.** Raise `NotFound`/`Conflict` (not HTTP errors) | Know about HTTP |
| Domain | `app/domain/` | Pure rules: buckets, statuses, over/trending/on-track math | Touch the DB, web or QB |
| Repositories | `app/repositories/` | All SQL for app data, one module per table group. Plain functions taking a connection | Commit, or make business decisions |
| DB | `app/db/` | Connections, numbered migrations, backups | Hold table-specific queries |
| QuickBooks | `app/qb/` | `base.Connector` Protocol; `fake.py` (sample data); `qbxml.py` (real QB SDK). `qb/__init__.py` picks one from `JCT_QB_MODE` | Be imported for a specific mode anywhere else |
| Scheduler | `app/scheduler.py` | Calls `services.sync.run_sync` every N minutes in a worker thread | — |
| Frontend | `app/static/` | `index.html` + native ES modules in `js/` (see `js/main.js` header) | Need a bundler |
| Scripts | `scripts/` | Command-line entry points: seed demo data, migrate, back up, QB discovery | Contain logic the app also needs (put it in `app/` and call it) |

Dependencies point one way: `api → services → (repositories, domain, qb) → db`.

## Fake vs real QuickBooks

These are two separate concerns, connected only through the `Connector` Protocol in `app/qb/base.py`:

- **Fake** (`JCT_QB_MODE=fake`, the default): deterministic sample jobs and costs, so any PC can run the
  full app. Also supplies a starting account→bucket map (`qb.default_account_map()`).
- **Desktop** (`JCT_QB_MODE=desktop`): not built yet (PLAN step 3). It will live in `app/qb/desktop.py`,
  use `qbxml.Session` and the parsers already in `qbxml.py`, and be returned by `get_connector()`.
  `tests/test_connector_contract.py` is the checklist it must pass.

Nothing outside `app/qb/__init__.py` checks the mode.

## Request lifecycle (example: add a job)

1. `POST /api/jobs` → `api/routes/jobs.py` validates the body against `schemas.JobIn`.
2. `deps.get_conn` opens a SQLite connection and `deps.get_qb` returns the active connector.
3. `services.jobs.add` looks the job up in QB, checks for duplicates (`Conflict` → 409), inserts it
   through `repositories.jobs`, commits, then runs `services.sync.sync_job` to pull actuals.
4. The response is `services.jobs.job_view(...)`, the same shape the dashboard cards use, with status
   math from `domain.calc.summarize`.

## Data

- Schema: `app/db/migrations/*.sql`, applied in order on startup and by `scripts.migrate`.
  The version is stored in SQLite's `PRAGMA user_version`.
- Jobs keep the latest synced actuals per bucket plus the QB transaction lines behind them, so the
  dashboard never waits on QuickBooks.
- A failed sync keeps the last good numbers and shows the error on the job card.

## Where new features go

| Feature | Touch |
|---|---|
| New filter or sort on the dashboard | `static/js/dashboard.js` (`visibleJobs`, `controls`), `index.html`; saved automatically in user prefs |
| New per-job field (e.g. PM name, status override) | new migration → `repositories/jobs.py` → `services/jobs.job_view` → `api/schemas.py` → UI |
| Status rule change | `domain/calc.py` + `tests/test_calc.py` only |
| Settings screen for account → bucket map | `repositories/settings.py` (already has the reads), new `services/settings.py`, new `api/routes/settings.py`, new `static/js/settings.js` |
| Real QuickBooks | `app/qb/desktop.py` + one line in `qb/__init__.get_connector` + contract test param |
