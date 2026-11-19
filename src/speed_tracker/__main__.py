"""Application composition root and small database maintenance CLI."""

import argparse
from collections.abc import Sequence

from speed_tracker.infrastructure.database import DatabaseError, initialize_database
from speed_tracker.infrastructure.repository import SQLiteResultRepository


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Speed Tracker (early project skeleton)")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("init-db", "list"),
        help="Database tasks; omit for an empty PySide6 window",
    )
    args = parser.parse_args(argv)

    if args.command == "init-db":
        try:
            db_path = initialize_database()
        except DatabaseError as exc:
            parser.exit(1, f"Database error: {exc}\n")
        print(f"SQLite database ready: {db_path}")
        return 0

    if args.command == "list":
        try:
            records = SQLiteResultRepository().list_all()
        except DatabaseError as exc:
            parser.exit(1, f"Database error: {exc}\n")
        if not records:
            print("No speed test results saved yet.")
        for record in records:
            print(
                f"#{record.id}: {record.measured_at.isoformat()} "
                f"download={record.download_mbps:.2f} Mbps, "
                f"upload={record.upload_mbps:.2f} Mbps, ping={record.ping_ms:.2f} ms"
            )
        return 0

    try:
        from PySide6.QtWidgets import QApplication

        from speed_tracker.ui.main_window import MainWindow
    except ImportError:
        parser.exit(1, "UI placeholder requires: pip install -e '.[ui]'\n")

    application = QApplication([])
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
