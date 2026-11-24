"""SQLite connection lifecycle, schema creation and migrations (US03.2).

The schema version is stored in ``PRAGMA user_version``:

* version 0 - empty database, or one created by the 0.1.0 skeleton
* version 1 - ``speed_tests`` table and timestamp index (0.1.0 layout)
* version 2 - adds the nullable ``server_name`` column (0.2.0)

``initialize_database`` upgrades any older database in place, so existing
measurement history is kept.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from speed_tracker.core.errors import SpeedTrackerError
from speed_tracker.infrastructure.paths import get_database_path

SCHEMA_VERSION = 2

_SCHEMA_V1 = """
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

_MIGRATIONS: dict[int, str] = {
    1: _SCHEMA_V1,
    2: "ALTER TABLE speed_tests ADD COLUMN server_name TEXT;",
}


class DatabaseError(SpeedTrackerError):
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


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _migrate(connection: sqlite3.Connection) -> None:
    current = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if current > SCHEMA_VERSION:
        raise DatabaseError(
            f"Database schema version {current} is newer than this application "
            f"supports ({SCHEMA_VERSION}). Please update Speed Tracker."
        )
    for version in range(current + 1, SCHEMA_VERSION + 1):
        # Each step must be safe to re-run: executescript() commits implicitly, so a
        # crash could leave the change applied but user_version not yet bumped.
        already_applied = version == 2 and "server_name" in _column_names(connection, "speed_tests")
        if not already_applied:
            connection.executescript(_MIGRATIONS[version])
        # PRAGMA cannot be parameterized; the value is a trusted integer.
        connection.execute(f"PRAGMA user_version = {version}")


def get_schema_version(database_path: Path) -> int:
    """Return the ``user_version`` stored in an existing database file."""
    with open_connection(database_path) as connection:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])


def initialize_database(database_path: Path | None = None) -> Path:
    """Create the data folder and schema, or upgrade an older one. Safe to rerun."""
    path = database_path if database_path is not None else get_database_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open_connection(path) as connection:
            _migrate(connection)
    except DatabaseError:
        raise
    except (sqlite3.Error, OSError) as exc:
        raise DatabaseError(f"Cannot initialize Speed Tracker database at {path}: {exc}") from exc
    return path
