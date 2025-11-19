"""
Example demonstrating Swiss tournament standings calculation.

Shows how standings evolve round-by-round and how different tiebreaker
configurations produce different final rankings.

Run with: python3 examples/swiss_standings_example.py

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4

from src.models.tournament import TournamentRegistration
from src.models.match import Match
from src.models.base import PlayerStatus
from src.swiss.standings import calculate_standings


def print_standings_table(standings, title="STANDINGS"):
    """Print standings in a formatted table."""
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)
    print(
        f"{'Rank':<6} {'Player':<12} {'Record':<10} {'Pts':<5} {'MW%':<8} {'GW%':<8} {'OMW%':<8} {'OGW%':<8}"
    )
    print("-" * 100)

    for entry in standings:
        record = f"{entry.wins}-{entry.losses}-{entry.draws}"
        player_name = f"Player {entry.player.sequence_id}"

        # Get tiebreaker values
        mw = entry.tiebreakers.get("mw", 0.0)
        gw = entry.tiebreakers.get("gw", 0.0)
        omw = entry.tiebreakers.get("omw", 0.0)
        ogw = entry.tiebreakers.get("ogw", 0.0)

        print(
            f"{entry.rank:<6} {player_name:<12} {record:<10} {entry.match_points:<5} "
            f"{mw*100:>6.2f}% {gw*100:>6.2f}% {omw*100:>6.2f}% {ogw*100:>6.2f}%"
        )


def create_example_tournament():
    """
    Create a 6-player, 3-round Swiss tournament.

    Round 1: Random pairings
    - Player 1 beats Player 2 (2-0)
    - Player 3 beats Player 4 (2-1)
    - Player 5 beats Player 6 (2-0)

    Round 2: Paired by standings (all 1-0 vs 1-0, all 0-1 vs 0-1)
    - Player 1 beats Player 3 (2-1)
    - Player 5 beats Player 2 (2-0)
    - Player 4 beats Player 6 (2-1)

    Round 3: Paired by standings
    - Player 1 beats Player 5 (2-0) [both 2-0]
    - Player 3 beats Player 2 (2-1) [both 1-1]
    - Player 4 beats Player 6 (2-0) [both 1-1]

    Final Records:
    - Player 1: 3-0 (9 points) - Undefeated
    - Player 5: 2-1 (6 points)
    - Player 3: 2-1 (6 points)
    - Player 4: 2-1 (6 points)
    - Player 2: 0-3 (0 points)
    - Player 6: 0-3 (0 points)
    """
    tournament_id = uuid4()
    component_id = uuid4()

    # Create 6 players
    players = [
        TournamentRegistration(
            id=uuid4(),
            tournament_id=tournament_id,
            player_id=uuid4(),
            sequence_id=i + 1,
            status=PlayerStatus.ACTIVE,
        )
        for i in range(6)
    ]

    # Round 1 matches
    round1_matches = [
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=1,
            table_number=1,
            player1_id=players[0].player_id,  # Player 1
            player2_id=players[1].player_id,  # Player 2
            player1_wins=2,
            player2_wins=0,
        ),
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=1,
            table_number=2,
            player1_id=players[2].player_id,  # Player 3
            player2_id=players[3].player_id,  # Player 4
            player1_wins=2,
            player2_wins=1,
        ),
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=1,
            table_number=3,
            player1_id=players[4].player_id,  # Player 5
            player2_id=players[5].player_id,  # Player 6
            player1_wins=2,
            player2_wins=0,
        ),
    ]

    # Round 2 matches
    round2_matches = [
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=2,
            table_number=1,
            player1_id=players[0].player_id,  # Player 1
            player2_id=players[2].player_id,  # Player 3
            player1_wins=2,
            player2_wins=1,
        ),
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=2,
            table_number=2,
            player1_id=players[4].player_id,  # Player 5
            player2_id=players[1].player_id,  # Player 2
            player1_wins=2,
            player2_wins=0,
        ),
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=2,
            table_number=3,
            player1_id=players[3].player_id,  # Player 4
            player2_id=players[5].player_id,  # Player 6
            player1_wins=2,
            player2_wins=1,
        ),
    ]

    # Round 3 matches
    round3_matches = [
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=3,
            table_number=1,
            player1_id=players[0].player_id,  # Player 1
            player2_id=players[4].player_id,  # Player 5
            player1_wins=2,
            player2_wins=0,
        ),
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=3,
            table_number=2,
            player1_id=players[2].player_id,  # Player 3
            player2_id=players[1].player_id,  # Player 2
            player1_wins=2,
            player2_wins=1,
        ),
        Match(
            id=uuid4(),
            tournament_id=tournament_id,
            component_id=component_id,
            round_id=uuid4(),
            round_number=3,
            table_number=3,
            player1_id=players[3].player_id,  # Player 4
            player2_id=players[5].player_id,  # Player 6
            player1_wins=2,
            player2_wins=0,
        ),
    ]

    return {
        "players": players,
        "round1_matches": round1_matches,
        "round2_matches": round2_matches,
        "round3_matches": round3_matches,
    }


def main():
    """Run the standings example."""
    print("=" * 100)
    print("Swiss Tournament Standings Example")
    print("6 Players, 3 Rounds")
    print("=" * 100)

    # Create tournament
    tournament_data = create_example_tournament()
    players = tournament_data["players"]

    # Configuration (MTG standard)
    config = {
        "standings_tiebreakers": ["omw", "gw", "ogw", "random"],
        "omw_floor": 0.33,
        "gw_floor": 0.33,
        "mw_floor": 0.33,
    }

    # Show standings after each round
    print("\n\n")
    print("📊 STANDINGS PROGRESSION")

    # After Round 1
    standings_r1 = calculate_standings(
        players, tournament_data["round1_matches"], config
    )
    print_standings_table(standings_r1, "AFTER ROUND 1")

    # After Round 2
    all_matches_r2 = (
        tournament_data["round1_matches"] + tournament_data["round2_matches"]
    )
    standings_r2 = calculate_standings(players, all_matches_r2, config)
    print_standings_table(standings_r2, "AFTER ROUND 2")

    # After Round 3 (Final)
    all_matches = (
        tournament_data["round1_matches"]
        + tournament_data["round2_matches"]
        + tournament_data["round3_matches"]
    )
    standings_final = calculate_standings(players, all_matches, config)
    print_standings_table(standings_final, "FINAL STANDINGS (OMW% Primary)")

    # Show what happens with different tiebreaker config
    print("\n\n")
    print("🔀 DIFFERENT TIEBREAKER CONFIGURATION")
    print("=" * 100)
    print("What if we used GW% as the primary tiebreaker instead of OMW%?")
    print("=" * 100)

    config_gw_primary = {
        "standings_tiebreakers": ["gw", "omw", "ogw", "random"],
        "omw_floor": 0.33,
        "gw_floor": 0.33,
        "mw_floor": 0.33,
    }

    standings_gw = calculate_standings(players, all_matches, config_gw_primary)
    print_standings_table(standings_gw, "FINAL STANDINGS (GW% Primary)")

    # Compare rankings of tied players
    print("\n\n")
    print("🎯 TIEBREAKER ANALYSIS")
    print("=" * 100)
    print("Players 3, 4, and 5 are all tied at 2-1 (6 points)")
    print("=" * 100)

    # Get the 2-1 players from both standings
    tied_players_omw = [s for s in standings_final if s.match_points == 6]
    tied_players_gw = [s for s in standings_gw if s.match_points == 6]

    print("\nWith OMW% primary:")
    for i, entry in enumerate(tied_players_omw, start=1):
        player_num = entry.player.sequence_id
        omw = entry.tiebreakers["omw"]
        gw = entry.tiebreakers["gw"]
        print(
            f"  {i}. Player {player_num} - OMW%: {omw*100:.2f}%, GW%: {gw*100:.2f}%"
        )

    print("\nWith GW% primary:")
    for i, entry in enumerate(tied_players_gw, start=1):
        player_num = entry.player.sequence_id
        omw = entry.tiebreakers["omw"]
        gw = entry.tiebreakers["gw"]
        print(
            f"  {i}. Player {player_num} - GW%: {gw*100:.2f}%, OMW%: {omw*100:.2f}%"
        )

    print("\n")
    print("🎯 Configuration matters! Different tiebreaker orders can change rankings.")
    print()


if __name__ == "__main__":
    main()
