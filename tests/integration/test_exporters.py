"""CSV/JSON export written to real temporary files (US03.3)."""

import csv
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from speed_tracker.core.errors import ExportError
from speed_tracker.core.models import SpeedTestResult
from speed_tracker.core.statistics import calculate_statistics
from speed_tracker.infrastructure.exporters import CSV_COLUMNS, CsvExporter, JsonExporter


@pytest.fixture
def results(make_result: Callable[..., SpeedTestResult]) -> list[SpeedTestResult]:
    return [
        make_result(download=120.5, upload=30.0, ping=8.0, hours=1, server_name="Виваком - София"),
        make_result(download=80.0, upload=20.0, ping=12.0, server_name=None),
    ]


def test_csv_export(tmp_path: Path, results: list[SpeedTestResult]) -> None:
    path = CsvExporter().export(results, tmp_path / "out" / "history.csv")

    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM for Excel
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert tuple(rows[0]) == CSV_COLUMNS
    assert rows[0]["server_name"] == "Виваком - София"
    assert float(rows[0]["download_mbps"]) == 120.5
    assert rows[0]["measured_at"] == "2026-11-05T13:00:00+00:00"
    assert rows[1]["server_name"] == ""
    assert list(tmp_path.joinpath("out").iterdir()) == [path]  # no temp files left


def test_csv_export_of_nothing_has_header_only(tmp_path: Path) -> None:
    path = CsvExporter().export([], tmp_path / "empty.csv")
    assert path.read_text(encoding="utf-8-sig").strip() == ",".join(CSV_COLUMNS)


def test_json_export_with_summary(tmp_path: Path, results: list[SpeedTestResult]) -> None:
    summary = calculate_statistics(results)
    path = JsonExporter().export(results, tmp_path / "history.json", summary)

    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["format_version"] == 1
    assert document["count"] == 2
    assert document["results"][0]["server_name"] == "Виваком - София"
    assert document["results"][1]["server_name"] is None
    assert document["summary"]["count"] == 2
    assert document["summary"]["download"]["mean"] == pytest.approx(100.25)
    assert document["summary"]["first_measured_at"] == "2026-11-05T12:00:00+00:00"
    assert "Виваком" in path.read_text(encoding="utf-8")  # not \u-escaped


def test_json_export_without_summary(tmp_path: Path, results: list[SpeedTestResult]) -> None:
    path = JsonExporter().export(results, tmp_path / "history.json")
    assert json.loads(path.read_text(encoding="utf-8"))["summary"] is None


def test_export_overwrites_existing_file(tmp_path: Path, results: list[SpeedTestResult]) -> None:
    target = tmp_path / "history.json"
    target.write_text("old content")
    JsonExporter().export(results, target)
    assert json.loads(target.read_text(encoding="utf-8"))["count"] == 2


@pytest.mark.parametrize("exporter", [CsvExporter(), JsonExporter()])
def test_unwritable_destination_raises_export_error(
    tmp_path: Path, results: list[SpeedTestResult], exporter: CsvExporter | JsonExporter
) -> None:
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x")
    with pytest.raises(ExportError, match="Could not export"):
        exporter.export(results, blocker / "out.file")


def test_failed_write_keeps_old_file_and_removes_temp(
    tmp_path: Path, results: list[SpeedTestResult], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "history.json"
    target.write_text("previous export")

    def broken_replace(*_: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("speed_tracker.infrastructure.exporters.os.replace", broken_replace)
    with pytest.raises(ExportError, match="disk full"):
        JsonExporter().export(results, target)
    assert target.read_text() == "previous export"
    assert list(tmp_path.iterdir()) == [target]
