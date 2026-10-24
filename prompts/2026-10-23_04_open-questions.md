# 2026-10-23 #04 — Consolidated open questions

| Field | Value |
|---|---|
| Date | 2026-10-23 |
| Requested by | EPerez |
| Status | **Done 2026-10-23** (plan approved; Step 0 complete) |
| Starting commit | `9e43580` (branch `foundation-scaffold`) |

## Request (verbatim)

> Can you consolidate any questions you have outstanding or about the project, its scope, or our goals and
> deliver them to be for answers? If no further questions, state that you have no questions.

## Context

No code or docs change in this task. It gathers every open question from PLAN.md "Still needed from the
business", paused prompt #02, the follow-ups in docs/MEMORY.md, and gaps found while building the
foundation. Note: the QB data segregation task referred to as "#04" in prompt #03 will now be logged as
**#05**, because this request took number 04.

## Questions and answers

Answered by EPerez, 2026-10-23. **DEFERRED** = marked for later review at the user's request.

| # | Question | Answer |
|---|---|---|
| 1 | QB edition and year | **QuickBooks 24.0 Contractor Edition** |
| 2 | Where the job number lives | ⏸ **DEFERRED: review later** (discovery script will show it) |
| 3 | How labor posts; include burden? | **Include burden in Labor.** How labor posts: ⏸ answered by discovery |
| 4 | Materials vs subs: separate accounts or items? | ⏸ **DEFERRED: review later** (discovery script will show it) |
| 5 | "Invoiced to date" meaning | Default: **total billed, no separate retainage line** |
| 6 | QB Admin to approve the connection | **EPerez** (owner of this account) |
| 7 | Change orders | **Track change orders separately, independent of the main job** |
| 8 | Estimate history | **Yes. Log everything about each change: timestamp, the change, and a possible reason** |
| 9 | "Trending over" threshold | **85%** (was 90%) |
| 10 | Closed jobs | **Keep syncing forever.** Jobs get 1-year warranty work and unexpected costs after close |
| 11 | Overhead and profit | **Profit is on top of overhead.** Profit is inclusive of the X% overhead; overhead must never eat into profit |
| 12 | Who edits account → bucket mapping | Default: **anyone, with change history** |
| 13 | Deleting jobs | Default: **replace Delete with Archive** (hidden for everyone, undoable) |
| 14 | Users / remote access | **About 10 users, LAN only** |
| 15 | Server session state | **Locked / logged-out screen** |
| 16 | Push branch + PR to main | **Yes** |
| 17 | Backups | **Not necessary** |
| 18 | Go-live target | **N/A** |
| 19 | Order: #05 (QB data split) before #02 | Default: **yes** |
| 20 | Cheaper model for programmer/QC agents | **"Yes"** (needs clarifying, see follow-ups) |
| 21 | Small fixes go through the pipeline | **Yes** |
| 22 | `.vscode/` | Default: **add to .gitignore** |

## Follow-up questions

Asked 2026-10-23 before drafting the plan (see conversation; answers recorded below).

| # | Topic | Answer |
|---|---|---|
| F1 | Change order contents / numbering | **Numbering: `JJJ-YY-CC`.** JJJ = job number 000–999, up by one for each new job. YY = last two digits of the current year. CC = change order number: 00 is the base job, 01–99 are change orders. Other contents (description, status, own price and estimates): no answer yet |
| F2 | Change order statuses | **Approved only; no other statuses** (a change order is entered once approved) |
| F3 | How totals and status show | **Base job and each change order are judged independently**, to see whether each change order's estimate was sufficient. Break them out |
| F4 | How CO costs are recorded in QB | Answered by N4: **each change order is its own QB job with the same number** |
| F5 | Overhead | **Overhead = X% of the job's total direct cost** (labor + material + sub + misc). Profit is after overhead. Rate scope (company-wide vs per job): not stated → assumed company-wide |
| F6 | Change reason | **Optional** |
| F7 | Closed status | **Yes** (default: show the QuickBooks status as a badge; no separate app status) |
| F8 | Highlight costs posted after close | **Yes** |
| F9 | Dedicated server account stays signed in (auto sign-in + lock) | **Yes** |
| F10 | Backups: keep only the automatic pre-update copy | **Yes** |
| F11 | Agent models | **"Yes"**, interpreted as option A (Sonnet 5.5 for programmer + QC, Opus 5.5 for PM). Called out in the plan for confirmation |
| F12 | QB edition | **Enterprise** (Enterprise Solutions 24.0 Contractor) |

Numbering follow-ups asked: N1–N5 (see conversation). Answers (EPerez, 2026-10-23):

| # | Question | Answer |
|---|---|---|
| N1 | Is JJJ-YY-CC already used in QB? | "Interpretation is correct" (e.g. `117-24-00` base, `117-24-01` CO1). Combined with N4: **the numbers exist in QuickBooks, so they are QB-owned** (pending confirmation) |
| N2 | Does JJJ restart yearly? After 999? | **Never more than 999 jobs; no rollover handling needed.** Restart vs continue: not answered; moot if QB assigns the numbers |
| N3 | Who picks the next number? | Not answered. If the numbers are QB-owned, the app reads them from QB and never assigns one (pending confirmation) |
| N4 | Are COs set up in QB with the same number? | **Yes. Each change order exists in QuickBooks with the same number** → CO actual costs can be tracked separately |
| N5 | Which year YY uses | Default: **the base job's year**; COs inherit it |

## Assumptions to confirm at approval

- **A1 (N1/N3):** base jobs are also in QuickBooks with their number (e.g. `117-24-00`). Job numbers are
  therefore QB-owned; the app reads them and never assigns or edits them. The discovery script confirms
  this (deferred Q2).
- **A2 (F5):** one company-wide overhead rate, set in Settings with change history. The rate value
  itself is still needed.
- **A3 (F11):** programmer + qc-reviewer on Sonnet 5.5, project-manager on Opus 5.5.
- **A4 (F3):** the base job and each change order get their own status and their own budget-vs-actual
  lines. A combined job total is shown for information only and doesn't drive any status.
- **A5 (F2):** a change order appears in the tracker once it exists in QuickBooks. It counts as approved
  as soon as someone enters its price and estimates. Until then it shows "needs estimate".

## Plan (needs approval)

A roadmap of tasks. **Approving this plan approves the order and scope.** Each code task still runs the
full pipeline with its own prompt log: PM brief, your approval of that brief, programmer, QC.
Pipeline tasks start in a **fresh session**, because the agents load at session start.

### Step 0. Housekeeping (this session; config/docs only, no app code)

1. `.gitignore`: add `.vscode/`.
2. Agent models (A3): `model: sonnet` in `programmer.md` and `qc-reviewer.md`; `model: opus` in `project-manager.md`.
3. `PLAN.md`: record the new business decisions:
   - 85% trending threshold
   - change orders (JJJ-YY-CC, own QB job, judged independently, approved only)
   - overhead on direct cost, profit after overhead
   - Archive instead of Delete
   - closed jobs synced forever, with post-close costs highlighted
   - about 10 users on the LAN
   - Enterprise 24.0 Contractor
   - deferred Q2/Q4
4. `docs/DEPLOYMENT.md`:
   - dedicated Windows account with auto sign-in and lock
   - the app starts at sign-in, not as a service, because the QB SDK needs a signed-in session
   - remove the nightly backup; keep only the automatic pre-update copy (F10)
5. `docs/MEMORY.md`: an entry for these business decisions. This log is then marked Done.
6. Commit, push `foundation-scaffold`, and give you the GitHub link to open the PR to `main`.

### Pipeline tasks, in order

| # | Task | What it delivers | Rule 1 notes | Blocked by |
|---|---|---|---|---|
| **05** | QB data segregation | QB-owned data moves out of `jobs` into sync-only `qb_jobs` (name, customer, QB status, dates, actuals, invoiced, sync status) and `qb_transactions`. `jobs` keeps only app-owned data. Guard test: `app/qb` builds only `*QueryRq`. **No visible change.** | The fix for the known gap | — |
| **06** | Quick rule changes | Trending threshold 90% → **85%**. **Archive replaces Delete**: hidden for everyone, undoable, with a "Show archived" filter. | `archived`/`archived_by`/`archived_at` are app-owned | 05 |
| **07** | Change history | App-owned `change_log`: who, when, what (field old → new), optional reason. Covers every user change: estimates, contract, % complete, archive, notes, change orders, settings. **History tab** per job; optional "Reason" box on edit forms. | Logs app-owned changes only. QB changes are visible through sync, never edited | 05 |
| **08** | Change orders | COs read from QB by number (`JJJ-YY-01…99` linked to base `JJJ-YY-00`). Users enter each CO's price + bucket estimates. The base job and each CO get their own budget-vs-actual lines and status; the card shows the breakdown, plus an information-only combined total. Fake QB data renumbered to `JJJ-YY-CC` with sample COs. | CO existence, actuals and invoiced are QB-owned; CO price and estimates are app-owned | 05, 07 |
| **09** | Overhead | Company-wide overhead % (Settings, logged in change history). Shown as its own line for the base job and each CO: overhead = rate × direct cost (estimated and actual). Estimated, projected and remaining profit all become *after overhead*. Excel export updated. | Rate is app-owned | 07, 08 |
| **10** | Closed jobs | QB job status and end date shown as a badge (QB-owned). Sync continues forever. **Post-close costs** (posted after the end date) are highlighted on the card and in the detail view, plus a "Closed" filter. | QB status is read-only in the app | 05 |
| **02** | Real QuickBooks + Settings screen | Run discovery on the server → answers Q2/Q4 → `DesktopConnector`. Settings screen for the account → bucket map, logged in change history. | Query-only connector | Discovery output, 05–10 |

### Inputs still needed (asked during the relevant PM step, not now)

- Overhead rate value (task 09).
- Discovery output from the server (task 02): resolves deferred Q2, Q4 and how labor posts.
- Which QB date marks "closed": the job's End Date field, or something else (task 10; the PM agent will check
  what qbXML exposes).

### Out of scope

Logins/permissions, remote access, nightly backups, a frontend framework, writing anything to QuickBooks.

## Decisions

Answers recorded above. **Plan approved by EPerez, 2026-10-23** ("I approve of this plan. Get started"),
including assumptions A1–A5 as written.

## Outcome

Step 0 (housekeeping) done 2026-10-23:

- `.gitignore`: `.vscode/` added.
- Agent models: `programmer` + `qc-reviewer` → `model: sonnet`; `project-manager` → `model: opus`.
- `PLAN.md`: QB edition, read-only rule, server sign-in, ~10 users, Archive, backups policy, new sections
  (Job numbers and change orders, Overhead and profit, Closed jobs), 85% threshold (code in task 06),
  data ownership pointer, roadmap 05–10 → 02, deferred questions.
- `docs/DEPLOYMENT.md`: auto sign-in + locked account + Task Scheduler "at log on" (not a Windows service);
  nightly backup removed, pre-update copy kept.
- `docs/MEMORY.md`: "Business decisions + approved roadmap" entry.
- Branch `foundation-scaffold` committed and pushed; PR to `main` opened by EPerez from the compare link
  (GitHub CLI not installed on the dev PC).

Next: task **05 QB data segregation**, the first pipeline run, in a fresh session so the agents load.
