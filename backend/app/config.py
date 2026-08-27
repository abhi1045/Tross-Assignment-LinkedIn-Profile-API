from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LinkedIn Profile API"
    app_version: str = "1.0.0"

    provider_base_url: str | None = None
    provider_api_key: str | None = None

    cache_ttl_seconds: int = 300
    request_timeout_seconds: float = 15.0

    allowed_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
