import hmac
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse

from app.config import settings
from app.schemas.profile import (
    SessionStatusResponse,
)
from app.services import linkedin_oauth
from app.services.session_store import (
    session_store,
)
from app.services.token_store import (
    is_token_valid,
    token_store,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)

SESSION_COOKIE = "session_id"
STATE_COOKIE = "linkedin_oauth_state"

STATE_MAX_AGE_SECONDS = 600


def _set_cookie(
    response: Response,
    key: str,
    value: str,
    max_age: int,
) -> None:

    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.cookies_secure,
        # Lax is required so the cookie
        # survives LinkedIn's top-level
        # redirect back to the callback.
        samesite="lax",
        path="/",
    )


def _clear_cookie(
    response: Response,
    key: str,
) -> None:

    response.delete_cookie(
        key=key,
        httponly=True,
        secure=settings.cookies_secure,
        samesite="lax",
        path="/",
    )


@router.get(
    "/linkedin/login",
    summary="Start LinkedIn OAuth sign-in",
    description=(
        "Optional. Returns 503 unless "
        "LINKEDIN_CLIENT_ID and "
        "LINKEDIN_CLIENT_SECRET are configured. "
        "Profile lookups by URL do not need this."
    ),
)
async def linkedin_login():

    if not settings.linkedin_oauth_configured:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "LinkedIn sign-in is "
                "not configured"
            ),
        )

    state = linkedin_oauth.generate_state()

    response = RedirectResponse(
        url=(
            linkedin_oauth
            .build_authorization_url(state)
        ),
        status_code=(
            status.HTTP_307_TEMPORARY_REDIRECT
        ),
    )

    _set_cookie(
        response,
        STATE_COOKIE,
        state,
        STATE_MAX_AGE_SECONDS,
    )

    return response


@router.get("/linkedin/callback")
async def linkedin_callback(
    request: Request,
    code: str | None = Query(
        default=None,
        max_length=2048,
    ),
    state: str | None = Query(
        default=None,
        max_length=512,
    ),
    error: str | None = Query(
        default=None,
        max_length=256,
    ),
):

    # Fixed destination from configuration.
    # Never derived from request input.
    failure_redirect = RedirectResponse(
        url=(
            f"{settings.frontend_url}"
            "/?auth=failed"
        ),
        status_code=(
            status.HTTP_307_TEMPORARY_REDIRECT
        ),
    )

    _clear_cookie(
        failure_redirect,
        STATE_COOKIE,
    )

    if error or not code or not state:
        logger.warning(
            "LinkedIn callback rejected: "
            "missing code or state, "
            "or member denied consent"
        )
        return failure_redirect

    expected_state = request.cookies.get(
        STATE_COOKIE
    )

    if not expected_state or not hmac.compare_digest(
        expected_state,
        state,
    ):
        logger.warning(
            "LinkedIn callback rejected: "
            "state mismatch"
        )
        return failure_redirect

    try:
        token_payload = await (
            linkedin_oauth
            .exchange_code_for_token(code)
        )

        access_token = token_payload[
            "access_token"
        ]

        userinfo = await (
            linkedin_oauth.fetch_userinfo(
                access_token
            )
        )

    except linkedin_oauth.LinkedInOAuthError:
        logger.exception(
            "LinkedIn OAuth exchange failed"
        )
        return failure_redirect

    except Exception:
        logger.exception(
            "Unexpected failure during "
            "LinkedIn OAuth exchange"
        )
        return failure_redirect

    await token_store.save(token_payload)

    session_id = await session_store.create(
        {
            "access_token": access_token,
            "userinfo": userinfo,
        }
    )

    response = RedirectResponse(
        url=(
            f"{settings.frontend_url}"
            "/?auth=success"
        ),
        status_code=(
            status.HTTP_307_TEMPORARY_REDIRECT
        ),
    )

    _set_cookie(
        response,
        SESSION_COOKIE,
        session_id,
        settings.session_ttl_seconds,
    )

    _clear_cookie(response, STATE_COOKIE)

    return response


@router.get(
    "/session",
    response_model=SessionStatusResponse,
)
async def read_session(request: Request):

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    session = (
        await session_store.get(session_id)
        if session_id
        else None
    )

    token_valid = is_token_valid(
        await token_store.load()
    )

    if session is None:

        return SessionStatusResponse(
            authenticated=False,
            oauth_configured=(
                settings.linkedin_oauth_configured
            ),
            token_valid=token_valid,
        )

    userinfo = session.get("userinfo") or {}

    return SessionStatusResponse(
        authenticated=True,
        oauth_configured=(
            settings.linkedin_oauth_configured
        ),
        token_valid=token_valid,
        name=userinfo.get("name"),
    )


@router.post("/logout")
async def logout(request: Request):

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    if session_id:
        await session_store.delete(session_id)

    await token_store.clear()

    response = Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        ),
    )

    _clear_cookie(response, SESSION_COOKIE)

    return response
