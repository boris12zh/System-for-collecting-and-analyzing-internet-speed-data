"""End-to-end backend pipeline through the CLI: measure -> store -> analyze -> export.

A fake provider replaces the network; everything else (SQLite, statistics,
exporters, CLI parsing) is real.
"""

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from speed_tracker.__main__ import main
from speed_tracker.core.models import SpeedTestResult
from speed_tracker.infrastructure.repository import SQLiteResultRepository
from tests.fakes import FakeProvider


def test_run_list_stats_export(
    db_path: Path,
    tmp_path: Path,
    make_result: Callable[..., SpeedTestResult],
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = ["--db", str(db_path)]
    provider = FakeProvider(
        make_result(download=100, upload=10, ping=20, server_name="Test ISP - Sofia"),
        make_result(download=50, upload=30, ping=10, hours=1),
    )
    assert main([*db, "run"], provider=provider) == 0
    assert main([*db, "run"], provider=provider) == 0
    out = capsys.readouterr().out
    assert "... fake measurement" in out
    assert "#1:" in out and "[Test ISP - Sofia]" in out

    assert main([*db, "list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("#2:") and lines[1].startswith("#1:")

    assert main([*db, "stats"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("2 test(s)")
    assert "mean     75.00" in out

    json_path = tmp_path / "export" / "history.json"
    assert main([*db, "export", "json", str(json_path)]) == 0
    document = json.loads(json_path.read_text(encoding="utf-8"))
    assert [r["id"] for r in document["results"]] == [2, 1]
    assert document["summary"]["upload"]["mean"] == 20

    csv_path = tmp_path / "history.csv"
    assert main([*db, "export", "csv", str(csv_path)]) == 0
    assert "Exported 2 result(s)" in capsys.readouterr().out
    assert len(csv_path.read_text(encoding="utf-8-sig").splitlines()) == 3


def test_failed_run_reports_error_and_saves_nothing(
    db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["--db", str(db_path), "run"], provider=FakeProvider(error="No internet"))
    assert code == 1
    assert "Error: No internet" in capsys.readouterr().err
    assert SQLiteResultRepository(db_path).count() == 0


def test_empty_database_messages(
    db_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = ["--db", str(db_path)]
    assert main([*db, "init-db"]) == 0
    assert "SQLite database ready" in capsys.readouterr().out
    assert main([*db, "list"]) == 0
    assert "No speed test results saved yet." in capsys.readouterr().out
    assert main([*db, "stats"]) == 0
    assert "No speed test results to analyze." in capsys.readouterr().out
    assert main([*db, "export", "json", str(tmp_path / "e.json")]) == 0
    assert json.loads((tmp_path / "e.json").read_text(encoding="utf-8"))["summary"] is None


def test_days_filter(db_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repository = SQLiteResultRepository(db_path)
    now = datetime.now(UTC)
    repository.save(SpeedTestResult(10, 1, 1, measured_at=now - timedelta(days=10)))
    repository.save(SpeedTestResult(30, 1, 1, measured_at=now - timedelta(hours=1)))
    assert main(["--db", str(db_path), "stats", "--days", "7"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("1 test(s)")
    assert "mean     30.00" in out


def test_export_error_is_friendly(
    db_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    assert main(["--db", str(db_path), "export", "csv", str(blocker / "x.csv")]) == 1
    assert capsys.readouterr().err.startswith("Error: Could not export")


@pytest.mark.parametrize("bad", [["stats", "--days", "0"], ["export", "xml", "out"], ["nope"]])
def test_invalid_arguments_exit_with_usage_error(db_path: Path, bad: list[str]) -> None:
    with pytest.raises(SystemExit) as info:
        main(["--db", str(db_path), *bad])
    assert info.value.code == 2
