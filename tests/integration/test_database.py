"""SQLite schema and persistence tests (US03.2)."""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from speed_tracker.core.models import SpeedTestResult
from speed_tracker.infrastructure.database import initialize_database
from speed_tracker.infrastructure.repository import SQLiteResultRepository


def test_database_created_on_first_run(tmp_path: Path) -> None:
    path = tmp_path / "SpeedTracker" / "speed_tracker.db"
    assert not path.exists()
    assert initialize_database(path) == path
    assert path.exists()
    # The initializer must be idempotent.
    assert initialize_database(path) == path
    with sqlite3.connect(path) as db:
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master")}
    assert "speed_tests" in names


def test_save_load_round_trip_and_newest_first(tmp_path: Path) -> None:
    repository = SQLiteResultRepository(tmp_path / "db.sqlite3")
    now = datetime(2026, 11, 5, tzinfo=timezone.utc)
    older = SpeedTestResult(90.1, 20.2, 8.9, measured_at=now)
    newer = SpeedTestResult(110.5, 25.0, 7.0, measured_at=now + timedelta(hours=1))
    old_saved = repository.save(older)
    new_saved = repository.save(newer)
    assert old_saved.id == 1
    assert new_saved.id == 2
    assert repository.get(1) == old_saved
    assert repository.get(999) is None
    assert repository.list_all() == [new_saved, old_saved]
    assert SQLiteResultRepository(tmp_path / "db.sqlite3").list_all() == [
        new_saved,
        old_saved,
    ]


def test_cyrillic_directory(tmp_path: Path) -> None:
    repository = SQLiteResultRepository(tmp_path / "Измервания" / "резултати.sqlite")
    result = repository.save(SpeedTestResult(50.0, 10.0, 15.0))
    assert repository.get(result.id or -1) == result


def test_insert_existing_result_not_allowed(tmp_path: Path) -> None:
    repository = SQLiteResultRepository(tmp_path / "db.sqlite3")
    stored = repository.save(SpeedTestResult(20.0, 10.0, 5.0))
    with pytest.raises(ValueError, match="Only new results"):
        repository.save(stored)
    assert len(repository.list_all()) == 1
