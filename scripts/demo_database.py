"""Save a deliberately fake example and read it back. No speed test occurs."""

from speed_tracker.core.models import SpeedTestResult
from speed_tracker.infrastructure.repository import SQLiteResultRepository


def main() -> None:
    repository = SQLiteResultRepository()
    example = SpeedTestResult(download_mbps=95.5, upload_mbps=38.2, ping_ms=12.8)
    saved = repository.save(example)
    print(f"SAMPLE (not measured) result stored under ID {saved.id}")
    print(f"History currently contains {len(repository.list_all())} record(s).")


if __name__ == "__main__":
    main()
