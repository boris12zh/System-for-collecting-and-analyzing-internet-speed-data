@echo off
setlocal
cd /d "%~dp0\.."
python -m ruff check src tests scripts || exit /b 1
python -m ruff format --check src tests scripts || exit /b 1
python -m mypy src\speed_tracker\core src\speed_tracker\infrastructure || exit /b 1
python -m pytest --cov=speed_tracker --cov-report=term-missing tests || exit /b 1
echo All current skeleton checks passed.
