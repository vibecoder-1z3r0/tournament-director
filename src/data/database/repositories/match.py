"""Database repository for Match entities.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models import MatchModel
from src.data.exceptions import DuplicateError, NotFoundError
from src.data.interface import MatchRepository
from src.models.match import Match


class DatabaseMatchRepository(MatchRepository):
    """Database implementation of MatchRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    def _to_pydantic(self, db_match: MatchModel) -> Match:
        """Convert database model to Pydantic model."""
        return Match(
            id=db_match.id,
            tournament_id=db_match.tournament_id,
            component_id=db_match.component_id,
            round_id=db_match.round_id,
            round_number=db_match.round_number,
            table_number=db_match.table_number,
            player1_id=db_match.player1_id,
            player2_id=db_match.player2_id,
            player1_wins=db_match.player1_wins,
            player2_wins=db_match.player2_wins,
            draws=db_match.draws,
            start_time=db_match.start_time,
            end_time=db_match.end_time,
            notes=db_match.notes,
        )

    async def create(self, match: Match) -> Match:
        """Create a new match."""
        # Check for duplicate ID
        existing = await self.session.get(MatchModel, match.id)
        if existing:
            raise DuplicateError("Match", "id", str(match.id))

        db_match = MatchModel(
            id=match.id,
            tournament_id=match.tournament_id,
            component_id=match.component_id,
            round_id=match.round_id,
            round_number=match.round_number,
            table_number=match.table_number,
            player1_id=match.player1_id,
            player2_id=match.player2_id,
            player1_wins=match.player1_wins,
            player2_wins=match.player2_wins,
            draws=match.draws,
            start_time=match.start_time,
            end_time=match.end_time,
            notes=match.notes,
        )

        self.session.add(db_match)
        await self.session.flush()

        return match

    async def get_by_id(self, match_id: UUID) -> Match:
        """Get match by ID. Raises NotFoundError if not found."""
        db_match = await self.session.get(MatchModel, match_id)
        if not db_match:
            raise NotFoundError("Match", match_id)

        return self._to_pydantic(db_match)

    async def list_by_tournament(self, tournament_id: UUID) -> list[Match]:
        """List matches for a tournament, ordered by round number."""
        stmt = (
            select(MatchModel)
            .where(MatchModel.tournament_id == tournament_id)
            .order_by(MatchModel.round_number, MatchModel.table_number)
        )

        result = await self.session.execute(stmt)
        db_matches = result.scalars().all()

        return [self._to_pydantic(db_match) for db_match in db_matches]

    async def list_by_round(self, round_id: UUID) -> list[Match]:
        """List matches for a round, ordered by table number."""
        stmt = (
            select(MatchModel)
            .where(MatchModel.round_id == round_id)
            .order_by(MatchModel.table_number)
        )

        result = await self.session.execute(stmt)
        db_matches = result.scalars().all()

        return [self._to_pydantic(db_match) for db_match in db_matches]

    async def list_by_component(self, component_id: UUID) -> list[Match]:
        """List matches for a component, ordered by round and table number."""
        stmt = (
            select(MatchModel)
            .where(MatchModel.component_id == component_id)
            .order_by(MatchModel.round_number, MatchModel.table_number)
        )

        result = await self.session.execute(stmt)
        db_matches = result.scalars().all()

        return [self._to_pydantic(db_match) for db_match in db_matches]

    async def list_by_player(
        self, player_id: UUID, tournament_id: UUID | None = None
    ) -> list[Match]:
        """List matches for a player, optionally filtered by tournament."""
        stmt = select(MatchModel).where(
            or_(MatchModel.player1_id == player_id, MatchModel.player2_id == player_id)
        )
        if tournament_id:
            stmt = stmt.where(MatchModel.tournament_id == tournament_id)

        stmt = stmt.order_by(MatchModel.round_number)

        result = await self.session.execute(stmt)
        db_matches = result.scalars().all()

        return [self._to_pydantic(db_match) for db_match in db_matches]

    async def update(self, match: Match) -> Match:
        """Update an existing match."""
        db_match = await self.session.get(MatchModel, match.id)
        if not db_match:
            raise NotFoundError("Match", match.id)

        db_match.table_number = match.table_number
        db_match.player1_wins = match.player1_wins
        db_match.player2_wins = match.player2_wins
        db_match.draws = match.draws
        db_match.start_time = match.start_time
        db_match.end_time = match.end_time
        db_match.notes = match.notes
        # Other fields are immutable

        await self.session.flush()

        return match

    async def delete(self, match_id: UUID) -> None:
        """Delete a match. Raises NotFoundError if not found."""
        db_match = await self.session.get(MatchModel, match_id)
        if not db_match:
            raise NotFoundError("Match", match_id)

        await self.session.delete(db_match)
        await self.session.flush()
