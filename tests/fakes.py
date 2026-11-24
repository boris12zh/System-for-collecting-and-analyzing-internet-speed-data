"""Test doubles shared by unit and integration tests."""

from datetime import UTC, datetime

from speed_tracker.core.errors import SpeedTestError
from speed_tracker.core.interfaces import ProgressCallback
from speed_tracker.core.models import SpeedTestResult

BASE_TIME = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


class FakeProvider:
    """Returns queued results (or raises) instead of measuring over the network."""

    def __init__(self, *results: SpeedTestResult, error: str | None = None) -> None:
        self.results = list(results)
        self.error = error
        self.calls = 0

    def run_test(self, on_progress: ProgressCallback | None = None) -> SpeedTestResult:
        self.calls += 1
        if on_progress is not None:
            on_progress("fake measurement")
        if self.error is not None:
            raise SpeedTestError(self.error)
        return self.results.pop(0)
