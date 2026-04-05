"""
Configuration management using Pydantic Settings.
Reads values from .env file automatically.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.
    Pydantic automatically reads from .env and validates types.
    """
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = "your_openrouter_api_key_here"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    OPENROUTER_SITE_URL: str = "http://localhost:8000"
    OPENROUTER_SITE_NAME: str = "AI Interview Assistant"
    
    # Backend Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    # FAISS Storage
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    
    # Token limits
    MAX_TOKENS: int = 4096
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ):
        # Prefer the project's .env over machine-level environment variables.
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Using lru_cache means we only read the .env file once.
    """
    return Settings()


# Global settings instance - import this in other modules
settings = get_settings()
