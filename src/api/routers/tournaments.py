"""
Tournament CRUD API endpoints.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from src.data.exceptions import DuplicateError, NotFoundError
from src.lifecycle import end_tournament, start_tournament
from src.models.base import ComponentStatus, ComponentType, TournamentStatus
from src.models.match import Component
from src.models.tournament import (
    RegistrationControl,
    Tournament,
    TournamentCreate,
    TournamentUpdate,
)

from ..dependencies import DataLayerDep, PaginationDep

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("/", response_model=Tournament, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    tournament_data: TournamentCreate, data_layer: DataLayerDep
) -> Tournament:
    """
    Create a new tournament.

    - **name**: Tournament name (1-200 characters)
    - **format_id**: UUID of tournament format
    - **venue_id**: UUID of tournament venue
    - **created_by**: UUID of tournament organizer (player)
    - **visibility**: PUBLIC or PRIVATE (default: PUBLIC)
    - **description**: Optional tournament description
    - **registration_deadline**: Optional registration cutoff
    - **auto_advance_rounds**: Auto-advance on round completion (default: false)
    - **registration_auto_open_time**: Auto-open registration at time
    - **registration_auto_close_time**: Auto-close registration at time
    - **registration_password**: Password required for registration
    - **max_players**: Maximum player count
    """
    # Build RegistrationControl from flattened fields
    registration = RegistrationControl(
        auto_open_time=tournament_data.registration_auto_open_time,
        auto_close_time=tournament_data.registration_auto_close_time,
        registration_password=tournament_data.registration_password,
        max_players=tournament_data.max_players,
    )

    # Create Tournament with generated ID
    tournament = Tournament(
        id=uuid4(),
        name=tournament_data.name,
        format_id=tournament_data.format_id,
        venue_id=tournament_data.venue_id,
        created_by=tournament_data.created_by,
        visibility=tournament_data.visibility,
        description=tournament_data.description,
        registration_deadline=tournament_data.registration_deadline,
        auto_advance_rounds=tournament_data.auto_advance_rounds,
        registration=registration,
    )

    try:
        return await data_layer.tournaments.create(tournament)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None


@router.get("/", response_model=list[Tournament])
async def list_tournaments(
    data_layer: DataLayerDep,
    pagination: PaginationDep,
) -> list[Tournament]:
    """
    List all tournaments with pagination.

    - **limit**: Maximum number of results (default: 20, max: 100)
    - **offset**: Number of results to skip (default: 0)
    """
    tournaments = await data_layer.tournaments.list_all()
    start = pagination["offset"]
    end = start + pagination["limit"]
    return tournaments[start:end]


@router.get("/{tournament_id}", response_model=Tournament)
async def get_tournament(tournament_id: UUID, data_layer: DataLayerDep) -> Tournament:
    """
    Get tournament by ID.

    - **tournament_id**: UUID of tournament to retrieve
    """
    try:
        return await data_layer.tournaments.get_by_id(tournament_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament {tournament_id} not found",
        ) from None


@router.put("/{tournament_id}", response_model=Tournament)
async def update_tournament(
    tournament_id: UUID,
    tournament_update: TournamentUpdate,
    data_layer: DataLayerDep,
) -> Tournament:
    """
    Update tournament by ID.

    - **tournament_id**: UUID of tournament to update
    - **name**: Updated tournament name (optional)
    - **status**: Updated tournament status (optional)
    - **visibility**: Updated visibility (optional)
    - **description**: Updated description (optional)
    - **registration_deadline**: Updated registration deadline (optional)
    - **auto_advance_rounds**: Updated auto-advance setting (optional)
    - **registration_***: Updated registration control fields (optional)
    """
    try:
        # Get existing tournament
        tournament = await data_layer.tournaments.get_by_id(tournament_id)

        # Update fields if provided
        update_data = tournament_update.model_dump(exclude_unset=True)

        # Handle registration control updates
        registration_fields = {
            "auto_open_time": update_data.pop("registration_auto_open_time", None),
            "auto_close_time": update_data.pop("registration_auto_close_time", None),
            "registration_password": update_data.pop("registration_password", None),
            "max_players": update_data.pop("max_players", None),
        }

        # Update registration control if any fields provided
        if any(v is not None for v in registration_fields.values()):
            current_reg = tournament.registration.model_dump()
            for key, value in registration_fields.items():
                if value is not None:
                    current_reg[key] = value
            tournament.registration = RegistrationControl(**current_reg)

        # Update other fields
        for field, value in update_data.items():
            setattr(tournament, field, value)

        return await data_layer.tournaments.update(tournament)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament {tournament_id} not found",
        ) from None


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tournament(tournament_id: UUID, data_layer: DataLayerDep) -> None:
    """
    Delete tournament by ID.

    - **tournament_id**: UUID of tournament to delete
    """
    try:
        await data_layer.tournaments.delete(tournament_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament {tournament_id} not found",
        ) from None


@router.get("/status/{status}", response_model=list[Tournament])
async def list_tournaments_by_status(
    status: TournamentStatus,
    data_layer: DataLayerDep,
    pagination: PaginationDep,
) -> list[Tournament]:
    """
    List tournaments filtered by status.

    - **status**: Tournament status (DRAFT, IN_PROGRESS, COMPLETED, CANCELLED)
    - **limit**: Maximum number of results (default: 20, max: 100)
    - **offset**: Number of results to skip (default: 0)
    """
    tournaments = await data_layer.tournaments.list_by_status(status)
    start = pagination["offset"]
    end = start + pagination["limit"]
    return tournaments[start:end]


@router.get("/venue/{venue_id}", response_model=list[Tournament])
async def list_tournaments_by_venue(
    venue_id: UUID,
    data_layer: DataLayerDep,
    pagination: PaginationDep,
) -> list[Tournament]:
    """
    List tournaments filtered by venue.

    - **venue_id**: UUID of venue
    - **limit**: Maximum number of results (default: 20, max: 100)
    - **offset**: Number of results to skip (default: 0)
    """
    tournaments = await data_layer.tournaments.list_by_venue(venue_id)
    start = pagination["offset"]
    end = start + pagination["limit"]
    return tournaments[start:end]


@router.get("/format/{format_id}", response_model=list[Tournament])
async def list_tournaments_by_format(
    format_id: UUID,
    data_layer: DataLayerDep,
    pagination: PaginationDep,
) -> list[Tournament]:
    """
    List tournaments filtered by format.

    - **format_id**: UUID of format
    - **limit**: Maximum number of results (default: 20, max: 100)
    - **offset**: Number of results to skip (default: 0)
    """
    tournaments = await data_layer.tournaments.list_by_format(format_id)
    start = pagination["offset"]
    end = start + pagination["limit"]
    return tournaments[start:end]


@router.post("/{tournament_id}/start", response_model=Tournament)
async def start_tournament_endpoint(tournament_id: UUID, data_layer: DataLayerDep) -> Tournament:
    """
    Start a tournament: transition from DRAFT/REGISTRATION_CLOSED → IN_PROGRESS.

    This endpoint:
    1. Validates tournament can be started (not already running)
    2. Validates minimum player count (2+)
    3. Changes tournament status to IN_PROGRESS
    4. Sets tournament start_time
    5. Creates a Swiss component
    6. Creates Round 1

    - **tournament_id**: UUID of tournament to start

    Returns the updated tournament with IN_PROGRESS status.

    Raises:
    - **400**: If tournament is already IN_PROGRESS or COMPLETED
    - **400**: If fewer than 2 active players registered
    - **404**: If tournament not found
    """
    try:
        # Get tournament
        tournament = await data_layer.tournaments.get_by_id(tournament_id)

        # Get registrations
        registrations = await data_layer.registrations.list_by_tournament(tournament_id)

        # Create Swiss component for the tournament
        component = Component(
            id=uuid4(),
            tournament_id=tournament_id,
            name="Swiss Component",
            type=ComponentType.SWISS,
            sequence_order=1,  # First component in tournament
            status=ComponentStatus.PENDING,
            config={"max_rounds": None},  # Will be determined by format or manual setting
        )

        # Start tournament (modifies tournament and component in-place, returns Round 1)
        round1 = start_tournament(tournament, component, registrations)

        # Persist changes
        await data_layer.tournaments.update(tournament)
        await data_layer.components.create(component)
        await data_layer.rounds.create(round1)

        return tournament

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament {tournament_id} not found",
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None


@router.post("/{tournament_id}/complete", response_model=Tournament)
async def complete_tournament_endpoint(tournament_id: UUID, data_layer: DataLayerDep) -> Tournament:
    """
    Complete a tournament: transition from IN_PROGRESS → COMPLETED.

    This endpoint:
    1. Validates tournament is IN_PROGRESS
    2. Changes tournament status to COMPLETED
    3. Sets tournament end_time
    4. Completes all associated components

    - **tournament_id**: UUID of tournament to complete

    Returns the updated tournament with COMPLETED status.

    This can be called manually by TO for early termination or after final round.

    Raises:
    - **400**: If tournament is not IN_PROGRESS
    - **404**: If tournament not found
    """
    try:
        # Get tournament
        tournament = await data_layer.tournaments.get_by_id(tournament_id)

        # Get components for this tournament
        components = await data_layer.components.list_by_tournament(tournament_id)

        if not components:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tournament has no components (was it started?)",
            )

        # Complete tournament (modifies tournament and component in-place)
        # Use first component (typically tournaments have one Swiss component)
        component = components[0]
        end_tournament(tournament, component)

        # Persist changes
        await data_layer.tournaments.update(tournament)
        await data_layer.components.update(component)

        return tournament

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament {tournament_id} not found",
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
