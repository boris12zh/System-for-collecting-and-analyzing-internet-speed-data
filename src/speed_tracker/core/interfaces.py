"""Contracts for infrastructure adapters, with no framework dependencies."""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from speed_tracker.core.models import SpeedTestResult, StatisticsSummary

ProgressCallback = Callable[[str], None]


class SpeedTestProvider(Protocol):
    def run_test(self, on_progress: ProgressCallback | None = None) -> SpeedTestResult:
        """Measure ping, download and upload (US03.3)."""
        ...


class ResultRepository(Protocol):
    def save(self, result: SpeedTestResult) -> SpeedTestResult:
        """Insert and return a result with its database ID."""
        ...

    def list_all(self) -> list[SpeedTestResult]:
        """Return recorded tests, newest first."""
        ...

    def get(self, result_id: int) -> SpeedTestResult | None:
        """Return one stored test or None."""
        ...


class ResultExporter(Protocol):
    def export(
        self,
        results: Sequence[SpeedTestResult],
        destination: Path,
        summary: StatisticsSummary | None = None,
    ) -> Path:
        """Export results to a file (US03.3)."""
        ...
