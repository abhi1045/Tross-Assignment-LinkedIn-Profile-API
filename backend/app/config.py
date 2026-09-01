from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT_ENV = (
    Path(__file__).resolve().parents[2] / ".env"
)


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

    # Unique profile URLs per client IP per
    # window. Default: 10 per minute.
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=10, ge=1)
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
    )

    # Opt-in only. When false, a configured
    # provider URL is required.
    use_demo_provider: bool = False

    # LinkedIn OAuth 2.0 (OpenID Connect).
    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = None
    linkedin_redirect_uri: str = (
        "http://localhost:8000"
        "/api/v1/auth/linkedin/callback"
    )
    linkedin_scopes: str = "openid profile email"

    # Fixed post-login destination. Never
    # taken from request input.
    frontend_url: str = "http://localhost:5173"

    session_ttl_seconds: int = 3600
    session_max_items: int = 500

    # Server-side token persistence. Survives
    # restarts so sign-in is not required again.
    token_persistence_enabled: bool = True
    token_store_path: str = (
        ".secrets/linkedin_token.json"
    )

    # When true, URL lookups require a visitor
    # OAuth cookie. The public challenge API
    # uses the server session instead.
    require_auth_for_profile: bool = False

    # Session cookie from a browser where you
    # are already logged into LinkedIn. Never
    # commit this value.
    linkedin_li_at: str | None = None
    linkedin_jsessionid: str | None = None
    linkedin_user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X "
        "10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # Optional configured provider.
    provider_base_url: str | None = None
    provider_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=(
            str(_REPO_ROOT_ENV),
            ".env",
        ),
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

    @property
    def linkedin_session_configured(self) -> bool:
        return bool(self.linkedin_li_at)

    @property
    def linkedin_oauth_configured(self) -> bool:
        return bool(
            self.linkedin_client_id
            and self.linkedin_client_secret
        )

    @property
    def cookies_secure(self) -> bool:
        # Browsers reject Secure cookies over
        # plain HTTP on local development.
        return self.environment != "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
