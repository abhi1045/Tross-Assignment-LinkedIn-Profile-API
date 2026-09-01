import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.routes import router
from app.config import settings
from app.middleware.rate_limit import (
    RateLimitMiddleware,
)
from app.middleware.security import (
    SecurityHeadersMiddleware,
)
from app.services import linkedin_oauth
from app.services.token_store import (
    is_token_valid,
    token_store,
)

logger = logging.getLogger(__name__)


async def _restore_linkedin_token() -> bool:
    """Load a stored token and confirm it works.

    Attempts a refresh when the stored token has
    expired. Returns whether the application has
    a usable token.
    """

    if not settings.linkedin_oauth_configured:
        logger.info(
            "LinkedIn OAuth is not configured; "
            "sign-in is unavailable"
        )
        return False

    token = await token_store.load()

    if token is None:
        logger.info(
            "No stored LinkedIn token; sign-in "
            "is required"
        )
        return False

    if is_token_valid(token):
        logger.info(
            "Restored a valid LinkedIn token"
        )
        return True

    refresh_token = token.get("refresh_token")

    if not refresh_token:
        logger.info(
            "Stored LinkedIn token expired and "
            "no refresh token is available; "
            "sign-in is required"
        )
        await token_store.clear()
        return False

    try:
        payload = await (
            linkedin_oauth.refresh_access_token(
                refresh_token
            )
        )

    except (
        linkedin_oauth.LinkedInOAuthError,
        httpx.HTTPError,
    ):
        logger.warning(
            "LinkedIn token refresh failed; "
            "sign-in is required"
        )
        await token_store.clear()
        return False

    await token_store.save(payload)

    logger.info("Refreshed the LinkedIn token")

    return True


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.linkedin_ready = (
        await _restore_linkedin_token()
    )

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Accepts a LinkedIn profile URL and returns "
        "structured JSON. Profile data is read "
        "directly from LinkedIn's Voyager HTTPS "
        "endpoints using a member session cookie "
        "(LINKEDIN_LI_AT). No browser automation.\n\n"
        "The `auth` endpoints and `/api/v1/me` are "
        "optional OAuth extras and return 401/503 "
        "when no LinkedIn developer app is "
        "configured."
    ),
    lifespan=lifespan,
)


# Inner middleware. CORS is added last so
# it wraps 429 responses with CORS headers.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Required so the session cookie is sent
    # on cross-origin frontend requests.
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
    expose_headers=[
        "Retry-After",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
    ],
)


app.include_router(auth_router)
app.include_router(router)


@app.get(
    "/health",
    tags=["health"],
)
async def health_check():

    if settings.use_demo_provider:
        provider = "demo"
    elif settings.linkedin_session_configured:
        provider = "voyager"
    elif settings.provider_base_url:
        provider = "http"
    else:
        provider = "unconfigured"

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "provider": provider,
        "linkedin_session_configured": (
            settings.linkedin_session_configured
        ),
    }


static_path = Path(__file__).resolve().parent.parent / (
    "static"
)

if static_path.exists():

    app.mount(
        "/",
        StaticFiles(
            directory=str(static_path),
            html=True,
        ),
        name="frontend",
    )
