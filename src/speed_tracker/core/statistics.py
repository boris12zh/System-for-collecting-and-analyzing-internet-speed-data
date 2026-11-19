"""Statistics calculation location (implementation scheduled for US03.3)."""

from collections.abc import Sequence

from speed_tracker.core.models import SpeedTestResult, StatisticsSummary


def calculate_statistics(results: Sequence[SpeedTestResult]) -> StatisticsSummary:
    """Calculate min/max/mean/median/stdev for three metrics in US03.3."""
    raise NotImplementedError("Statistics are planned for backlog story US03.3")
