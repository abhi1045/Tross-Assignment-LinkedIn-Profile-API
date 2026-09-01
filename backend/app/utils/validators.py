import re
from urllib.parse import urlparse

# LinkedIn vanity slugs are ASCII. Restricting
# the identifier prevents path injection into
# the fixed Voyager URL.
_VANITY_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?$"
)


def _is_linkedin_hostname(hostname: str | None) -> bool:

    if not hostname:
        return False

    host = hostname.lower().rstrip(".")

    return host == "linkedin.com" or host.endswith(
        ".linkedin.com"
    )


def validate_linkedin_profile_url(
    profile_url: str,
) -> str:

    parsed = urlparse(profile_url)

    if parsed.scheme != "https":
        raise ValueError(
            "Profile URL must use HTTPS"
        )

    if not _is_linkedin_hostname(parsed.hostname):
        raise ValueError(
            "Please provide a valid LinkedIn URL"
        )

    path = parsed.path.rstrip("/")

    if not path.startswith("/in/"):
        raise ValueError(
            "Please provide a LinkedIn profile URL"
        )

    extract_profile_identifier(profile_url)

    return profile_url.rstrip("/")


def extract_profile_identifier(
    profile_url: str,
) -> str:

    path = urlparse(profile_url).path.rstrip("/")
    parts = [
        part
        for part in path.split("/")
        if part
    ]

    if len(parts) < 2:
        raise ValueError(
            "LinkedIn profile identifier is missing"
        )

    vanity = parts[1]

    if not _VANITY_PATTERN.fullmatch(vanity):
        raise ValueError(
            "LinkedIn profile identifier is invalid"
        )

    return vanity
