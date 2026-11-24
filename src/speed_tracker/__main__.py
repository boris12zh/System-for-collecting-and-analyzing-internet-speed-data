"""Application composition root and command-line interface.

Commands (all work without PySide6):

    init-db                       create or upgrade the SQLite database
    run                           perform one real speed test and save it
    list                          print the stored history, newest first
    stats [--days N]              print min/max/mean/median/stdev
    export {csv,json} OUTPUT      export history (JSON includes statistics)
           [--days N]

With no command, the PySide6 window is opened.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from speed_tracker.core.errors import SpeedTrackerError
from speed_tracker.core.interfaces import ResultExporter, ResultRepository, SpeedTestProvider
from speed_tracker.core.models import MetricSummary, SpeedTestResult
from speed_tracker.core.statistics import calculate_statistics
from speed_tracker.core.test_runner import SpeedTestRunner
from speed_tracker.infrastructure.database import initialize_database
from speed_tracker.infrastructure.exporters import CsvExporter, JsonExporter
from speed_tracker.infrastructure.repository import SQLiteResultRepository
from speed_tracker.infrastructure.speedtest_provider import SpeedtestCliProvider

EXPORTERS: dict[str, type[ResultExporter]] = {"csv": CsvExporter, "json": JsonExporter}


def _positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive whole number")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="speed_tracker", description="Collect and analyze internet speed measurements."
    )
    parser.add_argument("--db", type=Path, help="Use this database file instead of the default")
    commands = parser.add_subparsers(dest="command", metavar="command")
    commands.add_parser("init-db", help="Create or upgrade the database")
    commands.add_parser("run", help="Run one speed test and save the result")
    commands.add_parser("list", help="Show saved results, newest first")
    stats = commands.add_parser("stats", help="Show statistics for saved results")
    stats.add_argument("--days", type=_positive_int, help="Only the last N days")
    export = commands.add_parser("export", help="Export saved results to CSV or JSON")
    export.add_argument("format", choices=sorted(EXPORTERS))
    export.add_argument("output", type=Path)
    export.add_argument("--days", type=_positive_int, help="Only the last N days")
    return parser


def format_result(result: SpeedTestResult) -> str:
    server = f" [{result.server_name}]" if result.server_name else ""
    return (
        f"#{result.id}: {result.measured_at.isoformat()} "
        f"download={result.download_mbps:.2f} Mbps, "
        f"upload={result.upload_mbps:.2f} Mbps, ping={result.ping_ms:.2f} ms{server}"
    )


def _format_metric(label: str, unit: str, metric: MetricSummary) -> str:
    return (
        f"{label:<9} min {metric.minimum:9.2f}  max {metric.maximum:9.2f}  "
        f"mean {metric.mean:9.2f}  median {metric.median:9.2f}  "
        f"stdev {metric.standard_deviation:8.2f}  {unit}"
    )


def _load(repository: ResultRepository, days: int | None) -> list[SpeedTestResult]:
    if days is None:
        return repository.list_all()
    return repository.list_between(start=datetime.now(UTC) - timedelta(days=days))


def _run_ui() -> int:
    try:
        from PySide6.QtWidgets import QApplication

        from speed_tracker.ui.main_window import MainWindow
    except ImportError:
        print('The window requires PySide6: pip install -e ".[ui]"', file=sys.stderr)
        return 1
    application = QApplication([])
    window = MainWindow()
    window.show()
    return int(application.exec())


def main(
    argv: Sequence[str] | None = None,
    provider: SpeedTestProvider | None = None,
) -> int:
    """Entry point. ``provider`` can be injected so tests avoid the network."""
    args = build_parser().parse_args(argv)
    if args.command is None:
        return _run_ui()

    try:
        if args.command == "init-db":
            print(f"SQLite database ready: {initialize_database(args.db)}")
            return 0

        repository = SQLiteResultRepository(args.db)

        if args.command == "run":
            runner = SpeedTestRunner(provider or SpeedtestCliProvider(), repository)
            result = runner.run(on_progress=lambda message: print(f"... {message}"))
            print(format_result(result))
        elif args.command == "list":
            records = repository.list_all()
            if not records:
                print("No speed test results saved yet.")
            for record in records:
                print(format_result(record))
        elif args.command == "stats":
            records = _load(repository, args.days)
            if not records:
                print("No speed test results to analyze.")
                return 0
            summary = calculate_statistics(records)
            print(
                f"{summary.count} test(s) from {summary.first_measured_at.isoformat()} "
                f"to {summary.last_measured_at.isoformat()}"
            )
            print(_format_metric("Download", "Mbps", summary.download))
            print(_format_metric("Upload", "Mbps", summary.upload))
            print(_format_metric("Ping", "ms", summary.ping))
        elif args.command == "export":
            records = _load(repository, args.days)
            export_summary = calculate_statistics(records) if records else None
            path = EXPORTERS[args.format]().export(records, args.output, export_summary)
            print(f"Exported {len(records)} result(s) to {path}")
    except SpeedTrackerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
