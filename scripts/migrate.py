"""Bring the database schema up to date. Safe to run any number of times.

Usage:  python -m scripts.migrate
The deploy pipeline runs this after backing up and before restarting the app.
"""

from app import config, db
from app.db.migrator import current_version, latest_version


def main():
    config.load_env_file()
    path = config.db_path()
    conn = db.connect(path)
    try:
        before = current_version(conn)
        applied = db.migrate(conn)
    finally:
        conn.close()
    if applied:
        print(f"{path}: migrated v{before} -> v{applied[-1]} (applied {', '.join(map(str, applied))})")
    else:
        print(f"{path}: already at v{latest_version()}, nothing to do")


if __name__ == "__main__":
    main()
