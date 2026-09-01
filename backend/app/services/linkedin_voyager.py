import logging
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from app.config import settings
from app.utils.validators import (
    extract_profile_identifier,
)

logger = logging.getLogger(__name__)

VOYAGER_ORIGIN = "https://www.linkedin.com"
VOYAGER_API = f"{VOYAGER_ORIGIN}/voyager/api"

# Nested JSON is easier to map. Normalized
# JSON is still accepted as a fallback.
_ACCEPT_NESTED = "application/json"
_ACCEPT_NORMALIZED = (
    "application/vnd.linkedin.normalized+json+2.1"
)

_EMPLOYMENT_LABELS = {
    "FULL_TIME": "Full-time",
    "PART_TIME": "Part-time",
    "SELF_EMPLOYED": "Self-employed",
    "FREELANCE": "Freelance",
    "CONTRACT": "Contract",
    "INTERNSHIP": "Internship",
    "APPRENTICESHIP": "Apprenticeship",
    "SEASONAL": "Seasonal",
}


class LinkedInSessionError(RuntimeError):
    """Raised when the LinkedIn session cannot be used."""


class ProfileNotFoundError(ValueError):
    """Raised when LinkedIn has no matching profile."""


def _quote_jsessionid(value: str) -> str:

    trimmed = value.strip()

    if trimmed.startswith('"') and trimmed.endswith(
        '"'
    ):
        return trimmed

    return f'"{trimmed}"'


def _csrf_from_jsessionid(jsessionid: str) -> str:

    return jsessionid.strip().strip('"')


def _safe_media_url(url: str | None) -> str | None:

    if not url:
        return None

    parsed = urlparse(url)

    if parsed.scheme != "https":
        return None

    host = (parsed.hostname or "").lower()

    if host == "licdn.com" or host.endswith(
        ".licdn.com"
    ):
        return url

    return None


def _vector_image(
    node: Any,
    depth: int = 0,
) -> dict[str, Any] | None:

    if depth > 8 or not isinstance(node, dict):
        return None

    artifacts = node.get("artifacts")
    root = node.get("rootUrl")

    if isinstance(root, str) and isinstance(
        artifacts, list
    ):
        return node

    nested = node.get("vectorImage")

    if isinstance(nested, dict):
        found = _vector_image(nested, depth + 1)
        if found is not None:
            return found

    for key, value in node.items():
        if "VectorImage" in str(key) and isinstance(
            value, dict
        ):
            found = _vector_image(value, depth + 1)
            if found is not None:
                return found

        if key in {
            "displayImageReference",
            "displayImageReferenceResolutionResult",
            "displayImage",
            "picture",
            "profilePicture",
            "backgroundImage",
        }:
            found = _vector_image(value, depth + 1)
            if found is not None:
                return found

    return None


def _picture_url(node: Any) -> str | None:

    vector = _vector_image(node)

    if vector is None:
        return None

    root = vector.get("rootUrl")
    artifacts = vector.get("artifacts") or []

    if not isinstance(root, str) or not artifacts:
        return None

    widest: dict[str, Any] | None = None
    widest_width = -1

    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        width = artifact.get("width") or 0
        try:
            width_int = int(width)
        except (TypeError, ValueError):
            width_int = 0
        if width_int >= widest_width:
            widest_width = width_int
            widest = artifact

    if widest is None:
        last = artifacts[-1]
        widest = last if isinstance(last, dict) else None

    if widest is None:
        return None

    fragment = widest.get(
        "fileIdentifyingUrlPathSegment"
    )

    if not fragment:
        return None

    return _safe_media_url(f"{root}{fragment}")


def _text(value: Any) -> str | None:

    if isinstance(value, str):
        return value or None

    if isinstance(value, dict):
        localized = value.get("localized")
        if isinstance(localized, dict) and localized:
            first = next(iter(localized.values()))
            if isinstance(first, str) and first:
                return first
        text = value.get("text")
        if isinstance(text, str) and text:
            return text

    return None


def _year_month(node: Any) -> str | None:

    if not isinstance(node, dict):
        return None

    year = node.get("year")
    month = node.get("month")

    if year and month:
        try:
            return f"{int(year)}-{int(month):02d}"
        except (TypeError, ValueError):
            return str(year)

    if year:
        return str(year)

    return None


def _date_part(
    node: dict[str, Any],
    which: str,
) -> Any:

    period = (
        node.get("timePeriod")
        or node.get("dateRange")
        or {}
    )

    if not isinstance(period, dict):
        return None

    if which == "start":
        return (
            period.get("startDate")
            or period.get("start")
        )

    return period.get("endDate") or period.get("end")


def _company_name(position: dict[str, Any]) -> str | None:

    company = position.get("companyName")

    if isinstance(company, str) and company:
        return company

    nested = position.get("company")

    if isinstance(nested, dict):
        mini = nested.get("miniCompany") or nested
        if isinstance(mini, dict):
            name = mini.get("name") or mini.get(
                "localizedName"
            )
            if isinstance(name, str) and name:
                return name

    return _text(position.get("companyUrn"))


def _school_name(school: dict[str, Any]) -> str | None:

    name = school.get("schoolName")

    if isinstance(name, str) and name:
        return name

    nested = school.get("school")

    if isinstance(nested, dict):
        nested_name = nested.get("name") or nested.get(
            "localizedName"
        )
        if isinstance(nested_name, str) and nested_name:
            return nested_name

    return None


def _employment_type(value: Any) -> str | None:

    if not isinstance(value, str) or not value:
        return None

    return _EMPLOYMENT_LABELS.get(value, value)


def _skill_name(skill: dict[str, Any]) -> str | None:

    name = skill.get("name")

    if isinstance(name, str) and name:
        return name

    nested = skill.get("skill") or skill.get(
        "standardizedSkill"
    )

    if isinstance(nested, dict):
        nested_name = nested.get("name")
        if isinstance(nested_name, str) and nested_name:
            return nested_name

    return _text(name)


def _elements(view: Any) -> list[Any]:

    if isinstance(view, list):
        return view

    if not isinstance(view, dict):
        return []

    elements = view.get("elements") or view.get(
        "*elements"
    )

    if isinstance(elements, list):
        return elements

    return []


def denormalize(payload: dict[str, Any]) -> dict[str, Any]:
    """Resolve Rest.li `included` URN references."""

    included = payload.get("included")

    if not isinstance(included, list):
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        return payload

    index: dict[str, dict[str, Any]] = {}

    for item in included:
        if not isinstance(item, dict):
            continue
        urn = item.get("entityUrn")
        if isinstance(urn, str) and urn:
            index[urn] = item

    resolving: set[str] = set()

    def resolve(node: Any, depth: int = 0) -> Any:

        if depth > 24:
            return node

        if isinstance(node, str) and node in index:
            if node in resolving:
                return {"entityUrn": node}
            resolving.add(node)
            try:
                return resolve(index[node], depth + 1)
            finally:
                resolving.discard(node)

        if isinstance(node, list):
            return [
                resolve(item, depth + 1)
                for item in node
            ]

        if isinstance(node, dict):
            out: dict[str, Any] = {}
            for key, value in node.items():
                resolved = resolve(value, depth + 1)
                if key.startswith("*") and len(key) > 1:
                    out[key[1:]] = resolved
                else:
                    out[key] = resolved
            return out

        return node

    data = payload.get("data", payload)

    resolved = resolve(data)

    if isinstance(resolved, dict):
        return resolved

    return payload


def prepare_profile_view(
    payload: dict[str, Any],
) -> dict[str, Any]:

    prepared = denormalize(payload)

    if "profile" in prepared or "positionView" in (
        prepared
    ):
        return prepared

    elements = _elements(prepared)

    if elements and isinstance(elements[0], dict):
        first = elements[0]
        return {
            "profile": first,
            **prepared,
        }

    return prepared


def skills_from_payload(
    payload: dict[str, Any],
) -> list[str]:

    prepared = prepare_profile_view(payload)
    names: list[str] = []
    seen: set[str] = set()

    candidates = _elements(prepared)

    skill_view = prepared.get("skillView")

    if not candidates:
        candidates = _elements(skill_view)

    for skill in candidates:
        if not isinstance(skill, dict):
            continue
        label = _skill_name(skill)
        if not label or label in seen:
            continue
        seen.add(label)
        names.append(label)

    return names


def map_profile_view(
    payload: dict[str, Any],
    profile_url: str,
) -> dict[str, Any]:

    data = prepare_profile_view(payload)

    profile = data.get("profile") or {}

    if not isinstance(profile, dict):
        profile = {}

    mini = profile.get("miniProfile") or {}

    if not isinstance(mini, dict):
        mini = {}

    first = profile.get("firstName") or mini.get(
        "firstName"
    )
    last = profile.get("lastName") or mini.get(
        "lastName"
    )
    name = " ".join(
        part
        for part in (first, last)
        if isinstance(part, str) and part
    ) or None

    experience = []

    position_elements = _elements(
        data.get("positionView")
    )

    if not position_elements:
        maybe = _elements(data)
        if maybe and isinstance(maybe[0], dict) and (
            maybe[0].get("title")
            or maybe[0].get("companyName")
        ):
            position_elements = maybe

    for position in position_elements:
        if not isinstance(position, dict):
            continue
        experience.append(
            {
                "company": _company_name(position),
                "title": position.get("title"),
                "employment_type": _employment_type(
                    position.get("employmentType")
                    or position.get(
                        "employmentTypeUrn"
                    )
                ),
                "location": (
                    position.get("geoLocationName")
                    or position.get("locationName")
                ),
                "start_date": _year_month(
                    _date_part(position, "start")
                ),
                "end_date": _year_month(
                    _date_part(position, "end")
                ),
                "description": position.get(
                    "description"
                ),
            }
        )

    education = []

    education_elements = _elements(
        data.get("educationView")
    )

    if not education_elements:
        maybe = _elements(data)
        if maybe and isinstance(maybe[0], dict) and (
            maybe[0].get("schoolName")
            or maybe[0].get("degreeName")
        ):
            education_elements = maybe

    for school in education_elements:
        if not isinstance(school, dict):
            continue
        start = _date_part(school, "start")
        end = _date_part(school, "end")
        start_year = (
            start.get("year")
            if isinstance(start, dict)
            else None
        )
        end_year = (
            end.get("year")
            if isinstance(end, dict)
            else None
        )
        education.append(
            {
                "school": _school_name(school),
                "degree": school.get("degreeName"),
                "field_of_study": school.get(
                    "fieldOfStudy"
                ),
                "start_year": start_year,
                "end_year": end_year,
            }
        )

    certifications = []

    for cert in _elements(
        data.get("certificationView")
    ):
        if not isinstance(cert, dict):
            continue
        certifications.append(
            {
                "name": cert.get("name"),
                "organization": cert.get("authority"),
                "issue_date": _year_month(
                    _date_part(cert, "start")
                ),
                "expiration_date": _year_month(
                    _date_part(cert, "end")
                ),
                "credential_id": cert.get(
                    "licenseNumber"
                ),
            }
        )

    languages = []

    for language in _elements(
        data.get("languageView")
    ):
        if not isinstance(language, dict):
            continue
        label = language.get("name")
        if not isinstance(label, str) or not label:
            continue
        languages.append(
            {
                "name": label,
                "proficiency": language.get(
                    "proficiency"
                ),
            }
        )

    skills = skills_from_payload(data)

    location = (
        profile.get("geoLocationName")
        or profile.get("locationName")
        or _text(profile.get("geoLocation"))
    )

    return {
        "profile_url": profile_url,
        "name": name,
        "headline": profile.get("headline")
        or mini.get("occupation"),
        "location": location,
        "about": profile.get("summary"),
        "profile_image": _picture_url(mini)
        or _picture_url(profile),
        "background_image": _picture_url(
            profile.get("backgroundImage")
        ),
        "experience": experience,
        "education": education,
        "skills": skills,
        "certifications": certifications,
        "languages": languages,
    }


class LinkedInVoyagerProvider:
    """HTTP client for LinkedIn member Voyager APIs.

    No browser. Host is fixed to www.linkedin.com.
    The submitted profile URL is reduced to a
    vanity slug after validation.
    """

    async def get_profile(
        self,
        profile_url: str,
    ) -> dict[str, Any]:

        if not settings.linkedin_li_at:
            raise LinkedInSessionError(
                "LinkedIn session is not configured"
            )

        vanity = extract_profile_identifier(
            profile_url
        )
        encoded = quote(vanity, safe="")

        timeout = httpx.Timeout(
            settings.request_timeout_seconds
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    settings.linkedin_user_agent
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:

            cookies, headers = (
                await self._session_headers(
                    client,
                    vanity,
                )
            )

            payload = await self._get_json(
                client,
                (
                    f"{VOYAGER_API}/identity/profiles/"
                    f"{encoded}/profileView"
                ),
                cookies,
                headers,
            )

            mapped = map_profile_view(
                payload,
                profile_url,
            )

            if not mapped.get("skills"):
                skills_payload = (
                    await self._get_json_optional(
                        client,
                        (
                            f"{VOYAGER_API}/identity/"
                            f"profiles/{encoded}/skills"
                        ),
                        cookies,
                        headers,
                    )
                )
                if skills_payload is not None:
                    mapped["skills"] = (
                        skills_from_payload(
                            skills_payload
                        )
                    )

            if not mapped.get("experience"):
                extra = await self._get_json_optional(
                    client,
                    (
                        f"{VOYAGER_API}/identity/"
                        f"profiles/{encoded}/"
                        "positionView"
                    ),
                    cookies,
                    headers,
                )
                if extra is not None:
                    mapped["experience"] = (
                        map_profile_view(
                            extra,
                            profile_url,
                        )["experience"]
                    )

            if not mapped.get("education"):
                extra = await self._get_json_optional(
                    client,
                    (
                        f"{VOYAGER_API}/identity/"
                        f"profiles/{encoded}/"
                        "educationView"
                    ),
                    cookies,
                    headers,
                )
                if extra is not None:
                    mapped["education"] = (
                        map_profile_view(
                            extra,
                            profile_url,
                        )["education"]
                    )

        if not mapped.get("name"):
            raise ProfileNotFoundError(
                "LinkedIn profile was not found"
            )

        return mapped

    async def _session_headers(
        self,
        client: httpx.AsyncClient,
        vanity: str,
    ) -> tuple[dict[str, str], dict[str, str]]:

        cookies: dict[str, str] = {
            "li_at": settings.linkedin_li_at or "",
        }

        jsessionid = settings.linkedin_jsessionid

        if not jsessionid:
            jsessionid = (
                await self._bootstrap_jsessionid(
                    client,
                    cookies,
                )
            )

        if not jsessionid:
            raise LinkedInSessionError(
                "LinkedIn session is not authorized"
            )

        cookies["JSESSIONID"] = _quote_jsessionid(
            jsessionid
        )

        headers = {
            "Accept": _ACCEPT_NESTED,
            "csrf-token": _csrf_from_jsessionid(
                jsessionid
            ),
            "x-restli-protocol-version": "2.0.0",
            "x-li-lang": "en_US",
            "Referer": (
                f"{VOYAGER_ORIGIN}/in/{vanity}/"
            ),
        }

        return cookies, headers

    async def _bootstrap_jsessionid(
        self,
        client: httpx.AsyncClient,
        cookies: dict[str, str],
    ) -> str | None:

        for url in (
            f"{VOYAGER_API}/me",
            f"{VOYAGER_ORIGIN}/",
        ):
            try:
                response = await client.get(
                    url,
                    cookies=cookies,
                    headers={
                        "Accept": _ACCEPT_NESTED,
                    },
                )
            except httpx.HTTPError:
                logger.warning(
                    "LinkedIn session bootstrap failed"
                )
                continue

            jsessionid = response.cookies.get(
                "JSESSIONID"
            )

            if jsessionid:
                return jsessionid

        return None

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        cookies: dict[str, str],
        headers: dict[str, str],
    ) -> dict[str, Any]:

        response = await self._get(
            client,
            url,
            cookies,
            headers,
        )

        if response.status_code in {401, 403, 999}:
            raise LinkedInSessionError(
                "LinkedIn session is not authorized"
            )

        if response.status_code == 404:
            raise ProfileNotFoundError(
                "LinkedIn profile was not found"
            )

        if response.status_code != 200:
            logger.warning(
                "LinkedIn request failed status=%s",
                response.status_code,
            )
            raise LinkedInSessionError(
                "LinkedIn profile request failed"
            )

        payload = response.json()

        if not isinstance(payload, dict):
            raise LinkedInSessionError(
                "LinkedIn returned an unexpected payload"
            )

        return payload

    async def _get_json_optional(
        self,
        client: httpx.AsyncClient,
        url: str,
        cookies: dict[str, str],
        headers: dict[str, str],
    ) -> dict[str, Any] | None:

        try:
            response = await self._get(
                client,
                url,
                cookies,
                headers,
            )
        except httpx.HTTPError:
            return None

        if response.status_code != 200:
            return None

        payload = response.json()

        if not isinstance(payload, dict):
            return None

        return payload

    async def _get(
        self,
        client: httpx.AsyncClient,
        url: str,
        cookies: dict[str, str],
        headers: dict[str, str],
    ) -> httpx.Response:

        response = await client.get(
            url,
            cookies=cookies,
            headers=headers,
        )

        if (
            response.status_code == 400
            and headers.get("Accept")
            == _ACCEPT_NESTED
        ):
            retry_headers = {
                **headers,
                "Accept": _ACCEPT_NORMALIZED,
            }
            response = await client.get(
                url,
                cookies=cookies,
                headers=retry_headers,
            )

        return response
