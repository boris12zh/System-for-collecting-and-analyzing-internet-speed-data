"""Contracts for infrastructure adapters, with no framework dependencies."""

from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol

from speed_tracker.core.models import SpeedTestResult, StatisticsSummary

ProgressCallback = Callable[[str], None]


class SpeedTestProvider(Protocol):
    def run_test(self, on_progress: ProgressCallback | None = None) -> SpeedTestResult:
        """Measure ping, download and upload; raise ``SpeedTestError`` on failure."""
        ...


class ResultRepository(Protocol):
    def save(self, result: SpeedTestResult) -> SpeedTestResult:
        """Insert and return a result with its database ID."""
        ...

    def list_all(self) -> list[SpeedTestResult]:
        """Return recorded tests, newest first."""
        ...

    def list_between(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[SpeedTestResult]:
        """Return tests with ``start <= measured_at < end``, newest first."""
        ...

    def get(self, result_id: int) -> SpeedTestResult | None:
        """Return one stored test or None."""
        ...

    def delete(self, result_id: int) -> bool:
        """Delete one stored test; return False if it did not exist."""
        ...

    def count(self) -> int:
        """Return the number of stored tests."""
        ...


class ResultExporter(Protocol):
    def export(
        self,
        results: Sequence[SpeedTestResult],
        destination: Path,
        summary: StatisticsSummary | None = None,
    ) -> Path:
        """Write results to a file and return its path; raise ``ExportError``."""
        ...
