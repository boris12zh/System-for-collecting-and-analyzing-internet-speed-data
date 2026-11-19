"""Placeholder window only; full dashboard belongs to US05."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Speed Tracker")
        self.resize(650, 350)
        label = QLabel("Speed Tracker — UI is planned for US05")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)
