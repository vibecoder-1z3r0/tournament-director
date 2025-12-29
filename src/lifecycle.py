"""
Tournament lifecycle management.

Handles round advancement, tournament state transitions,
and automated tournament progression.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.models.base import ComponentStatus, PlayerStatus, RoundStatus, TournamentStatus
from src.models.match import Component, Match, Round
from src.models.tournament import Tournament, TournamentRegistration

logger = logging.getLogger(__name__)


def is_round_complete(round_obj: Round, matches: list[Match]) -> bool:
    """
    Check if a round is complete (all matches have results).

    A round is complete when:
    1. All matches have end_time set (indicating match completion)
    2. OR the round status is manually set to COMPLETED

    Args:
        round_obj: The round to check
        matches: All matches for this round

    Returns:
        True if round is complete, False otherwise
    """
    logger.debug(
        f"Checking round completion: round={round_obj.id}, "
        f"round_number={round_obj.round_number}, status={round_obj.status.value}"
    )

    # If round is manually marked complete, trust that
    if round_obj.status == RoundStatus.COMPLETED:
        logger.debug(f"Round {round_obj.round_number}: Manually marked as COMPLETED")
        return True

    # Filter to only matches in this round
    round_matches = [m for m in matches if m.round_id == round_obj.id]

    logger.debug(f"Round {round_obj.round_number}: Found {len(round_matches)} matches")

    # If no matches, round is not complete
    if not round_matches:
        logger.warning(f"Round {round_obj.round_number}: No matches found, marking incomplete")
        return False

    # Check if all matches have been completed
    incomplete_count = 0
    for match in round_matches:
        # A match is complete if it has an end_time
        if match.end_time is None:
            incomplete_count += 1

    if incomplete_count > 0:
        logger.info(
            f"Round {round_obj.round_number}: {incomplete_count}/{len(round_matches)} matches "
            f"still in progress"
        )
        return False

    # All matches have been completed
    logger.info(
        f"Round {round_obj.round_number}: COMPLETE - all {len(round_matches)} matches finished"
    )
    return True


def advance_to_next_round(
    current_round: Round,
    component_id: UUID,
    tournament_id: UUID,
    max_rounds: int | None = None,
    tournament: Tournament | None = None,
    component: Component | None = None,
) -> Round | None:
    """
    Advance tournament from current round to the next round.

    This function:
    1. Marks current round as COMPLETED
    2. Creates the next round with ACTIVE status
    3. Returns the new round, or None if tournament should end
    4. If tournament and component provided, automatically ends tournament when max_rounds reached

    Args:
        current_round: The round that just completed
        component_id: Component UUID
        tournament_id: Tournament UUID
        max_rounds: Optional maximum number of rounds (None = unlimited)
        tournament: Optional Tournament object for automatic completion (will be modified in-place)
        component: Optional Component object for automatic completion (will be modified in-place)

    Returns:
        New Round object for next round, or None if tournament is complete

    Example:
        >>> current_round.status = RoundStatus.ACTIVE
        >>> next_round = advance_to_next_round(
        ...     current_round, component_id, tournament_id, max_rounds=3
        ... )
        >>> if next_round:
        ...     # Continue tournament with next_round
        ... else:
        ...     # Tournament is complete

        >>> # With automatic tournament completion:
        >>> next_round = advance_to_next_round(
        ...     current_round, component_id, tournament_id,
        ...     tournament=tournament, component=component, max_rounds=3
        ... )
        >>> if next_round is None:
        ...     # Tournament automatically transitioned to COMPLETED

    AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - Updated for automatic tournament completion
    """
    logger.info(
        f"Advancing from Round {current_round.round_number}: "
        f"component={component_id}, max_rounds={max_rounds}, "
        f"auto_complete={tournament is not None and component is not None}"
    )

    # Mark current round as complete
    current_round.status = RoundStatus.COMPLETED
    current_round.end_time = datetime.now(timezone.utc)

    logger.debug(
        f"Round {current_round.round_number}: Marked as COMPLETED, "
        f"end_time={current_round.end_time}"
    )

    # Check if we've reached max rounds
    next_round_number = current_round.round_number + 1

    if max_rounds is not None and next_round_number > max_rounds:
        logger.info(
            f"Tournament complete: Reached maximum rounds ({max_rounds}), "
            f"not creating Round {next_round_number}"
        )

        # Automatically end tournament if tournament and component provided
        if tournament is not None and component is not None:
            logger.info("Automatically ending tournament (max_rounds reached)")
            end_tournament(tournament, component)

        return None

    # Create next round
    next_round = Round(
        id=uuid4(),
        tournament_id=tournament_id,
        component_id=component_id,
        round_number=next_round_number,
        status=RoundStatus.ACTIVE,
        start_time=datetime.now(timezone.utc),
        end_time=None,
    )

    logger.info(
        f"Round {next_round_number} created: id={next_round.id}, status=ACTIVE, "
        f"start_time={next_round.start_time}"
    )

    return next_round


def should_tournament_end(
    rounds: list[Round],
    matches: list[Match],
    max_rounds: int | None = None,
    min_rounds: int | None = None,
) -> bool:
    """
    Determine if a Swiss tournament should end.

    Tournament ends when:
    1. Reached maximum rounds (if configured)
    2. Reached minimum rounds AND only one undefeated player remains
    3. All players have played each other (impossible to continue)

    Args:
        rounds: All rounds in the tournament
        matches: All matches in the tournament
        max_rounds: Optional maximum rounds
        min_rounds: Optional minimum rounds before checking for clear winner

    Returns:
        True if tournament should end, False otherwise
    """
    if not rounds:
        logger.debug("Tournament should not end: No rounds yet")
        return False

    current_round_number = max(r.round_number for r in rounds)

    # Check max rounds limit
    if max_rounds is not None and current_round_number >= max_rounds:
        logger.info(
            f"Tournament should end: Reached max rounds ({current_round_number}/{max_rounds})"
        )
        return True

    # Check if we've met minimum rounds requirement
    if min_rounds is not None and current_round_number < min_rounds:
        logger.debug(
            f"Tournament should not end: Haven't reached min rounds "
            f"({current_round_number}/{min_rounds})"
        )
        return False

    # For Swiss, could add logic here to check for clear winner
    # (only one undefeated player, etc.)
    # For now, we rely on max_rounds

    logger.debug(
        f"Tournament should not end: Round {current_round_number}, no termination conditions met"
    )
    return False


def start_tournament(
    tournament: Tournament,
    component: Component,
    registrations: list[TournamentRegistration],
) -> Round:
    """
    Start a tournament: transition from DRAFT/REGISTRATION_CLOSED → IN_PROGRESS.

    This function:
    1. Validates tournament can be started (not already running)
    2. Validates minimum player count (2+)
    3. Changes tournament status to IN_PROGRESS
    4. Sets tournament start_time
    5. Activates the component
    6. Creates Round 1 with ACTIVE status

    Args:
        tournament: Tournament to start (will be modified in-place)
        component: Component to activate (will be modified in-place)
        registrations: List of registered players

    Returns:
        Round 1 object with ACTIVE status

    Raises:
        ValueError: If tournament is already IN_PROGRESS or COMPLETED
        ValueError: If fewer than 2 players registered

    Example:
        >>> tournament = Tournament(status=TournamentStatus.DRAFT, ...)
        >>> component = Component(status=ComponentStatus.PENDING, ...)
        >>> registrations = [reg1, reg2, reg3, ...]
        >>> round1 = start_tournament(tournament, component, registrations)
        >>> assert tournament.status == TournamentStatus.IN_PROGRESS
        >>> assert round1.round_number == 1

    AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - TDD GREEN phase
    """
    logger.info(
        f"Starting tournament: {tournament.name} (id={tournament.id}), "
        f"current status={tournament.status.value}, "
        f"players={len(registrations)}"
    )

    # Validate tournament state
    if tournament.status == TournamentStatus.IN_PROGRESS:
        error_msg = f"Cannot start tournament in {tournament.status.value} status (already running)"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if tournament.status == TournamentStatus.COMPLETED:
        error_msg = (
            f"Cannot start tournament in {tournament.status.value} status (already finished)"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate minimum player count
    active_players = [r for r in registrations if r.status == PlayerStatus.ACTIVE]
    if len(active_players) < 2:
        error_msg = f"Cannot start tournament: need at least 2 players, have {len(active_players)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug(
        f"Tournament state valid: status={tournament.status.value}, "
        f"active_players={len(active_players)}"
    )

    # Transition tournament to IN_PROGRESS
    tournament.status = TournamentStatus.IN_PROGRESS
    tournament.start_time = datetime.now(timezone.utc)

    logger.info(
        f"Tournament started: status={tournament.status.value}, start_time={tournament.start_time}"
    )

    # Activate component
    component.status = ComponentStatus.ACTIVE

    logger.debug(f"Component activated: {component.name} (id={component.id})")

    # Create Round 1
    round1 = Round(
        id=uuid4(),
        tournament_id=tournament.id,
        component_id=component.id,
        round_number=1,
        status=RoundStatus.ACTIVE,
        start_time=datetime.now(timezone.utc),
        end_time=None,
    )

    logger.info(
        f"Round 1 created: id={round1.id}, status={round1.status.value}, "
        f"start_time={round1.start_time}"
    )

    return round1


def end_tournament(
    tournament: Tournament,
    component: Component,
) -> None:
    """
    End a tournament: transition from IN_PROGRESS → COMPLETED.

    This function:
    1. Validates tournament is IN_PROGRESS
    2. Changes tournament status to COMPLETED
    3. Sets tournament end_time
    4. Completes the component

    This can be called either:
    - Manually by TO (early termination or final round)
    - Automatically when max_rounds reached

    Args:
        tournament: Tournament to end (will be modified in-place)
        component: Component to complete (will be modified in-place)

    Raises:
        ValueError: If tournament is not IN_PROGRESS

    Example:
        >>> tournament = Tournament(status=TournamentStatus.IN_PROGRESS, ...)
        >>> component = Component(status=ComponentStatus.ACTIVE, ...)
        >>> end_tournament(tournament, component)
        >>> assert tournament.status == TournamentStatus.COMPLETED

    AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - TDD GREEN phase
    """
    logger.info(
        f"Ending tournament: {tournament.name} (id={tournament.id}), "
        f"current status={tournament.status.value}"
    )

    # Validate tournament state
    if tournament.status != TournamentStatus.IN_PROGRESS:
        error_msg = (
            f"Cannot end tournament in {tournament.status.value} status. "
            f"Tournament must be IN_PROGRESS to be ended."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Transition tournament to COMPLETED
    tournament.status = TournamentStatus.COMPLETED
    tournament.end_time = datetime.now(timezone.utc)

    logger.info(
        f"Tournament completed: status={tournament.status.value}, end_time={tournament.end_time}"
    )

    # Complete component
    component.status = ComponentStatus.COMPLETED

    logger.debug(f"Component completed: {component.name} (id={component.id})")
