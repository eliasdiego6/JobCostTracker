"""App settings, read from environment variables so the server and dev PCs can differ."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    # On the server this should point outside the code folder, e.g. C:\AppData\JobCostTracker
    return Path(os.environ.get("JCT_DATA_DIR", ROOT / "data"))


def db_path() -> Path:
    return data_dir() / "jobs.db"


def qb_mode() -> str:
    # "fake" = built-in sample data (any PC); "desktop" = real QuickBooks Desktop (server only)
    return os.environ.get("JCT_QB_MODE", "fake").lower()


def sync_minutes() -> int:
    return int(os.environ.get("JCT_SYNC_MINUTES", "30"))
