# Changelog

## 0.2.0 — US03.2, US03.3, US04.1, US04.2

### Database (US03.2)
- Schema versioning through `PRAGMA user_version` with in-place, re-runnable
  migrations; 0.1.0 databases are upgraded without losing data.
- New nullable `server_name` column.
- Repository: `list_between(start, end)`, `delete(id)`, `count()`.
- Databases from a newer app version are refused with a clear message.

### Speed test engine, statistics, export (US03.3)
- `SpeedtestCliProvider` performs real measurements via speedtest-cli, reports
  progress, converts bit/s to Mbps and records the server.
- `SpeedTestRunner` measures and saves; failed measurements save nothing.
- `calculate_statistics` computes min/max/mean/median/sample stdev per metric.
- `CsvExporter` (UTF-8 BOM) and `JsonExporter` (with statistics), atomic writes.
- CLI commands `run`, `stats [--days N]`, `export {csv,json} OUTPUT [--days N]`
  and a global `--db PATH` option.
- Error hierarchy in `core/errors.py`; `DatabaseError` now derives from
  `SpeedTrackerError`.

### Tests (US04.1)
- 72 tests: unit tests with fakes (models, statistics, runner, provider, paths)
  and integration tests on real files (database, migrations, exporters, full
  CLI pipeline). Backend coverage 96 %; no test uses the network.

### Cleanup (US04.2)
- `pytest-qt` moved from `dev` to a new `ui-test` extra: without a Qt binding it
  prevented the whole test suite from starting.
- mypy now also checks `__main__.py`; ruff isort treats `tests` as first-party.
- `run_checks.bat` enforces 90 % backend coverage.
- Added `.gitignore`; removed outdated "no Git" / skeleton notes from the docs.
- Models reject non-numeric values (e.g. strings, booleans) explicitly.

## 0.1.0 — US03.1 / US03.2

- Added the layered Python 3.12 `src/` skeleton.
- Added typed core result models and repository/provider/export contracts.
- Implemented SQLite initialization, schema, insertion, read by ID and history.
- Added per-user data directories and friendly DB errors.
- Created placeholders for speed measurement, statistics, exports, UI and packaging.
- Added CLI, local example script and DB-focused tests.
