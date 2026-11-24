# Speed Tracker — collect and analyze internet speed data

A Python 3.12+ application that measures your internet connection (download,
upload, ping) with speedtest.net, stores every measurement in a local SQLite
database, computes statistics, and exports history to CSV or JSON.

## Status

| Story | Scope | State |
|---|---|---|
| US03.1 | Python skeleton | done |
| US03.2 | SQLite database, schema versioning and migrations | done |
| US03.3 | Speed test engine, statistics, CSV/JSON export | done |
| US04.1 | Backend unit and integration tests | done |
| US04.2 | Backend bug fixing and code cleanup | done |
| US05 / US06 | PySide6 window, history table, UI tests | planned — `ui/` is still a placeholder |
| US07 | Installer / executable | planned — `packaging/` holds placeholders |

The backend is usable today through the command-line interface below.

## Setup

From the project folder:

```console
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[measurement,dev]"
```

On Linux/macOS use `source .venv/bin/activate`. Extras:

| Extra | Contents | Needed for |
|---|---|---|
| `measurement` | speedtest-cli | the `run` command (real measurements) |
| `dev` | pytest, pytest-cov, ruff, mypy | backend checks |
| `ui` | PySide6 | the window (US05) |
| `ui-test` | pytest-qt | UI tests (US06); requires a Qt binding |
| `build` | PyInstaller | packaging (US07) |

> `pytest-qt` refuses to load without a Qt binding, so it lives in `ui-test`,
> not `dev`. Note that the pinned `PySide6==6.8.3` has no wheels for Python 3.14;
> use Python 3.12/3.13 for UI work or update the pin in US05.

## Command-line usage

```console
python -m speed_tracker run                      # measure once and save
python -m speed_tracker list                     # history, newest first
python -m speed_tracker stats                    # min/max/mean/median/stdev
python -m speed_tracker stats --days 7           # ...for the last 7 days only
python -m speed_tracker export csv history.csv   # one row per measurement
python -m speed_tracker export json history.json --days 30   # results + statistics
python -m speed_tracker init-db                  # create/upgrade the database
python -m speed_tracker --db other.db list       # use a different database file
```

Without a command, `python -m speed_tracker` opens the (placeholder) window.
Failures such as no internet connection, an unwritable export path or a damaged
database are reported as one-line `Error: ...` messages with exit code 1.

The database lives in `%LOCALAPPDATA%\SpeedTracker\speed_tracker.db` on Windows
and `$XDG_DATA_HOME/SpeedTracker/` (default `~/.local/share/SpeedTracker/`) elsewhere.

## Checks

```console
python -m pytest
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m mypy src/speed_tracker/core src/speed_tracker/infrastructure src/speed_tracker/__main__.py
```

On Windows `scripts\run_checks.bat` runs all of them and requires at least 90 %
coverage of the backend (`core`, `infrastructure`, `__main__`). Tests never use
the network: the speed test provider is replaced by fakes.

| Folder | What is tested |
|---|---|
| `tests/unit/` | models, statistics, runner, speedtest-cli adapter (fake client), paths |
| `tests/integration/` | real SQLite files (schema, migrations, queries, errors), real export files, full CLI pipeline run → list → stats → export |
| `tests/ui/`, `tests/smoke/` | reserved for US06 / US07 |

## Architecture

```text
src/speed_tracker/
├── __main__.py            # composition root + CLI
├── core/                  # pure Python: no SQLite, network, files or Qt
│   ├── models.py          # SpeedTestResult, MetricSummary, StatisticsSummary
│   ├── interfaces.py      # SpeedTestProvider / ResultRepository / ResultExporter protocols
│   ├── statistics.py      # calculate_statistics()
│   ├── test_runner.py     # SpeedTestRunner: measure, then save
│   └── errors.py          # SpeedTrackerError, SpeedTestError, ExportError
├── infrastructure/        # adapters to the outside world
│   ├── database.py        # connections, schema, migrations, DatabaseError
│   ├── repository.py      # SQLiteResultRepository
│   ├── speedtest_provider.py  # SpeedtestCliProvider (speedtest-cli)
│   ├── exporters.py       # CsvExporter, JsonExporter (atomic writes)
│   └── paths.py           # per-user data folder
└── ui/                    # PySide6 placeholders (US05)
```

All expected failures derive from `SpeedTrackerError`, so a caller (CLI now,
UI later) can catch a single exception type and show its message.

## Database schema

Table `speed_tests` (schema version 2, stored in `PRAGMA user_version`):

| Column | SQLite type | Purpose |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Assigned on insert |
| `measured_at` | TEXT NOT NULL | UTC ISO 8601 timestamp (text order = time order) |
| `download_mbps` | REAL NOT NULL, ≥ 0 | Download speed in Mbps |
| `upload_mbps` | REAL NOT NULL, ≥ 0 | Upload speed in Mbps |
| `ping_ms` | REAL NOT NULL, ≥ 0 | Latency in ms |
| `server_name` | TEXT NULL | Test server, e.g. `ISP - Sofia, Bulgaria` (added in v2) |

An index on `(measured_at DESC, id DESC)` serves history and date-range queries.
Databases created by 0.1.0 are upgraded automatically and keep their data; a
database from a newer application version is refused instead of being damaged.

## Export formats

- **CSV** — UTF-8 with BOM (opens correctly in Excel, including Cyrillic),
  columns `id, measured_at, download_mbps, upload_mbps, ping_ms, server_name`.
  Contains results only.
- **JSON** — `{format_version, exported_at, count, results: [...], summary}` where
  `summary` holds min/max/mean/median/standard deviation per metric (or `null`
  when there are no results).

Both are written to a temporary file and then moved into place, so a failed
export never leaves a half-written file.
