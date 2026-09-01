from datetime import UTC, datetime

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

MEMBER_KEY_PREFIX = "member:"


class ProfileService:

    def __init__(
        self,
        provider: ProfileProvider | None = None,
    ):

        self._provider = provider

        self.cache = TTLCache(
            ttl_seconds=(
                settings.cache_ttl_seconds
            ),
            max_items=(
                settings.cache_max_items
            ),
        )

    @property
    def provider(self) -> ProfileProvider:

        if self._provider is None:
            self._provider = (
                get_profile_provider()
            )

        return self._provider

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

        raw_data.pop("profile_url", None)

        response = ProfileResponse(
            **raw_data,
            profile_url=normalized_url,
            metadata=ProfileMetadata(
                retrieved_at=datetime.now(
                    UTC
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

    async def get_cached_member_profile(
        self,
        member_id: str,
    ) -> ProfileResponse | None:

        cached_data = await self.cache.get(
            f"{MEMBER_KEY_PREFIX}{member_id}"
        )

        if cached_data is None:
            return None

        response = (
            ProfileResponse.model_validate(
                cached_data
            )
        )

        response.metadata.cached = True

        return response

    async def store_member_profile(
        self,
        member_id: str,
        response: ProfileResponse,
    ) -> None:

        await self.cache.set(
            f"{MEMBER_KEY_PREFIX}{member_id}",
            response.model_dump(mode="json"),
        )

    async def get_cached_profile(
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

        if cached_data is None:
            raise KeyError(
                "Profile is not present in cache"
            )

        response = (
            ProfileResponse.model_validate(
                cached_data
            )
        )

        response.metadata.cached = True

        return response

    async def list_cached_profiles(
        self,
    ) -> list[ProfileResponse]:

        cached_items = await self.cache.items()

        profiles: list[ProfileResponse] = []

        for cached_data in cached_items.values():
            response = (
                ProfileResponse.model_validate(
                    cached_data
                )
            )
            response.metadata.cached = True
            profiles.append(response)

        return profiles
