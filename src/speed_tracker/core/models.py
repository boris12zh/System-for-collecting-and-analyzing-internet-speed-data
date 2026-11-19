"""Domain objects. This module stays independent of I/O and UI."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True, slots=True)
class SpeedTestResult:
    """A single internet speed measurement (speed Mbps, ping milliseconds)."""

    download_mbps: float
    upload_mbps: float
    ping_ms: float
    measured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None

    def __post_init__(self) -> None:
        for field_name in ("download_mbps", "upload_mbps", "ping_ms"):
            value = getattr(self, field_name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{field_name} must be a finite, nonnegative number")
        if self.measured_at.tzinfo is None or self.measured_at.utcoffset() is None:
            raise ValueError("measured_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class MetricSummary:
    """Planned per-metric statistical summary for US03.3."""

    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float


@dataclass(frozen=True, slots=True)
class StatisticsSummary:
    """Planned aggregate for download, upload and ping (US03.3)."""

    count: int
    download: MetricSummary
    upload: MetricSummary
    ping: MetricSummary
