"""
Backend factory for creating data layer instances.

Creates the appropriate DataLayer backend based on configuration.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from src.api.config import Settings
from src.data.database.data_layer import DatabaseDataLayer
from src.data.interface import DataLayer
from src.data.local import LocalDataLayer
from src.data.mock import MockDataLayer


def create_data_layer(settings: Settings) -> DataLayer:
    """
    Create data layer instance based on settings.

    Instantiates the appropriate backend (Mock, Local, or Database)
    based on the backend_type configuration.

    Args:
        settings: Application settings with backend configuration

    Returns:
        DataLayer instance of the appropriate type

    Raises:
        ValueError: If backend_type is not recognized

    Example:
        # Create mock backend
        settings = Settings(backend_type="mock")
        data_layer = create_data_layer(settings)

        # Create local JSON backend
        settings = Settings(backend_type="local", local_data_path="./data")
        data_layer = create_data_layer(settings)

        # Create SQLite database backend
        settings = Settings(
            backend_type="sqlite",
            database_url="sqlite+aiosqlite:///./tournament.db"
        )
        data_layer = create_data_layer(settings)

        # Create PostgreSQL backend
        settings = Settings(
            backend_type="postgresql",
            database_url="postgresql+asyncpg://user:pass@localhost/tournament"
        )
        data_layer = create_data_layer(settings)
    """
    backend_type = settings.backend_type

    # Mock backend - in-memory storage
    if backend_type == "mock":
        return MockDataLayer()

    # Local backend - JSON file storage
    elif backend_type == "local":
        return LocalDataLayer(settings.local_data_path)

    # Database backends - SQLAlchemy with async drivers
    elif backend_type in ("sqlite", "postgresql", "mysql", "mariadb"):
        return DatabaseDataLayer(settings.database_url)

    # Should never reach here due to Settings validation
    else:
        raise ValueError(
            f"Unknown backend type: {backend_type}. "
            f"Valid options: mock, local, sqlite, postgresql, mysql, mariadb"
        )
