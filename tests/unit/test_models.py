"""Quick domain validation tests."""

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from speed_tracker.core.models import SpeedTestResult


def test_result_accepts_valid_values() -> None:
    result = SpeedTestResult(42.0, 10.0, 8.5)
    assert result.id is None
    assert result.server_name is None
    assert result.measured_at.tzinfo is not None


def test_zero_and_integer_values_are_accepted() -> None:
    result = SpeedTestResult(0, 0, 0)
    assert result.download_mbps == 0


@pytest.mark.parametrize("field_index", [0, 1, 2])
@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_result_rejects_invalid_numbers(field_index: int, value: float) -> None:
    values = [10.0, 10.0, 10.0]
    values[field_index] = value
    with pytest.raises(ValueError, match="finite, nonnegative"):
        SpeedTestResult(*values)


@pytest.mark.parametrize("value", ["10", None, True])
def test_result_rejects_non_numbers(value: Any) -> None:
    with pytest.raises(ValueError, match="must be a number"):
        SpeedTestResult(value, 10.0, 8.5)


def test_timestamp_must_have_timezone() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        SpeedTestResult(10.0, 10.0, 8.5, measured_at=datetime(2026, 11, 5))


def test_non_utc_timezone_is_accepted() -> None:
    sofia = timezone(timedelta(hours=2))
    result = SpeedTestResult(10.0, 10.0, 8.5, measured_at=datetime(2026, 11, 5, tzinfo=sofia))
    assert result.measured_at.utcoffset() == timedelta(hours=2)
