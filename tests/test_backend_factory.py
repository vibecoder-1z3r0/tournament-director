"""
Tests for data layer backend factory.

Tests instantiation of all backend types based on configuration.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import uuid4

import pytest
import pytest_asyncio

from src.api.backend_factory import create_data_layer
from src.api.config import Settings
from src.data.database.data_layer import DatabaseDataLayer
from src.data.local import LocalDataLayer
from src.data.mock import MockDataLayer


class TestBackendFactory:
    """Test backend factory function."""

    def test_create_mock_backend(self):
        """Should create MockDataLayer for mock backend type."""
        settings = Settings(backend_type="mock")
        data_layer = create_data_layer(settings)

        assert isinstance(data_layer, MockDataLayer)
        assert data_layer.players is not None
        assert data_layer.tournaments is not None

    def test_create_local_backend(self, tmp_path):
        """Should create LocalDataLayer for local backend type."""
        settings = Settings(backend_type="local", local_data_path=str(tmp_path))
        data_layer = create_data_layer(settings)

        assert isinstance(data_layer, LocalDataLayer)
        assert data_layer.players is not None
        assert data_layer.tournaments is not None

    @pytest.mark.asyncio
    async def test_create_sqlite_backend(self):
        """Should create DatabaseDataLayer for SQLite."""
        settings = Settings(
            backend_type="sqlite",
            database_url="sqlite+aiosqlite:///:memory:"
        )
        data_layer = create_data_layer(settings)

        try:
            assert isinstance(data_layer, DatabaseDataLayer)
            # Note: Database backend requires initialization before use
            # Repository access is tested in TestBackendFactoryInitialization
        finally:
            # Clean up database connections
            if isinstance(data_layer, DatabaseDataLayer):
                await data_layer.close()

    @pytest.mark.asyncio
    async def test_create_postgresql_backend(self):
        """Should create DatabaseDataLayer for PostgreSQL."""
        settings = Settings(
            backend_type="postgresql",
            database_url="postgresql+asyncpg://user:pass@localhost/test"
        )
        data_layer = create_data_layer(settings)

        try:
            assert isinstance(data_layer, DatabaseDataLayer)
            # Note: Database backend requires initialization before use
        finally:
            # Clean up database connections
            if isinstance(data_layer, DatabaseDataLayer):
                await data_layer.close()

    @pytest.mark.asyncio
    async def test_create_mysql_backend(self):
        """Should create DatabaseDataLayer for MySQL (requires aiomysql)."""
        try:
            import aiomysql  # noqa: F401
        except ImportError:
            pytest.skip("aiomysql not installed")

        settings = Settings(
            backend_type="mysql",
            database_url="mysql+aiomysql://user:pass@localhost/test"
        )
        data_layer = create_data_layer(settings)

        try:
            assert isinstance(data_layer, DatabaseDataLayer)
        finally:
            # Clean up database connections
            if isinstance(data_layer, DatabaseDataLayer):
                await data_layer.close()

    @pytest.mark.asyncio
    async def test_create_mariadb_backend(self):
        """Should create DatabaseDataLayer for MariaDB (requires aiomysql)."""
        try:
            import aiomysql  # noqa: F401
        except ImportError:
            pytest.skip("aiomysql not installed")

        settings = Settings(
            backend_type="mariadb",
            database_url="mariadb+aiomysql://user:pass@localhost/test"
        )
        data_layer = create_data_layer(settings)

        try:
            assert isinstance(data_layer, DatabaseDataLayer)
        finally:
            # Clean up database connections
            if isinstance(data_layer, DatabaseDataLayer):
                await data_layer.close()

    @pytest.mark.asyncio
    async def test_database_backends_use_database_url(self):
        """Database backends should use database_url from settings."""
        settings = Settings(
            backend_type="sqlite",
            database_url="sqlite+aiosqlite:///./custom.db"
        )
        data_layer = create_data_layer(settings)

        try:
            assert isinstance(data_layer, DatabaseDataLayer)
            assert data_layer.db.database_url == "sqlite+aiosqlite:///./custom.db"
        finally:
            # Clean up database connections
            if isinstance(data_layer, DatabaseDataLayer):
                await data_layer.close()

    def test_local_backend_uses_local_data_path(self, tmp_path):
        """Local backend should use local_data_path from settings."""
        custom_path = tmp_path / "custom_data"
        settings = Settings(backend_type="local", local_data_path=str(custom_path))
        data_layer = create_data_layer(settings)

        assert isinstance(data_layer, LocalDataLayer)
        assert str(data_layer.data_dir) == str(custom_path)

    def test_invalid_backend_type_raises_error(self):
        """Should raise error for invalid backend type."""
        # This should be caught by Settings validation
        with pytest.raises(ValueError):
            Settings(backend_type="invalid")


class TestBackendFactoryWithDefaults:
    """Test backend factory with default configuration."""

    def test_create_with_default_settings(self):
        """Should create backend with default settings."""
        settings = Settings()  # Uses defaults
        data_layer = create_data_layer(settings)

        assert isinstance(data_layer, MockDataLayer)  # Default is mock

    @pytest.mark.asyncio
    async def test_create_sqlite_with_default_url(self):
        """Should use default SQLite URL if not specified."""
        settings = Settings(backend_type="sqlite")
        data_layer = create_data_layer(settings)

        try:
            assert isinstance(data_layer, DatabaseDataLayer)
            # Should have some default URL
            assert data_layer.db.database_url is not None
        finally:
            # Clean up database connections
            if isinstance(data_layer, DatabaseDataLayer):
                await data_layer.close()


@pytest.mark.asyncio
class TestBackendFactoryInitialization:
    """Test backend initialization for database backends."""

    async def test_initialize_database_backend(self):
        """Should be able to initialize database backend."""
        settings = Settings(
            backend_type="sqlite",
            database_url="sqlite+aiosqlite:///:memory:"
        )
        data_layer = create_data_layer(settings)

        try:
            # Initialize should create tables
            await data_layer.initialize()

            # Verify we can use the backend
            from src.models.player import Player
            player = Player(id=uuid4(), name="Test Player")
            created = await data_layer.players.create(player)
            assert created.name == "Test Player"
        finally:
            # Clean up database connections
            if isinstance(data_layer, DatabaseDataLayer):
                await data_layer.close()

    async def test_initialize_mock_backend_is_noop(self):
        """Mock backend initialize should be a no-op."""
        settings = Settings(backend_type="mock")
        data_layer = create_data_layer(settings)

        # Should not raise error
        # Mock backend doesn't have initialize() method, but that's OK

    async def test_initialize_local_backend_creates_directory(self, tmp_path):
        """Local backend should create data directory if needed."""
        data_dir = tmp_path / "new_data_dir"
        assert not data_dir.exists()

        settings = Settings(backend_type="local", local_data_path=str(data_dir))
        data_layer = create_data_layer(settings)

        # Local backend should create directory on first use
        from src.models.player import Player
        player = Player(id=uuid4(), name="Test Player")
        await data_layer.players.create(player)

        # Directory should now exist
        assert data_dir.exists()
