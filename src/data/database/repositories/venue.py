"""Database repository for Venue entities.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models import VenueModel
from src.data.exceptions import DuplicateError, NotFoundError
from src.data.interface import VenueRepository
from src.models.venue import Venue


class DatabaseVenueRepository(VenueRepository):
    """Database implementation of VenueRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, venue: Venue) -> Venue:
        """Create a new venue."""
        # Check for duplicate ID
        existing = await self.session.get(VenueModel, venue.id)
        if existing:
            raise DuplicateError("Venue", "id", str(venue.id))

        db_venue = VenueModel(
            id=venue.id,
            name=venue.name,
            address=venue.address,
            description=venue.description,
        )

        self.session.add(db_venue)
        await self.session.flush()

        return venue

    async def get_by_id(self, venue_id: UUID) -> Venue:
        """Get venue by ID. Raises NotFoundError if not found."""
        db_venue = await self.session.get(VenueModel, venue_id)
        if not db_venue:
            raise NotFoundError("Venue", venue_id)

        return Venue(
            id=db_venue.id,
            name=db_venue.name,
            address=db_venue.address,
            description=db_venue.description,
        )

    async def get_by_name(self, name: str) -> Venue | None:
        """Get venue by name. Returns None if not found."""
        stmt = select(VenueModel).where(VenueModel.name == name)
        result = await self.session.execute(stmt)
        db_venue = result.scalar_one_or_none()

        if not db_venue:
            return None

        return Venue(
            id=db_venue.id,
            name=db_venue.name,
            address=db_venue.address,
            description=db_venue.description,
        )

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Venue]:
        """List all venues with optional pagination."""
        stmt = select(VenueModel).offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        db_venues = result.scalars().all()

        return [
            Venue(
                id=db_venue.id,
                name=db_venue.name,
                address=db_venue.address,
                description=db_venue.description,
            )
            for db_venue in db_venues
        ]

    async def update(self, venue: Venue) -> Venue:
        """Update an existing venue."""
        db_venue = await self.session.get(VenueModel, venue.id)
        if not db_venue:
            raise NotFoundError("Venue", venue.id)

        db_venue.name = venue.name
        db_venue.address = venue.address
        db_venue.description = venue.description

        await self.session.flush()

        return venue

    async def delete(self, venue_id: UUID) -> None:
        """Delete a venue. Raises NotFoundError if not found."""
        db_venue = await self.session.get(VenueModel, venue_id)
        if not db_venue:
            raise NotFoundError("Venue", venue_id)

        await self.session.delete(db_venue)
        await self.session.flush()
