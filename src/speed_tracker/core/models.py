"""Domain objects. This module stays independent of I/O and UI."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite


@dataclass(frozen=True, slots=True)
class SpeedTestResult:
    """A single internet speed measurement (speed Mbps, ping milliseconds).

    ``server_name`` is optional descriptive metadata about the test server
    (for example ``"Vivacom – Sofia, Bulgaria"``); it is ``None`` for results
    recorded before the field existed.
    """

    download_mbps: float
    upload_mbps: float
    ping_ms: float
    measured_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None
    server_name: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("download_mbps", "upload_mbps", "ping_ms"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError(f"{field_name} must be a number")
            if not isfinite(value) or value < 0:
                raise ValueError(f"{field_name} must be a finite, nonnegative number")
        if self.measured_at.tzinfo is None or self.measured_at.utcoffset() is None:
            raise ValueError("measured_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class MetricSummary:
    """Descriptive statistics for one metric (download, upload or ping)."""

    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float


@dataclass(frozen=True, slots=True)
class StatisticsSummary:
    """Aggregate statistics for download, upload and ping over a set of results."""

    count: int
    download: MetricSummary
    upload: MetricSummary
    ping: MetricSummary
    first_measured_at: datetime
    last_measured_at: datetime
