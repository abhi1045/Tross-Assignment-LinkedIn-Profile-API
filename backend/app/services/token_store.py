import asyncio
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Treat a token as stale slightly early so a
# request cannot start with a valid token and
# finish with an expired one.
EXPIRY_SKEW_SECONDS = 60

_FILE_MODE = 0o600
_DIR_MODE = 0o700


class TokenStore:
    """Stores the LinkedIn token server-side.

    Written with owner-only permissions and
    never returned to the browser. Persistence
    can be disabled entirely, in which case the
    token lives only in memory.
    """

    def __init__(
        self,
        path: Path,
        persist: bool,
    ):
        self._path = path
        self._persist = persist
        self._token: dict[str, Any] | None = None
        self._lock = asyncio.Lock()

    async def load(self) -> dict[str, Any] | None:

        async with self._lock:

            if self._token is not None:
                return self._token

            if not self._persist:
                return None

            if not self._path.exists():
                return None

            try:
                raw = self._path.read_text(
                    encoding="utf-8"
                )
                data = json.loads(raw)

            except (OSError, ValueError):
                logger.warning(
                    "Stored LinkedIn token could "
                    "not be read; ignoring it"
                )
                return None

            if not isinstance(data, dict):
                return None

            self._token = data

            return self._token

    async def save(
        self,
        payload: dict[str, Any],
    ) -> None:

        expires_in = payload.get("expires_in")

        record = {
            "access_token": payload.get(
                "access_token"
            ),
            "refresh_token": payload.get(
                "refresh_token"
            ),
            "expires_at": (
                time.time() + float(expires_in)
                if isinstance(
                    expires_in, (int, float)
                )
                else None
            ),
        }

        async with self._lock:
            self._token = record

            if not self._persist:
                return

            self._write_atomically(record)

    async def clear(self) -> None:

        async with self._lock:
            self._token = None

            if not self._persist:
                return

            try:
                self._path.unlink(missing_ok=True)
            except OSError:
                logger.warning(
                    "Stored LinkedIn token could "
                    "not be removed"
                )

    def _write_atomically(
        self,
        record: dict[str, Any],
    ) -> None:

        try:
            self._path.parent.mkdir(
                parents=True,
                exist_ok=True,
                mode=_DIR_MODE,
            )

            # mkstemp gives an exclusive fd, so
            # the file cannot be pre-created or
            # symlinked by another user.
            handle, temp_path = tempfile.mkstemp(
                dir=str(self._path.parent),
                prefix=".token-",
            )

            try:
                os.fchmod(handle, _FILE_MODE)
                os.write(
                    handle,
                    json.dumps(record).encode(
                        "utf-8"
                    ),
                )
            finally:
                os.close(handle)

            os.replace(temp_path, self._path)

        except OSError:
            logger.warning(
                "Stored LinkedIn token could "
                "not be written"
            )


def is_token_valid(
    token: dict[str, Any] | None,
) -> bool:

    if not token or not token.get("access_token"):
        return False

    expires_at = token.get("expires_at")

    if expires_at is None:
        # No expiry recorded. Treat as usable and
        # let the first API call decide.
        return True

    return (
        float(expires_at)
        > time.time() + EXPIRY_SKEW_SECONDS
    )


token_store = TokenStore(
    path=Path(settings.token_store_path),
    persist=settings.token_persistence_enabled,
)
