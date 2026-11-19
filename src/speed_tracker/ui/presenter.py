"""Presenter placeholder: interactive behavior is planned for US05."""

from speed_tracker.core.interfaces import ResultRepository
from speed_tracker.core.models import SpeedTestResult


class SpeedTrackerPresenter:
    """Keeps future UI logic out of the main window."""

    def __init__(self, repository: ResultRepository) -> None:
        self.repository = repository

    def get_history(self) -> list[SpeedTestResult]:
        """Basic read-only history action, usable without Qt."""
        return self.repository.list_all()
