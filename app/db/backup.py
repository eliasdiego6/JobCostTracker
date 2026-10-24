"""Consistent copies of the live database (safe while the app is running, unlike copying the file)."""

import sqlite3
from datetime import datetime
from pathlib import Path


def backup(db_path: Path, dest_dir: Path, keep: int) -> Path:
    """Write dest_dir/jobs-YYYYMMDD-HHMMSS.db, then delete all but the newest `keep` backups."""
    if not db_path.exists():
        raise FileNotFoundError(f"No database at {db_path}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{db_path.stem}-{datetime.now():%Y%m%d-%H%M%S}.db"
    src = sqlite3.connect(db_path)
    out = sqlite3.connect(dest)
    try:
        src.backup(out)
    finally:
        out.close()
        src.close()

    old = sorted(dest_dir.glob(f"{db_path.stem}-*.db"), reverse=True)[max(keep, 1):]
    for path in old:
        path.unlink()
    return dest
