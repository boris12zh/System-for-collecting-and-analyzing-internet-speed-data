"""SQLite CRUD adapter implementing the core ResultRepository contract."""

import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from speed_tracker.core.models import SpeedTestResult
from speed_tracker.infrastructure.database import (
    DatabaseError,
    initialize_database,
    open_connection,
)
from speed_tracker.infrastructure.paths import get_database_path


class SQLiteResultRepository:
    """Save and retrieve speed test history, with no Qt or network imports."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path if database_path is not None else get_database_path()
        initialize_database(self.database_path)

    def save(self, result: SpeedTestResult) -> SpeedTestResult:
        """Insert one complete measurement and return a copy with its new ID."""
        if result.id is not None:
            raise ValueError("Only new results (id=None) can be inserted")
        timestamp = result.measured_at.astimezone(timezone.utc).isoformat()
        try:
            with open_connection(self.database_path) as connection:
                cursor = connection.execute(
                    """INSERT INTO speed_tests
                       (measured_at, download_mbps, upload_mbps, ping_ms)
                       VALUES (?, ?, ?, ?)""",
                    (timestamp, result.download_mbps, result.upload_mbps, result.ping_ms),
                )
                new_id = cursor.lastrowid
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save speed test: {exc}") from exc
        if new_id is None:
            raise DatabaseError("Could not save speed test: no ID returned")
        return replace(result, id=new_id)

    def list_all(self) -> list[SpeedTestResult]:
        """Load entire history, newest measurement first."""
        try:
            with open_connection(self.database_path) as connection:
                rows = connection.execute(
                    """SELECT id, measured_at, download_mbps, upload_mbps, ping_ms
                       FROM speed_tests
                       ORDER BY measured_at DESC, id DESC"""
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not load speed test history: {exc}") from exc
        return [self._from_row(row) for row in rows]

    def get(self, result_id: int) -> SpeedTestResult | None:
        """Get a single record, or None if the ID does not exist."""
        try:
            with open_connection(self.database_path) as connection:
                row = connection.execute(
                    """SELECT id, measured_at, download_mbps, upload_mbps, ping_ms
                       FROM speed_tests WHERE id = ?""",
                    (result_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not load speed test {result_id}: {exc}") from exc
        return None if row is None else self._from_row(row)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> SpeedTestResult:
        return SpeedTestResult(
            id=int(row["id"]),
            measured_at=datetime.fromisoformat(str(row["measured_at"])),
            download_mbps=float(row["download_mbps"]),
            upload_mbps=float(row["upload_mbps"]),
            ping_ms=float(row["ping_ms"]),
        )
