"""Application error hierarchy shared by all layers.

Every error raised on purpose by Speed Tracker derives from ``SpeedTrackerError``,
so the CLI and (later) the UI can catch one type and show a friendly message.
"""


class SpeedTrackerError(Exception):
    """Base class for expected, user-presentable failures."""


class SpeedTestError(SpeedTrackerError):
    """A speed measurement could not be completed (no network, server error...)."""


class ExportError(SpeedTrackerError):
    """Results could not be written to the requested export file."""
