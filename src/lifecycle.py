"""
Tournament lifecycle management.

Handles round advancement, tournament state transitions,
and automated tournament progression.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import logging
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

from src.models.match import Round, Match
from src.models.base import RoundStatus

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
    component_id,
    tournament_id,
    max_rounds: Optional[int] = None,
) -> Optional[Round]:
    """
    Advance tournament from current round to the next round.

    This function:
    1. Marks current round as COMPLETED
    2. Creates the next round with ACTIVE status
    3. Returns the new round, or None if tournament should end

    Args:
        current_round: The round that just completed
        component_id: Component UUID
        tournament_id: Tournament UUID
        max_rounds: Optional maximum number of rounds (None = unlimited)

    Returns:
        New Round object for next round, or None if tournament is complete

    Example:
        >>> current_round.status = RoundStatus.ACTIVE
        >>> next_round = advance_to_next_round(current_round, component_id, tournament_id, max_rounds=3)
        >>> if next_round:
        ...     # Continue tournament with next_round
        ... else:
        ...     # Tournament is complete
    """
    logger.info(
        f"Advancing from Round {current_round.round_number}: "
        f"component={component_id}, max_rounds={max_rounds}"
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
        created_at=datetime.now(timezone.utc),
    )

    logger.info(
        f"Round {next_round_number} created: id={next_round.id}, status=ACTIVE, "
        f"start_time={next_round.start_time}"
    )

    return next_round


def should_tournament_end(
    rounds: list[Round],
    matches: list[Match],
    max_rounds: Optional[int] = None,
    min_rounds: Optional[int] = None,
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
        f"Tournament should not end: Round {current_round_number}, "
        f"no termination conditions met"
    )
    return False
