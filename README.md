# Speed Tracker — Python + SQLite foundation

This is the **US03.1 (Python skeleton)** and **US03.2 (database)** implementation
from the supplied backlog, not a finished speed-test application.

## Implemented now

- Layered structure: `core/` (pure Python contracts/models), `infrastructure/`
  (SQLite and filesystem paths), `ui/` (empty PySide6 scaffold).
- SQLite database and `speed_tests` table created on first use.
- Save a speed test result; list stored results newest-first; retrieve a result by ID.
- Windows data location: `%LOCALAPPDATA%\SpeedTracker\speed_tracker.db`.
- Linux/macOS fallback data location to make development and tests possible.
- Small CLI to initialize DB and show stored results, and a sample-data script.
- Database integration tests using temporary directories.

## Not implemented (later backlog stories)

- **US03.3:** actual speedtest-cli measurement, calculations, CSV/JSON export.
- **US05:** functional UI controls, history panel and worker threads.
- **US07:** production executable/installer (packaging files are placeholders).

No real internet speed test is performed by this skeleton. The sample script saves
explicitly labeled example values only.

## Setup

Use Python **3.12+** from the `speed-tracker/` folder:

```console
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
python -m speed_tracker init-db
python -m speed_tracker list
python scripts/demo_database.py
```

On Linux/macOS use `source .venv/bin/activate` instead. The package install step
is needed because the project uses the `src/` layout. `init-db` and `list` work
without PySide6 or an internet connection.

To open the **placeholder window** on Windows with the optional UI dependency:

```console
python -m pip install -e ".[ui]"
python -m speed_tracker
```

To run test and quality checks:

```console
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m mypy src/speed_tracker/core src/speed_tracker/infrastructure
```

On Windows, `scripts\run_checks.bat` combines the checks. It does not enforce the
backlog's final coverage targets yet because large parts of the application are
intentionally not implemented.

## Project organization

```text
speed-tracker/
├── pyproject.toml
├── README.md / CONTRIBUTING.md / CHANGELOG.md
├── src/speed_tracker/
│   ├── __main__.py
│   ├── core/              # models, interfaces, unfinished statistics and runner
│   ├── infrastructure/    # working paths, SQLite schema and repository;
│   │                      # future provider and exporters
│   └── ui/                # intentionally minimal PySide6 scaffold
├── tests/{unit,integration,ui,smoke}/
├── packaging/            # reserved for US07
├── scripts/              # DB demo and quality/backup/build batch files
└── backups/
```

## Database schema

The `speed_tests` table has these columns:

| Column | SQLite type | Purpose |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Assigned on insert |
| `measured_at` | TEXT NOT NULL | UTC ISO 8601 timestamp |
| `download_mbps` | REAL NOT NULL | Download speed in Mbps |
| `upload_mbps` | REAL NOT NULL | Upload speed in Mbps |
| `ping_ms` | REAL NOT NULL | Network latency in ms |

Nonnegative numerical constraints protect the stored values. The history query is
sorted by timestamp descending, then ID descending. `SQLiteResultRepository`
initializes the database automatically on construction.

## Design notes

- `core/` imports no network, SQLite, file-export, or Qt dependencies.
- `infrastructure/` handles external interactions and translates SQLite failures
  into understandable `DatabaseError` messages.
- `__main__.py` is the composition/entry point. UI classes are not connected to
  backend services until US05.
- There is **no Git repository** in this folder, per US03.1.
