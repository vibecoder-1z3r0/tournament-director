"""
Dependency injection for FastAPI endpoints.

Provides shared resources like data layer instances for API endpoints.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from typing import Annotated

from fastapi import Depends

from src.api.backend_factory import create_data_layer
from src.api.config import config
from src.data.interface import DataLayer

# Singleton data layer instance
_data_layer: DataLayer | None = None


def get_data_layer() -> DataLayer:
    """
    Get data layer instance (singleton).

    Returns the configured data layer backend based on configuration.
    Supports mock, local (JSON), and database (SQLite, PostgreSQL, MySQL, MariaDB) backends.

    The backend is determined by the backend_type configuration setting, which can be set via:
    - Environment variable: TD_BACKEND_TYPE
    - Config file (TOML)
    - CLI arguments (when using CLI tool)
    - Default: "mock"

    Creates the instance on first call and reuses it for subsequent calls.
    """
    global _data_layer

    if _data_layer is None:
        _data_layer = create_data_layer(config)

    return _data_layer


# Type alias for dependency injection
DataLayerDep = Annotated[DataLayer, Depends(get_data_layer)]


# Pagination dependencies
def get_pagination_params(
    limit: int = config.default_page_size,
    offset: int = 0,
) -> dict[str, int]:
    """
    Get pagination parameters with validation.

    Args:
        limit: Maximum number of items to return (default: 20, max: 100)
        offset: Number of items to skip (default: 0)

    Returns:
        Dictionary with validated limit and offset
    """
    # Validate and cap limit
    limit = min(limit, config.max_page_size)
    limit = max(limit, 1)

    # Validate offset
    offset = max(offset, 0)

    return {"limit": limit, "offset": offset}


PaginationDep = Annotated[dict[str, int], Depends(get_pagination_params)]
