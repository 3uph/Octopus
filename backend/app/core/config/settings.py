from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "octopus"
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://octopus:octopus@localhost:5432/octopus"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change_me_in_production"
    encryption_key: str = "change_me_in_production"

    # LLM
    llm_provider: Literal["mock", "ollama", "anthropic"] = "mock"
    ollama_base_url: str = "http://localhost:11434"
    anthropic_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
