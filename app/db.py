import os
import sqlite3

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_filename TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    success_count INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deployments (
    deployment_id TEXT PRIMARY KEY,
    service_name TEXT NOT NULL CHECK (service_name <> ''),
    status TEXT NOT NULL CHECK (status IN ('success','failed')),
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
    error_message TEXT NOT NULL DEFAULT '',
    deployment_date TEXT NOT NULL,
    environment TEXT NOT NULL CHECK (environment <> ''),
    batch_id INTEGER NOT NULL REFERENCES import_batches(id)
);
CREATE INDEX IF NOT EXISTS ix_dep_service ON deployments(service_name);
CREATE INDEX IF NOT EXISTS ix_dep_status ON deployments(status);
CREATE INDEX IF NOT EXISTS ix_dep_date ON deployments(deployment_date);
"""


def connect() -> sqlite3.Connection:
    path = config.db_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, timeout=2.0)  # explicit transactions
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn
