from urllib.parse import urlparse


def validate_linkedin_profile_url(
    profile_url: str,
) -> str:

    parsed = urlparse(profile_url)

    if parsed.scheme != "https":
        raise ValueError(
            "Profile URL must use HTTPS"
        )

    hostname = parsed.hostname

    if hostname not in {
        "linkedin.com",
        "www.linkedin.com",
    }:
        raise ValueError(
            "Please provide a valid LinkedIn URL"
        )

    path = parsed.path.rstrip("/")

    if not path.startswith("/in/"):
        raise ValueError(
            "Please provide a LinkedIn profile URL"
        )

    parts = [
        part
        for part in path.split("/")
        if part
    ]

    if len(parts) < 2:
        raise ValueError(
            "LinkedIn profile identifier is missing"
        )

    return profile_url.rstrip("/")
