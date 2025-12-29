"""Database repository for TournamentRegistration entities.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models import TournamentRegistrationModel
from src.data.exceptions import DuplicateError, NotFoundError
from src.data.interface import RegistrationRepository
from src.models.base import PlayerStatus
from src.models.tournament import TournamentRegistration


class DatabaseRegistrationRepository(RegistrationRepository):
    """Database implementation of RegistrationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    def _to_pydantic(self, db_reg: TournamentRegistrationModel) -> TournamentRegistration:
        """Convert database model to Pydantic model."""
        return TournamentRegistration(
            id=db_reg.id,
            tournament_id=db_reg.tournament_id,
            player_id=db_reg.player_id,
            sequence_id=db_reg.sequence_id,
            status=PlayerStatus(db_reg.status),
            registration_time=db_reg.registration_time,
            drop_time=db_reg.drop_time,
            notes=db_reg.notes,
        )

    async def create(self, registration: TournamentRegistration) -> TournamentRegistration:
        """Create a new tournament registration."""
        # Check for duplicate ID
        existing = await self.session.get(TournamentRegistrationModel, registration.id)
        if existing:
            raise DuplicateError("TournamentRegistration", "id", registration.id)

        # Check for duplicate player in tournament
        stmt = select(TournamentRegistrationModel).where(
            TournamentRegistrationModel.tournament_id == registration.tournament_id,
            TournamentRegistrationModel.player_id == registration.player_id,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise DuplicateError(
                "TournamentRegistration",
                "player_id",
                f"{registration.player_id} in tournament {registration.tournament_id}",
            )

        db_reg = TournamentRegistrationModel(
            id=registration.id,
            tournament_id=registration.tournament_id,
            player_id=registration.player_id,
            sequence_id=registration.sequence_id,
            status=registration.status.value,
            registration_time=registration.registration_time,
            drop_time=registration.drop_time,
            notes=registration.notes,
        )

        self.session.add(db_reg)
        await self.session.flush()

        return registration

    async def get_by_id(self, registration_id: UUID) -> TournamentRegistration:
        """Get registration by ID. Raises NotFoundError if not found."""
        db_reg = await self.session.get(TournamentRegistrationModel, registration_id)
        if not db_reg:
            raise NotFoundError("Registration", registration_id)

        return self._to_pydantic(db_reg)

    async def get_by_tournament_and_player(
        self, tournament_id: UUID, player_id: UUID
    ) -> TournamentRegistration | None:
        """Get registration by tournament and player. Returns None if not found."""
        stmt = select(TournamentRegistrationModel).where(
            TournamentRegistrationModel.tournament_id == tournament_id,
            TournamentRegistrationModel.player_id == player_id,
        )
        result = await self.session.execute(stmt)
        db_reg = result.scalar_one_or_none()

        if not db_reg:
            return None

        return self._to_pydantic(db_reg)

    async def get_by_tournament_and_sequence_id(
        self, tournament_id: UUID, sequence_id: int
    ) -> TournamentRegistration | None:
        """Get registration by tournament and sequence ID. Returns None if not found."""
        stmt = select(TournamentRegistrationModel).where(
            TournamentRegistrationModel.tournament_id == tournament_id,
            TournamentRegistrationModel.sequence_id == sequence_id,
        )
        result = await self.session.execute(stmt)
        db_reg = result.scalar_one_or_none()

        if not db_reg:
            return None

        return self._to_pydantic(db_reg)

    async def list_by_tournament(
        self, tournament_id: UUID, status: str | None = None
    ) -> list[TournamentRegistration]:
        """List registrations for a tournament, optionally filtered by status."""
        stmt = select(TournamentRegistrationModel).where(
            TournamentRegistrationModel.tournament_id == tournament_id
        )
        if status:
            stmt = stmt.where(TournamentRegistrationModel.status == status)

        result = await self.session.execute(stmt)
        db_regs = result.scalars().all()

        return [self._to_pydantic(db_reg) for db_reg in db_regs]

    async def list_by_player(
        self, player_id: UUID, status: str | None = None
    ) -> list[TournamentRegistration]:
        """List registrations for a player, optionally filtered by status."""
        stmt = select(TournamentRegistrationModel).where(
            TournamentRegistrationModel.player_id == player_id
        )
        if status:
            stmt = stmt.where(TournamentRegistrationModel.status == status)

        result = await self.session.execute(stmt)
        db_regs = result.scalars().all()

        return [self._to_pydantic(db_reg) for db_reg in db_regs]

    async def get_next_sequence_id(self, tournament_id: UUID) -> int:
        """Get the next available sequence ID for a tournament."""
        stmt = select(func.max(TournamentRegistrationModel.sequence_id)).where(
            TournamentRegistrationModel.tournament_id == tournament_id
        )
        result = await self.session.execute(stmt)
        max_sequence = result.scalar_one_or_none()

        return (max_sequence or 0) + 1

    async def update(self, registration: TournamentRegistration) -> TournamentRegistration:
        """Update an existing registration."""
        db_reg = await self.session.get(TournamentRegistrationModel, registration.id)
        if not db_reg:
            raise NotFoundError("Registration", registration.id)

        db_reg.status = registration.status.value
        db_reg.drop_time = registration.drop_time
        db_reg.notes = registration.notes
        # Other fields are immutable

        await self.session.flush()

        return registration

    async def delete(self, registration_id: UUID) -> None:
        """Delete a registration. Raises NotFoundError if not found."""
        db_reg = await self.session.get(TournamentRegistrationModel, registration_id)
        if not db_reg:
            raise NotFoundError("Registration", registration_id)

        await self.session.delete(db_reg)
        await self.session.flush()
