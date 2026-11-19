"""Use case orchestrating speed tests (scheduled for US03.3)."""

from speed_tracker.core.interfaces import (
    ProgressCallback,
    ResultRepository,
    SpeedTestProvider,
)
from speed_tracker.core.models import SpeedTestResult


class SpeedTestRunner:
    """Holds injected dependencies; execution arrives in US03.3."""

    def __init__(self, provider: SpeedTestProvider, repository: ResultRepository) -> None:
        self.provider = provider
        self.repository = repository

    def run(self, on_progress: ProgressCallback | None = None) -> SpeedTestResult:
        """Future: measure, validate, and persist one complete result."""
        raise NotImplementedError("Speed test runner is planned for US03.3")
