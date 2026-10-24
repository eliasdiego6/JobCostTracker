"""Back up the database to JCT_BACKUP_DIR, keeping the newest JCT_BACKUP_KEEP copies.

Usage:  python -m scripts.backup_db
Safe while the app is running. Schedule nightly with Windows Task Scheduler (see docs/DEPLOYMENT.md);
the deploy pipeline also runs it before every migrate.
"""

from app import config
from app.db.backup import backup


def main():
    config.load_env_file()
    dest = backup(config.db_path(), config.backup_dir(), config.backup_keep())
    print(f"Backed up {config.db_path()} -> {dest}")


if __name__ == "__main__":
    main()
