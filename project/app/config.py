"""
HealthOps Studio — Centralized Configuration

WHY THIS FILE EXISTS:
Instead of hardcoding values like database URLs, JWT secrets, and API keys
throughout the codebase, we load everything from environment variables.

- In development: values come from .env file
- In production: values come from a secrets manager (AWS Secrets Manager, Vault, etc.)

Pydantic BaseSettings automatically reads from env vars and .env files,
validates types, and gives us autocomplete + type safety everywhere.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    All configuration for the HealthOps Studio platform.
    Each field maps to an environment variable of the same name (case-insensitive).
    """

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql://healthops:healthops_dev_2024@127.0.0.1:5433/healthops"

    # ── Redis ─────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT (RS256 — asymmetric keys) ─────────────────────
    # RS256 uses a private key to SIGN tokens, and a public key to VERIFY.
    # This means only the auth service needs the private key;
    # other services can verify tokens with just the public key.
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "RS256"

    # ── Security ──────────────────────────────────────────
    # A pepper is an application-level secret mixed into password hashing.
    # Even if the database is stolen, passwords can't be cracked without it.
    PASSWORD_PEPPER: str = "dev-pepper-not-for-production"

    # ── Gemini AI ─────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── App ───────────────────────────────────────────────
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ── AI Integration ────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore Docker-specific vars (POSTGRES_USER, etc.)
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance — loaded once on startup.
    lru_cache ensures we don't re-read .env on every request.
    """
    return Settings()
