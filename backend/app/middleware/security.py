from collections.abc import Awaitable, Callable

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

_CSP = (
    "default-src 'self'; "
    "img-src 'self' https://media.licdn.com "
    "https://*.licdn.com data:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

# Swagger UI and ReDoc load their bundles from
# jsDelivr and bootstrap through an inline
# script tag. Relaxed only on the docs routes.
_DOCS_CSP = (
    "default-src 'self'; "
    "img-src 'self' https://fastapi.tiangolo.com "
    "https://cdn.jsdelivr.net data: blob:; "
    "style-src 'self' 'unsafe-inline' "
    "https://cdn.jsdelivr.net "
    "https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "script-src 'self' 'unsafe-inline' "
    "https://cdn.jsdelivr.net; "
    "worker-src 'self' blob:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

_DOCS_PATHS = {
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = (
            "nosniff"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = (
            "no-referrer"
        )
        response.headers[
            "Permissions-Policy"
        ] = "geolocation=(), microphone=(), camera=()"

        if settings.environment != "development":
            response.headers[
                "Strict-Transport-Security"
            ] = (
                "max-age=31536000; includeSubDomains"
            )

        content_type = response.headers.get(
            "content-type",
            "",
        )

        if "text/html" in content_type:
            is_docs = (
                request.url.path.rstrip("/")
                in _DOCS_PATHS
            )
            response.headers[
                "Content-Security-Policy"
            ] = (_DOCS_CSP if is_docs else _CSP)

        return response
