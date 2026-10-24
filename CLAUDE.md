# Job Cost Tracker: rules for Claude

An internal LAN web app for an electric contractor. It compares each job's **actual costs, pulled from
QuickBooks Desktop**, against **estimates the team enters** (labor, material, subcontractor, direct/misc,
contract price). The stack is Python 3.13 + FastAPI + SQLite on one Windows server, with a plain HTML/CSS/JS
dashboard (ES modules, no build step). There are no logins: users pick their name.

Read first: [PLAN.md](PLAN.md) (business decisions), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
(layers, data ownership, where features go), [docs/CONVENTIONS.md](docs/CONVENTIONS.md) (code rules).

```powershell
.\.venv\Scripts\python -m pytest                 # tests (temp DB, fake QB)
.\.venv\Scripts\python -m scripts.seed_demo      # demo data, fake QB mode
.\.venv\Scripts\python run.py                    # http://localhost:8000
.\.venv\Scripts\python -m scripts.migrate        # apply schema migrations
.\.venv\Scripts\python -m scripts.backup_db      # back up the database
```

---

## Rule 1: QuickBooks data is a one-way street

Data flows **QuickBooks → sync → SQLite → screens**, never back. Every line of code in this project
preserves this.

1. **The app never writes to QuickBooks.** Only qbXML `*QueryRq` requests are allowed. No `*AddRq`,
   `*ModRq`, `*DelRq`, `*VoidRq` or any other write request, anywhere, for any reason.
2. **QB-owned data is written only by the sync** (`app/services/sync.py`, through repositories). No
   route, user action or other service may insert, update or delete QB-owned data. Deleting a tracked job
   removes the app's record of it, never anything in QuickBooks.
3. **App-owned data is written only by user actions.** This covers estimates, contract, % complete,
   notes, users, prefs, star/hide and the account → bucket map. The sync never modifies it.
4. **The two meet only when read.** Services combine QB-owned and app-owned data when building a
   response (e.g. `services/jobs.job_view`). Neither side is copied into the other's storage.
5. **Corrections are overrides, not edits.** If users need to adjust a QB-sourced value, store an
   app-owned override next to it and apply it when read. The QB copy stays exactly what QuickBooks said.
6. **Every new table or column is declared QB-owned or app-owned** in the Data ownership table in
   [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), in the same change that adds it. New QB-owned tables
   use the `qb_` prefix.
7. **Known gap:** the `jobs` table still mixes app-owned and QB-owned columns (see ARCHITECTURE.md).
   Don't add more mixing. A planned task splits it.

## Rule 2: every code or schema change goes through the three-agent pipeline

Any task that changes code, tests, schema/migrations or frontend assets runs through these agents
(`.claude/agents/`). Docs-only edits, prompt logs and memory entries skip the agents but still need
plan → approval.

| Step | Who | Does |
|---|---|---|
| 0 | Main session | Log the prompt in `prompts/` (verbatim) |
| 1 | **project-manager** | Turns the request into a task brief, with questions for the user |
| 2 | Main session | Asks the user the PM's questions, sends the answers back to the PM to finalize the brief, writes the plan into the prompt log, and gets **explicit user approval** |
| 3 | **programmer** | Implements exactly the approved brief and reports changes and test results |
| 4 | **qc-reviewer** | Verifies the change and returns **PASS** or **FAIL** with numbered findings |
| 5 | Main session | On FAIL, sends the findings to the programmer (same agent, via SendMessage) → QC again. **Max 3 fix rounds**; after that, bring QC's findings to the user to decide |
| 6 | Main session | On PASS: browser check if the UI changed, `docs/MEMORY.md` entry, prompt log Outcome, commit |

- In a pipeline task the main session **orchestrates only**. It doesn't write app code or tests itself,
  and it never skips QC.
- Sub-agents can't talk to the user or call each other; the main session relays everything.
- Paste each hand-off into the prompt log: PM brief, programmer report, every QC verdict.
- Questions QC raises for the user go to the user before the next round.

## Standing process rules (every request)

1. **Log** the request in `prompts/YYYY-MM-DD_NN_short-slug.md` (template in [prompts/README.md](prompts/README.md))
   before any work, and add it to the index there.
2. **Clarify** when scope is unclear: ask, and record questions and answers in the log.
3. **Plan** in writing, then **wait for explicit approval**. Nothing is implemented before that.
4. **Record** every new feature or significant decision in [docs/MEMORY.md](docs/MEMORY.md): feature,
   rationale, business impact, implementation notes, follow-ups/risks.
5. **Git:** work on a branch, never commit directly to `main`, commit only when the user approved it.
   Never commit `data/`, `.env`, `discovery_output/` or QuickBooks exports.

## Code rules (summary; details in docs/CONVENTIONS.md)

- Layers: `api/routes` → `services` → `repositories` → `db`. `domain/` holds pure math. `qb/` is
  reached only through the `Connector` Protocol, and only `app/qb/__init__.py` reads `JCT_QB_MODE`.
- Routes have no SQL. Repositories never commit. Services own commits and raise `NotFound`/`Conflict`.
- Schema changes only via new numbered files in `app/db/migrations/`. Never edit a shipped migration.
- Fake QB mode must keep working on any PC. Tests never touch `data/` or real QuickBooks.
- Match the surrounding code style. No new frameworks or dependencies without approval in the plan.
