import sqlite3

import pytest

from app import db
from app.db import migrator as m


def tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_fresh_database_reaches_latest_version(tmp_path):
    conn = db.connect(tmp_path / "new.db")
    applied = db.migrate(conn)
    assert applied == list(range(1, m.latest_version() + 1))
    assert m.current_version(conn) == m.latest_version()
    assert {"jobs", "transactions", "notes", "users", "user_jobs", "account_map", "meta"} <= tables(conn)


def test_running_again_does_nothing(conn):
    assert db.migrate(conn) == []


def test_pre_migration_database_is_adopted_with_data_kept(tmp_path):
    # databases created before migrations existed: tables present, user_version 0
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript((m.MIGRATIONS_DIR / "0001_initial.sql").read_text())
    old.execute("INSERT INTO users (name) VALUES ('Alice')")
    old.commit()
    old.close()

    conn = db.connect(path)
    assert m.current_version(conn) == 0
    db.migrate(conn)
    assert m.current_version(conn) == m.latest_version()
    assert conn.execute("SELECT name FROM users").fetchone()[0] == "Alice"


def test_failed_migration_rolls_back(tmp_path, monkeypatch):
    bad_dir = tmp_path / "migrations"
    bad_dir.mkdir()
    (bad_dir / "0001_initial.sql").write_text((m.MIGRATIONS_DIR / "0001_initial.sql").read_text())
    (bad_dir / "0002_broken.sql").write_text("CREATE TABLE extra (id INTEGER); SELECT * FROM no_such_table;")
    monkeypatch.setattr(m, "MIGRATIONS_DIR", bad_dir)

    conn = db.connect(tmp_path / "x.db")
    with pytest.raises(sqlite3.OperationalError):
        db.migrate(conn)
    assert m.current_version(conn) == 1
    assert "extra" not in tables(conn)


def test_migration_numbers_must_be_contiguous(tmp_path, monkeypatch):
    (tmp_path / "0001_a.sql").write_text("")
    (tmp_path / "0003_c.sql").write_text("")
    monkeypatch.setattr(m, "MIGRATIONS_DIR", tmp_path)
    with pytest.raises(ValueError, match="no gaps"):
        m.migrations()
