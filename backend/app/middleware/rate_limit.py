import json
from collections.abc import Awaitable, Callable

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.utils.rate_limit import (
    SlidingWindowRateLimiter,
)

limiter = SlidingWindowRateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=(
        settings.rate_limit_window_seconds
    ),
)

_PROFILE_PATH = "/api/v1/profile"


def _client_key(request: Request) -> str:
    client = request.client
    if client is not None and client.host:
        return client.host
    return "unknown"


async def _request_id(request: Request) -> str:
    profile_url = request.query_params.get(
        "profile_url"
    )

    if (
        not profile_url
        and request.method == "POST"
        and request.url.path.rstrip("/")
        == _PROFILE_PATH
    ):
        body = await request.body()
        if body:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                value = payload.get("profile_url")
                if isinstance(value, str):
                    profile_url = value

    if isinstance(profile_url, str) and profile_url:
        return profile_url.rstrip("/").lower()

    return (
        f"{request.method}:"
        f"{request.url.path}:"
        f"{request.url.query}"
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit unique profile lookups per IP.

    Default is RATE_LIMIT_REQUESTS unique
    profile URLs per RATE_LIMIT_WINDOW_SECONDS.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:

        if not settings.rate_limit_enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.rstrip("/")

        if path != _PROFILE_PATH:
            return await call_next(request)

        request_id = await _request_id(request)

        allowed, remaining, retry_after = (
            await limiter.check(
                _client_key(request),
                request_id,
            )
        )

        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many unique profile "
                        "requests. Please try again "
                        "later"
                    )
                },
            )
            response.headers["Retry-After"] = str(
                retry_after
            )
            response.headers["X-RateLimit-Limit"] = (
                str(settings.rate_limit_requests)
            )
            response.headers["X-RateLimit-Remaining"] = (
                "0"
            )
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(
            settings.rate_limit_requests
        )
        response.headers["X-RateLimit-Remaining"] = str(
            remaining
        )
        return response
