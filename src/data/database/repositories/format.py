"""Database repository for Format entities.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models import FormatModel
from src.data.exceptions import DuplicateError, NotFoundError
from src.data.interface import FormatRepository
from src.models.base import BaseFormat, GameSystem
from src.models.format import Format


class DatabaseFormatRepository(FormatRepository):
    """Database implementation of FormatRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, format_obj: Format) -> Format:
        """Create a new format."""
        # Check for duplicate ID
        existing = await self.session.get(FormatModel, format_obj.id)
        if existing:
            raise DuplicateError("Format", "id", str(format_obj.id))

        db_format = FormatModel(
            id=format_obj.id,
            name=format_obj.name,
            game_system=format_obj.game_system.value,
            base_format=format_obj.base_format.value,
            sub_format=format_obj.sub_format,
            card_pool=format_obj.card_pool,
            match_structure=format_obj.match_structure,
            description=format_obj.description,
        )

        self.session.add(db_format)
        await self.session.flush()

        return format_obj

    async def get_by_id(self, format_id: UUID) -> Format:
        """Get format by ID. Raises NotFoundError if not found."""
        db_format = await self.session.get(FormatModel, format_id)
        if not db_format:
            raise NotFoundError("Format", format_id)

        return Format(
            id=db_format.id,
            name=db_format.name,
            game_system=GameSystem(db_format.game_system),
            base_format=BaseFormat(db_format.base_format),
            sub_format=db_format.sub_format,
            card_pool=db_format.card_pool,
            match_structure=db_format.match_structure,
            description=db_format.description,
        )

    async def get_by_name(self, name: str, game_system: str | None = None) -> Format | None:
        """Get format by name and optionally game system. Returns None if not found."""
        stmt = select(FormatModel).where(FormatModel.name == name)
        if game_system:
            stmt = stmt.where(FormatModel.game_system == game_system)

        result = await self.session.execute(stmt)
        db_format = result.scalar_one_or_none()

        if not db_format:
            return None

        return Format(
            id=db_format.id,
            name=db_format.name,
            game_system=GameSystem(db_format.game_system),
            base_format=BaseFormat(db_format.base_format),
            sub_format=db_format.sub_format,
            card_pool=db_format.card_pool,
            match_structure=db_format.match_structure,
            description=db_format.description,
        )

    async def list_by_game_system(self, game_system: str) -> list[Format]:
        """List all formats for a specific game system."""
        stmt = select(FormatModel).where(FormatModel.game_system == game_system)
        result = await self.session.execute(stmt)
        db_formats = result.scalars().all()

        return [
            Format(
                id=db_format.id,
                name=db_format.name,
                game_system=GameSystem(db_format.game_system),
                base_format=BaseFormat(db_format.base_format),
                sub_format=db_format.sub_format,
                card_pool=db_format.card_pool,
                match_structure=db_format.match_structure,
                description=db_format.description,
            )
            for db_format in db_formats
        ]

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Format]:
        """List all formats with optional pagination."""
        stmt = select(FormatModel).offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        db_formats = result.scalars().all()

        return [
            Format(
                id=db_format.id,
                name=db_format.name,
                game_system=GameSystem(db_format.game_system),
                base_format=BaseFormat(db_format.base_format),
                sub_format=db_format.sub_format,
                card_pool=db_format.card_pool,
                match_structure=db_format.match_structure,
                description=db_format.description,
            )
            for db_format in db_formats
        ]

    async def update(self, format_obj: Format) -> Format:
        """Update an existing format."""
        db_format = await self.session.get(FormatModel, format_obj.id)
        if not db_format:
            raise NotFoundError("Format", format_obj.id)

        db_format.name = format_obj.name
        db_format.game_system = format_obj.game_system.value
        db_format.base_format = format_obj.base_format.value
        db_format.sub_format = format_obj.sub_format
        db_format.card_pool = format_obj.card_pool
        db_format.match_structure = format_obj.match_structure
        db_format.description = format_obj.description

        await self.session.flush()

        return format_obj

    async def delete(self, format_id: UUID) -> None:
        """Delete a format. Raises NotFoundError if not found."""
        db_format = await self.session.get(FormatModel, format_id)
        if not db_format:
            raise NotFoundError("Format", format_id)

        await self.session.delete(db_format)
        await self.session.flush()
