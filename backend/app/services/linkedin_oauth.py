import secrets
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings

AUTHORIZATION_ENDPOINT = (
    "https://www.linkedin.com/oauth/v2/authorization"
)

TOKEN_ENDPOINT = (
    "https://www.linkedin.com/oauth/v2/accessToken"
)

USERINFO_ENDPOINT = (
    "https://api.linkedin.com/v2/userinfo"
)


class LinkedInOAuthError(RuntimeError):
    """Raised when the OAuth flow cannot complete."""


def require_configured() -> None:

    if not settings.linkedin_oauth_configured:
        raise LinkedInOAuthError(
            "LinkedIn OAuth is not configured"
        )


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorization_url(
    state: str,
) -> str:

    require_configured()

    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": (
            settings.linkedin_redirect_uri
        ),
        "state": state,
        "scope": settings.linkedin_scopes,
    }

    return (
        f"{AUTHORIZATION_ENDPOINT}"
        f"?{urlencode(params)}"
    )


async def _request_token(
    form: dict[str, str | None],
    failure_message: str,
) -> dict[str, Any]:

    require_configured()

    timeout = httpx.Timeout(
        settings.request_timeout_seconds
    )

    async with httpx.AsyncClient(
        timeout=timeout,
    ) as client:

        response = await client.post(
            TOKEN_ENDPOINT,
            data=form,
            headers={
                "Accept": "application/json",
                "Content-Type": (
                    "application/"
                    "x-www-form-urlencoded"
                ),
            },
        )

    if response.status_code != 200:
        raise LinkedInOAuthError(failure_message)

    payload = response.json()

    access_token = payload.get("access_token")

    if (
        not isinstance(access_token, str)
        or not access_token
    ):
        raise LinkedInOAuthError(
            "Token response did not include "
            "an access token"
        )

    return payload


async def exchange_code_for_token(
    code: str,
) -> dict[str, Any]:

    return await _request_token(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": (
                settings.linkedin_redirect_uri
            ),
            "client_id": (
                settings.linkedin_client_id
            ),
            "client_secret": (
                settings.linkedin_client_secret
            ),
        },
        "Authorization code exchange failed",
    )


async def refresh_access_token(
    refresh_token: str,
) -> dict[str, Any]:
    """Exchange a refresh token for a new one.

    LinkedIn only issues refresh tokens to
    approved partner apps, so this is a
    best-effort path.
    """

    return await _request_token(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": (
                settings.linkedin_client_id
            ),
            "client_secret": (
                settings.linkedin_client_secret
            ),
        },
        "Access token refresh failed",
    )


async def fetch_userinfo(
    access_token: str,
) -> dict[str, Any]:

    timeout = httpx.Timeout(
        settings.request_timeout_seconds
    )

    async with httpx.AsyncClient(
        timeout=timeout,
    ) as client:

        response = await client.get(
            USERINFO_ENDPOINT,
            headers={
                "Accept": "application/json",
                "Authorization": (
                    f"Bearer {access_token}"
                ),
            },
        )

    if response.status_code == 401:
        raise LinkedInOAuthError(
            "LinkedIn access token is no "
            "longer valid"
        )

    if response.status_code != 200:
        raise LinkedInOAuthError(
            "LinkedIn userinfo request failed"
        )

    payload = response.json()

    if not isinstance(payload, dict):
        raise LinkedInOAuthError(
            "LinkedIn returned an "
            "unexpected userinfo payload"
        )

    return payload


def _normalize_locale(
    value: Any,
) -> str | None:

    if isinstance(value, str):
        return value or None

    if isinstance(value, dict):
        country = value.get("country")
        language = value.get("language")

        parts = [
            str(part)
            for part in (language, country)
            if part
        ]

        return "-".join(parts) or None

    return None


def map_userinfo_to_profile(
    userinfo: dict[str, Any],
) -> dict[str, Any]:
    """Map OIDC claims onto profile fields.

    Only identity claims are available under
    the openid/profile/email scopes, so
    experience, education and skills stay
    empty unless a partner-level product is
    approved.
    """

    given_name = userinfo.get("given_name")
    family_name = userinfo.get("family_name")

    name = userinfo.get("name") or " ".join(
        str(part)
        for part in (given_name, family_name)
        if part
    )

    return {
        "member_id": userinfo.get("sub"),
        "name": name or None,
        "email": userinfo.get("email"),
        "profile_image": userinfo.get("picture"),
        "location": _normalize_locale(
            userinfo.get("locale")
        ),
    }
