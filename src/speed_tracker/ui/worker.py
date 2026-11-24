"""QThread shell; it will wrap SpeedTestRunner in US05."""

from PySide6.QtCore import QThread, Signal


class SpeedTestWorker(QThread):
    """Worker API placeholder. It does not perform a speed test yet."""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def run(self) -> None:
        """Signal that the feature is unavailable until the next project stories."""
        self.error_occurred.emit("The UI is not connected to the speed test engine yet (US05).")
