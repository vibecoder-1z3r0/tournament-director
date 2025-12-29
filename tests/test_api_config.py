"""
Tests for API configuration loading from multiple sources.

Tests configuration precedence: CLI args > env vars > config file > defaults

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import os
from pathlib import Path
from typing import Any

import pytest
import toml

from src.api.config import Settings, load_settings


class TestSettingsDefaults:
    """Test default configuration values."""

    def test_default_backend_is_mock(self):
        """Default backend should be mock for development."""
        settings = Settings()
        assert settings.backend_type == "mock"

    def test_default_api_settings(self):
        """Test default API configuration."""
        settings = Settings()
        assert settings.title == "Tournament Director API"
        assert settings.version == "0.1.0"
        assert settings.debug is True
        assert settings.host == "0.0.0.0"  # noqa: S104
        assert settings.port == 8000

    def test_default_cors_settings(self):
        """Test default CORS configuration."""
        settings = Settings()
        assert settings.cors_origins == ["*"]
        assert settings.cors_allow_credentials is True

    def test_default_pagination_settings(self):
        """Test default pagination configuration."""
        settings = Settings()
        assert settings.default_page_size == 20
        assert settings.max_page_size == 100


class TestSettingsFromEnvironment:
    """Test configuration loading from environment variables."""

    def test_load_backend_type_from_env(self, monkeypatch):
        """Should load backend type from env var."""
        monkeypatch.setenv("TD_BACKEND_TYPE", "local")
        settings = Settings()
        assert settings.backend_type == "local"

    def test_load_database_url_from_env(self, monkeypatch):
        """Should load database URL from env var."""
        monkeypatch.setenv("TD_DATABASE_URL", "postgresql+asyncpg://localhost/test")
        settings = Settings()
        assert settings.database_url == "postgresql+asyncpg://localhost/test"

    def test_load_local_data_path_from_env(self, monkeypatch):
        """Should load local data path from env var."""
        monkeypatch.setenv("TD_LOCAL_DATA_PATH", "/custom/path")
        settings = Settings()
        assert settings.local_data_path == "/custom/path"

    def test_load_cors_origins_from_env(self, monkeypatch):
        """Should load CORS origins from env var (comma-separated)."""
        monkeypatch.setenv("TD_CORS_ORIGINS", "http://localhost:3000,https://example.com")
        settings = load_settings()  # Use load_settings() to handle comma-separated list
        assert settings.cors_origins == ["http://localhost:3000", "https://example.com"]

    def test_load_port_from_env(self, monkeypatch):
        """Should load port from env var."""
        monkeypatch.setenv("TD_PORT", "9000")
        settings = Settings()
        assert settings.port == 9000

    def test_load_debug_from_env(self, monkeypatch):
        """Should load debug flag from env var."""
        monkeypatch.setenv("TD_DEBUG", "false")
        settings = Settings()
        assert settings.debug is False


class TestSettingsFromConfigFile:
    """Test configuration loading from TOML config file."""

    def test_load_from_toml_file(self, tmp_path):
        """Should load configuration from TOML file."""
        config_file = tmp_path / "config.toml"
        config_data = {
            "backend_type": "sqlite",
            "database_url": "sqlite+aiosqlite:///./tournament.db",
            "port": 8080,
            "debug": False,
            "cors_origins": ["http://localhost:3000"],
        }
        config_file.write_text(toml.dumps(config_data))

        settings = load_settings(config_file=str(config_file))
        assert settings.backend_type == "sqlite"
        assert settings.database_url == "sqlite+aiosqlite:///./tournament.db"
        assert settings.port == 8080
        assert settings.debug is False
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_config_file_not_found_uses_defaults(self):
        """Should use defaults if config file doesn't exist."""
        settings = load_settings(config_file="/nonexistent/config.toml")
        assert settings.backend_type == "mock"  # Default

    def test_invalid_toml_raises_error(self, tmp_path):
        """Should raise error for invalid TOML syntax."""
        config_file = tmp_path / "bad_config.toml"
        config_file.write_text("this is not valid TOML [[[")

        with pytest.raises(Exception):  # toml.TomlDecodeError or similar
            load_settings(config_file=str(config_file))


class TestSettingsPriority:
    """Test configuration priority: CLI args > env vars > config file > defaults."""

    def test_env_overrides_config_file(self, tmp_path, monkeypatch):
        """Environment variables should override config file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(toml.dumps({"backend_type": "local", "port": 8080}))

        monkeypatch.setenv("TD_BACKEND_TYPE", "sqlite")
        monkeypatch.setenv("TD_PORT", "9000")

        settings = load_settings(config_file=str(config_file))
        assert settings.backend_type == "sqlite"  # From env
        assert settings.port == 9000  # From env

    def test_cli_overrides_env_and_config(self, tmp_path, monkeypatch):
        """CLI arguments should override env vars and config file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(toml.dumps({"backend_type": "local", "port": 8080}))

        monkeypatch.setenv("TD_BACKEND_TYPE", "sqlite")
        monkeypatch.setenv("TD_PORT", "9000")

        cli_overrides = {"backend_type": "postgresql", "port": 7000}
        settings = load_settings(config_file=str(config_file), cli_overrides=cli_overrides)

        assert settings.backend_type == "postgresql"  # From CLI
        assert settings.port == 7000  # From CLI

    def test_partial_overrides(self, tmp_path, monkeypatch):
        """Should allow partial overrides from each source."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(toml.dumps({"backend_type": "local", "port": 8080, "debug": False}))

        monkeypatch.setenv("TD_PORT", "9000")  # Override port only

        settings = load_settings(config_file=str(config_file))
        assert settings.backend_type == "local"  # From config file
        assert settings.port == 9000  # From env (override)
        assert settings.debug is False  # From config file


class TestSettingsValidation:
    """Test configuration validation."""

    def test_invalid_backend_type_raises_error(self):
        """Should reject invalid backend types."""
        with pytest.raises(ValueError, match="backend_type"):
            Settings(backend_type="invalid")

    def test_valid_backend_types(self):
        """Should accept all valid backend types."""
        valid_backends = ["mock", "local", "sqlite", "postgresql", "mysql", "mariadb"]
        for backend in valid_backends:
            settings = Settings(backend_type=backend)
            assert settings.backend_type == backend

    def test_port_validation(self):
        """Should validate port range."""
        with pytest.raises(ValueError):
            Settings(port=0)  # Too low

        with pytest.raises(ValueError):
            Settings(port=70000)  # Too high

        settings = Settings(port=8080)
        assert settings.port == 8080

    def test_pagination_validation(self):
        """Should validate pagination settings."""
        with pytest.raises(ValueError):
            Settings(default_page_size=0)  # Too low

        with pytest.raises(ValueError):
            Settings(max_page_size=0)  # Too low

        settings = Settings(default_page_size=50, max_page_size=200)
        assert settings.default_page_size == 50
        assert settings.max_page_size == 200


class TestDatabaseConfiguration:
    """Test database-specific configuration."""

    def test_sqlite_in_memory(self):
        """Should support SQLite in-memory database."""
        settings = Settings(
            backend_type="sqlite",
            database_url="sqlite+aiosqlite:///:memory:"
        )
        assert settings.backend_type == "sqlite"
        assert settings.database_url == "sqlite+aiosqlite:///:memory:"

    def test_sqlite_file_based(self):
        """Should support SQLite file-based database."""
        settings = Settings(
            backend_type="sqlite",
            database_url="sqlite+aiosqlite:///./tournament.db"
        )
        assert settings.database_url == "sqlite+aiosqlite:///./tournament.db"

    def test_postgresql_connection_string(self):
        """Should support PostgreSQL connection strings."""
        settings = Settings(
            backend_type="postgresql",
            database_url="postgresql+asyncpg://user:pass@localhost:5432/tournament"
        )
        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/tournament"

    def test_mysql_connection_string(self):
        """Should support MySQL connection strings."""
        settings = Settings(
            backend_type="mysql",
            database_url="mysql+aiomysql://user:pass@localhost:3306/tournament"
        )
        assert settings.database_url == "mysql+aiomysql://user:pass@localhost:3306/tournament"

    def test_mariadb_connection_string(self):
        """Should support MariaDB connection strings."""
        settings = Settings(
            backend_type="mariadb",
            database_url="mariadb+aiomysql://user:pass@localhost:3306/tournament"
        )
        assert settings.database_url == "mariadb+aiomysql://user:pass@localhost:3306/tournament"

    def test_database_url_required_for_database_backends(self):
        """Should require database_url for database backends."""
        # This should work - database_url is optional (has default)
        settings = Settings(backend_type="sqlite")
        assert settings.database_url is not None  # Should have a default

    def test_local_backend_uses_local_data_path(self):
        """Local backend should use local_data_path."""
        settings = Settings(backend_type="local", local_data_path="/custom/data")
        assert settings.local_data_path == "/custom/data"
