@echo off
setlocal
cd /d "%~dp0\.."
python -m ruff check src tests scripts || exit /b 1
python -m ruff format --check src tests scripts || exit /b 1
python -m mypy src\speed_tracker\core src\speed_tracker\infrastructure src\speed_tracker\__main__.py || exit /b 1
python -m pytest --cov=speed_tracker.core --cov=speed_tracker.infrastructure --cov=speed_tracker.__main__ --cov-report=term-missing --cov-fail-under=90 tests || exit /b 1
echo All backend checks passed.
