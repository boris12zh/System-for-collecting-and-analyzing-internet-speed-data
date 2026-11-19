"""Quick domain validation tests."""

from datetime import datetime, timezone

import pytest

from speed_tracker.core.models import SpeedTestResult


def test_result_accepts_valid_values() -> None:
    result = SpeedTestResult(42.0, 10.0, 8.5)
    assert result.id is None
    assert result.measured_at.tzinfo is not None


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_result_rejects_invalid_download(value: float) -> None:
    with pytest.raises(ValueError, match="download_mbps"):
        SpeedTestResult(value, 10.0, 8.5)


def test_timestamp_must_have_timezone() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        SpeedTestResult(10.0, 10.0, 8.5, measured_at=datetime(2026, 11, 5))


def test_utc_timestamp_is_accepted() -> None:
    result = SpeedTestResult(10.0, 10.0, 8.5, measured_at=datetime.now(timezone.utc))
    assert result.measured_at.tzinfo is not None
