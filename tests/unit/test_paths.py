"""Per-user data locations."""

from pathlib import Path

import pytest

from speed_tracker.infrastructure import paths


def test_windows_uses_localappdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert paths.get_data_directory() == tmp_path / "SpeedTracker"
    assert paths.get_database_path() == tmp_path / "SpeedTracker" / "speed_tracker.db"
    assert paths.get_log_directory() == tmp_path / "SpeedTracker" / "logs"


def test_windows_without_localappdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path)
    assert paths.get_data_directory() == tmp_path / "AppData" / "Local" / "SpeedTracker"


def test_linux_uses_xdg_data_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert paths.get_data_directory() == tmp_path / "SpeedTracker"


def test_linux_default_location(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path)
    assert paths.get_data_directory() == tmp_path / ".local" / "share" / "SpeedTracker"
