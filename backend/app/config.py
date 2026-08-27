from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LinkedIn Profile API"
    app_version: str = "1.0.0"
    environment: str = "development"

    allowed_origins: str = (
        "http://localhost:5173,"
        "http://localhost:8000"
    )

    cache_ttl_seconds: int = 300
    cache_max_items: int = 100
    request_timeout_seconds: float = 20.0

    # Backend-only credentials.
    linkedin_email: str | None = None
    linkedin_password: str | None = None

    # Optional configured provider.
    provider_base_url: str | None = None
    provider_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
