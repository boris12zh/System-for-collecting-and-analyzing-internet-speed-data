"""SQLite CRUD adapter implementing the core ResultRepository contract."""

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from speed_tracker.core.models import SpeedTestResult
from speed_tracker.infrastructure.database import (
    DatabaseError,
    initialize_database,
    open_connection,
)
from speed_tracker.infrastructure.paths import get_database_path

_SELECT_COLUMNS = "SELECT id, measured_at, download_mbps, upload_mbps, ping_ms, server_name"
_NEWEST_FIRST = "ORDER BY measured_at DESC, id DESC"


def _to_db_timestamp(value: datetime) -> str:
    """Normalize to UTC ISO 8601 so that text ordering equals time ordering."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat()


class SQLiteResultRepository:
    """Save and retrieve speed test history, with no Qt or network imports."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path if database_path is not None else get_database_path()
        initialize_database(self.database_path)

    def save(self, result: SpeedTestResult) -> SpeedTestResult:
        """Insert one complete measurement and return a copy with its new ID."""
        if result.id is not None:
            raise ValueError("Only new results (id=None) can be inserted")
        try:
            with open_connection(self.database_path) as connection:
                cursor = connection.execute(
                    """INSERT INTO speed_tests
                       (measured_at, download_mbps, upload_mbps, ping_ms, server_name)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        _to_db_timestamp(result.measured_at),
                        result.download_mbps,
                        result.upload_mbps,
                        result.ping_ms,
                        result.server_name,
                    ),
                )
                new_id = cursor.lastrowid
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save speed test: {exc}") from exc
        if new_id is None:
            raise DatabaseError("Could not save speed test: no ID returned")
        return replace(result, id=new_id)

    def list_all(self) -> list[SpeedTestResult]:
        """Load entire history, newest measurement first."""
        return self.list_between()

    def list_between(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[SpeedTestResult]:
        """Load results with ``start <= measured_at < end`` (bounds optional)."""
        conditions: list[str] = []
        parameters: list[str] = []
        if start is not None:
            conditions.append("measured_at >= ?")
            parameters.append(_to_db_timestamp(start))
        if end is not None:
            conditions.append("measured_at < ?")
            parameters.append(_to_db_timestamp(end))
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        try:
            with open_connection(self.database_path) as connection:
                rows = connection.execute(
                    f"{_SELECT_COLUMNS} FROM speed_tests {where} {_NEWEST_FIRST}",
                    parameters,
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not load speed test history: {exc}") from exc
        return [self._from_row(row) for row in rows]

    def get(self, result_id: int) -> SpeedTestResult | None:
        """Get a single record, or None if the ID does not exist."""
        try:
            with open_connection(self.database_path) as connection:
                row = connection.execute(
                    f"{_SELECT_COLUMNS} FROM speed_tests WHERE id = ?",
                    (result_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not load speed test {result_id}: {exc}") from exc
        return None if row is None else self._from_row(row)

    def delete(self, result_id: int) -> bool:
        """Delete one record; return False if the ID did not exist."""
        try:
            with open_connection(self.database_path) as connection:
                cursor = connection.execute("DELETE FROM speed_tests WHERE id = ?", (result_id,))
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not delete speed test {result_id}: {exc}") from exc
        return cursor.rowcount > 0

    def count(self) -> int:
        """Return the number of stored results."""
        try:
            with open_connection(self.database_path) as connection:
                row = connection.execute("SELECT COUNT(*) FROM speed_tests").fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not count speed tests: {exc}") from exc
        return int(row[0])

    @staticmethod
    def _from_row(row: sqlite3.Row) -> SpeedTestResult:
        server_name = row["server_name"]
        return SpeedTestResult(
            id=int(row["id"]),
            measured_at=datetime.fromisoformat(str(row["measured_at"])),
            download_mbps=float(row["download_mbps"]),
            upload_mbps=float(row["upload_mbps"]),
            ping_ms=float(row["ping_ms"]),
            server_name=None if server_name is None else str(server_name),
        )
