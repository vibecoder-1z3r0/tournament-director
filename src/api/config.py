"""
API configuration settings.

Supports loading from:
1. CLI arguments (highest priority)
2. Environment variables (prefix: TD_)
3. Config file (TOML)
4. Defaults (lowest priority)

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from pathlib import Path
from typing import Any, Literal

import toml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration for FastAPI application.

    Supports multiple backend types and configuration sources.
    Environment variables use TD_ prefix (e.g., TD_BACKEND_TYPE).
    """

    model_config = SettingsConfigDict(
        env_prefix="TD_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    title: str = "Tournament Director API"
    version: str = "0.1.0"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"  # noqa: S104  # Intentional - API server binding
    port: int = Field(default=8000, ge=1, le=65535)
    reload: bool = True

    # CORS
    cors_origins: list[str] = Field(default=["*"])
    cors_allow_credentials: bool = True

    # Data Layer Backend Type
    backend_type: Literal["mock", "local", "sqlite", "postgresql", "mysql", "mariadb"] = "mock"

    # Local Backend Configuration
    local_data_path: str = "./data"

    # Database Backend Configuration
    database_url: str = "sqlite+aiosqlite:///./tournament.db"

    # Pagination
    default_page_size: int = Field(default=20, ge=1)
    max_page_size: int = Field(default=100, ge=1)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            # Split comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return [str(v)]  # Convert single value to list

    @field_validator("backend_type")
    @classmethod
    def validate_backend_type(cls, v: str) -> str:
        """Validate backend type."""
        valid_backends = {"mock", "local", "sqlite", "postgresql", "mysql", "mariadb"}
        if v not in valid_backends:
            raise ValueError(
                f"Invalid backend_type: {v}. Must be one of: {', '.join(sorted(valid_backends))}"
            )
        return v


def load_settings(
    config_file: str | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> Settings:
    """
    Load settings from multiple sources with priority order.

    Priority (highest to lowest):
    1. CLI arguments (cli_overrides parameter)
    2. Environment variables (TD_* prefix)
    3. Config file (TOML)
    4. Defaults

    Args:
        config_file: Path to TOML config file (optional)
        cli_overrides: Dictionary of CLI argument overrides (optional)

    Returns:
        Settings instance with configuration loaded

    Example:
        # Load with all sources
        settings = load_settings(
            config_file="config.toml",
            cli_overrides={"backend_type": "postgresql", "port": 9000}
        )

        # Load with defaults and env vars only
        settings = load_settings()

        # Load from config file only
        settings = load_settings(config_file="production.toml")
    """
    # Build configuration dict with proper priority
    config_data: dict[str, Any] = {}

    # 1. Load from config file (priority 3 - above defaults, below env and CLI)
    if config_file and Path(config_file).exists():
        try:
            with open(config_file) as f:
                file_data = toml.load(f)
                config_data.update(file_data)
        except Exception as e:
            raise ValueError(f"Failed to load config file {config_file}: {e}") from e

    # 2. Load from environment variables (priority 2 - below CLI, above file and defaults)
    import os
    env_mapping = {
        "TD_BACKEND_TYPE": "backend_type",
        "TD_DATABASE_URL": "database_url",
        "TD_LOCAL_DATA_PATH": "local_data_path",
        "TD_PORT": "port",
        "TD_DEBUG": "debug",
        "TD_CORS_ORIGINS": "cors_origins",
        "TD_CORS_ALLOW_CREDENTIALS": "cors_allow_credentials",
        "TD_HOST": "host",
        "TD_RELOAD": "reload",
        "TD_TITLE": "title",
        "TD_VERSION": "version",
        "TD_DEFAULT_PAGE_SIZE": "default_page_size",
        "TD_MAX_PAGE_SIZE": "max_page_size",
    }

    for env_var, field_name in env_mapping.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            # Convert string values to appropriate types
            if field_name in ("port", "default_page_size", "max_page_size"):
                config_data[field_name] = int(env_value)
            elif field_name in ("debug", "reload", "cors_allow_credentials"):
                config_data[field_name] = env_value.lower() in ("true", "1", "yes")
            elif field_name == "cors_origins":
                # Handle comma-separated list
                config_data[field_name] = [o.strip() for o in env_value.split(",") if o.strip()]
            else:
                config_data[field_name] = env_value

    # 3. Apply CLI overrides (priority 1 - highest)
    if cli_overrides:
        config_data.update(cli_overrides)

    # Create Settings instance
    # Use model_validate to create instance with our config_data without triggering
    # pydantic-settings automatic env var loading (since we handled it manually)
    if config_data:
        # Use model_construct to bypass pydantic-settings env loading
        # Pydantic will fill in defaults for missing fields
        instance = Settings.model_construct(**config_data)
        # Validate the instance
        Settings.model_validate(instance)
        return instance
    else:
        # No overrides, use defaults only (will load from env automatically)
        return Settings()


# Global config instance (uses defaults + env vars)
config = Settings()
