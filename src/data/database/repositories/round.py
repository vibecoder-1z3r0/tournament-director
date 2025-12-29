"""Database repository for Round entities.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models import RoundModel
from src.data.exceptions import DuplicateError, NotFoundError
from src.data.interface import RoundRepository
from src.models.base import RoundStatus
from src.models.match import Round


class DatabaseRoundRepository(RoundRepository):
    """Database implementation of RoundRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    def _to_pydantic(self, db_round: RoundModel) -> Round:
        """Convert database model to Pydantic model."""
        return Round(
            id=db_round.id,
            tournament_id=db_round.tournament_id,
            component_id=db_round.component_id,
            round_number=db_round.round_number,
            start_time=db_round.start_time,
            end_time=db_round.end_time,
            time_limit_minutes=db_round.time_limit_minutes,
            scheduled_start=db_round.scheduled_start,
            scheduled_end=db_round.scheduled_end,
            auto_advance=db_round.auto_advance,
            status=RoundStatus(db_round.status),
        )

    async def create(self, round_obj: Round) -> Round:
        """Create a new round."""
        # Check for duplicate ID
        existing = await self.session.get(RoundModel, round_obj.id)
        if existing:
            raise DuplicateError("Round", "id", str(round_obj.id))

        db_round = RoundModel(
            id=round_obj.id,
            tournament_id=round_obj.tournament_id,
            component_id=round_obj.component_id,
            round_number=round_obj.round_number,
            start_time=round_obj.start_time,
            end_time=round_obj.end_time,
            time_limit_minutes=round_obj.time_limit_minutes,
            scheduled_start=round_obj.scheduled_start,
            scheduled_end=round_obj.scheduled_end,
            auto_advance=round_obj.auto_advance,
            status=round_obj.status.value,
        )

        self.session.add(db_round)
        await self.session.flush()

        return round_obj

    async def get_by_id(self, round_id: UUID) -> Round:
        """Get round by ID. Raises NotFoundError if not found."""
        db_round = await self.session.get(RoundModel, round_id)
        if not db_round:
            raise NotFoundError("Round", round_id)

        return self._to_pydantic(db_round)

    async def list_by_tournament(self, tournament_id: UUID) -> list[Round]:
        """List rounds for a tournament, ordered by component sequence and round number."""
        stmt = (
            select(RoundModel)
            .where(RoundModel.tournament_id == tournament_id)
            .order_by(RoundModel.component_id, RoundModel.round_number)
        )

        result = await self.session.execute(stmt)
        db_rounds = result.scalars().all()

        return [self._to_pydantic(db_round) for db_round in db_rounds]

    async def list_by_component(self, component_id: UUID) -> list[Round]:
        """List rounds for a component, ordered by round number."""
        stmt = (
            select(RoundModel)
            .where(RoundModel.component_id == component_id)
            .order_by(RoundModel.round_number)
        )

        result = await self.session.execute(stmt)
        db_rounds = result.scalars().all()

        return [self._to_pydantic(db_round) for db_round in db_rounds]

    async def get_by_component_and_round_number(
        self, component_id: UUID, round_number: int
    ) -> Round | None:
        """Get round by component and round number. Returns None if not found."""
        stmt = select(RoundModel).where(
            RoundModel.component_id == component_id, RoundModel.round_number == round_number
        )
        result = await self.session.execute(stmt)
        db_round = result.scalar_one_or_none()

        if not db_round:
            return None

        return self._to_pydantic(db_round)

    async def update(self, round_obj: Round) -> Round:
        """Update an existing round."""
        db_round = await self.session.get(RoundModel, round_obj.id)
        if not db_round:
            raise NotFoundError("Round", round_obj.id)

        db_round.start_time = round_obj.start_time
        db_round.end_time = round_obj.end_time
        db_round.time_limit_minutes = round_obj.time_limit_minutes
        db_round.scheduled_start = round_obj.scheduled_start
        db_round.scheduled_end = round_obj.scheduled_end
        db_round.auto_advance = round_obj.auto_advance
        db_round.status = round_obj.status.value
        # Other fields are immutable

        await self.session.flush()

        return round_obj

    async def delete(self, round_id: UUID) -> None:
        """Delete a round. Raises NotFoundError if not found."""
        db_round = await self.session.get(RoundModel, round_id)
        if not db_round:
            raise NotFoundError("Round", round_id)

        await self.session.delete(db_round)
        await self.session.flush()
