import asyncio
import time
from collections import OrderedDict
from typing import Any


class TTLCache:
    """TTL cache with LRU eviction.

    Entries expire after ttl_seconds. When the
    cache is full, the least recently used
    entry is dropped first.
    """

    def __init__(
        self,
        ttl_seconds: int,
        max_items: int,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items

        self._data: OrderedDict[
            str,
            tuple[float, Any],
        ] = OrderedDict()

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

            self._data.move_to_end(key)

            return value

    async def set(
        self,
        key: str,
        value: Any,
    ) -> None:

        async with self._lock:
            if key in self._data:
                self._data.move_to_end(key)

            else:
                while (
                    len(self._data)
                    >= self.max_items
                ):
                    self._data.popitem(
                        last=False,
                    )

            expires_at = (
                time.monotonic()
                + self.ttl_seconds
            )

            self._data[key] = (
                expires_at,
                value,
            )

    async def items(self) -> dict[str, Any]:

        async with self._lock:
            now = time.monotonic()

            expired_keys = [
                key
                for key, (expires_at, _) in self._data.items()
                if now >= expires_at
            ]

            for key in expired_keys:
                self._data.pop(key, None)

            return {
                key: value
                for key, (_, value) in self._data.items()
            }

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._data.clear()
