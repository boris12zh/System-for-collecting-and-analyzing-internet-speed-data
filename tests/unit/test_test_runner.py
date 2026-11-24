"""SpeedTestRunner orchestration with test doubles only."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

import pytest

from speed_tracker.core.errors import SpeedTestError
from speed_tracker.core.models import SpeedTestResult
from speed_tracker.core.test_runner import SpeedTestRunner
from tests.fakes import FakeProvider


class InMemoryRepository:
    def __init__(self) -> None:
        self.saved: list[SpeedTestResult] = []

    def save(self, result: SpeedTestResult) -> SpeedTestResult:
        stored = replace(result, id=len(self.saved) + 1)
        self.saved.append(stored)
        return stored

    def list_all(self) -> list[SpeedTestResult]:
        return list(reversed(self.saved))

    def list_between(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[SpeedTestResult]:
        return self.list_all()

    def get(self, result_id: int) -> SpeedTestResult | None:
        return next((r for r in self.saved if r.id == result_id), None)

    def delete(self, result_id: int) -> bool:
        return False

    def count(self) -> int:
        return len(self.saved)


def test_run_measures_saves_and_reports(make_result: Callable[..., SpeedTestResult]) -> None:
    repository = InMemoryRepository()
    runner = SpeedTestRunner(FakeProvider(make_result(download=88.0)), repository)
    messages: list[str] = []

    stored = runner.run(on_progress=messages.append)

    assert stored.id == 1
    assert stored.download_mbps == 88.0
    assert repository.saved == [stored]
    assert messages == ["fake measurement", "Result saved"]


def test_run_without_progress_callback(make_result: Callable[..., SpeedTestResult]) -> None:
    runner = SpeedTestRunner(FakeProvider(make_result()), InMemoryRepository())
    assert runner.run().id == 1


def test_failed_measurement_saves_nothing() -> None:
    repository = InMemoryRepository()
    runner = SpeedTestRunner(FakeProvider(error="offline"), repository)
    with pytest.raises(SpeedTestError, match="offline"):
        runner.run()
    assert repository.saved == []
