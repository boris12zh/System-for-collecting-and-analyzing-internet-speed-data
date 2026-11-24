"""Shared fixtures. No test may touch the real network."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from speed_tracker.core.models import SpeedTestResult
from speed_tracker.infrastructure.repository import SQLiteResultRepository
from tests.fakes import BASE_TIME


@pytest.fixture
def make_result() -> Callable[..., SpeedTestResult]:
    """Build results at ``BASE_TIME + hours`` with sensible default values."""

    def factory(
        download: float = 100.0,
        upload: float = 20.0,
        ping: float = 10.0,
        hours: float = 0,
        server_name: str | None = None,
    ) -> SpeedTestResult:
        return SpeedTestResult(
            download,
            upload,
            ping,
            measured_at=BASE_TIME + timedelta(hours=hours),
            server_name=server_name,
        )

    return factory


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "SpeedTracker" / "speed_tracker.db"


@pytest.fixture
def repository(db_path: Path) -> SQLiteResultRepository:
    return SQLiteResultRepository(db_path)
