"""Shared fixtures. Every test gets its own temp database and fake QuickBooks."""

import pytest
from fastapi.testclient import TestClient

from app import config, db


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("JCT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JCT_QB_MODE", "fake")
    monkeypatch.delenv("JCT_BACKUP_DIR", raising=False)


@pytest.fixture
def conn():
    """A migrated database connection, for service and repository tests."""
    c = db.connect(config.db_path())
    db.migrate(c)
    yield c
    c.close()


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c
