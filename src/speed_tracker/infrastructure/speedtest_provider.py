"""speedtest-cli adapter that performs real measurements (US03.3).

``speedtest-cli`` is an optional dependency (``pip install -e ".[measurement]"``)
and is imported lazily, so the rest of the application works without it.
The client factory is injectable so tests never touch the network.
"""

import importlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from speed_tracker.core.errors import SpeedTestError
from speed_tracker.core.interfaces import ProgressCallback
from speed_tracker.core.models import SpeedTestResult

BITS_PER_MEGABIT = 1_000_000

ClientFactory = Callable[[], Any]


def _default_client_factory() -> Any:
    try:
        speedtest = importlib.import_module("speedtest")
    except ImportError as exc:
        raise SpeedTestError(
            'speedtest-cli is not installed. Run: pip install -e ".[measurement]"'
        ) from exc
    return speedtest.Speedtest(secure=True)


def _describe_server(server: Any) -> str | None:
    if not isinstance(server, dict):
        return None
    sponsor = str(server.get("sponsor", "")).strip()
    location = ", ".join(
        part for part in (str(server.get(key, "")).strip() for key in ("name", "country")) if part
    )
    text = " - ".join(part for part in (sponsor, location) if part)
    return text or None


class SpeedtestCliProvider:
    """Measure ping, download and upload against the nearest Speedtest.net server."""

    def __init__(self, client_factory: ClientFactory | None = None) -> None:
        self._client_factory = client_factory or _default_client_factory

    def run_test(self, on_progress: ProgressCallback | None = None) -> SpeedTestResult:
        def report(message: str) -> None:
            if on_progress is not None:
                on_progress(message)

        try:
            report("Connecting to speedtest.net")
            client = self._client_factory()
            report("Selecting best server and measuring ping")
            server = client.get_best_server()
            report("Measuring download speed")
            download_bps = float(client.download())
            report("Measuring upload speed")
            upload_bps = float(client.upload(pre_allocate=False))
            ping_ms = float(client.results.ping)
        except SpeedTestError:
            raise
        except Exception as exc:  # Network/library failures of any kind end the test.
            raise SpeedTestError(f"Speed test failed: {exc or type(exc).__name__}") from exc

        if download_bps <= 0 or upload_bps <= 0:
            raise SpeedTestError("Speed test failed: the server returned no measurement data")
        try:
            result = SpeedTestResult(
                download_mbps=download_bps / BITS_PER_MEGABIT,
                upload_mbps=upload_bps / BITS_PER_MEGABIT,
                ping_ms=ping_ms,
                measured_at=datetime.now(UTC),
                server_name=_describe_server(server),
            )
        except ValueError as exc:
            raise SpeedTestError(f"Speed test returned invalid values: {exc}") from exc
        report("Speed test complete")
        return result
