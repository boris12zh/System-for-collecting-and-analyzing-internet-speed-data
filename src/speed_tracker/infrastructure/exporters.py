"""CSV and JSON export adapters (US03.3).

Both exporters write to a temporary file next to the destination and then
replace it, so a failed export never leaves a half-written file behind.

* CSV is UTF-8 with a BOM so Excel on Windows shows Cyrillic text correctly.
  It contains one row per result; the statistics summary is not included
  because mixing tables would break CSV tools. Use JSON for the summary.
* JSON contains ``results`` and, when given, a ``summary`` object.
"""

import csv
import json
import os
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any

from speed_tracker.core.errors import ExportError
from speed_tracker.core.models import SpeedTestResult, StatisticsSummary

CSV_COLUMNS = ("id", "measured_at", "download_mbps", "upload_mbps", "ping_ms", "server_name")
JSON_FORMAT_VERSION = 1


def _result_to_dict(result: SpeedTestResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "measured_at": result.measured_at.astimezone(UTC).isoformat(),
        "download_mbps": result.download_mbps,
        "upload_mbps": result.upload_mbps,
        "ping_ms": result.ping_ms,
        "server_name": result.server_name,
    }


def _summary_to_dict(summary: StatisticsSummary) -> dict[str, Any]:
    data = asdict(summary)
    data["first_measured_at"] = summary.first_measured_at.astimezone(UTC).isoformat()
    data["last_measured_at"] = summary.last_measured_at.astimezone(UTC).isoformat()
    return data


def _write_atomically(
    destination: Path, encoding: str, newline: str | None, write: Callable[[IO[str]], None]
) -> Path:
    destination = Path(destination)
    temporary: Path | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        temporary = Path(name)
        with os.fdopen(descriptor, "w", encoding=encoding, newline=newline) as handle:
            write(handle)
        os.replace(temporary, destination)
        temporary = None
    except OSError as exc:
        raise ExportError(f"Could not export to {destination}: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


class CsvExporter:
    def export(
        self,
        results: Sequence[SpeedTestResult],
        destination: Path,
        summary: StatisticsSummary | None = None,
    ) -> Path:
        """Write one CSV row per result; ``summary`` is ignored (see module doc)."""

        def write(handle: IO[str]) -> None:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for result in results:
                writer.writerow(_result_to_dict(result))

        return _write_atomically(destination, "utf-8-sig", "", write)


class JsonExporter:
    def export(
        self,
        results: Sequence[SpeedTestResult],
        destination: Path,
        summary: StatisticsSummary | None = None,
    ) -> Path:
        """Write a JSON document with results and an optional statistics summary."""
        document = {
            "format_version": JSON_FORMAT_VERSION,
            "exported_at": datetime.now(UTC).isoformat(),
            "count": len(results),
            "results": [_result_to_dict(result) for result in results],
            "summary": None if summary is None else _summary_to_dict(summary),
        }

        def write(handle: IO[str]) -> None:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        return _write_atomically(destination, "utf-8", None, write)
