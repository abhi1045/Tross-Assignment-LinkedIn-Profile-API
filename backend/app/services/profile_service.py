from datetime import datetime, timezone

from app.config import settings
from app.schemas.profile import (
    ProfileMetadata,
    ProfileResponse,
)
from app.services.provider import (
    ProfileProvider,
    get_profile_provider,
)
from app.utils.cache import TTLCache
from app.utils.validators import (
    validate_linkedin_profile_url,
)


class ProfileService:

    def __init__(
        self,
        provider: ProfileProvider | None = None,
    ):

        self.provider = (
            provider
            or get_profile_provider()
        )

        self.cache = TTLCache(
            ttl_seconds=(
                settings.cache_ttl_seconds
            ),
            max_items=(
                settings.cache_max_items
            ),
        )

    async def get_profile(
        self,
        profile_url: str,
    ) -> ProfileResponse:

        normalized_url = (
            validate_linkedin_profile_url(
                profile_url
            )
        )

        cached_data = await self.cache.get(
            normalized_url
        )

        if cached_data is not None:

            response = (
                ProfileResponse.model_validate(
                    cached_data
                )
            )

            response.metadata.cached = True

            return response

        raw_data = await self.provider.get_profile(
            normalized_url
        )

        response = ProfileResponse(
            **raw_data,
            profile_url=normalized_url,
            metadata=ProfileMetadata(
                retrieved_at=datetime.now(
                    timezone.utc
                ),
                cached=False,
                status="success",
            ),
        )

        await self.cache.set(
            normalized_url,
            response.model_dump(
                mode="json"
            ),
        )

        return response
