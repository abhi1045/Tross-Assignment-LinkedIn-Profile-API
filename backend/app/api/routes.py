from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    status,
)
from pydantic import ValidationError

from app.api.auth import SESSION_COOKIE
from app.config import settings
from app.schemas.profile import (
    CacheListResponse,
    ProfileMetadata,
    ProfileRequest,
    ProfileResponse,
)
from app.services import linkedin_oauth
from app.services.linkedin_voyager import (
    LinkedInSessionError,
    ProfileNotFoundError,
)
from app.services.profile_service import (
    ProfileService,
)
from app.services.session_store import (
    session_store,
)
from app.services.token_store import (
    is_token_valid,
    token_store,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["profiles"],
)

profile_service = ProfileService()


async def _require_linkedin_ready(
    request: Request,
) -> None:
    """Reject lookups until sign-in completed.

    Mirrors the "application ready" gate: a
    session cookie or a stored token must be
    present before any profile request runs.
    """

    if not settings.require_auth_for_profile:
        return

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    if session_id and await session_store.get(
        session_id
    ):
        return

    if is_token_valid(await token_store.load()):
        return

    raise HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=(
            "Sign in with LinkedIn before "
            "requesting a profile"
        ),
    )


@router.post(
    "/profile",
    response_model=ProfileResponse,
    summary="Look up a LinkedIn profile by URL",
    description=(
        "Fetches the profile over HTTPS from "
        "LinkedIn's Voyager endpoints. Requires "
        "LINKEDIN_LI_AT to be configured, or "
        "USE_DEMO_PROVIDER=true for sample data."
    ),
    responses={
        400: {
            "description": "URL is not a LinkedIn /in/ profile"
        },
        404: {"description": "Profile not found"},
        429: {
            "description": "Unique profile lookup limit reached"
        },
        503: {
            "description": (
                "LinkedIn session missing or expired"
            )
        },
    },
)
async def get_profile(
    request: ProfileRequest,
    http_request: Request,
):

    await _require_linkedin_ready(http_request)

    try:
        return (
            await profile_service.get_profile(
                str(request.profile_url)
            )
        )

    except ProfileNotFoundError as error:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile information is unavailable",
        ) from error

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    except (
        LinkedInSessionError,
        RuntimeError,
    ) as error:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Profile service "
                "temporarily unavailable"
            ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to retrieve "
                "profile information"
            ),
        ) from error


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Look up a LinkedIn profile by URL",
    description=(
        "Query-string form of POST /profile, for "
        "quick checks from a browser or curl."
    ),
)
async def get_profile_by_query(
    http_request: Request,
    profile_url: str = Query(
        ...,
        min_length=1,
        max_length=2048,
        examples=[
            "https://www.linkedin.com/in/williamhgates"
        ],
    ),
):
    try:
        request = ProfileRequest.model_validate(
            {"profile_url": profile_url}
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Please provide a valid "
                "LinkedIn profile URL"
            ),
        ) from error

    return await get_profile(
        request,
        http_request,
    )


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Profile of the signed-in member",
    description=(
        "Optional. Requires LINKEDIN_CLIENT_ID / "
        "LINKEDIN_CLIENT_SECRET and an OAuth "
        "sign-in. Returns 401 when no session "
        "exists. Not used for URL lookups."
    ),
    responses={
        401: {"description": "Not signed in"},
    },
)
async def get_signed_in_profile(
    request: Request,
):
    """Return the signed-in member's profile.

    Served from the TTL/LRU cache when warm.
    On a miss, LinkedIn's OIDC userinfo
    endpoint is called and the result cached.
    Only identity claims are populated.
    """

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    session = (
        await session_store.get(session_id)
        if session_id
        else None
    )

    if session is None:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Sign in with LinkedIn first",
        )

    # The member id is captured at sign-in, so
    # a cache hit costs no LinkedIn call.
    member_id = (
        session.get("userinfo") or {}
    ).get("sub")

    if member_id:

        cached = await (
            profile_service
            .get_cached_member_profile(
                member_id
            )
        )

        if cached is not None:
            return cached

    try:
        userinfo = await (
            linkedin_oauth.fetch_userinfo(
                session["access_token"]
            )
        )

    except linkedin_oauth.LinkedInOAuthError as error:

        await session_store.delete(session_id)

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "LinkedIn session expired. "
                "Please sign in again"
            ),
        ) from error

    profile_fields = (
        linkedin_oauth
        .map_userinfo_to_profile(userinfo)
    )

    response = ProfileResponse(
        **profile_fields,
        metadata=ProfileMetadata(
            retrieved_at=datetime.now(
                UTC
            ),
            cached=False,
            status="success",
        ),
    )

    if response.member_id:
        await profile_service.store_member_profile(
            response.member_id,
            response,
        )

    return response


@router.get(
    "/cache",
    response_model=CacheListResponse,
)
async def list_cached_profiles():

    profiles = (
        await profile_service.list_cached_profiles()
    )

    return CacheListResponse(
        count=len(profiles),
        profiles=profiles,
    )


@router.get(
    "/cache/profile",
    response_model=ProfileResponse,
)
async def get_cached_profile(
    profile_url: str = Query(
        ...,
        min_length=1,
        max_length=2048,
    ),
):

    try:
        return (
            await profile_service.get_cached_profile(
                profile_url
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    except KeyError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Profile is not present in cache"
            ),
        ) from error
