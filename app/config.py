"""App settings, read from environment variables so the server and dev PCs can differ.

Every setting is read when it's used, not at import time, so tests can change them with
monkeypatch. See .env.example for the full list.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env_file(path: Path = ROOT / ".env") -> None:
    """Read KEY=value lines from .env into the environment. Real environment variables win.

    Only entry points (run.py, scripts) call this; tests never do.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def data_dir() -> Path:
    # On the server this should point outside the code folder, e.g. C:\AppData\JobCostTracker
    return Path(os.environ.get("JCT_DATA_DIR", ROOT / "data"))


def db_path() -> Path:
    return data_dir() / "jobs.db"


def backup_dir() -> Path:
    return Path(os.environ.get("JCT_BACKUP_DIR", data_dir() / "backups"))


def backup_keep() -> int:
    # how many backup files to keep; older ones are deleted after each backup
    return int(os.environ.get("JCT_BACKUP_KEEP", "30"))


def qb_mode() -> str:
    # "fake" = built-in sample data (any PC); "desktop" = real QuickBooks Desktop (server only)
    return os.environ.get("JCT_QB_MODE", "fake").lower()


def sync_minutes() -> int:
    return int(os.environ.get("JCT_SYNC_MINUTES", "30"))


def host() -> str:
    return os.environ.get("JCT_HOST", "0.0.0.0")


def port() -> int:
    return int(os.environ.get("JCT_PORT", "8000"))
