"""Pure statistics over stored speed test results (US03.3)."""

import statistics
from collections.abc import Iterable, Sequence

from speed_tracker.core.models import MetricSummary, SpeedTestResult, StatisticsSummary


def summarize_metric(values: Iterable[float]) -> MetricSummary:
    """Return min/max/mean/median/sample standard deviation of ``values``.

    The standard deviation of a single value is defined as 0.0.
    Raises ``ValueError`` when ``values`` is empty.
    """
    data = list(values)
    if not data:
        raise ValueError("Cannot summarize an empty set of values")
    return MetricSummary(
        minimum=min(data),
        maximum=max(data),
        mean=statistics.fmean(data),
        median=statistics.median(data),
        standard_deviation=statistics.stdev(data) if len(data) > 1 else 0.0,
    )


def calculate_statistics(results: Sequence[SpeedTestResult]) -> StatisticsSummary:
    """Calculate min/max/mean/median/stdev for download, upload and ping.

    Raises ``ValueError`` when ``results`` is empty: callers should show an
    "no data yet" message instead of an all-zero summary.
    """
    if not results:
        raise ValueError("No speed test results to analyze")
    timestamps = [result.measured_at for result in results]
    return StatisticsSummary(
        count=len(results),
        download=summarize_metric(result.download_mbps for result in results),
        upload=summarize_metric(result.upload_mbps for result in results),
        ping=summarize_metric(result.ping_ms for result in results),
        first_measured_at=min(timestamps),
        last_measured_at=max(timestamps),
    )
