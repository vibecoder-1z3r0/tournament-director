"""
Logging demonstration for Tournament Director.

Shows the difference between INFO and DEBUG logging levels.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logging_config import setup_logging
from src.swiss import pair_round_1, pair_round
from uuid import uuid4
from datetime import datetime, timezone

from src.models.player import Player
from src.models.tournament import TournamentRegistration
from src.models.match import Component
from src.models.base import ComponentType, ComponentStatus, PlayerStatus


def create_test_players(count: int) -> list[Player]:
    """Create test players."""
    return [
        Player(id=uuid4(), name=f"Player {i+1}", created_at=datetime.now(timezone.utc))
        for i in range(count)
    ]


def create_registrations(
    tournament_id, players: list[Player]
) -> list[TournamentRegistration]:
    """Create tournament registrations."""
    return [
        TournamentRegistration(
            id=uuid4(),
            tournament_id=tournament_id,
            player_id=player.id,
            sequence_id=i + 1,
            status=PlayerStatus.ACTIVE,
            registration_time=datetime.now(timezone.utc),
        )
        for i, player in enumerate(players)
    ]


def create_component(tournament_id):
    """Create a Swiss component."""
    return Component(
        id=uuid4(),
        tournament_id=tournament_id,
        type=ComponentType.SWISS,
        name="Swiss Rounds",
        sequence_order=1,
        status=ComponentStatus.ACTIVE,
        config={},
        created_at=datetime.now(timezone.utc),
    )


def demo_info_logging():
    """Demo INFO level logging (key events only)."""
    print("\n" + "=" * 80)
    print("INFO LEVEL LOGGING - Key Events Only")
    print("=" * 80 + "\n")

    setup_logging(level="INFO", console=True, detailed=False)

    # Create 8-player tournament
    tournament_id = uuid4()
    component = create_component(tournament_id)
    players = create_test_players(8)
    registrations = create_registrations(tournament_id, players)

    # Round 1
    print("\n--- Round 1 Pairing ---")
    round1 = pair_round_1(registrations, component, mode="random")

    # Simulate results
    for match in round1:
        match.player1_wins = 2
        match.player2_wins = 0

    # Round 2
    print("\n--- Round 2 Pairing ---")
    config = {"standings_tiebreakers": ["omw", "gw", "ogw"]}
    round2 = pair_round(registrations, round1, component, config, round_number=2)


def demo_debug_logging():
    """Demo DEBUG level logging (detailed algorithm steps)."""
    print("\n" + "=" * 80)
    print("DEBUG LEVEL LOGGING - Detailed Algorithm Steps")
    print("=" * 80 + "\n")

    setup_logging(level="DEBUG", console=True, detailed=False)

    # Create 8-player tournament
    tournament_id = uuid4()
    component = create_component(tournament_id)
    players = create_test_players(8)
    registrations = create_registrations(tournament_id, players)

    # Round 1
    print("\n--- Round 1 Pairing ---")
    round1 = pair_round_1(registrations, component, mode="random")

    # Simulate results
    for match in round1:
        match.player1_wins = 2
        match.player2_wins = 0

    # Round 2
    print("\n--- Round 2 Pairing ---")
    config = {"standings_tiebreakers": ["omw", "gw", "ogw"]}
    round2 = pair_round(registrations, round1, component, config, round_number=2)


if __name__ == "__main__":
    # Demo INFO level first
    demo_info_logging()

    # Demo DEBUG level
    demo_debug_logging()

    print("\n" + "=" * 80)
    print("Notice how DEBUG shows detailed algorithm steps,")
    print("while INFO shows only key events and summaries.")
    print("=" * 80 + "\n")
