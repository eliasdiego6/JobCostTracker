# Deployment (office server)

Target: the always-on Windows server that also runs QuickBooks Desktop. One process serves the app
and runs the QB sync. This covers the manual setup; automating it as a Windows service plus a GitHub
self-hosted runner is PLAN step 5.

## 1. Folders

| What | Where (example) | Notes |
|---|---|---|
| Code | `C:\Apps\JobCostTracker` | `git clone`; replaced on each deploy |
| Data | `C:\AppData\JobCostTracker` | `jobs.db` lives here. **Never inside the code folder** |
| Backups | `D:\Backups\JobCostTracker` | Ideally a different disk, or a folder your offsite backup covers |

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

**Keeping it running (until step 5):** a Task Scheduler task that runs at startup, whether or not
anyone is logged in, as a service account that can open QuickBooks:

- Program: `C:\Apps\JobCostTracker\.venv\Scripts\python.exe`
- Arguments: `run.py`
- Start in: `C:\Apps\JobCostTracker`
- Settings: restart on failure every 1 minute

Step 5 replaces this with a proper Windows service. The QB SDK has session/desktop constraints that
must be tested on the server first.

## 5. Nightly backup

Task Scheduler, daily at 2:00 AM:

- Program: `C:\Apps\JobCostTracker\.venv\Scripts\python.exe`
- Arguments: `-m scripts.backup_db`
- Start in: `C:\Apps\JobCostTracker`

It uses SQLite's backup API, so it's safe while the app is running. It keeps the newest `JCT_BACKUP_KEEP` copies.
**Test a restore** once: stop the app, copy a backup over `jobs.db`, start the app.

## 6. Updating

```powershell
cd C:\Apps\JobCostTracker
.\.venv\Scripts\python -m scripts.backup_db       # always back up first
git pull
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m scripts.migrate
# restart the scheduled task (or service)
```

The step 5 pipeline runs exactly this order automatically: test → backup → migrate → restart.

## Rollback

Code: `git checkout <previous tag/commit>` and restart. Data: restore the backup taken right before
the update. Migrations only go forward, so rolling back code past a migration means restoring that backup.
