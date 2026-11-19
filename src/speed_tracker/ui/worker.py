"""QThread shell for asynchronous tests (real execution is scheduled for US05)."""

from PySide6.QtCore import QThread, Signal


class SpeedTestWorker(QThread):
    """Worker API placeholder. It does not perform a speed test yet."""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def run(self) -> None:
        """Signal that the feature is unavailable until the next project stories."""
        self.error_occurred.emit("Speed testing is not implemented yet (US03.3/US05).")
