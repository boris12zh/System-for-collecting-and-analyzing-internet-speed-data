"""SQLite connection lifecycle and creation of the schema (US03.2)."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from speed_tracker.infrastructure.paths import get_database_path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS speed_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measured_at TEXT NOT NULL,
    download_mbps REAL NOT NULL CHECK (download_mbps >= 0),
    upload_mbps REAL NOT NULL CHECK (upload_mbps >= 0),
    ping_ms REAL NOT NULL CHECK (ping_ms >= 0)
);
CREATE INDEX IF NOT EXISTS idx_speed_tests_measured_at
    ON speed_tests (measured_at DESC, id DESC);
"""


class DatabaseError(Exception):
    """Friendly storage-layer error for database or filesystem failures."""


@contextmanager
def open_connection(database_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a row-aware connection, committing or rolling back atomically."""
    path = database_path if database_path is not None else get_database_path()
    try:
        connection = sqlite3.connect(path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
    except (sqlite3.Error, OSError) as exc:
        raise DatabaseError(f"Cannot open Speed Tracker database at {path}: {exc}") from exc
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(database_path: Path | None = None) -> Path:
    """Create the data folder and SQLite schema if missing. Safe to rerun."""
    path = database_path if database_path is not None else get_database_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open_connection(path) as connection:
            # executescript commits implicitly; this fixed idempotent schema is safe.
            connection.executescript(SCHEMA_SQL)
    except (sqlite3.Error, OSError) as exc:
        raise DatabaseError(f"Cannot initialize Speed Tracker database at {path}: {exc}") from exc
    return path
