# Development practices (from US02)

- Python 3.12+, PEP 8 naming, type hints and small single-purpose modules.
- Respect layering: `core` cannot import Qt, SQLite, speedtest, CSV or JSON.
- Implement adapters in `infrastructure`; compose dependencies in `__main__.py`.
- Use `ruff`, `mypy`, and `pytest`; add unit/integration/UI tests as stories grow.
- Keep DB writes atomic and present friendly errors on I/O failures.
- Before/after stories, make a local dated backup using `scripts/backup.bat`.
- Update `CHANGELOG.md` with each completed story.

## Definition of done (target for full project)

Checks pass; local backup exists; changelog updated; the UI remains responsive;
the final installed app works. This foundation implements **US03.1 and US03.2
only**; speed test, full test coverage, UI, packaging are later stories.
