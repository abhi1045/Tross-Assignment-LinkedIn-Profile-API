from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import settings


class ProfileProvider(ABC):

    @abstractmethod
    async def get_profile(
        self,
        profile_url: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class DemoProfileProvider(ProfileProvider):

    async def get_profile(
        self,
        profile_url: str,
    ) -> dict[str, Any]:

        return {
            "profile_url": profile_url,
            "name": "Demo User",
            "headline": "Software Engineer",
            "location": "Bengaluru, Karnataka, India",
            "about": (
                "Demo data returned by the "
                "development provider."
            ),
            "profile_image": None,
            "background_image": None,

            "experience": [
                {
                    "company": "Example Company",
                    "title": "Software Engineer",
                    "employment_type": "Full-time",
                    "location": "Bengaluru, India",
                    "start_date": "2023-01",
                    "end_date": None,
                    "description": (
                        "Building scalable applications."
                    ),
                }
            ],

            "education": [
                {
                    "school": "Example University",
                    "degree": (
                        "Bachelor of Engineering"
                    ),
                    "field_of_study": (
                        "Computer Science"
                    ),
                    "start_year": 2018,
                    "end_year": 2022,
                }
            ],

            "skills": [
                "Python",
                "FastAPI",
                "React",
            ],

            "certifications": [],

            "languages": [
                {
                    "name": "English",
                    "proficiency": "Professional",
                }
            ],
        }


class AuthorizedHttpProfileProvider(
    ProfileProvider
):

    async def get_profile(
        self,
        profile_url: str,
    ) -> dict[str, Any]:

        if not settings.provider_base_url:
            raise RuntimeError(
                "Profile provider is not configured"
            )

        headers: dict[str, str] = {
            "Accept": "application/json",
        }

        if settings.provider_api_key:
            headers["Authorization"] = (
                "Bearer "
                f"{settings.provider_api_key}"
            )

        timeout = httpx.Timeout(
            settings.request_timeout_seconds
        )

        async with httpx.AsyncClient(
            timeout=timeout,
        ) as client:

            response = await client.post(
                settings.provider_base_url,
                json={
                    "profile_url": profile_url,
                },
                headers=headers,
            )

            response.raise_for_status()

            data = response.json()

        if not isinstance(data, dict):
            raise RuntimeError(
                "Profile provider returned "
                "an invalid response"
            )

        return data


def get_profile_provider() -> ProfileProvider:

    if settings.provider_base_url:
        return AuthorizedHttpProfileProvider()

    return DemoProfileProvider()
