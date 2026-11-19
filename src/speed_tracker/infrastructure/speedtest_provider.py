"""Future speedtest-cli adapter; real measurements belong to US03.3."""

from speed_tracker.core.interfaces import ProgressCallback
from speed_tracker.core.models import SpeedTestResult


class SpeedtestCliProvider:
    """Placeholder implementing the provider contract (no network calls yet)."""

    def run_test(self, on_progress: ProgressCallback | None = None) -> SpeedTestResult:
        raise NotImplementedError("Actual speed measurements are planned for US03.3")
