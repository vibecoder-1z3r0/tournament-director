"""
Round and Pairing API endpoints for tournament management.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from src.data.exceptions import NotFoundError
from src.models.base import PlayerStatus, RoundStatus, TournamentStatus
from src.models.match import Round
from src.models.match import StandingsEntry as APIStandingsEntry
from src.swiss.models import StandingsEntry as SwissStandingsEntry
from src.swiss.pairing import pair_round, pair_round_1
from src.swiss.standings import calculate_standings

from ..dependencies import DataLayerDep

router = APIRouter(prefix="/tournaments")


@router.post(
    "/{tournament_id}/rounds/{round_number}/pair",
    response_model=Round,
    status_code=status.HTTP_201_CREATED,
)
async def pair_round_endpoint(
    tournament_id: UUID, round_number: int, data_layer: DataLayerDep
) -> Round:
    """
    Generate pairings for a round.

    - Validates tournament is IN_PROGRESS
    - Gets active registrations
    - Uses Swiss pairing algorithms
    - Creates Round and Match objects
    - Returns round with pairings
    """
    # Verify tournament exists and is in progress
    try:
        tournament = await data_layer.tournaments.get_by_id(tournament_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Tournament {tournament_id} not found"
        ) from None

    if tournament.status != TournamentStatus.IN_PROGRESS:
        current_status = tournament.status.value
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Tournament must be IN_PROGRESS to pair rounds (current status: {current_status})"
            ),
        )

    # Check if round already exists
    existing_rounds = await data_layer.rounds.list_by_tournament(tournament_id)
    existing_round = next((r for r in existing_rounds if r.round_number == round_number), None)

    # If round exists, check if it has matches already
    if existing_round:
        existing_matches = await data_layer.matches.list_by_round(existing_round.id)
        if existing_matches:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Round {round_number} already has pairings",
            )

    # Get tournament component (should exist after tournament start)
    components = await data_layer.components.list_by_tournament(tournament_id)
    if not components:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament has no components - cannot generate pairings",
        )
    component = components[0]  # Use first component (Swiss)

    # Get active registrations
    registrations = await data_layer.registrations.list_by_tournament(
        tournament_id, status=PlayerStatus.ACTIVE.value
    )

    if len(registrations) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need at least 2 active players to generate pairings",
        )

    # Generate pairings based on round number
    if round_number == 1:
        # First round: random pairing
        matches = pair_round_1(registrations, component)
    else:
        # Subsequent rounds: Swiss pairing by standings
        all_matches = await data_layer.matches.list_by_tournament(tournament_id)
        config = component.config or {}
        matches = pair_round(registrations, all_matches, component, config, round_number)

    # Create or use existing round
    if existing_round:
        # Round exists but no matches - use existing round
        created_round = existing_round
    else:
        # Create new round
        round_obj = Round(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component.id,
            round_number=round_number,
            start_time=datetime.now(timezone.utc),
            status=RoundStatus.ACTIVE,
        )
        created_round = await data_layer.rounds.create(round_obj)

    # Set round_id and save matches
    for match in matches:
        match.round_id = created_round.id
        match.round_number = round_number
        match.start_time = datetime.now(timezone.utc)
        await data_layer.matches.create(match)

    return created_round


@router.get("/{tournament_id}/rounds/{round_number}", response_model=Round)
async def get_round(tournament_id: UUID, round_number: int, data_layer: DataLayerDep) -> Round:
    """
    Get round details by tournament and round number.

    Returns the round object. Use GET /tournaments/{id}/matches?round={n}
    to get the matches for this round.
    """
    # Verify tournament exists
    try:
        await data_layer.tournaments.get_by_id(tournament_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Tournament {tournament_id} not found"
        ) from None

    # Get round by tournament and round number
    rounds = await data_layer.rounds.list_by_tournament(tournament_id)
    round_obj = next((r for r in rounds if r.round_number == round_number), None)

    if not round_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Round {round_number} not found in tournament {tournament_id}",
        )

    return round_obj


@router.post("/{tournament_id}/rounds/{round_number}/complete", response_model=Round)
async def complete_round(tournament_id: UUID, round_number: int, data_layer: DataLayerDep) -> Round:
    """
    Mark a round as complete.

    - Validates all matches have results (end_time set)
    - Updates round status to COMPLETED
    - Sets round end_time
    """
    # Get round
    rounds = await data_layer.rounds.list_by_tournament(tournament_id)
    round_obj = next((r for r in rounds if r.round_number == round_number), None)

    if not round_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Round {round_number} not found"
        )

    # Check all matches have results
    matches = await data_layer.matches.list_by_round(round_obj.id)
    incomplete_matches = [m for m in matches if m.end_time is None]

    if incomplete_matches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete round: {len(incomplete_matches)} matches still in progress",
        )

    # Update round status
    round_obj.status = RoundStatus.COMPLETED
    round_obj.end_time = datetime.now(timezone.utc)

    return await data_layer.rounds.update(round_obj)


@router.get("/{tournament_id}/standings", response_model=list[APIStandingsEntry])
async def get_standings(tournament_id: UUID, data_layer: DataLayerDep) -> list[APIStandingsEntry]:
    """
    Calculate and return current tournament standings.

    Uses Swiss tiebreaker system:
    - Match Points (primary)
    - OMW% (Opponent Match Win Percentage)
    - GW% (Game Win Percentage)
    - OGW% (Opponent Game Win Percentage)
    """
    # Verify tournament exists
    try:
        await data_layer.tournaments.get_by_id(tournament_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Tournament {tournament_id} not found"
        ) from None

    # Get all registrations (including dropped players)
    registrations = await data_layer.registrations.list_by_tournament(tournament_id)

    # Get all matches
    matches = await data_layer.matches.list_by_tournament(tournament_id)

    # Get component config for tiebreakers
    components = await data_layer.components.list_by_tournament(tournament_id)
    config = components[0].config if components else {}

    # Calculate standings (returns Swiss StandingsEntry objects)
    swiss_standings: list[SwissStandingsEntry] = calculate_standings(registrations, matches, config)

    # Convert Swiss standings to API standings
    api_standings = []
    for swiss_entry in swiss_standings:
        # Get player name
        try:
            player = await data_layer.players.get_by_id(swiss_entry.player.player_id)
            player_name = player.name
        except NotFoundError:
            player_name = "Unknown Player"

        # Calculate percentages from tiebreakers dict
        mw_pct = swiss_entry.tiebreakers.get("mw", 0.0)
        gw_pct = swiss_entry.tiebreakers.get("gw", 0.0)
        omw_pct = swiss_entry.tiebreakers.get("omw", 0.0)
        ogw_pct = swiss_entry.tiebreakers.get("ogw", 0.0)

        # Create API standings entry
        api_entry = APIStandingsEntry(
            rank=swiss_entry.rank,
            player_id=swiss_entry.player.player_id,
            player_name=player_name,
            sequence_id=swiss_entry.player.sequence_id,
            match_points=swiss_entry.match_points,
            # Calculate game points
            game_points=(swiss_entry.game_wins * 3) + swiss_entry.game_draws,
            matches_played=swiss_entry.matches_played,
            match_win_percentage=mw_pct,
            game_win_percentage=gw_pct,
            opponent_match_win_percentage=omw_pct,
            opponent_game_win_percentage=ogw_pct,
        )
        api_standings.append(api_entry)

    return api_standings
