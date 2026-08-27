from datetime import datetime, timezone

from app.config import settings
from app.schemas.profile import (
    ProfileMetadata,
    ProfileResponse,
)
from app.services.provider import MockProfileProvider
from app.utils.cache import TTLCache


class ProfileService:

    def __init__(self):

        self.provider = MockProfileProvider()

        self.cache = TTLCache(
            ttl_seconds=settings.cache_ttl_seconds,
            max_items=100,
        )

    @staticmethod
    def validate_url(
        profile_url: str,
    ) -> None:

        valid_hosts = (
            "linkedin.com",
            "www.linkedin.com",
        )

        if not profile_url.startswith("https://"):
            raise ValueError(
                "Profile URL must use HTTPS"
            )

        if not any(
            host in profile_url
            for host in valid_hosts
        ):
            raise ValueError(
                "Please provide a valid LinkedIn URL"
            )

        if "/in/" not in profile_url:
            raise ValueError(
                "Please provide a LinkedIn profile URL"
            )

    async def get_profile(
        self,
        profile_url: str,
    ) -> ProfileResponse:

        self.validate_url(profile_url)

        cached_data = await self.cache.get(
            profile_url
        )

        if cached_data:
            response = ProfileResponse.model_validate(
                cached_data
            )

            response.metadata.cached = True

            return response

        raw_data = await self.provider.get_profile(
            profile_url
        )

        response = ProfileResponse(
            **raw_data,
            metadata=ProfileMetadata(
                retrieved_at=datetime.now(
                    timezone.utc
                ),
                cached=False,
                status="success",
            ),
        )

        await self.cache.set(
            profile_url,
            response.model_dump(mode="json"),
        )

        return response