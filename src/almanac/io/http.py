"""A polite range-request client: connection reuse, a hard concurrency cap, bounded retries."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import httpx

MAX_CONNECTIONS = 16  # blueprint section 7.5


@dataclass(frozen=True)
class RangeResponse:
    data: bytes
    etag: str
    last_modified: str
    total_size: int


@dataclass
class TransferStats:
    requests: int = 0
    bytes: int = 0
    retries: int = 0
    peak_in_flight: int = 0
    _in_flight: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def begin(self) -> None:
        with self._lock:
            self._in_flight += 1
            self.peak_in_flight = max(self.peak_in_flight, self._in_flight)

    def end(self, n_bytes: int, retries: int) -> None:
        with self._lock:
            self._in_flight -= 1
            self.requests += 1
            self.bytes += n_bytes
            self.retries += retries


class RangeClient:
    """Thread-safe byte-range reads from one supplier.

    At most ``connections`` requests are in flight at any time, whatever the number of threads.
    Server errors and timeouts are retried with exponential back-off; client errors are not.
    """

    def __init__(self, connections: int = 8, timeout_s: float = 60.0, max_retries: int = 5) -> None:
        if not 1 <= connections <= MAX_CONNECTIONS:
            raise ValueError(f"connections must be 1..{MAX_CONNECTIONS}")
        self.connections = connections
        self.max_retries = max_retries
        self.stats = TransferStats()
        self._gate = threading.BoundedSemaphore(connections)
        self._client = httpx.Client(
            http2=False,  # the HTTP/2 path is not safe under threads (protocol errors in the first run)
            timeout=timeout_s,
            limits=httpx.Limits(max_connections=connections, max_keepalive_connections=connections),
            headers={"User-Agent": "almanac-research-client"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> RangeClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get_range(self, url: str, start: int, end_exclusive: int) -> RangeResponse:
        """Bytes ``[start, end_exclusive)`` of the object at ``url``."""
        if not 0 <= start < end_exclusive:
            raise ValueError(f"bad range {start}-{end_exclusive} for {url}")
        headers = {"Range": f"bytes={start}-{end_exclusive - 1}"}
        last: Exception | None = None
        with self._gate:
            self.stats.begin()
            got, attempt = 0, 0
            try:
                for attempt in range(self.max_retries + 1):
                    try:
                        resp = self._client.get(url, headers=headers)
                        if resp.status_code in (200, 206):
                            got = len(resp.content)
                            return _response(resp)
                        if resp.status_code < 500 and resp.status_code != 429:
                            raise httpx.HTTPStatusError(
                                f"HTTP {resp.status_code} for {url}", request=resp.request, response=resp
                            )
                        last = httpx.HTTPStatusError(
                            f"HTTP {resp.status_code} for {url}", request=resp.request, response=resp
                        )
                    except httpx.HTTPStatusError:
                        raise
                    except Exception as exc:  # transport, timeout and protocol errors are all retried
                        last = exc
                    time.sleep(min(60.0, 2.0**attempt))
                raise RuntimeError(f"gave up after {self.max_retries + 1} attempts: {url}") from last
            finally:
                self.stats.end(got, attempt)


def _response(resp: httpx.Response) -> RangeResponse:
    content_range = resp.headers.get("Content-Range", "")
    total = int(content_range.rsplit("/", 1)[1]) if "/" in content_range else len(resp.content)
    return RangeResponse(
        data=resp.content,
        etag=resp.headers.get("ETag", "").strip('"'),
        last_modified=resp.headers.get("Last-Modified", ""),
        total_size=total,
    )
