import asyncio
import time
from typing import Any


class TTLCache:
    def __init__(
        self,
        ttl_seconds: int,
        max_items: int,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items

        self._data: dict[
            str,
            tuple[float, Any],
        ] = {}

        self._lock = asyncio.Lock()

    async def get(
        self,
        key: str,
    ) -> Any | None:

        async with self._lock:
            item = self._data.get(key)

            if item is None:
                return None

            expires_at, value = item

            if time.monotonic() >= expires_at:
                self._data.pop(key, None)
                return None

            return value

    async def set(
        self,
        key: str,
        value: Any,
    ) -> None:

        async with self._lock:
            if key not in self._data:

                while (
                    len(self._data)
                    >= self.max_items
                ):
                    oldest_key = next(
                        iter(self._data)
                    )

                    self._data.pop(
                        oldest_key,
                        None,
                    )

            expires_at = (
                time.monotonic()
                + self.ttl_seconds
            )

            self._data[key] = (
                expires_at,
                value,
            )

    async def clear(self) -> None:
        async with self._lock:
            self._data.clear()
