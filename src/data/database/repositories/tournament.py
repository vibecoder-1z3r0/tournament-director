"""Database repository for Tournament entities.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models import TournamentModel
from src.data.exceptions import DuplicateError, NotFoundError
from src.data.interface import TournamentRepository
from src.models.base import TournamentStatus, TournamentVisibility
from src.models.tournament import RegistrationControl, Tournament


class DatabaseTournamentRepository(TournamentRepository):
    """Database implementation of TournamentRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    def _to_pydantic(self, db_tournament: TournamentModel) -> Tournament:
        """Convert database model to Pydantic model."""
        return Tournament(
            id=db_tournament.id,
            name=db_tournament.name,
            status=TournamentStatus(db_tournament.status),
            visibility=TournamentVisibility(db_tournament.visibility),
            registration=RegistrationControl(**db_tournament.registration),
            start_time=db_tournament.start_time,
            end_time=db_tournament.end_time,
            format_id=db_tournament.format_id,
            venue_id=db_tournament.venue_id,
            created_by=db_tournament.created_by,
            created_at=db_tournament.created_at,
            description=db_tournament.description,
            registration_deadline=db_tournament.registration_deadline,
            auto_advance_rounds=db_tournament.auto_advance_rounds,
        )

    async def create(self, tournament: Tournament) -> Tournament:
        """Create a new tournament."""
        # Check for duplicate ID
        existing = await self.session.get(TournamentModel, tournament.id)
        if existing:
            raise DuplicateError("Tournament", "id", str(tournament.id))

        db_tournament = TournamentModel(
            id=tournament.id,
            name=tournament.name,
            status=tournament.status.value,
            visibility=tournament.visibility.value,
            registration=tournament.registration.model_dump(),
            start_time=tournament.start_time,
            end_time=tournament.end_time,
            format_id=tournament.format_id,
            venue_id=tournament.venue_id,
            created_by=tournament.created_by,
            created_at=tournament.created_at,
            description=tournament.description,
            registration_deadline=tournament.registration_deadline,
            auto_advance_rounds=tournament.auto_advance_rounds,
        )

        self.session.add(db_tournament)
        await self.session.flush()

        return tournament

    async def get_by_id(self, tournament_id: UUID) -> Tournament:
        """Get tournament by ID. Raises NotFoundError if not found."""
        db_tournament = await self.session.get(TournamentModel, tournament_id)
        if not db_tournament:
            raise NotFoundError("Tournament", tournament_id)

        return self._to_pydantic(db_tournament)

    async def list_by_status(self, status: str) -> list[Tournament]:
        """List tournaments by status."""
        stmt = select(TournamentModel).where(TournamentModel.status == status)
        result = await self.session.execute(stmt)
        db_tournaments = result.scalars().all()

        return [self._to_pydantic(db_tournament) for db_tournament in db_tournaments]

    async def list_by_venue(self, venue_id: UUID) -> list[Tournament]:
        """List tournaments by venue."""
        stmt = select(TournamentModel).where(TournamentModel.venue_id == venue_id)
        result = await self.session.execute(stmt)
        db_tournaments = result.scalars().all()

        return [self._to_pydantic(db_tournament) for db_tournament in db_tournaments]

    async def list_by_format(self, format_id: UUID) -> list[Tournament]:
        """List tournaments by format."""
        stmt = select(TournamentModel).where(TournamentModel.format_id == format_id)
        result = await self.session.execute(stmt)
        db_tournaments = result.scalars().all()

        return [self._to_pydantic(db_tournament) for db_tournament in db_tournaments]

    async def list_by_organizer(self, organizer_id: UUID) -> list[Tournament]:
        """List tournaments by organizer (created_by)."""
        stmt = select(TournamentModel).where(TournamentModel.created_by == organizer_id)
        result = await self.session.execute(stmt)
        db_tournaments = result.scalars().all()

        return [self._to_pydantic(db_tournament) for db_tournament in db_tournaments]

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Tournament]:
        """List all tournaments with optional pagination."""
        stmt = select(TournamentModel).offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        db_tournaments = result.scalars().all()

        return [self._to_pydantic(db_tournament) for db_tournament in db_tournaments]

    async def update(self, tournament: Tournament) -> Tournament:
        """Update an existing tournament."""
        db_tournament = await self.session.get(TournamentModel, tournament.id)
        if not db_tournament:
            raise NotFoundError("Tournament", tournament.id)

        db_tournament.name = tournament.name
        db_tournament.status = tournament.status.value
        db_tournament.visibility = tournament.visibility.value
        db_tournament.registration = tournament.registration.model_dump()
        db_tournament.start_time = tournament.start_time
        db_tournament.end_time = tournament.end_time
        db_tournament.format_id = tournament.format_id
        db_tournament.venue_id = tournament.venue_id
        db_tournament.created_by = tournament.created_by
        # created_at is immutable
        db_tournament.description = tournament.description
        db_tournament.registration_deadline = tournament.registration_deadline
        db_tournament.auto_advance_rounds = tournament.auto_advance_rounds

        await self.session.flush()

        return tournament

    async def delete(self, tournament_id: UUID) -> None:
        """Delete a tournament. Raises NotFoundError if not found."""
        db_tournament = await self.session.get(TournamentModel, tournament_id)
        if not db_tournament:
            raise NotFoundError("Tournament", tournament_id)

        await self.session.delete(db_tournament)
        await self.session.flush()
