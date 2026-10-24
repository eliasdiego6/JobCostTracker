# 2026-10-23 #03 — CLAUDE.md rules: one-way QB data + three-agent pipeline

| Field | Value |
|---|---|
| Date | 2026-10-23 |
| Requested by | EPerez |
| Status | **Done 2026-10-23** (approved by EPerez before implementation) |
| Starting commit | `603a6f1` (branch `foundation-scaffold`) |

## Request (verbatim)

> There are some important rules I need incorporated into this project that we need to have documented
> in the claude.md so that it is known. 1. There should be a clean seperation between the quickbooks data
> being pulled into the sqlite database and the sqlite database being used. When users are interacting
> with the app the data should remain segregated. This programming methodology should be preserved in all
> code writen in the project. DATA COMING FROM QUICKBOOKS IS A ONE WAY STREET. 2. All tasks created in this
> project should go through a multi step vetting project. This multistep process should be broken down by
> specialized sub agents defined as follows: 1. The first agent ingests the task and converts the prompt
> into a cohesive prompt that is passed downstream. This agent asks all the questions and is set up to be a
> project manager that looks at the input. 2. The second agent is the programming agent. This agent is
> specialzed to write code based on the responses from the first agent. This agent writes codes
> intelligently, beautifuly, and efficiently. IThis agent should be prepared to recieve input from the next
> agent if its code does not pass qc. 3. The third agent is a QC agent that ensures the code base writen by
> the second agent. This agent is specialized in attention to detail, it asks questions and if the test does
> not pass it sends the information back to the second agent for fixes. Ask any questions about this task
> before getting started. A final plan is required to be approved before getting started.

## Context

- No `CLAUDE.md` exists yet. The process rules (log, clarify, plan, approve, memory) live in `docs/CONVENTIONS.md`.
- Prompt #02 (real QB connector + Settings) was interrupted for this request and is paused.
- **Rule 1 vs the current code:**
  - QB → app is already one-way. `app/qb/qbxml.py` only sends *Query* requests and nothing writes to QuickBooks.
  - Inside SQLite the data is **not fully segregated**. The `jobs` table mixes user-owned columns
    (`job_number`, `est_*`, `contract`, `pct_complete`, `created_*`) with QB-owned columns (`qb_full_name`,
    `customer`, `act_*`, `invoiced`, `synced_at`, `sync_error`). `transactions` is purely QB-owned.
    `account_map` is user-owned config that controls how QB data is bucketed.
- **Rule 2 vs how Claude Code works:**
  - Sub-agents are defined as `.claude/agents/<name>.md`.
  - A sub-agent can't talk to the user directly or start another sub-agent. The main session therefore
    runs the pipeline: it relays the PM agent's questions to the user, passes the approved brief to the
    programmer, and routes QC failures back to the programmer.

## Clarifying questions

1. Rule 1 scope: document only, or also restructure the current `jobs` table so QB-owned and user-owned data
   are in separate tables, now or as a separate task?
2. Which tasks must go through the three-agent pipeline (all, or code changes only)?

## Decisions

Answered by EPerez, 2026-10-23:

1. Rule 1 → **document now, refactor next**. This task covers CLAUDE.md and the agents. Splitting QB-owned
   data into sync-only tables is a separate follow-up task and the pipeline's first real run.
2. Pipeline → **any change to code or schema**. Docs-only edits, prompt logs and memory entries still
   need plan → approve, but skip the agents.
3. QC loop → **3 fix rounds**, then escalate to the user with QC's findings.

## Plan (needs approval)

This task changes docs and agent definitions only, with no app code. It is the last task done under
the old single-agent process.

### 1. `CLAUDE.md` (new, repo root)

Loaded automatically in every Claude Code session. Kept short; links to docs for detail.

- **Project in one paragraph** + key commands (run, test, seed, migrate, backup).
- **Rule 1: QuickBooks data is a one-way street** (non-negotiable):
  - The app never writes to QuickBooks. Only qbXML `*QueryRq` requests; any `Add`/`Mod`/`Del`/`Void`
    request is forbidden.
  - **QB-owned data** in SQLite is written **only by the sync** (`services/sync.py`). No user action, route
    or other service may insert, update or delete it.
  - **App-owned data** (estimates, contract, % complete, notes, users, prefs, account map) is written
    only by user actions. The sync never touches it.
  - Combined numbers are built at **read time** in services; neither side is copied into the other.
  - If a user needs to "correct" a QB value, store an app-owned override next to it and never edit the QB copy.
  - Every new table or column must be declared QB-owned or app-owned (the ownership table in ARCHITECTURE.md).
  - Known gap: the `jobs` table currently mixes both. Fixing it is the follow-up task; until then, new
    code must not add to the mix.
- **Rule 2: three-agent pipeline** for any change to code or schema (see section 2), including who
  does what, how questions reach the user, the 3-round QC limit, and that the main session only
  orchestrates and does not write code itself.
- **Standing process rules** (moved here from CONVENTIONS.md so they're always loaded): prompt log in
  `prompts/`, clarify → plan → approval, `docs/MEMORY.md` for features and decisions, branch + commit rules.
- Layer rules summary + pointers to `docs/ARCHITECTURE.md` and `docs/CONVENTIONS.md`.

### 2. Sub-agents in `.claude/agents/`

| Agent | File | Tools | Job |
|---|---|---|---|
| Project manager | `project-manager.md` | Read, Glob, Grep, Bash (read-only use: git log/diff, pytest --collect-only) | Turns the raw request into a **task brief**: goal, context found in the repo, blocking questions for the user, assumptions, in/out of scope, acceptance criteria, Rule 1 ownership check, files likely touched, test plan. It writes no files. |
| Programmer | `programmer.md` | Read, Edit, Write, Glob, Grep, Bash | Implements **only** the approved brief, following CLAUDE.md, the layer rules and the existing code style. Writes or updates tests. Returns: files changed, tests run with results, and a Rule 1 self-check. On a QC FAIL it receives the findings, fixes each one, and reports what it did per finding. |
| QC reviewer | `qc-reviewer.md` | Read, Glob, Grep, Bash (tests, git diff); **no Edit/Write** | Checks the change against the brief: runs the full test suite, checks acceptance criteria, Rule 1, layer rules, conventions, edge cases and missing tests. Returns **PASS** or **FAIL** with numbered findings (file:line, expected vs actual, how to reproduce), plus questions for the user. It never fixes code itself, so every fix goes back through the programmer. |

### 3. Pipeline flow (written into CLAUDE.md)

```
user request
  → main: log prompt (prompts/)
  → PM agent: brief + questions
  → main: asks the user the questions, PM finalizes the brief → plan in the prompt log
  → USER APPROVES
  → Programmer agent: implements
  → QC agent: PASS / FAIL
       FAIL → Programmer fixes (up to 3 rounds) → QC again
       still FAIL after round 3 → user decides
  → main: browser check if UI changed, docs/MEMORY.md, prompt log Outcome, commit
```

Every hand-off (brief, programmer report, each QC verdict) is pasted into the prompt log, so the
whole review trail is in one file.

### 4. Doc updates

- `docs/CONVENTIONS.md`: "Work process" section points to CLAUDE.md instead of duplicating it.
- `docs/ARCHITECTURE.md`: new **Data ownership** section with a table classifying every current
  table and column as QB-owned or app-owned, and marking the mixed `jobs` table as the known gap.
- `README.md`: CLAUDE.md added to the docs table.
- `prompts/README.md`: index updated (#02 paused, #03); template gains "PM brief", "Programmer report"
  and "QC verdicts" sections.
- `docs/MEMORY.md`: entry for both rules (rationale, impact, follow-ups).

### 5. Wrap-up

- Check that the three agents are picked up: list agent files and do a dry run of the PM agent on a sample
  request; the output goes in this log.
- Commit on `foundation-scaffold`.

### Follow-up tasks (not in this plan)

- **#04 QB data segregation**: the pipeline's first run. Split QB-owned columns out of `jobs` into
  sync-only tables via a migration, and add a guard test that `app/qb` never builds non-Query qbXML.
- **#02 Real QB connector + Settings**: resume after #04, through the pipeline.

## Outcome

Done on branch `foundation-scaffold`. Docs and agent definitions only; no app code changed.

- `CLAUDE.md` (new): Rule 1 (QB one-way, ownership rules 1–7), Rule 2 (pipeline table, 3-round limit, main
  session orchestrates only), standing process rules, code-rule summary.
- `.claude/agents/project-manager.md`, `programmer.md`, `qc-reviewer.md` (new). QC has no Edit/Write tools.
- `docs/ARCHITECTURE.md`: Data ownership table, with the `jobs` mix marked as the known gap.
  `docs/CONVENTIONS.md` now points to CLAUDE.md. `README.md`, `prompts/README.md` (template
  sections and index) and `docs/MEMORY.md` updated.
- **Verification:** all three agent files have valid frontmatter (name, description, tools).
  The planned PM dry run **could not run in this session**: Claude Code loads agent definitions at
  session start, so it reported "Agent type 'project-manager' not found". **Deviation from plan.**
  The dry run will happen as the first step of task #04 after a session restart.
- Next: #04 QB data segregation (first pipeline run), then resume #02.
