# 2026-10-23 #01 — Foundation scaffold

| Field | Value |
|---|---|
| Date | 2026-10-23 |
| Requested by | EPerez |
| Status | **Done 2026-10-23** (approved by EPerez before implementation) |
| Starting commit | `706cf34` (Add read-only QuickBooks discovery script and qbXML layer) |

## Request (verbatim)

> You are helping build a Python-based internal business dashboard application for an electric
> company that tracks job cost performance against estimates and actuals, with SQLite storage and a
> browser-based dashboard. This project already has a base structure and business context, and the
> goal is to lay down a scalable foundation without overengineering it.
>
> Project context:
> - The app is designed for internal LAN use, not a public SaaS product.
> - It should support job tracking, cost bucket analysis, QuickBooks integration, dashboard views, filters, notes, and sync behavior.
> - It uses SQLite on a local Windows server-style deployment.
> - The frontend is currently lightweight static HTML/CSS/JS and should remain simple unless a clear need for a framework emerges.
> - The business workflow is more important than broad platform features.
> - The project should be structured to scale cleanly but still stay practical and maintainable.
>
> Current repo direction:
> - Use the existing app concept from the project as the starting point.
> - Align with the project plan and goals already described in the repo docs.
> - Keep the project business-appropriate and operationally realistic.
> - Preserve the fake QuickBooks mode and real QuickBooks integration path as separate concerns.
>
> Required operating rules for all work:
> 1. Every request must begin with clarifying questions when the task is ambiguous or requires scope decisions.
> 2. Never begin implementation before a written plan is created.
> 3. A written plan must be reviewed and approved before starting any task.
> 4. For any new feature, update the memory file to document the feature, the rationale, and implementation notes.
> 5. Maintain a prompts folder to log every prompt used for work tracking and auditability.
> 6. If the task is unclear or scope is uncertain, ask clarifying questions before proceeding.
> 7. The system should operate in a disciplined, traceable way that supports project continuity.
>
> Your objectives:
> 1. Review the existing project structure and architecture.
> 2. Create a clean, modular foundation for the application.
> 3. Improve the project skeleton so it is easier to scale and extend.
> 4. Add or refine the necessary structure for: app configuration; database layer; models or schema
>    definitions; repository/service patterns; API endpoints; dashboard/static frontend organization;
>    sync flow abstraction; seed/demo data and testing; environment and deployment setup.
> 5. Introduce a stronger project structure without changing the business intent.
>
> Required behavior:
> - Be surgical and practical: do not add unnecessary frameworks or heavy abstractions.
> - Prefer simple, maintainable patterns over enterprise complexity.
> - Keep the architecture aligned with a Windows + SQLite business app.
> - Separate concerns clearly: database access; business logic; API layer; frontend assets; sync/integration layer; scripts and utilities.
> - Add project documentation and conventions that make the codebase easier to evolve.
> - Include a realistic development setup and a clear path for testing and local execution.
> - Preserve the ability to support both fake QuickBooks mode and later real QuickBooks integration.
> - Make sure the app can be extended with filters, notes, status logic, and per-job details without creating a messy codebase.
> - If needed, propose a phased build plan but prioritize the first production-usable foundation.
>
> Prompt logging requirement:
> - Every prompt or work request must be saved in a prompts folder for traceability and task tracking.
> - Use a consistent naming pattern for stored prompts.
> - Each saved prompt should reflect the task request, task context, and any clarifying questions or decisions made.
> - This log should help maintain a record of work over time.
>
> Memory requirement:
> - When any new feature is added or a significant decision is made, update the memory file with the relevant details.
> - Memory should capture: feature description; decision rationale; business impact; implementation notes; follow-up items or risks.
>
> Output expectations:
> - Explain the recommended project structure and why it fits the business use case.
> - Create the actual scaffold and code organization needed to begin building the app.
> - Add or improve supporting docs so another developer can understand the project quickly.
> - Keep the project practical and future-friendly.
> - Provide a concise summary of changes and the reasoning behind each key decision.
> - Clearly identify the plan, approvals, and traceability steps taken before implementation.
>
> Important constraints:
> - Do not over-engineer with a full microservice architecture or heavy front-end framework unless the project clearly requires it.
> - Focus on maintainability, clear responsibilities, and business value.
> - Treat this as an internal business tool, not a consumer product.
> - Assume the project will evolve from a Windows-local app into a more structured system over time, but do not force that complexity prematurely.
> - Always follow the project's prompt logging, planning, approval, and memory update rules.
>
> Begin by assessing the current repo and then scaffold the most solid, scalable structure for this
> app. Provide a concise summary of what you changed and why.

## Assessment of the repo at `706cf34`

What's there already works and is in good shape: about 1,000 lines of Python plus a 600-line
vanilla-JS dashboard, and 22 passing tests.

| Area | Current state | Gap |
|---|---|---|
| Config | `app/config.py`: env-var functions | No `.env.example`; settings spread across `run.py` and `config.py` |
| DB | `app/db.py`: one `CREATE IF NOT EXISTS` script | **No migrations.** Can't add or alter columns safely, but PLAN.md's deploy pipeline has a "migrate" step |
| Business logic | `app/calc.py`: pure, tested | Good. Job-view building and account-map seeding sit in `main.py` |
| API | `app/main.py` (~280 lines): routes, inline SQL, Pydantic models, sync loop, startup | Everything is in one file, and each new feature (filters, notes, settings screen) makes it bigger |
| QB integration | `app/qb/` Protocol + fake + qbXML layer | Good separation. Desktop connector is a stub (waits on discovery results, PLAN step 3) |
| Sync | `app/sync.py` + loop inside `main.py` | Scheduler is tied to the web module |
| Frontend | `static/app.js` is one 600-line file | Will be harder to grow as detail, settings and filter views are added |
| Scripts | `seed_demo` imports a private `_seed_account_map` from `main` | No backup or migrate script (both needed for PLAN step 5) |
| Tests | API, calc, qbXML | No shared fixtures; no sync or repository tests; no connector contract test |
| Docs | README, PLAN | No architecture or conventions doc, no decision/memory log, no prompt log |

## Proposed plan (needs approval)

**Guiding rule:** no change in behavior. API URLs and JSON shapes stay the same, the existing
`data/jobs.db` keeps working, and the existing tests pass with nothing changed except where fixtures
are imported from. No new runtime dependencies.

### Target layout

```
app/
  main.py              create_app(): routers, static files, lifespan (thin)
  config.py            Settings in one place (env vars, same names as today) + host/port
  domain/
    calc.py            (moved from app/calc.py) status and variance math, pure functions
    buckets.py         bucket keys, labels and status names: one source of truth
  db/
    connection.py      connect(), WAL, foreign keys
    migrate.py         numbered .sql runner using PRAGMA user_version
    migrations/0001_initial.sql   current schema, unchanged
  repositories/        SQL only, returns rows/dicts: jobs, notes, users, settings (account_map, meta)
  services/            business workflows: jobs (add/edit/view), sync (moved from app/sync.py), export
  api/
    deps.py            get_conn dependency
    schemas.py         Pydantic request models
    routes/            users, jobs, notes, qb, sync, export (one router each)
  qb/                  unchanged: base (Protocol), fake, qbxml; factory in __init__
  scheduler.py         background sync loop (out of main.py)
  static/
    index.html, styles.css, manifest.json, icon.svg
    js/                (only if approved, Q2) api.js, state.js, dashboard.js, detail.js, forms.js, main.js
scripts/
  seed_demo.py         uses services, not private main.py helpers
  qb_discover.py       unchanged
  migrate.py           apply migrations (used by deploy pipeline)
  backup_db.py         consistent SQLite backup (sqlite3 backup API) with timestamped file + retention
tests/
  conftest.py          shared temp-DB + client fixtures
  test_api.py, test_calc.py, test_qbxml.py  (kept)
  test_sync.py         bucket mapping, error keeps last good numbers
  test_migrations.py   fresh DB and existing DB both end at latest version
  test_connector_contract.py   any Connector (fake now, desktop later) meets the Protocol
docs/
  ARCHITECTURE.md      layers, data flow, request lifecycle, where new features go
  CONVENTIONS.md       naming, layer rules, migrations, tests, prompt and memory rules
  DEVELOPMENT.md       local setup, fake mode, running, testing, seeding
  DEPLOYMENT.md        server setup, data dir, backup, migrate, service (scope per Q3)
  MEMORY.md            feature and decision log (location per Q1)
prompts/
  README.md            naming pattern + template
  2026-10-23_01_foundation-scaffold.md   (this file)
.env.example, requirements-dev.txt (pytest, httpx moved out of runtime requirements)
```

### Layer rules

`api → services → repositories → db`. Services also call `domain` (pure math) and `qb` (through the
`Connector` Protocol only). Routes contain no SQL. Repositories contain no business rules. Only
`app/qb/__init__.get_connector()` knows which QuickBooks mode is active. Fake-only things like
the default account map stay in `qb/fake.py`.

### Steps

1. Log the prompt and plan (this file); create `prompts/README.md`. *(done before approval)*
2. Move `db` into a package and add the migration runner; `0001_initial.sql` = today's schema.
3. Pull SQL out of `main.py` into `repositories/`; pull workflows into `services/`.
4. Split routes into `api/routes/*`, move the sync loop to `scheduler.py`; `main.py` becomes the app factory.
5. Move `calc.py` → `domain/`, centralize bucket/status constants.
6. Frontend reorganization (scope per Q2).
7. Scripts: `migrate.py`, `backup_db.py`; fix `seed_demo` imports.
8. Tests: `conftest.py`, sync/migration/contract tests. Full suite must pass.
9. Docs: ARCHITECTURE, CONVENTIONS, DEVELOPMENT, DEPLOYMENT; update README layout section.
10. Memory entry for the foundation decision; append the outcome to this prompt log.
11. Verify: `pytest` green; run the app on fake data and check the dashboard loads, add job, notes and export.

### Out of scope (later phases)

- Real QuickBooks Desktop connector and Settings screen for account → bucket mapping (PLAN step 3, blocked on discovery output)
- New features (new filters, status rules, etc.); this pass is structure only
- Auth, ORMs, frontend frameworks, build tooling

### Phased roadmap after this pass

1. **Foundation** (this task)
2. Discovery results → real `DesktopConnector` + account-map Settings screen
3. Feedback polish (filters, notes, per-job detail improvements) on the new layers
4. Windows service + GitHub self-hosted runner: test → backup → migrate → restart

## Clarifying questions

Asked 2026-10-23. Answers are recorded below.

1. Where should the project "memory file" live?
2. Split `app.js` into ES modules now, or leave it as one file?
3. How much deployment setup to build in this pass?

## Decisions

Answered by EPerez, 2026-10-23:

1. Memory file → **`docs/MEMORY.md` in the repo**
2. Frontend → **split `app.js` into native ES modules** (no build step)
3. Deployment → **scripts + doc**: `migrate.py`, `backup_db.py`, `.env.example`, `DEPLOYMENT.md`. Service install and CI stay in PLAN step 5.
4. Plan → **approved, plus commit** on a new branch once tests pass

## Outcome

Done on branch `foundation-scaffold`.

- Built the layout as planned: `api/`, `services/`, `domain/`, `repositories/`, `db/` (migrations +
  backup), `scheduler.py`, app factory in `main.py`. API URLs and JSON responses unchanged.
- Deviations from plan:
  - The migration module is `app/db/migrator.py`, not `migrate.py`, so it doesn't clash with
    the re-exported `db.migrate` function.
  - Frontend modules are `util, api, state, users, dashboard, forms, detail, main`. `users.js` and
    `util.js` were added to the planned list; `chip`/`tile` live in `dashboard.js`.
- Tests: **38 passed** (22 existing + 16 new: migrations, sync, backup, connector contract). The only
  edits to existing tests: `test_calc` import path, and the `client` fixture moved to `conftest.py`.
- Scripts checked on a scratch database: `migrate` (v0→v1, then no-op), `seed_demo` (twice, idempotent),
  `backup_db`.
- Browser check (headless Chrome via Playwright, scratch DB): add user → 10 cards and 5 tiles; status filter;
  job detail with 22 transactions; add note; add job 24-146 via QB lookup → 11 cards. No console errors.
- Memory: [docs/MEMORY.md](../docs/MEMORY.md) entry "Layered foundation".
- Not changed: `data/jobs.db` (it will adopt migration v1 the next time the app starts, with no data change).
