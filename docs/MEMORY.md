# Project memory

A running log of features and significant decisions: what was done, why, and what to watch.
Newest first. Every entry links to the prompt log that produced it (`prompts/`).

Entry template:

```
## YYYY-MM-DD — Title
Prompt: prompts/<file>.md
- Feature / decision:
- Rationale:
- Business impact:
- Implementation notes:
- Follow-ups / risks:
```

---

## 2026-10-23 — Rules: QuickBooks one-way data + three-agent pipeline

Prompt: [prompts/2026-10-23_03_claude-md-agent-pipeline.md](../prompts/2026-10-23_03_claude-md-agent-pipeline.md)

- **Decision:** Added `CLAUDE.md` with two binding rules, plus three Claude Code sub-agents in `.claude/agents/`.
  - **Rule 1:** QuickBooks data is one-way. Only qbXML queries. QB-owned data is written only by the sync,
    app-owned data only by users, and the two are combined when read. Corrections are app-owned overrides.
  - **Rule 2:** every code/schema change goes project-manager (brief + questions) → user approval →
    programmer → qc-reviewer (PASS/FAIL, max 3 fix rounds, then the user decides).
- **Rationale:** QuickBooks is the accounting system of record, so the tracker must never alter it, and
  must never blur what QB said with what users entered. Otherwise nobody can trust the numbers. An
  independent reviewer that can't edit code catches mistakes the author misses, and every hand-off lands in
  the prompt log for auditability.
- **Business impact:** Numbers on the dashboard always trace back to either QuickBooks or a named user's
  input. Changes are slower to land but reviewed and traceable.
- **Implementation notes:** Sub-agents can't talk to the user or to each other, so the main session
  orchestrates: it relays PM questions, sends QC findings back to the same programmer agent, and does
  no coding itself during pipeline tasks. QC has no Edit/Write tools by design. A Data ownership
  table was added to `docs/ARCHITECTURE.md`; process rules moved from CONVENTIONS.md into CLAUDE.md.
- **Follow-ups / risks:**
  - `jobs` mixes QB-owned and app-owned columns. The next pipeline task splits it into sync-only `qb_`
    tables and adds a guard test that `app/qb` builds only Query requests.
  - Prompt #02 (real QB connector + Settings) is paused and resumes through the pipeline after that.
  - The pipeline costs more tokens and time per change; docs-only work is exempt.

## 2026-10-23 — Layered foundation (structure only, no behavior change)

Prompt: [prompts/2026-10-23_01_foundation-scaffold.md](../prompts/2026-10-23_01_foundation-scaffold.md)

- **Decision:** Split the single `main.py` into layers: `api/` (routes and schemas) → `services/`
  (workflows, commits) → `repositories/` (SQL) → `db/` (connection, migrations, backup), with pure
  business math in `domain/`. The QB fake and real paths stay behind the `Connector` Protocol.
- **Rationale:** Filters, notes, status logic, per-job details and the Settings screen were all going to
  land in one 280-line file mixing HTTP, SQL and rules. Clear layers keep each feature to a
  predictable set of small files without adding frameworks: no ORM, no DI container, no frontend build.
- **Business impact:** None visible to users; the API and screens are identical. Lowers the cost and
  risk of the next phases (real QB, Settings, polish) and lets another developer find things quickly.
- **Implementation notes:**
  - Migrations: numbered `.sql` files + `PRAGMA user_version`. `0001_initial.sql` is the original schema with
    `IF NOT EXISTS`, so pre-existing databases (e.g. dev `data/jobs.db`) adopt v1 with no data change.
    Each migration runs in one transaction.
  - `scripts.migrate` and `scripts.backup_db` (SQLite backup API + retention) exist for the deploy pipeline.
  - Fake-only data (the default account map) is reached through `qb.default_account_map()`; only
    `app/qb/__init__.py` reads `JCT_QB_MODE`.
  - Frontend: `app.js` split into ES modules under `static/js/`; logic unchanged. Verified in Chrome:
    dashboard, filters, detail, notes, add job.
  - `requirements-dev.txt` holds pytest/httpx; `.env.example` + a tiny `.env` loader (no new dependency).
  - Tests went from 22 to 38: migrations, sync, backup, connector contract.
- **Follow-ups / risks:**
  - Delete-note and save-prefs don't 404 on unknown IDs (same as before; kept to avoid behavior change).
  - Task Scheduler is the interim way to keep the app running; a real Windows service and CI remain PLAN step 5.
  - Whether the QB SDK works from a non-interactive service session must be tested on the server.
