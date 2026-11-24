"""speedtest-cli adapter, driven by a fake client (no network)."""

import sys
from types import SimpleNamespace
from typing import Any

import pytest

from speed_tracker.core.errors import SpeedTestError
from speed_tracker.infrastructure.speedtest_provider import SpeedtestCliProvider

SERVER = {"sponsor": "Vivacom", "name": "Sofia", "country": "Bulgaria"}


class FakeClient:
    def __init__(
        self,
        download: float = 95_500_000.0,
        upload: float = 38_200_000.0,
        ping: float = 12.8,
        server: Any = SERVER,
        fail_on: str | None = None,
    ) -> None:
        self._download = download
        self._upload = upload
        self._server = server
        self._fail_on = fail_on
        self.results = SimpleNamespace(ping=ping)
        self.upload_kwargs: dict[str, Any] = {}

    def _maybe_fail(self, step: str) -> None:
        if self._fail_on == step:
            raise OSError(f"{step} connection reset")

    def get_best_server(self) -> Any:
        self._maybe_fail("server")
        return self._server

    def download(self) -> float:
        self._maybe_fail("download")
        return self._download

    def upload(self, **kwargs: Any) -> float:
        self._maybe_fail("upload")
        self.upload_kwargs = kwargs
        return self._upload


def test_converts_bits_to_megabits_and_reports_progress() -> None:
    client = FakeClient()
    messages: list[str] = []
    result = SpeedtestCliProvider(lambda: client).run_test(messages.append)

    assert result.download_mbps == pytest.approx(95.5)
    assert result.upload_mbps == pytest.approx(38.2)
    assert result.ping_ms == 12.8
    assert result.server_name == "Vivacom - Sofia, Bulgaria"
    assert result.id is None
    assert result.measured_at.tzinfo is not None
    assert client.upload_kwargs == {"pre_allocate": False}
    assert messages[0] == "Connecting to speedtest.net"
    assert messages[-1] == "Speed test complete"
    assert "Measuring download speed" in messages


@pytest.mark.parametrize(
    ("server", "expected"),
    [
        ({"sponsor": "ISP"}, "ISP"),
        ({"name": "Plovdiv", "country": "Bulgaria"}, "Plovdiv, Bulgaria"),
        ({}, None),
        (None, None),
    ],
)
def test_server_description_is_defensive(server: Any, expected: str | None) -> None:
    result = SpeedtestCliProvider(lambda: FakeClient(server=server)).run_test()
    assert result.server_name == expected


@pytest.mark.parametrize("step", ["server", "download", "upload"])
def test_library_errors_become_speed_test_errors(step: str) -> None:
    provider = SpeedtestCliProvider(lambda: FakeClient(fail_on=step))
    with pytest.raises(SpeedTestError, match=f"{step} connection reset"):
        provider.run_test()


def test_client_construction_failure_is_wrapped() -> None:
    def factory() -> Any:
        raise RuntimeError("config retrieval failed")

    with pytest.raises(SpeedTestError, match="config retrieval failed"):
        SpeedtestCliProvider(factory).run_test()


def test_zero_throughput_is_an_error() -> None:
    provider = SpeedtestCliProvider(lambda: FakeClient(download=0.0))
    with pytest.raises(SpeedTestError, match="no measurement data"):
        provider.run_test()


def test_invalid_ping_is_an_error() -> None:
    provider = SpeedtestCliProvider(lambda: FakeClient(ping=float("nan")))
    with pytest.raises(SpeedTestError, match="invalid values"):
        provider.run_test()


def test_missing_library_gives_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    # A None entry in sys.modules makes any import of that name raise ImportError.
    monkeypatch.setitem(sys.modules, "speedtest", None)
    with pytest.raises(SpeedTestError, match="not installed"):
        SpeedtestCliProvider().run_test()
