import asyncio
import time


class SlidingWindowRateLimiter:
    """Count unique requests in a sliding window.

    Each distinct request fingerprint is stored
    once per window. Repeating the same
    fingerprint (same client + same profile)
    does not consume another slot.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        max_keys: int = 10_000,
    ):
        if max_requests < 1:
            raise ValueError(
                "max_requests must be at least 1"
            )

        if window_seconds < 1:
            raise ValueError(
                "window_seconds must be at least 1"
            )

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys

        self._windows: dict[
            str,
            dict[str, float],
        ] = {}
        self._lock = asyncio.Lock()

    async def check(
        self,
        client_key: str,
        request_id: str,
    ) -> tuple[bool, int, int]:
        """Return (allowed, remaining, retry_after)."""

        now = time.monotonic()
        window_start = now - self.window_seconds

        async with self._lock:
            seen = self._windows.get(client_key, {})

            seen = {
                fingerprint: stamp
                for fingerprint, stamp in seen.items()
                if stamp > window_start
            }

            if request_id in seen:
                self._windows[client_key] = seen
                remaining = max(
                    0,
                    self.max_requests - len(seen),
                )
                return True, remaining, 0

            if len(seen) >= self.max_requests:
                oldest = min(seen.values())
                retry_after = max(
                    1,
                    int(
                        oldest
                        + self.window_seconds
                        - now
                    )
                    + 1,
                )
                self._windows[client_key] = seen
                return False, 0, retry_after

            if (
                client_key not in self._windows
                and len(self._windows) >= self.max_keys
            ):
                self._evict_oldest()

            seen[request_id] = now
            self._windows[client_key] = seen

            remaining = (
                self.max_requests - len(seen)
            )

            return True, remaining, 0

    def _evict_oldest(self) -> None:
        oldest_key = next(iter(self._windows), None)
        if oldest_key is not None:
            self._windows.pop(oldest_key, None)
