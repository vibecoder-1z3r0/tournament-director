"""
Tournament lifecycle management.

Handles round advancement, tournament state transitions,
and automated tournament progression.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from src.models.match import Round, Match
from src.models.base import RoundStatus


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
    # If round is manually marked complete, trust that
    if round_obj.status == RoundStatus.COMPLETED:
        return True

    # Filter to only matches in this round
    round_matches = [m for m in matches if m.round_id == round_obj.id]

    # If no matches, round is not complete
    if not round_matches:
        return False

    # Check if all matches have been completed
    for match in round_matches:
        # A match is complete if it has an end_time
        if match.end_time is None:
            return False

    # All matches have been completed
    return True
