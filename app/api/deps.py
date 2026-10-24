"""FastAPI dependencies shared by the routes."""

from app import config, db
from app.qb import get_connector
from app.qb.base import Connector


def get_conn():
    conn = db.connect(config.db_path())
    try:
        yield conn
    finally:
        conn.close()


def get_qb() -> Connector:
    return get_connector()
