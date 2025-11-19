"""
Swiss Pairing Example - Full 8-Player Tournament.

Demonstrates Swiss pairing algorithm across 3 rounds:
- Round 1: Random pairing
- Round 2: Standings-based bracket pairing
- Round 3: More complex standings with tiebreakers

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from uuid import uuid4

from src.models.player import Player
from src.models.tournament import Tournament, TournamentRegistration, RegistrationControl
from src.models.match import Match, Component
from src.models.base import (
    TournamentStatus,
    TournamentVisibility,
    PlayerStatus,
    ComponentType,
    ComponentStatus,
)
from src.swiss import pair_round_1, pair_round, calculate_standings


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_pairings(round_num: int, pairings: list[Match], players_by_id: dict):
    """Print round pairings."""
    print(f"ROUND {round_num} PAIRINGS:")
    print("-" * 80)
    for i, match in enumerate(pairings, 1):
        p1_name = players_by_id[match.player1_id].name
        if match.player2_id is None:
            print(f"  Table {match.table_number or 'BYE'}: {p1_name} - BYE")
        else:
            p2_name = players_by_id[match.player2_id].name
            print(f"  Table {match.table_number}: {p1_name} vs {p2_name}")
    print()


def print_standings(standings, players_by_id: dict):
    """Print current standings."""
    print("CURRENT STANDINGS:")
    print("-" * 80)
    print(f"{'Rank':<6} {'Player':<15} {'Record':<10} {'Points':<8} {'OMW%':<8} {'GW%':<8}")
    print("-" * 80)

    for entry in standings:
        player_name = players_by_id[entry.player.player_id].name
        record = f"{entry.wins}-{entry.losses}-{entry.draws}"
        omw = entry.tiebreakers.get("omw", 0.0)
        gw = entry.tiebreakers.get("gw", 0.0)

        print(
            f"{entry.rank:<6} {player_name:<15} {record:<10} "
            f"{entry.match_points:<8} {omw:>6.2f}%  {gw:>6.2f}%"
        )
    print()


def simulate_round_results(pairings: list[Match], results: list[tuple[int, int]]):
    """
    Apply results to matches.

    Args:
        pairings: List of matches to update
        results: List of (player1_wins, player2_wins) tuples
    """
    for match, (p1_wins, p2_wins) in zip(pairings, results):
        match.player1_wins = p1_wins
        match.player2_wins = p2_wins
        match.draws = 0  # No draws in this example


def main():
    """Run a complete 8-player, 3-round Swiss tournament example."""

    print_section("SWISS PAIRING EXAMPLE - 8 PLAYERS, 3 ROUNDS")

    # Setup tournament
    tournament_id = uuid4()
    component_id = uuid4()

    component = Component(
        id=component_id,
        tournament_id=tournament_id,
        type=ComponentType.SWISS,
        name="Swiss Rounds",
        sequence_order=1,
        status=ComponentStatus.ACTIVE,
        config={},
    )

    # Create 8 players
    players = [
        Player(id=uuid4(), name=f"Player {i+1}", created_at=datetime.now(timezone.utc))
        for i in range(8)
    ]

    registrations = [
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

    # Create lookup
    players_by_id = {p.id: p for p in players}

    print("Tournament setup complete:")
    print(f"  Players: {len(players)}")
    print(f"  Format: Swiss (3 rounds)")
    print()

    # Configuration for tiebreakers
    config = {
        "standings_tiebreakers": ["omw", "gw", "ogw"],
        "match_win_floor": 0.33,
        "game_win_floor": 0.33,
    }

    # =========================================================================
    # ROUND 1 - Random Pairing
    # =========================================================================

    print_section("ROUND 1 - RANDOM PAIRING")

    round1_pairings = pair_round_1(registrations, component, mode="random")
    print_pairings(1, round1_pairings, players_by_id)

    # Simulate results (4 matches, varying game scores)
    round1_results = [
        (2, 0),  # Match 1: Player wins 2-0
        (2, 1),  # Match 2: Player wins 2-1
        (2, 0),  # Match 3: Player wins 2-0
        (2, 1),  # Match 4: Player wins 2-1
    ]
    simulate_round_results(round1_pairings, round1_results)

    print("Results reported. Calculating standings...")
    standings_r1 = calculate_standings(registrations, round1_pairings, config)
    print_standings(standings_r1, players_by_id)

    # =========================================================================
    # ROUND 2 - Standings-Based Pairing
    # =========================================================================

    print_section("ROUND 2 - STANDINGS-BASED BRACKET PAIRING")

    print("Expected: 3-point players paired together, 0-point players paired together")
    print()

    round2_pairings = pair_round(
        registrations,
        round1_pairings,
        component,
        config,
        round_number=2,
    )
    print_pairings(2, round2_pairings, players_by_id)

    # Verify no rematches
    print("Verifying no rematches from Round 1...")
    round1_pairs = {
        frozenset([m.player1_id, m.player2_id])
        for m in round1_pairings if m.player2_id is not None
    }
    round2_pairs = {
        frozenset([m.player1_id, m.player2_id])
        for m in round2_pairings if m.player2_id is not None
    }

    rematches = round1_pairs & round2_pairs
    if rematches:
        print(f"  ❌ ERROR: Found {len(rematches)} rematches!")
    else:
        print("  ✓ No rematches detected")
    print()

    # Simulate results (more varied)
    round2_results = [
        (2, 1),  # Winner bracket: Close match
        (0, 2),  # Winner bracket: Upset
        (2, 0),  # Loser bracket: Dominant win
        (1, 2),  # Loser bracket: Close match
    ]
    simulate_round_results(round2_pairings, round2_results)

    print("Results reported. Calculating standings...")
    all_matches = round1_pairings + round2_pairings
    standings_r2 = calculate_standings(registrations, all_matches, config)
    print_standings(standings_r2, players_by_id)

    # =========================================================================
    # ROUND 3 - Complex Standings
    # =========================================================================

    print_section("ROUND 3 - FINAL ROUND")

    print("Expected: Complex bracket structure with possible pair-downs")
    print()

    round3_pairings = pair_round(
        registrations,
        all_matches,
        component,
        config,
        round_number=3,
    )
    print_pairings(3, round3_pairings, players_by_id)

    # Verify no rematches from previous rounds
    print("Verifying no rematches from Rounds 1 or 2...")
    round3_pairs = {
        frozenset([m.player1_id, m.player2_id])
        for m in round3_pairings if m.player2_id is not None
    }

    all_prev_pairs = round1_pairs | round2_pairs
    rematches = all_prev_pairs & round3_pairs
    if rematches:
        print(f"  ❌ ERROR: Found {len(rematches)} rematches!")
    else:
        print("  ✓ No rematches detected")
    print()

    # Simulate final results
    round3_results = [
        (2, 1),
        (2, 0),
        (1, 2),
        (2, 1),
    ]
    simulate_round_results(round3_pairings, round3_results)

    print("Results reported. Calculating FINAL standings...")
    all_matches = round1_pairings + round2_pairings + round3_pairings
    final_standings = calculate_standings(registrations, all_matches, config)
    print_standings(final_standings, players_by_id)

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print_section("TOURNAMENT SUMMARY")

    print(f"Total rounds: 3")
    print(f"Total matches: {len(all_matches)}")
    print()

    print("CHAMPION:")
    winner = final_standings[0]
    winner_name = players_by_id[winner.player.player_id].name
    print(f"  🏆 {winner_name}")
    print(f"     Record: {winner.wins}-{winner.losses}-{winner.draws}")
    print(f"     Match Points: {winner.match_points}")
    print(f"     OMW%: {winner.tiebreakers.get('omw', 0):.2f}%")
    print(f"     GW%: {winner.tiebreakers.get('gw', 0):.2f}%")
    print()

    print("TOP 4:")
    for i, entry in enumerate(final_standings[:4], 1):
        player_name = players_by_id[entry.player.player_id].name
        print(f"  {i}. {player_name} ({entry.wins}-{entry.losses}-{entry.draws}, {entry.match_points} pts)")
    print()

    print("✓ Swiss pairing algorithm demonstration complete!")


if __name__ == "__main__":
    main()
