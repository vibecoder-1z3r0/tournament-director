"""
Swiss tournament standings calculator.

Aggregates match results, calculates tiebreakers, and generates final standings
sorted by match points and configurable tiebreaker chains.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

from uuid import UUID

from src.models.tournament import TournamentRegistration
from src.models.match import Match
from .models import StandingsEntry
from .tiebreakers import (
    calculate_match_win_percentage,
    calculate_game_win_percentage,
    calculate_opponent_match_win_percentage,
    calculate_opponent_game_win_percentage,
    get_player_matches,
    get_match_result_for_player,
    get_game_result_for_player,
    get_opponent_id,
    is_bye_match,
)


# Tiebreaker calculator registry
TIEBREAKER_CALCULATORS = {
    "mw": calculate_match_win_percentage,
    "gw": calculate_game_win_percentage,
    "omw": calculate_opponent_match_win_percentage,
    "ogw": calculate_opponent_game_win_percentage,
}


def calculate_standings(
    players: list[TournamentRegistration],
    matches: list[Match],
    config: dict,
) -> list[StandingsEntry]:
    """
    Calculate tournament standings for all players.

    Aggregates match results, calculates tiebreakers, sorts by match points
    and configured tiebreaker chain, and assigns ranks.

    Args:
        players: List of all tournament registrations
        matches: List of all matches played
        config: Configuration dict with "standings_tiebreakers" list

    Returns:
        List of StandingsEntry objects sorted by rank (best to worst)
    """
    standings = []

    for player in players:
        # Get all matches for this player
        player_matches = get_player_matches(player, matches)

        # Calculate match record
        wins = 0
        losses = 0
        draws = 0
        match_points = 0

        for match in player_matches:
            w, l, d = get_match_result_for_player(player, match)
            wins += w
            losses += l
            draws += d

        # Calculate match points (3 for win, 1 for draw, 0 for loss)
        match_points = (wins * 3) + (draws * 1)

        # Calculate game record
        game_wins = 0
        game_losses = 0
        game_draws = 0

        for match in player_matches:
            gw, gl = get_game_result_for_player(player, match)
            game_wins += gw
            game_losses += gl
            # Game draws not currently tracked separately in Match model

        # Calculate metadata
        matches_played = len(player_matches)
        bye_count = sum(1 for match in player_matches if is_bye_match(match))

        # Get list of opponents faced (excluding byes)
        opponents_faced = []
        for match in player_matches:
            opponent_id = get_opponent_id(player, match)
            if opponent_id is not None:
                opponents_faced.append(str(opponent_id))

        # Calculate all configured tiebreakers
        tiebreaker_names = config.get("standings_tiebreakers", ["omw", "gw", "ogw"])
        tiebreaker_values = {}

        for tb_name in tiebreaker_names:
            if tb_name == "random":
                # Random tiebreaker - just use a random value
                import random
                tiebreaker_values[tb_name] = random.random()
            elif tb_name in TIEBREAKER_CALCULATORS:
                calculator = TIEBREAKER_CALCULATORS[tb_name]
                tiebreaker_values[tb_name] = calculator(player, matches, players, config)
            else:
                # Unknown tiebreaker - skip it
                tiebreaker_values[tb_name] = 0.0

        # Create standings entry
        entry = StandingsEntry(
            player=player,
            rank=0,  # Will be assigned after sorting
            wins=wins,
            losses=losses,
            draws=draws,
            match_points=match_points,
            game_wins=game_wins,
            game_losses=game_losses,
            game_draws=game_draws,
            tiebreakers=tiebreaker_values,
            matches_played=matches_played,
            bye_count=bye_count,
            opponents_faced=opponents_faced,
        )

        standings.append(entry)

    # Sort standings
    # Primary: Match points (descending)
    # Secondary: Tiebreakers in configured order (descending)
    def sort_key(entry: StandingsEntry):
        # Start with match points
        key = [entry.match_points]

        # Add each tiebreaker value in order
        for tb_name in config.get("standings_tiebreakers", []):
            if tb_name in entry.tiebreakers:
                key.append(entry.tiebreakers[tb_name])
            else:
                key.append(0.0)  # Missing tiebreaker = 0

        return tuple(key)

    standings.sort(key=sort_key, reverse=True)

    # Assign ranks
    for rank, entry in enumerate(standings, start=1):
        entry.rank = rank

    return standings
