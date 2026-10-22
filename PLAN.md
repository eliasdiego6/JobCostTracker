# Job Cost Tracker — Plan

A LAN web app that tracks each job's actual costs (pulled from QuickBooks Desktop)
against manually entered estimates, so PMs can see at a glance which jobs are
over or under budget.

## Decisions

| Topic | Decision |
|---|---|
| QuickBooks | QuickBooks Desktop, company file on the server in multi-user mode |
| Where it runs | On the always-on server (which has QB Desktop installed). One process: web app + scheduled QB sync |
| How people use it | Browser at `http://<server>:8000`; can be "installed" as an app from Edge/Chrome |
| Logins | None. Anyone on the LAN can view/edit. First visit asks for your name (no password) |
| Who can add jobs | Anyone |
| Delete | Anyone, behind a confirm prompt. Delete removes the job for **all** users (app only — never touches QB) |
| Hide | Personal — hides the job from your view only |
| Repo / CI/CD | Private GitHub repo; self-hosted runner on the server: test → back up DB → migrate → restart on merge to `main` |
| Database | SQLite on the server's local disk, **outside** the code folder. Backed up nightly and before every deploy |
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

## Status logic

- **Over** (red): actual > estimate.
- **Trending over** (yellow): projected-at-completion > estimate, where
  projected = actual ÷ % complete. With no % complete entered, yellow means ≥ 90% of the estimate is used.
- **On track** (green): otherwise.
- Overall status uses the same rules against the sum of the four estimates; going over the
  contract price is flagged as a loss.

## Data stored by the app

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
2. **Discovery script** against real QB: list Customer:Jobs, dump one job's costs by account/item.
   Answers: where the job number lives, how labor and subs are posted.
3. Real QB sync (qbXML via the QB SDK) + Settings screen for account → bucket mapping
4. Polish from feedback
5. Run as a Windows service on the server + GitHub repo + self-hosted runner pipeline

## Still needed from the business

- QuickBooks version and year (Help → About) — decides 32- vs 64-bit SDK setup
- A QB Admin to approve the app's first connection; a read-only "Reports" QB user for it
- One or two real job numbers to test with (ideally with labor and sub costs)
- Port 8000 open on the server's firewall for the office LAN
- Git installed on the dev PC and the server; a GitHub account/org for the private repo
