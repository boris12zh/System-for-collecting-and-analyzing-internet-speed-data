"""Statistics calculation (US03.3)."""

from collections.abc import Callable

import pytest

from speed_tracker.core.models import SpeedTestResult
from speed_tracker.core.statistics import calculate_statistics, summarize_metric


def test_summarize_metric_known_values() -> None:
    summary = summarize_metric([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert summary.minimum == 2.0
    assert summary.maximum == 9.0
    assert summary.mean == 5.0
    assert summary.median == 4.5
    assert summary.standard_deviation == pytest.approx(2.13809, rel=1e-5)  # sample stdev


def test_single_value_has_zero_deviation() -> None:
    summary = summarize_metric([42.0])
    assert (summary.minimum, summary.maximum, summary.mean, summary.median) == (42, 42, 42, 42)
    assert summary.standard_deviation == 0.0


def test_summarize_accepts_generators() -> None:
    assert summarize_metric(x for x in (1.0, 3.0)).mean == 2.0


def test_empty_values_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        summarize_metric([])


def test_empty_results_rejected() -> None:
    with pytest.raises(ValueError, match="No speed test results"):
        calculate_statistics([])


def test_calculate_statistics_per_metric(make_result: Callable[..., SpeedTestResult]) -> None:
    results = [
        make_result(download=100, upload=10, ping=20, hours=2),
        make_result(download=50, upload=30, ping=10, hours=0),
        make_result(download=75, upload=20, ping=30, hours=1),
    ]
    summary = calculate_statistics(results)
    assert summary.count == 3
    assert summary.download.mean == 75
    assert summary.download.minimum == 50
    assert summary.upload.maximum == 30
    assert summary.ping.median == 20
    assert summary.first_measured_at == results[1].measured_at
    assert summary.last_measured_at == results[0].measured_at
