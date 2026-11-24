"""SQLite schema, migration and persistence tests (US03.2)."""

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from speed_tracker.core.errors import SpeedTrackerError
from speed_tracker.core.models import SpeedTestResult
from speed_tracker.infrastructure.database import (
    SCHEMA_VERSION,
    DatabaseError,
    get_schema_version,
    initialize_database,
)
from speed_tracker.infrastructure.repository import SQLiteResultRepository
from tests.fakes import BASE_TIME

LEGACY_V1_SCHEMA = """
CREATE TABLE speed_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measured_at TEXT NOT NULL,
    download_mbps REAL NOT NULL CHECK (download_mbps >= 0),
    upload_mbps REAL NOT NULL CHECK (upload_mbps >= 0),
    ping_ms REAL NOT NULL CHECK (ping_ms >= 0)
);
INSERT INTO speed_tests (measured_at, download_mbps, upload_mbps, ping_ms)
VALUES ('2026-11-01T10:00:00+00:00', 80.0, 15.0, 9.0);
"""


def test_database_created_on_first_run(db_path: Path) -> None:
    assert not db_path.exists()
    assert initialize_database(db_path) == db_path
    assert db_path.exists()
    assert initialize_database(db_path) == db_path  # idempotent
    with sqlite3.connect(db_path) as db:
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master")}
        columns = {row[1] for row in db.execute("PRAGMA table_info(speed_tests)")}
    assert {"speed_tests", "idx_speed_tests_measured_at"} <= names
    assert "server_name" in columns
    assert get_schema_version(db_path) == SCHEMA_VERSION


def test_legacy_skeleton_database_is_upgraded_keeping_data(tmp_path: Path) -> None:
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as db:
        db.executescript(LEGACY_V1_SCHEMA)  # 0.1.0 never set user_version (= 0)

    repository = SQLiteResultRepository(path)

    assert get_schema_version(path) == SCHEMA_VERSION
    [old] = repository.list_all()
    assert old.download_mbps == 80.0
    assert old.server_name is None
    repository.save(SpeedTestResult(1.0, 1.0, 1.0, server_name="new"))
    assert repository.count() == 2


def test_partially_migrated_database_is_completed(tmp_path: Path) -> None:
    path = tmp_path / "partial.db"
    with sqlite3.connect(path) as db:
        db.executescript(LEGACY_V1_SCHEMA)
        db.execute("ALTER TABLE speed_tests ADD COLUMN server_name TEXT")
        db.execute("PRAGMA user_version = 1")
    initialize_database(path)
    assert get_schema_version(path) == SCHEMA_VERSION


def test_newer_schema_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as db:
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    with pytest.raises(DatabaseError, match="newer than this application"):
        initialize_database(path)


def test_unopenable_path_raises_friendly_error(tmp_path: Path) -> None:
    blocker = tmp_path / "file.txt"
    blocker.write_text("not a folder")
    with pytest.raises(DatabaseError) as info:
        initialize_database(blocker / "db.sqlite3")
    assert isinstance(info.value, SpeedTrackerError)


def test_save_load_round_trip_and_newest_first(
    repository: SQLiteResultRepository, db_path: Path
) -> None:
    older = SpeedTestResult(90.1, 20.2, 8.9, measured_at=BASE_TIME, server_name="ISP - Sofia")
    newer = SpeedTestResult(110.5, 25.0, 7.0, measured_at=BASE_TIME + timedelta(hours=1))
    old_saved = repository.save(older)
    new_saved = repository.save(newer)
    assert (old_saved.id, new_saved.id) == (1, 2)
    assert repository.get(1) == old_saved
    assert repository.get(999) is None
    assert repository.list_all() == [new_saved, old_saved]
    assert SQLiteResultRepository(db_path).list_all() == [new_saved, old_saved]


def test_non_utc_timestamps_sort_correctly(repository: SQLiteResultRepository) -> None:
    plus_three = timezone(timedelta(hours=3))
    # 12:30 at +03:00 is 09:30 UTC, i.e. earlier than 10:00 UTC.
    early = repository.save(
        SpeedTestResult(1, 1, 1, measured_at=datetime(2026, 11, 5, 12, 30, tzinfo=plus_three))
    )
    late = repository.save(
        SpeedTestResult(2, 2, 2, measured_at=datetime(2026, 11, 5, 10, 0, tzinfo=UTC))
    )
    assert [r.id for r in repository.list_all()] == [late.id, early.id]
    stored = repository.get(early.id or -1)
    assert stored is not None
    assert stored.measured_at == early.measured_at  # same instant
    assert stored.measured_at.utcoffset() == timedelta(0)  # normalized to UTC


def test_list_between_bounds(
    repository: SQLiteResultRepository, make_result: Callable[..., SpeedTestResult]
) -> None:
    saved = [repository.save(make_result(hours=h)) for h in range(5)]
    start, end = BASE_TIME + timedelta(hours=1), BASE_TIME + timedelta(hours=3)
    assert repository.list_between(start, end) == [saved[2], saved[1]]  # end exclusive
    assert repository.list_between(start=start) == saved[:0:-1]
    assert repository.list_between(end=start) == [saved[0]]
    assert repository.list_between() == repository.list_all()


def test_list_between_requires_aware_bounds(repository: SQLiteResultRepository) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        repository.list_between(start=datetime(2026, 1, 1))


def test_delete_and_count(
    repository: SQLiteResultRepository, make_result: Callable[..., SpeedTestResult]
) -> None:
    assert repository.count() == 0
    first = repository.save(make_result())
    repository.save(make_result(hours=1))
    assert repository.count() == 2
    assert repository.delete(first.id or -1) is True
    assert repository.delete(first.id or -1) is False
    assert repository.get(first.id or -1) is None
    assert repository.count() == 1


def test_cyrillic_directory_and_server_name(tmp_path: Path) -> None:
    repository = SQLiteResultRepository(tmp_path / "Измервания" / "резултати.sqlite")
    result = repository.save(SpeedTestResult(50.0, 10.0, 15.0, server_name="Виваком - София"))
    assert repository.get(result.id or -1) == result


def test_insert_existing_result_not_allowed(repository: SQLiteResultRepository) -> None:
    stored = repository.save(SpeedTestResult(20.0, 10.0, 5.0))
    with pytest.raises(ValueError, match="Only new results"):
        repository.save(stored)
    assert repository.count() == 1


def test_check_constraints_reject_negative_values(db_path: Path) -> None:
    initialize_database(db_path)
    with sqlite3.connect(db_path) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO speed_tests (measured_at, download_mbps, upload_mbps, ping_ms) "
            "VALUES ('2026-01-01T00:00:00+00:00', -1, 1, 1)"
        )


def test_sqlite_failures_become_database_errors(
    repository: SQLiteResultRepository, db_path: Path
) -> None:
    with sqlite3.connect(db_path) as db:
        db.execute("DROP TABLE speed_tests")
    operations: list[Callable[[], object]] = [
        lambda: repository.save(SpeedTestResult(1, 1, 1)),
        repository.list_all,
        lambda: repository.get(1),
        lambda: repository.delete(1),
        repository.count,
    ]
    for operation in operations:
        with pytest.raises(DatabaseError, match="no such table"):
            operation()


def test_corrupt_file_raises_database_error(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.db"
    path.write_bytes(b"this is not a sqlite database" * 100)
    with pytest.raises(DatabaseError, match="Cannot initialize"):
        initialize_database(path)


def test_locked_database_gives_readable_error(
    repository: SQLiteResultRepository, db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("speed_tracker.infrastructure.database.BUSY_TIMEOUT_SECONDS", 0.1)
    blocker = sqlite3.connect(db_path)
    try:
        blocker.execute("BEGIN EXCLUSIVE")  # another process is writing
        with pytest.raises(DatabaseError, match="Could not save speed test: database is locked"):
            repository.save(SpeedTestResult(1, 1, 1))
    finally:
        blocker.rollback()
        blocker.close()
    assert repository.save(SpeedTestResult(1, 1, 1)).id == 1  # works once released
