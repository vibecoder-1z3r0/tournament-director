"""
Tournament lifecycle management.

Handles round advancement, tournament state transitions,
and automated tournament progression.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import logging
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
