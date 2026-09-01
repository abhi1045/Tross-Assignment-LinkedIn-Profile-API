import secrets
from typing import Any

from app.config import settings
from app.utils.cache import TTLCache


class SessionStore:
    """In-process session storage.

    Access tokens stay server-side and are
    never sent to the browser. Sessions are
    lost on restart and are not shared across
    workers.
    """

    def __init__(
        self,
        ttl_seconds: int,
        max_items: int,
    ):
        self._cache = TTLCache(
            ttl_seconds=ttl_seconds,
            max_items=max_items,
        )

    async def create(
        self,
        data: dict[str, Any],
    ) -> str:

        session_id = secrets.token_urlsafe(32)

        await self._cache.set(
            session_id,
            data,
        )

        return session_id

    async def get(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:

        return await self._cache.get(
            session_id
        )

    async def delete(
        self,
        session_id: str,
    ) -> None:

        await self._cache.delete(session_id)


session_store = SessionStore(
    ttl_seconds=settings.session_ttl_seconds,
    max_items=settings.session_max_items,
)
