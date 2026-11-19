"""User-specific locations for the SQLite database and future logs."""

import os
import sys
from pathlib import Path

APPLICATION_FOLDER = "SpeedTracker"
DATABASE_FILENAME = "speed_tracker.db"


def get_data_directory() -> Path:
    """Use %LOCALAPPDATA% on Windows and a standard local path elsewhere."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return base / APPLICATION_FOLDER

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / APPLICATION_FOLDER


def get_database_path() -> Path:
    """Path only: the folder/database is created by initialize_database()."""
    return get_data_directory() / DATABASE_FILENAME


def get_log_directory() -> Path:
    """Reserved for later logging support."""
    return get_data_directory() / "logs"
