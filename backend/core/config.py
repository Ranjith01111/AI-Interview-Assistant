"""
Production Configuration — Pydantic Settings

Centralizes ALL application settings.  Values are read from the .env file
at the project root, with sensible defaults for local development.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


# ── Paths ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent   # e:\AI Interview Assistant
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings.

    Every field can be overridden by an environment variable of the same
    name (case-sensitive).  The .env file is loaded automatically.
    """

    # ── OpenRouter / OpenAI ──────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    OPENROUTER_SITE_URL: str = "http://localhost:8000"
    OPENROUTER_SITE_NAME: str = "AI Interview Assistant"

    # ── Local NLP Mode (no external API needed) ────────────────────
    USE_LOCAL_NLP: bool = True

    # ── Agentic AI (Ollama Local LLM) ─────────────────────────────
    USE_AGENTIC_AI: bool = True  # Enable LLM-based evaluation via local Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EVAL_MODEL: str = "deepseek-r1"  # Chain-of-thought evaluation
    OLLAMA_CHAT_MODEL: str = "llama3"  # Conversational interview agent
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"  # Semantic similarity
    OLLAMA_TIMEOUT: int = 60  # Seconds before fallback to rule-based

    # ── Backend Server ────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: bool = False

    # ── PostgreSQL (async) ───────────────────────────────────────────
    # Source default uses a placeholder username/password so that the app
    # does not silently fall back to insecure hard-coded credentials.
    # Override with DATABASE_URL env var before running.
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:REPLACE_ME@localhost:5432/interview_assistant"
    )

    # ── Redis ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_TTL: int = 7200  # 2 hours in seconds

    # ── Security ─────────────────────────────────────────────────────
    # These defaults intentionally break in production if not overridden,
    # preventing accidental usage of developer/hard-coded secrets.
    SECRET_KEY: str = "REPLACE_ME_WITH_64_HEX_CHARS"
    ALLOWED_ORIGINS: str = "http://localhost:8501,http://localhost:3000,http://localhost:5173"

    # ── JWT Authentication ───────────────────────────────────────────
    JWT_SECRET_KEY: str = "REPLACE_ME_WITH_128_HEX_CHARS"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes (use refresh tokens for renewal)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Rate Limiting ────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    # ── FAISS Storage ────────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "./data/faiss_index"

    # ── Anti-Repetition Engine ───────────────────────────────────────
    SIMILARITY_THRESHOLD: float = 0.85
    MAX_DEDUP_RETRIES: int = 1

    # ── Interview Agent ─────────────────────────────────────────────
    AGENT_MODEL: str = "openai/gpt-4o"
    AGENT_TEMPERATURE: float = 0.4
    AGENT_MAX_FOLLOW_UPS: int = 1          # 1 = allow 1 intelligent follow-up per answer (agentic mode)
    AGENT_FOLLOW_UP_SCORE_THRESHOLD: int = 0  # 0 = never trigger follow-up on low score
    AGENT_MIN_ANSWER_LENGTH: int = 1       # 1 = accept any non-empty answer
    AGENT_MEMORY_WINDOW: int = 20

    # ── Token limits ─────────────────────────────────────────────────
    MAX_TOKENS: int = 4096

    # ── AI Proctoring ────────────────────────────────────────────────
    PROCTOR_SNAPSHOT_DIR: str = "./backend/static/snapshots"
    PROCTOR_SNAPSHOT_QUALITY: int = 80
    PROCTOR_VIOLATION_COOLDOWN_SECONDS: int = 10
    PROCTOR_FRAME_INTERVAL_SECONDS: int = 4
    PROCTOR_FACE_MATCH_THRESHOLD: float = 0.78
    PROCTOR_RISK_LOW_THRESHOLD: float = 25.0
    PROCTOR_RISK_HIGH_THRESHOLD: float = 75.0

    # ── App metadata ─────────────────────────────────────────────────
    APP_NAME: str = "AI Interview Assistant"
    APP_VERSION: str = "2.0.0"

    # ── Pydantic-settings wiring ─────────────────────────────────────
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
        # Prefer .env over OS-level environment variables.
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    # ── Helpers ──────────────────────────────────────────────────────
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — .env is read only once."""
    return Settings()


# Global convenience import
settings = get_settings()


# ── Production safety validation ───────────────────────────────────────
def validate_settings_for_environment() -> None:
    """
    Ensure secrets are not left as placeholder values.

    In production (DEBUG=false) this function raises RuntimeError for any
    placeholder credential. In DEBUG mode it only logs a warning.
    """
    import os

    from backend.core.logging import get_logger

    logger = get_logger("backend.core.config")

    sensitive = {
        "OPENROUTER_API_KEY": (settings.OPENROUTER_API_KEY, ["REPLACE_ME", "your_openrouter_api_key_here"]),
        "POSTGRES_PASSWORD": (
            os.environ.get("POSTGRES_PASSWORD", ""),
            ["", "postgres", "changeme_use_openssl_rand_hex_32", "REPLACE_ME_WITH_STRONG_PASSWORD"],
        ),
        "REDIS_PASSWORD": (
            os.environ.get("REDIS_PASSWORD", ""),
            ["", "changeme_use_openssl_rand_hex_32", "REPLACE_ME_WITH_STRONG_PASSWORD"],
        ),
        "SECRET_KEY": (settings.SECRET_KEY, ["change-me", "REPLACE_ME_WITH_64_HEX_CHARS"]),
        "JWT_SECRET_KEY": (settings.JWT_SECRET_KEY, ["change-me", "REPLACE_ME_WITH_128_HEX_CHARS"]),
    }

    violations: List[str] = []
    for name, (value, bad_values) in sensitive.items():
        if any(bad in (value or "") for bad in bad_values):
            violations.append(name)

    if not violations:
        return

    msg = (
        "Insecure placeholder/weak values detected for: "
        + ", ".join(violations)
    )
    if settings.DEBUG:
        logger.warning("weak_secrets_in_dev_mode", keys=violations)
    else:
        logger.error("weak_secrets_in_production", keys=violations)
        raise RuntimeError(msg)
