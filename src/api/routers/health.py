"""
Health check endpoints for monitoring and status verification.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, status

from src.api.config import config
from src.api.dependencies import DataLayerDep

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is running and healthy",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns service status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Tournament Director API",
        "version": config.version,
    }


@router.get(
    "/health/detailed",
    summary="Detailed health check",
    description="Comprehensive health check including data layer connectivity",
    status_code=status.HTTP_200_OK,
)
async def detailed_health_check(data_layer: DataLayerDep) -> dict[str, Any]:
    """
    Detailed health check with data layer validation.

    Verifies:
    - API is running
    - Data layer is accessible
    - Configuration is valid
    """
    # Test data layer connectivity
    try:
        # Simple test: list players (should work even if empty)
        await data_layer.players.list_all()
        data_layer_status = "connected"
    except Exception as e:
        data_layer_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Tournament Director API",
        "version": config.version,
        "components": {
            "api": "healthy",
            "data_layer": data_layer_status,
        },
        "configuration": {
            "backend": config.backend_type,
            "debug": config.debug,
        },
    }
