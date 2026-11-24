"""Use case orchestrating one speed test: measure, then persist (US03.3)."""

from speed_tracker.core.interfaces import (
    ProgressCallback,
    ResultRepository,
    SpeedTestProvider,
)
from speed_tracker.core.models import SpeedTestResult


class SpeedTestRunner:
    """Runs a measurement through the provider and stores the result.

    Nothing is saved if the provider raises, so the history never contains
    partial measurements.
    """

    def __init__(self, provider: SpeedTestProvider, repository: ResultRepository) -> None:
        self.provider = provider
        self.repository = repository

    def run(self, on_progress: ProgressCallback | None = None) -> SpeedTestResult:
        """Measure once and return the stored result (with its database ID)."""
        result = self.provider.run_test(on_progress)
        saved = self.repository.save(result)
        if on_progress is not None:
            on_progress("Result saved")
        return saved
