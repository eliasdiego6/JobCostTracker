-- The schema as of the first release. IF NOT EXISTS so databases created before migrations
-- existed (user_version 0, tables already there) adopt version 1 without changes.
-- Later migrations should NOT need IF NOT EXISTS: each runs exactly once.

CREATE TABLE IF NOT EXISTS jobs (
    id            INTEGER PRIMARY KEY,
    job_number    TEXT NOT NULL UNIQUE COLLATE NOCASE,
    qb_list_id    TEXT NOT NULL,
    qb_full_name  TEXT NOT NULL,
    customer      TEXT NOT NULL,
    est_labor     REAL NOT NULL DEFAULT 0,
    est_material  REAL NOT NULL DEFAULT 0,
    est_sub       REAL NOT NULL DEFAULT 0,
    est_misc      REAL NOT NULL DEFAULT 0,
    contract      REAL NOT NULL DEFAULT 0,
    pct_complete  REAL,
    act_labor     REAL NOT NULL DEFAULT 0,
    act_material  REAL NOT NULL DEFAULT 0,
    act_sub       REAL NOT NULL DEFAULT 0,
    act_misc      REAL NOT NULL DEFAULT 0,
    invoiced      REAL NOT NULL DEFAULT 0,
    synced_at     TEXT,
    sync_error    TEXT,
    created_at    TEXT NOT NULL,
    created_by    TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id        INTEGER PRIMARY KEY,
    job_id    INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    txn_date  TEXT,
    txn_type  TEXT,
    ref       TEXT,
    name      TEXT,
    account   TEXT,
    memo      TEXT,
    amount    REAL NOT NULL,
    bucket    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY,
    job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    author      TEXT,
    body        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id     INTEGER PRIMARY KEY,
    name   TEXT NOT NULL UNIQUE COLLATE NOCASE,
    prefs  TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS user_jobs (
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id   INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    starred  INTEGER NOT NULL DEFAULT 0,
    hidden   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, job_id)
);

-- Which QB expense/COGS account feeds which bucket. Unmapped accounts count as misc.
CREATE TABLE IF NOT EXISTS account_map (
    account  TEXT PRIMARY KEY COLLATE NOCASE,
    bucket   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key    TEXT PRIMARY KEY,
    value  TEXT
);
