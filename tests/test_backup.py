import sqlite3

import pytest

from app.db.backup import backup


def test_backup_copies_data_and_prunes_old_copies(conn, tmp_path):
    conn.execute("INSERT INTO users (name) VALUES ('Alice')")
    conn.commit()
    dest_dir = tmp_path / "backups"
    dest_dir.mkdir()
    for stamp in ("20260101-000000", "20260102-000000", "20260103-000000"):
        (dest_dir / f"jobs-{stamp}.db").write_bytes(b"")

    out = backup(tmp_path / "jobs.db", dest_dir, keep=2)

    copy = sqlite3.connect(out)
    assert copy.execute("SELECT name FROM users").fetchone()[0] == "Alice"
    copy.close()
    assert sorted(p.name for p in dest_dir.iterdir()) == ["jobs-20260103-000000.db", out.name]


def test_missing_database_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup(tmp_path / "nope.db", tmp_path / "b", keep=5)
