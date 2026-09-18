import logging
import secrets
from typing import List, Union

from pydantic import (AnyHttpUrl, Field, PostgresDsn, computed_field,
                      field_validator)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Antarctic Navigation API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEMO_MODE: bool = True

    # Secrets - REQUIRED in production, auto-generated in dev for convenience.
    SECRET_KEY: str = ""

    # CORS - explicit allowlist. Wildcard is rejected in production.
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = []

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000

    # DB Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "antarctic_nav"
    POSTGRES_PORT: int = 5432
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # Redis / Celery
    REDIS_URI: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Trust proxy headers (X-Forwarded-Proto etc.) when running behind a reverse proxy.
    TRUST_PROXY_HEADERS: bool = False

    # Allowed hostnames for TrustedHostMiddleware. Comma-separated. Wildcard
    # ("*") is rejected when is_production() is True. Set explicitly per
    # deployment; for local dev, defaults cover localhost.
    TRUSTED_HOSTS: List[str] = []

    # Log level
    LOG_LEVEL: str = "INFO"

    # Forecast / risk engine limits
    RISK_CONFIDENCE_THRESHOLD: float = 0.5

    # External data source timeouts (seconds)
    EXTERNAL_DATA_TIMEOUT: float = 30.0

    @field_validator("ENVIRONMENT")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        normalized = v.lower().strip()
        if normalized not in {"development", "staging", "production", "test"}:
            raise ValueError(
                f"ENVIRONMENT must be one of development|staging|production|test (got {v!r})"
            )
        return normalized

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        # Pydantic Settings v2 parses JSON lists; allow comma-separated strings too.
        if isinstance(v, str) and not v.startswith("["):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def _split_trusted_hosts(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI_SYNC(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def validate_for_environment(self) -> None:
        """
        Enforce production-grade invariants when ENVIRONMENT=production.
        Raises ValueError if the deployment is unsafe.
        """
        if not self.is_production():
            return

        if not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be set in production. Refusing to start with an empty secret."
            )
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production.")
        if not self.BACKEND_CORS_ORIGINS:
            raise ValueError("BACKEND_CORS_ORIGINS must be configured in production.")
        if any(str(o) == "*" for o in self.BACKEND_CORS_ORIGINS):
            raise ValueError(
                "Wildcard CORS origins are forbidden in production. Set explicit allowlist."
            )
        if self.POSTGRES_PASSWORD in {"postgres", "password", "changeme", "admin"}:
            raise ValueError(
                "POSTGRES_PASSWORD is set to a default/weak value. Change it before production."
            )
        if "*" in self.TRUSTED_HOSTS:
            raise ValueError(
                "Wildcard TRUSTED_HOSTS is forbidden in production. Set explicit hosts."
            )
        if not self.TRUSTED_HOSTS:
            # Allow loopback as a sensible default in production when nothing
            # else is configured; deployments behind a domain should override.
            self.TRUSTED_HOSTS = ["localhost", "127.0.0.1"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
    )


def get_or_create_secret_key() -> str:
    """
    Return the configured SECRET_KEY, or auto-generate one if missing in development.
    Production environments must always set this explicitly.
    """
    settings_local = Settings()
    if settings_local.SECRET_KEY:
        return settings_local.SECRET_KEY
    if settings_local.is_production():
        raise RuntimeError(
            "SECRET_KEY missing in production. Refusing to auto-generate."
        )
    logging.getLogger(__name__).warning(
        "SECRET_KEY not set; generating an ephemeral key for development use only."
    )
    return secrets.token_urlsafe(48)


settings = Settings()
