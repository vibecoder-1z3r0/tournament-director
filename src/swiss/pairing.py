"""
Swiss tournament pairing algorithms.

Handles Round 1 random/seeded pairing and subsequent rounds with
standings-based bracket pairing and no-rematch constraints.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import random
from uuid import UUID, uuid4
from collections import defaultdict

from src.models.tournament import TournamentRegistration
from src.models.match import Match, Component
from src.swiss.standings import calculate_standings
from src.swiss.models import StandingsEntry


def pair_round_1(
    registrations: list[TournamentRegistration],
    component: Component,
    mode: str = "random",
) -> list[Match]:
    """
    Pair players for the first round of Swiss tournament.

    Args:
        registrations: List of active tournament registrations
        component: Tournament component configuration
        mode: Pairing mode - "random" (shuffle) or "seeded" (by sequence_id)

    Returns:
        List of Match objects for Round 1

    Raises:
        ValueError: If registrations list is empty
    """
    if not registrations:
        raise ValueError("Cannot pair empty player list")

    # Filter to only active players
    active_players = [
        reg for reg in registrations
        if reg.status.value == "active"  # PlayerStatus.ACTIVE
    ]

    if not active_players:
        raise ValueError("No active players to pair")

    # Sort/shuffle based on mode
    if mode == "random":
        players = list(active_players)
        random.shuffle(players)
    elif mode == "seeded":
        # Pair by sequence_id: #1 vs #2, #3 vs #4, etc.
        players = sorted(active_players, key=lambda p: p.sequence_id)
    else:
        raise ValueError(f"Invalid pairing mode: {mode}")

    # Create matches
    matches = []
    round_id = uuid4()  # Would come from Round in real implementation

    # Pair players sequentially
    for i in range(0, len(players) - 1, 2):
        match = Match(
            id=uuid4(),
            tournament_id=component.tournament_id,
            component_id=component.id,
            round_id=round_id,
            round_number=1,
            player1_id=players[i].player_id,
            player2_id=players[i + 1].player_id,
            table_number=len(matches) + 1,
        )
        matches.append(match)

    # Handle bye for odd player count
    if len(players) % 2 == 1:
        bye_player = players[-1]  # Last player gets bye
        bye_match = Match(
            id=uuid4(),
            tournament_id=component.tournament_id,
            component_id=component.id,
            round_id=round_id,
            round_number=1,
            player1_id=bye_player.player_id,
            player2_id=None,  # None indicates bye
            player1_wins=2,  # Bye counts as 2-0 win
            player2_wins=0,
            draws=0,
            table_number=None,  # Byes don't get table numbers
        )
        matches.append(bye_match)

    return matches


def generate_bye_losses_for_late_entry(
    registration: TournamentRegistration,
    component: Component,
    current_round: int,
) -> list[Match]:
    """
    Generate bye losses for a player who joined late.

    In Swiss tournaments, players who join after round 1 receive "bye losses"
    for each round they missed. This ensures fair standings calculations.

    Args:
        registration: The late entry tournament registration
        component: Tournament component
        current_round: The current round number (rounds 1 to current_round-1 are missed)

    Returns:
        List of Match objects representing bye losses

    Example:
        Player joins before Round 3:
        - Receives bye loss for Round 1
        - Receives bye loss for Round 2
        - Paired normally from Round 3 onwards
    """
    bye_losses = []

    for round_num in range(1, current_round):
        bye_loss = Match(
            id=uuid4(),
            tournament_id=component.tournament_id,
            component_id=component.id,
            round_id=uuid4(),  # Phantom round ID
            round_number=round_num,
            player1_id=registration.player_id,
            player2_id=None,  # Bye opponent
            player1_wins=0,  # Loss
            player2_wins=2,  # Bye "wins"
            draws=0,
            table_number=None,
        )
        bye_losses.append(bye_loss)

    return bye_losses


def pair_round(
    registrations: list[TournamentRegistration],
    matches: list[Match],
    component: Component,
    config: dict,
    round_number: int,
) -> list[Match]:
    """
    Pair players for rounds 2+ using standings-based bracket pairing.

    Algorithm:
    1. Calculate current standings from previous rounds
    2. Group players into brackets by match points
    3. Within each bracket, pair players avoiding rematches
    4. Handle pair-downs when necessary (player has played all in bracket)
    5. Assign bye to lowest-ranked player if odd count

    Args:
        registrations: List of active tournament registrations
        matches: List of all matches from previous rounds
        component: Tournament component configuration
        config: Tournament configuration (for tiebreakers)
        round_number: The round number to pair

    Returns:
        List of Match objects for this round

    Raises:
        ValueError: If pairing is impossible (all players have played each other)
    """
    # Filter to only active players
    active_players = [
        reg for reg in registrations
        if reg.status.value == "active"
    ]

    if not active_players:
        raise ValueError("No active players to pair")

    # Calculate current standings
    standings = calculate_standings(active_players, matches, config)

    # Build pairing history (who has played whom)
    pairing_history = _build_pairing_history(matches)

    # Check for odd player count and assign bye BEFORE pairing
    bye_player = None
    pairings_standings = standings

    if len(standings) % 2 == 1:
        # Find lowest-ranked player who hasn't had a bye yet
        bye_player = _select_bye_player(standings, matches)
        # Remove bye player from pairing pool
        pairings_standings = [s for s in standings if s.player.player_id != bye_player.player.player_id]

    # Group players into brackets by match points
    brackets = _group_into_brackets(pairings_standings)

    # Pair players within brackets
    new_matches = []
    round_id = uuid4()
    unpaired_players = []

    for match_points, bracket_entries in sorted(brackets.items(), reverse=True):
        # Add any pair-downs from higher brackets
        bracket_players = list(bracket_entries) + unpaired_players
        unpaired_players = []

        # Try to pair players in this bracket
        paired, unpaired = _pair_bracket(
            bracket_players,
            pairing_history,
            component,
            round_id,
            round_number,
            len(new_matches),
        )

        new_matches.extend(paired)
        unpaired_players = unpaired

    # Handle any remaining unpaired players (shouldn't happen with proper algorithm)
    if len(unpaired_players) > 0:
        raise ValueError(
            f"Failed to pair {len(unpaired_players)} players - algorithm error"
        )

    # Add bye match if we have a bye player
    if bye_player is not None:
        bye_match = Match(
            id=uuid4(),
            tournament_id=component.tournament_id,
            component_id=component.id,
            round_id=round_id,
            round_number=round_number,
            player1_id=bye_player.player.player_id,
            player2_id=None,
            player1_wins=2,
            player2_wins=0,
            draws=0,
            table_number=None,
        )
        new_matches.append(bye_match)

    return new_matches


def _select_bye_player(
    standings: list[StandingsEntry],
    matches: list[Match],
) -> StandingsEntry:
    """
    Select the player to receive a bye.

    Swiss pairing rules:
    1. Prefer lowest-ranked player who hasn't had a bye yet
    2. If all have had byes, give to lowest-ranked (minimizes advantage)

    Args:
        standings: Current standings (sorted by rank)
        matches: All previous matches (to check bye history)

    Returns:
        StandingsEntry for the player who should receive the bye
    """
    # Count previous byes for each player
    bye_counts = defaultdict(int)
    for match in matches:
        if match.player2_id is None:  # Bye match
            bye_counts[match.player1_id] += 1

    # Find minimum bye count
    min_byes = min((bye_counts.get(s.player.player_id, 0) for s in standings), default=0)

    # Get players with minimum byes (reverse order = lowest ranked first)
    candidates = [
        s for s in reversed(standings)
        if bye_counts.get(s.player.player_id, 0) == min_byes
    ]

    # Return lowest-ranked candidate
    return candidates[0]


def _build_pairing_history(matches: list[Match]) -> dict[UUID, set[UUID]]:
    """
    Build a mapping of player_id -> set of opponent player_ids.

    Args:
        matches: All matches from previous rounds

    Returns:
        Dictionary mapping each player to set of opponents they've faced
    """
    history = defaultdict(set)

    for match in matches:
        if match.player2_id is not None:  # Skip byes
            history[match.player1_id].add(match.player2_id)
            history[match.player2_id].add(match.player1_id)

    return history


def _group_into_brackets(
    standings: list[StandingsEntry],
) -> dict[int, list[StandingsEntry]]:
    """
    Group players into brackets by match points.

    Args:
        standings: Sorted standings entries

    Returns:
        Dictionary mapping match_points -> list of StandingsEntry objects
    """
    brackets = defaultdict(list)

    for entry in standings:
        brackets[entry.match_points].append(entry)

    return brackets


def _pair_bracket(
    players: list[StandingsEntry],
    pairing_history: dict[UUID, set[UUID]],
    component: Component,
    round_id: UUID,
    round_number: int,
    table_offset: int,
) -> tuple[list[Match], list[StandingsEntry]]:
    """
    Pair players within a bracket, avoiding rematches.

    Uses a greedy algorithm:
    1. Sort players by rank
    2. Pair first player with highest-ranked opponent they haven't played
    3. Repeat until all paired or pair-down needed

    Args:
        players: List of players in this bracket (and pair-downs from above)
        pairing_history: Who has played whom
        component: Tournament component
        round_id: ID for the round being paired
        round_number: Round number
        table_offset: Starting table number

    Returns:
        Tuple of (matches created, unpaired players needing pair-down)
    """
    matches = []
    available = list(players)  # Copy to modify

    while len(available) >= 2:
        # Take the highest-ranked available player
        player1 = available.pop(0)

        # Find best opponent (highest rank that they haven't played)
        opponent_idx = None
        for idx, player2 in enumerate(available):
            # Check if they've already played
            if player2.player.player_id not in pairing_history.get(
                player1.player.player_id, set()
            ):
                opponent_idx = idx
                break

        if opponent_idx is None:
            # No valid opponent in this bracket - needs pair-down
            available.insert(0, player1)  # Put back for pair-down
            break

        # Create the match
        player2 = available.pop(opponent_idx)
        match = Match(
            id=uuid4(),
            tournament_id=component.tournament_id,
            component_id=component.id,
            round_id=round_id,
            round_number=round_number,
            player1_id=player1.player.player_id,
            player2_id=player2.player.player_id,
            table_number=table_offset + len(matches) + 1,
        )
        matches.append(match)

    # Any remaining players need to pair down
    return matches, available
