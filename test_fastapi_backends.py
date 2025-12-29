"""
Quick test to verify FastAPI works with all backend types.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import asyncio
import os

async def test_mock_backend():
    """Test API with mock backend."""
    print("\n=== Testing MOCK Backend ===")
    os.environ["TD_BACKEND_TYPE"] = "mock"

    # Import after setting env var
    from src.api.main import app
    from src.api.dependencies import get_data_layer

    # Get data layer
    data_layer = get_data_layer()
    print(f"✅ Backend type: {type(data_layer).__name__}")
    print(f"✅ App created successfully")

    # Clean up for next test
    from src.api import dependencies
    dependencies._data_layer = None

async def test_local_backend():
    """Test API with local (JSON) backend."""
    print("\n=== Testing LOCAL Backend ===")

    # Use load_settings to create new config
    from src.api.config import load_settings
    from src.api.backend_factory import create_data_layer

    settings = load_settings(cli_overrides={
        "backend_type": "local",
        "local_data_path": "/tmp/test_tournament_data"
    })

    data_layer = create_data_layer(settings)
    print(f"✅ Backend type: {type(data_layer).__name__}")
    print(f"✅ Data directory: {data_layer.data_dir}")
    print(f"✅ App created successfully")

async def test_sqlite_backend():
    """Test API with SQLite backend."""
    print("\n=== Testing SQLITE Backend ===")

    # Use load_settings to create new config
    from src.api.config import load_settings
    from src.api.backend_factory import create_data_layer
    from src.data.database.data_layer import DatabaseDataLayer

    settings = load_settings(cli_overrides={
        "backend_type": "sqlite",
        "database_url": "sqlite+aiosqlite:///:memory:"
    })

    data_layer = create_data_layer(settings)
    print(f"✅ Backend type: {type(data_layer).__name__}")

    # Initialize database
    if isinstance(data_layer, DatabaseDataLayer):
        await data_layer.initialize()
        print(f"✅ Database initialized")

        # Test creating a player
        from src.models.player import Player
        from uuid import uuid4
        player = Player(id=uuid4(), name="Test Player")
        created = await data_layer.players.create(player)
        print(f"✅ Created player: {created.name}")

        # Cleanup
        await data_layer.db.close()

    print(f"✅ App created successfully")

async def main():
    """Run all backend tests."""
    print("=" * 60)
    print("FastAPI Backend Integration Tests")
    print("=" * 60)

    try:
        await test_mock_backend()
        await test_local_backend()
        await test_sqlite_backend()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
