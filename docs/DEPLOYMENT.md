# Deployment (office server)

Target: the always-on Windows server that also runs QuickBooks Desktop. One process serves the app
and runs the QB sync. This covers the manual setup; automating updates with a GitHub self-hosted runner is PLAN step 5.

## 1. Folders

| What | Where (example) | Notes |
|---|---|---|
| Code | `C:\Apps\JobCostTracker` | `git clone`; replaced on each deploy |
| Data | `C:\AppData\JobCostTracker` | `jobs.db` lives here. **Never inside the code folder** |
| Backups | `D:\Backups\JobCostTracker` | Pre-update copies only (see section 5) |

## 2. Install

```powershell
cd C:\Apps
git clone https://github.com/eliasdiego6/JobCostTracker.git
cd JobCostTracker
py -3.13 -m venv .venv          # 32-bit Python may be needed for the QB SDK; see PLAN "Still needed"
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Create `C:\Apps\JobCostTracker\.env`:

```
JCT_QB_MODE=fake                       # switch to desktop once the QB connector ships (PLAN step 3)
JCT_DATA_DIR=C:\AppData\JobCostTracker
JCT_BACKUP_DIR=D:\Backups\JobCostTracker
JCT_BACKUP_KEEP=30
JCT_SYNC_MINUTES=30
JCT_HOST=0.0.0.0
JCT_PORT=8000
```

## 3. Firewall

Allow inbound TCP 8000 on the **Domain/Private** profile only:

```powershell
New-NetFirewallRule -DisplayName "Job Cost Tracker" -Direction Inbound -Protocol TCP -LocalPort 8000 -Profile Domain,Private -Action Allow
```

## 4. Run

```powershell
.\.venv\Scripts\python -m scripts.migrate
.\.venv\Scripts\python run.py
```

Users open `http://<server-name>:8000` and can "Install app" from Edge/Chrome.

**Keeping it running:** the QuickBooks SDK only works reliably inside a signed-in Windows session, so the
app does **not** run as a Windows service. It runs under a dedicated account that stays signed in with a
locked screen:

1. Create a dedicated local/domain account (e.g. `svc-jobcost`) that can open QuickBooks and the company file.
2. Set Windows to **sign that account in automatically** after a reboot (Sysinternals *Autologon* stores the
   password encrypted), and lock the screen right after sign-in (or rely on the screen-lock policy).
3. Task Scheduler task for that account:
   - Trigger: **At log on** of `svc-jobcost`
   - Program: `C:\Apps\JobCostTracker\.venv\Scripts\python.exe`, arguments `run.py`, start in `C:\Apps\JobCostTracker`
   - "Run only when user is logged on"; restart on failure every 1 minute

A locked screen is fine; a signed-out account is not.

## 5. Backups

No nightly backup (business decision, 2026-10-23). The database is copied automatically **before every
update** (step 6) with `scripts.backup_db`, which keeps the newest `JCT_BACKUP_KEEP` copies.

Note: estimates, change orders, change history and notes exist only in this database, not in QuickBooks.
A lost disk between updates loses whatever changed since the last update.

## 6. Updating

```powershell
cd C:\Apps\JobCostTracker
.\.venv\Scripts\python -m scripts.backup_db       # always back up first
git pull
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m scripts.migrate
# restart: sign the app account out and back in, or end + run the scheduled task
```

The step 5 pipeline runs exactly this order automatically: test → backup → migrate → restart.

## Rollback

Code: `git checkout <previous tag/commit>` and restart. Data: restore the backup taken right before
the update. Migrations only go forward, so rolling back code past a migration means restoring that backup.
