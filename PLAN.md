# Job Cost Tracker — Plan

A LAN web app that tracks each job's actual costs (pulled from QuickBooks Desktop)
against manually entered estimates, so PMs can see at a glance which jobs are
over or under budget.

## Decisions

| Topic | Decision |
|---|---|
| QuickBooks | QuickBooks Desktop **Enterprise Solutions 24.0 Contractor**, company file on the server in multi-user mode. **Read-only: data flows QB → app only** (CLAUDE.md Rule 1) |
| Where it runs | On the always-on server (which has QB Desktop installed). One process: web app + scheduled QB sync. A dedicated Windows account signs in automatically and stays locked; the app starts at sign-in |
| How people use it | Browser at `http://<server>:8000`; can be "installed" as an app from Edge/Chrome |
| Logins | None. About 10 users, office LAN only. Anyone can view/edit. First visit asks for your name (no password). Every change is recorded with who/when/old → new/optional reason |
| Who can add jobs | Anyone |
| Delete → Archive | Anyone can **archive** a job: hidden for all users, undoable, never touches QB. Replaces the permanent Delete (task 06) |
| Hide | Personal — hides the job from your view only |
| Repo / CI/CD | Private GitHub repo; self-hosted runner on the server: test → back up DB → migrate → restart on merge to `main` |
| Database | SQLite on the server's local disk, **outside** the code folder. Backed up automatically before every update only; no nightly backup (business decision 2026-10-23) |
| Working copy | `C:\Users\<you>\Documents\JobCostTracker` |

## Cost buckets

| Bucket | Estimate (manual) | Actual (from QB) |
|---|---|---|
| Labor | yes | Accounts/items mapped to Labor |
| Material | yes | Accounts/items mapped to Material |
| Subcontractor | yes | Accounts/items mapped to Subcontractor |
| Direct expenses / misc | yes | Everything else posted to the job (unmapped = misc) |
| **Overall** | Contract price | Total cost of all buckets → profit remaining |

- Estimated profit = contract − sum of the four estimates.
- Invoiced to date (from QB) is shown against the contract.

## Job numbers and change orders

- Numbers follow **`JJJ-YY-CC`**: JJJ = job number 000–999 (one more for each new job; never more than 999),
  YY = the base job's year, CC = `00` for the base job and `01`–`99` for change orders. Example:
  `117-24-00` base job, `117-24-01` its first change order.
- Numbers come from QuickBooks: the base job and every change order is its own QB job with that number.
  The tracker reads them and never assigns or edits them.
- Change orders are tracked **independently** of the base job. Each has its own price and bucket estimates
  (entered in the tracker), its own actual costs (from its QB job) and its own status, so you can see whether
  each change order's estimate was enough. A combined job total is shown for information only.
- Only approved change orders are tracked; there are no pending/rejected states. A change order found in
  QB shows "needs estimate" until its price and estimates are entered (task 08).

## Overhead and profit

- Overhead = **X% of the total direct cost** (labor + material + subcontractor + misc). One company-wide
  rate, set in Settings and recorded in change history (task 09; the rate value is still needed).
- Profit is always **after** overhead: profit = price − direct cost − overhead. Overhead never eats into the
  profit figure. This applies to estimated, projected and remaining profit, for the base job and each change order.

## Closed jobs

- QB's job status is shown as a badge. Closed jobs **keep syncing forever** (1-year warranties and
  unexpected costs after close).
- Costs posted after the job's close date are highlighted as **post-close costs**, and there's a Closed
  filter (task 10).

## Status logic

- **Over** (red): actual > estimate.
- **Trending over** (yellow): projected-at-completion > estimate, where
  projected = actual ÷ % complete. With no % complete entered, yellow means ≥ **85%** of the estimate is used (changed from 90%; code updated in task 06).
- **On track** (green): otherwise.
- Overall status uses the same rules against the sum of the four estimates; going over the
  contract price is flagged as a loss.

## Data stored by the app

- Every table is either **QB-owned** (written only by the sync) or **app-owned** (written only by users); see
  the Data ownership table in docs/ARCHITECTURE.md
- Jobs: job number, linked QB Customer:Job, four estimates, contract price, % complete
- Notes per job (timestamped, with author name)
- Last synced actuals per bucket + invoiced + the transactions behind them + sync time
- Users (name only) and per-user view: starred jobs, hidden jobs, saved filters
- Account → bucket mapping (Settings)

## Features (v1)

- Dashboard of all jobs with five bars each and a status chip
- Add job (look up job number in QB, enter estimates + contract)
- Edit estimates / % complete; notes
- Filters: search, status, customer, starred only, show hidden; sort (e.g. most over budget)
- Star / hide (per user); delete (everyone, confirm)
- Job detail with the QB transactions behind each number
- Export: Excel (job list), print/PDF (single job)
- Sync every 30 minutes + "Refresh now"

## Build order

1. Project skeleton + **fake QuickBooks mode** + dashboard on fake data ← *done first, no QB needed*
   - Layered foundation, schema migrations, backup/migrate scripts, dev & deploy docs ← *done 2026-10-23*
2. **Discovery script** against real QB: list Customer:Jobs, dump one job's costs by account/item.
   Answers: where the job number lives, how labor and subs are posted.
3. Real QB sync (qbXML via the QB SDK) + Settings screen for account → bucket mapping
4. Polish from feedback
5. Run on the server (auto sign-in account, start at sign-in) + GitHub repo + self-hosted runner pipeline

Roadmap approved 2026-10-23 (prompts/2026-10-23_04_open-questions.md). Each runs through the agent pipeline:
05 QB data segregation → 06 85% threshold + Archive → 07 change history → 08 change orders →
09 overhead → 10 closed jobs → 02 real QB connector + Settings (needs discovery output).

## Still needed from the business

- ~~QuickBooks version and year~~ → Enterprise Solutions 24.0 Contractor
- **Deferred for review:** where the job number lives in QB, and whether materials vs subs are separated by
  account or by item. The discovery script on the server answers both
- Overhead rate (X%)
- QB Admin approving the app's first connection: EPerez. A read-only "Reports" QB user for it
- One or two real job numbers to test with (ideally with labor and sub costs)
- Port 8000 open on the server's firewall for the office LAN
- Git installed on the dev PC and the server; a GitHub account/org for the private repo
