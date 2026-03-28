from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Provider-specific API keys (kept for backward compatibility)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    librariesio_api_key: str = ""
    github_token: str = ""
    stackoverflow_api_key: str = ""

    # LLM
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    llm_api_key: str = ""

    # Runtime
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Cache
    cache_ttl_seconds: int = 3600
    cache_backend: str = "memory"

    # Service rate limiting (reserved for API middleware)
    max_requests_per_minute: int = 20

    model_config = {"env_file": ".env", "env_prefix": "OVERBUILD_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
