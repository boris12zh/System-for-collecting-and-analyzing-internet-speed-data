"""Future CSV and JSON export adapters (US03.3)."""

from collections.abc import Sequence
from pathlib import Path

from speed_tracker.core.models import SpeedTestResult, StatisticsSummary


class CsvExporter:
    def export(
        self,
        results: Sequence[SpeedTestResult],
        destination: Path,
        summary: StatisticsSummary | None = None,
    ) -> Path:
        """Planned CSV implementation."""
        raise NotImplementedError("CSV export is planned for US03.3")


class JsonExporter:
    def export(
        self,
        results: Sequence[SpeedTestResult],
        destination: Path,
        summary: StatisticsSummary | None = None,
    ) -> Path:
        """Planned JSON implementation."""
        raise NotImplementedError("JSON export is planned for US03.3")
