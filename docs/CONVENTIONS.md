# Conventions

## Code

- **Python 3.13**, standard library first. Add a dependency only when it removes real work, and pin it
  in `requirements.txt` (runtime) or `requirements-dev.txt` (tests/tools).
- Plain functions over classes. Classes only where the shape is genuinely an object (a connector, a QB session).
- Modules hold short, plain-English docstrings that say *what* and *why*. Comments explain business
  reasons ("unmapped accounts count as misc"), not syntax.
- Money is a float rounded to cents where it's stored or displayed. Bucket keys are always
  `labor`, `material`, `sub`, `misc` (`app/domain/buckets.py`).
- Dates are ISO strings (`db.now()` → `2026-10-23T14:05:00`).

## Layer rules (see ARCHITECTURE.md)

- Routes: validate, call one service function, return its result. No SQL.
- Services: commit when the workflow is complete. Raise `services.errors.NotFound` / `Conflict`.
- Repositories: SQL only, parameterized (`?`) always, never `commit()`.
- Only `app/qb/__init__.py` reads `JCT_QB_MODE`.
- Settings come from `app/config.py` functions, read at call time (tests monkeypatch env vars).

## Database changes

1. Add `app/db/migrations/NNNN_short_name.sql` with the next number. Numbers must be contiguous.
2. Never edit a migration that has been deployed. Fix forward with a new one.
3. SQLite `ALTER TABLE` is limited: adding a column is easy; renaming or dropping means creating a new
   table, copying, and swapping, all inside the migration.
4. Add or extend a test in `tests/test_migrations.py` when a migration transforms data.

## Frontend

- No framework, no build. Native ES modules in `app/static/js/`, one per screen area.
- All server calls go through `api.js`. All user-entered or QB text goes through `esc()` before
  being put into HTML.
- Shared state lives in `state.js`; modules export an `init*()` that wires events, called from `main.js`.

## Tests

- `python -m pytest`. Each test gets a temp database and fake QB (`tests/conftest.py`). Nothing touches `data/`.
- Business math → `test_calc.py`. Workflows through HTTP → `test_api.py`. Sync rules → `test_sync.py`.
- New QB connector → add it to `CONNECTORS` in `test_connector_contract.py`.
- A change that alters what users see should come with a test or a manual check noted in its prompt log.

## Work process (required)

The process rules live in [CLAUDE.md](../CLAUDE.md) so every Claude Code session loads them:

- **Rule 1:** QuickBooks data is a one-way street (QB-owned vs app-owned data).
- **Rule 2:** every code or schema change goes through the project-manager → programmer → qc-reviewer
  agents (`.claude/agents/`).
- Every request: log in `prompts/` → clarify → written plan → explicit approval → implement → record in
  `docs/MEMORY.md`.

Human developers follow the same rules: log the request, get the plan approved, and get an independent review before merging.

## Git

- Work on a branch, merge to `main` by PR. `main` deploys to the server (PLAN step 5).
- Commit messages: imperative summary line ("Add migration runner"), body says why.
- Never commit `data/`, `.env`, `discovery_output/` or any QuickBooks export.
