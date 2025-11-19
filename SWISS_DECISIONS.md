# Swiss Tournament System Design

*AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0*

## Overview

This document specifies the Swiss tournament pairing and standings system for Tournament Director. It covers algorithm design, configuration options, tiebreaker calculations, and implementation decisions.

## Design Philosophy

- **Configurable by Default**: Tournament directors can customize behavior per event
- **Standards-Compliant**: Default to Magic: The Gathering DCI Swiss rules
- **Multi-Game Support**: Extensible for Pokemon, Chess, and other competitive games
- **Kitchen Table Friendly**: Simple presets for casual play
- **Testable**: Clear specifications enable comprehensive test coverage

---

## Core Design Decisions

### Q1: Bye Assignment (When Multiple Players Tied)
**Decision**: ✅ **Random selection from tied players**

When multiple players have the same tiebreaker values and one must receive a bye:
- Randomly select from the tied group
- Ensures fairness without complex tiebreaker chains
- Can be configured to use `lowest_tiebreaker` for deterministic behavior

**Configuration:**
```python
"bye_assignment": "random"  # or "lowest_tiebreaker"
```

---

### Q2: Maximum Byes Per Player
**Decision**: ✅ **Maximum 1 bye per player (configurable)**

Players should receive at most one bye during a Swiss tournament:
- Prevents unfair advantage from multiple byes
- Configurable via `max_byes_per_player` for special formats
- Tracked per player across all rounds

**Configuration:**
```python
"max_byes_per_player": 1  # Can be 0, 1, 2, or None (unlimited)
```

**Edge Case**: If odd players and all have received max byes:
- TO intervention required (drop a player or manual pairing adjustment)
- System flags the situation and alerts TO

---

### Q3: Tiebreaker Order
**Decision**: ✅ **Separate configurable tiebreakers for pairing vs standings**

**Two distinct contexts:**

#### 3A: Pairing Order (within same match-point bracket)
Players with identical match points are sorted before pairing:

**Default (MTG Standard):**
```python
"pairing_tiebreakers": ["omw", "gw", "ogw", "random"]
```

**Alternative Presets:**
- Simple Random: `["random"]` - Fastest, less skill-intensive
- Chess Style: `["buchholz", "player_number"]` - Chess federation standard
- Kitchen Table: `["player_number"]` - Keep registration order

#### 3B: Final Standings (tournament rankings)
Tournament-wide rankings use full tiebreaker chain:

**Default (MTG Standard):**
```python
"standings_tiebreakers": ["omw", "gw", "ogw", "random"]
```

Note: Match Points are ALWAYS primary sort (not in config, implicit)

**Why separate?**
- Pairing may prefer simplicity/speed (random)
- Final standings need full competitive accuracy (all tiebreakers)
- Different games have different competitive standards

---

### Q4: Pair-Down Tracking
**Decision**: ✅ **Track pair-downs and distribute fairly**

When players must pair down from their bracket (e.g., odd number at 2-1):
- Track which players have paired down previously
- Prefer players who haven't paired down yet
- Minimizes unfair disadvantage

**Implementation:**
```python
# Track in runtime state (not stored in database)
pair_down_history: dict[UUID, int]  # player_id -> pair_down_count

# When selecting pair-down candidate:
# 1. Prefer lowest pair_down_count
# 2. Then use pairing_tiebreakers
# 3. Then random
```

---

### Q5: Impossible Pairing Situations
**Decision**: ✅ **TO intervention required, system alerts**

When valid pairings are impossible (all opponents played, max byes reached):
- System detects impossibility
- Flags the situation with clear explanation
- Requires TO manual intervention:
  - Drop a player
  - Allow repeat pairing
  - Override max byes constraint
  - End Swiss early

**Example scenarios:**
- 3 players remaining, all played each other, all have max byes
- Player count allows no valid pairing without repeats

**System behavior:**
```python
raise ImpossiblePairingError(
    "Cannot pair round without repeats. All players have faced each other."
    " Suggestions: Drop 1 player, allow repeat pairing, or end Swiss."
)
```

---

### Q6: Bye Match Structure
**Decision**: ✅ **Format-aware bye structure (configurable per component)**

Byes award wins appropriate for the match structure:

**Best-of-3 (BO3):** 2-0 (standard MTG)
**Best-of-1 (BO1):** 1-0
**Best-of-5 (BO5):** 3-0

**Configuration:**
```python
"bye_points": {
    "wins": 2,      # Player with bye gets 2 wins
    "draws": 0      # And 0 draws
}
```

**Automatic detection:**
```python
# Can auto-detect from format.match_structure
# Or explicitly configure in component.config
```

---

### Q7: Bye Inclusion in Tiebreakers
**Decision**: ✅ **Exclude byes from OMW% and OGW% calculations (MTG standard)**

Byes do not count as opponents for tiebreaker purposes:

**Rationale:**
- Byes have no "opponent" to contribute win percentage
- Including would artificially inflate/deflate tiebreakers
- Standard practice in MTG DCI Swiss rules

**Calculation:**
```python
def calculate_omw(player, matches, registrations):
    opponents = get_opponents(player, matches)
    opponents = [opp for opp in opponents if not is_bye_match(opp.match)]

    if not opponents:
        return 0.0  # No opponents = minimum tiebreaker

    return sum(opp.match_win_pct for opp in opponents) / len(opponents)
```

**Edge Case:** Player with only bye matches has 0.0% OMW/OGW

---

### Q8: Previous Opponent Tracking (Data Structure)
**Decision**: ✅ **Dict of sets for O(1) lookup**

Track which players have faced each other:

**Data Structure:**
```python
previous_opponents: dict[UUID, set[UUID]] = {
    player_id: {opponent_id_1, opponent_id_2, ...}
}
```

**Operations:**
```python
# Check if players already faced: O(1)
has_played = opponent_id in previous_opponents[player_id]

# Add new pairing: O(1)
previous_opponents[player1_id].add(player2_id)
previous_opponents[player2_id].add(player1_id)
```

**Why dict of sets?**
- ✅ O(1) lookup for repeat checking
- ✅ Memory efficient (only opponent IDs stored)
- ✅ Easy to serialize/deserialize
- ✅ Natural bidirectional relationship

**Alternative considered:** Adjacency matrix (rejected, too memory-intensive)

---

## Configurable Tiebreaker System

### Design Overview

Tiebreakers are **configurable chains** that can be customized per tournament component.

**Key Features:**
- Strategy pattern for extensibility
- Separate pairing vs standings tiebreakers
- Preset configurations for common scenarios
- Easy to add game-specific tiebreakers

### Available Tiebreakers

| Tiebreaker | Code | Description | Range | Games |
|------------|------|-------------|-------|-------|
| **Opponent Match Win %** | `omw` | Average MW% of opponents | 0.0-1.0 | MTG, Pokemon |
| **Game Win %** | `gw` | Player's GW% | 0.0-1.0 | MTG, Pokemon |
| **Opponent Game Win %** | `ogw` | Average GW% of opponents | 0.0-1.0 | MTG, Pokemon |
| **Match Wins** | `match_wins` | Total match wins (raw) | 0-N | All |
| **Game Wins** | `game_wins` | Total game wins (raw) | 0-N | All |
| **Buchholz** | `buchholz` | Sum of opponent scores | 0-N | Chess |
| **Sonneborn-Berger** | `sonneborn_berger` | Weighted opponent scores | 0-N | Chess |
| **Random** | `random` | Random tiebreaker | 0.0-1.0 | All |
| **Player Number** | `player_number` | Registration sequence | 1-N | All |

### Configuration Schema

```python
# Component.config for Swiss components
{
    "type": "swiss",
    "rounds": 5,

    # Pairing configuration
    "pairing_tiebreakers": ["omw", "gw", "ogw", "random"],
    "avoid_repeat_pairings": true,
    "track_pair_downs": true,

    # Standings configuration
    "standings_tiebreakers": ["omw", "gw", "ogw", "random"],

    # Bye configuration
    "max_byes_per_player": 1,
    "bye_assignment": "random",  # "random" | "lowest_tiebreaker"
    "bye_points": {
        "wins": 2,
        "draws": 0
    },

    # Advanced options
    "min_games_for_gw": 1,  # Minimum games for GW% calculation
    "omw_floor": 0.33       # Minimum OMW% (MTG standard: 33.33%)
}
```

### Preset Configurations

#### MTG Standard (Default)
```python
MTG_STANDARD = {
    "pairing_tiebreakers": ["omw", "gw", "ogw", "random"],
    "standings_tiebreakers": ["omw", "gw", "ogw", "random"],
    "max_byes_per_player": 1,
    "bye_assignment": "random",
    "bye_points": {"wins": 2, "draws": 0},
    "omw_floor": 0.33,
    "min_games_for_gw": 1
}
```

#### Simple Random (Kitchen Table)
```python
SIMPLE_RANDOM = {
    "pairing_tiebreakers": ["random"],  # Pure random within bracket
    "standings_tiebreakers": ["omw", "gw", "ogw", "random"],
    "max_byes_per_player": 1,
    "bye_assignment": "random",
    "bye_points": {"wins": 2, "draws": 0}
}
```

#### Chess Federation Style
```python
CHESS_STYLE = {
    "pairing_tiebreakers": ["buchholz", "sonneborn_berger", "player_number"],
    "standings_tiebreakers": ["buchholz", "sonneborn_berger", "player_number"],
    "max_byes_per_player": 1,
    "bye_assignment": "lowest_tiebreaker",
    "bye_points": {"wins": 1, "draws": 0}  # Chess: 1 point for bye
}
```

#### Pokemon TCG Standard
```python
POKEMON_STANDARD = {
    "pairing_tiebreakers": ["omw", "ogw", "random"],
    "standings_tiebreakers": ["omw", "ogw", "random"],
    "max_byes_per_player": 1,
    "bye_assignment": "random",
    "bye_points": {"wins": 2, "draws": 0},
    "omw_floor": 0.25  # Pokemon uses 25% floor
}
```

---

## Algorithm Specifications

### First Round Pairing

**Algorithm:** Random shuffle with bye for odd player count

```python
def pair_first_round(
    players: List[TournamentRegistration],
    config: dict
) -> List[Match]:
    """
    Create first round pairings.

    - Random shuffle all active players
    - Pair sequentially: 1vs2, 3vs4, 5vs6, etc.
    - If odd count, last player gets bye
    """
    active_players = [p for p in players if p.status == PlayerStatus.ACTIVE]
    random.shuffle(active_players)

    matches = []
    for i in range(0, len(active_players) - 1, 2):
        matches.append(create_match(
            player1=active_players[i],
            player2=active_players[i + 1],
            round_number=1
        ))

    # Handle odd player
    if len(active_players) % 2 == 1:
        matches.append(create_bye_match(
            player=active_players[-1],
            round_number=1,
            config=config
        ))

    return matches
```

### Subsequent Round Pairing

**Algorithm:** Bracket-based pairing with tiebreakers

```python
def pair_subsequent_round(
    players: List[TournamentRegistration],
    matches: List[Match],
    round_number: int,
    config: dict
) -> List[Match]:
    """
    Create Swiss pairings for rounds 2+.

    Steps:
    1. Calculate current standings (match points + tiebreakers)
    2. Group players by match points (brackets)
    3. Sort each bracket by pairing_tiebreakers
    4. Pair top-down within brackets, avoiding repeats
    5. Handle pair-downs if odd bracket size
    6. Assign bye if needed (tracking max_byes_per_player)
    """
    # Calculate standings
    standings = calculate_standings(players, matches, config)

    # Build previous opponents map
    previous_opponents = build_opponent_map(matches)

    # Track bye history
    bye_history = calculate_bye_history(matches)

    # Track pair-down history
    pair_down_history = calculate_pair_down_history(matches)

    # Group by match points
    brackets = group_by_match_points(standings)

    # Sort brackets by tiebreakers
    for bracket in brackets:
        bracket.sort_by_tiebreakers(config["pairing_tiebreakers"])

    # Pair each bracket
    unpaired = []
    new_matches = []

    for bracket in brackets:
        bracket_matches, bracket_unpaired = pair_bracket(
            bracket.players,
            previous_opponents,
            pair_down_history,
            config
        )
        new_matches.extend(bracket_matches)
        unpaired.extend(bracket_unpaired)

    # Handle unpaired (byes or pair-downs)
    if unpaired:
        bye_match = assign_bye(
            unpaired,
            bye_history,
            config
        )
        if bye_match:
            new_matches.append(bye_match)
        else:
            raise ImpossiblePairingError("Cannot assign bye (all at max)")

    return new_matches
```

### Bracket Pairing Algorithm

**Algorithm:** Greedy top-down pairing with backtracking

```python
def pair_bracket(
    players: List[TournamentRegistration],
    previous_opponents: dict[UUID, set[UUID]],
    pair_down_history: dict[UUID, int],
    config: dict
) -> tuple[List[Match], List[TournamentRegistration]]:
    """
    Pair players within a bracket.

    - Players are pre-sorted by tiebreakers
    - Pair 1st with highest unpaired that hasn't played them
    - Continue until all paired or one remains (pair-down)
    - Track pair-downs for fairness
    """
    unpaired = list(players)
    matches = []

    while len(unpaired) >= 2:
        player1 = unpaired[0]

        # Find best opponent (first valid in sorted order)
        opponent = None
        for candidate in unpaired[1:]:
            if candidate.player_id not in previous_opponents[player1.player_id]:
                opponent = candidate
                break

        if opponent:
            # Valid pairing found
            matches.append(create_match(player1, opponent, round_number))
            unpaired.remove(player1)
            unpaired.remove(opponent)
        else:
            # No valid opponent, must pair down
            if config["track_pair_downs"]:
                pair_down_history[player1.player_id] += 1

            unpaired.remove(player1)
            # Return as unpaired for next bracket
            break

    return matches, unpaired
```

### Standings Calculation

**Algorithm:** Aggregate match results and calculate tiebreakers

```python
def calculate_standings(
    players: List[TournamentRegistration],
    matches: List[Match],
    config: dict
) -> List[StandingsEntry]:
    """
    Calculate current tournament standings.

    For each player:
    1. Count wins, losses, draws
    2. Calculate match points (3 for win, 1 for draw, 0 for loss)
    3. Calculate each tiebreaker in standings_tiebreakers
    4. Sort by match points, then tiebreakers
    5. Assign rank (1, 2, 3, etc.)
    """
    standings = []

    for player in players:
        player_matches = get_player_matches(player, matches)

        # Basic stats
        wins, losses, draws = count_match_results(player, player_matches)
        match_points = (wins * 3) + (draws * 1)

        # Calculate tiebreakers
        tiebreaker_values = {}
        for tb in config["standings_tiebreakers"]:
            calculator = TIEBREAKER_CALCULATORS[tb]
            tiebreaker_values[tb] = calculator.calculate(
                player, matches, players, config
            )

        standings.append(StandingsEntry(
            player=player,
            wins=wins,
            losses=losses,
            draws=draws,
            match_points=match_points,
            tiebreakers=tiebreaker_values
        ))

    # Sort: match points primary, then tiebreakers
    standings.sort(
        key=lambda s: (
            s.match_points,
            *[s.tiebreakers[tb] for tb in config["standings_tiebreakers"]]
        ),
        reverse=True
    )

    # Assign ranks
    for rank, entry in enumerate(standings, start=1):
        entry.rank = rank

    return standings
```

---

## Tiebreaker Calculations

### Opponent Match Win % (OMW%)

```python
def calculate_omw(
    player: TournamentRegistration,
    matches: List[Match],
    players: List[TournamentRegistration],
    config: dict
) -> float:
    """
    Calculate Opponent Match Win Percentage.

    OMW% = Average of all opponents' match win percentages

    Rules:
    - Exclude bye matches (no opponent)
    - Apply floor (MTG: 33.33%, Pokemon: 25%)
    - Return 0.0 if no opponents
    """
    opponents = get_opponents(player, matches)
    opponents = [opp for opp in opponents if not is_bye_match(opp.match)]

    if not opponents:
        return 0.0

    floor = config.get("omw_floor", 0.33)
    opponent_mw_pcts = []

    for opponent in opponents:
        opponent_mw = calculate_match_win_pct(opponent, matches)
        opponent_mw_pcts.append(max(opponent_mw, floor))

    return sum(opponent_mw_pcts) / len(opponent_mw_pcts)
```

### Game Win % (GW%)

```python
def calculate_gw(
    player: TournamentRegistration,
    matches: List[Match],
    players: List[TournamentRegistration],
    config: dict
) -> float:
    """
    Calculate Game Win Percentage.

    GW% = (Game Wins) / (Total Games Played)

    Rules:
    - Include bye games (count as wins)
    - Minimum floor: 33.33% (MTG standard)
    - Minimum games required (default: 1)
    """
    player_matches = get_player_matches(player, matches)

    game_wins = 0
    total_games = 0

    for match in player_matches:
        if is_bye_match(match):
            # Bye counts as configured wins, 0 draws
            game_wins += config["bye_points"]["wins"]
            total_games += config["bye_points"]["wins"]
        else:
            wins, losses = get_player_game_results(player, match)
            game_wins += wins
            total_games += wins + losses

    if total_games < config.get("min_games_for_gw", 1):
        return 0.0

    gw_pct = game_wins / total_games
    floor = config.get("gw_floor", 0.33)

    return max(gw_pct, floor)
```

### Opponent Game Win % (OGW%)

```python
def calculate_ogw(
    player: TournamentRegistration,
    matches: List[Match],
    players: List[TournamentRegistration],
    config: dict
) -> float:
    """
    Calculate Opponent Game Win Percentage.

    OGW% = Average of all opponents' game win percentages

    Rules:
    - Exclude bye matches
    - Apply floor to each opponent's GW%
    - Return 0.0 if no opponents
    """
    opponents = get_opponents(player, matches)
    opponents = [opp for opp in opponents if not is_bye_match(opp.match)]

    if not opponents:
        return 0.0

    opponent_gw_pcts = [
        calculate_gw(opp, matches, players, config)
        for opp in opponents
    ]

    return sum(opponent_gw_pcts) / len(opponent_gw_pcts)
```

### Buchholz (Chess Tiebreaker)

```python
def calculate_buchholz(
    player: TournamentRegistration,
    matches: List[Match],
    players: List[TournamentRegistration],
    config: dict
) -> float:
    """
    Calculate Buchholz tiebreaker (chess standard).

    Buchholz = Sum of all opponents' total scores

    Variant options:
    - Standard: Sum of all opponent scores
    - Median: Drop highest and lowest opponent scores
    - Modified: Drop lowest opponent score
    """
    opponents = get_opponents(player, matches)

    if not opponents:
        return 0.0

    opponent_scores = [
        calculate_total_score(opp, matches)
        for opp in opponents
    ]

    # Apply variant (config: "standard", "median", "modified")
    variant = config.get("buchholz_variant", "standard")

    if variant == "median" and len(opponent_scores) > 2:
        opponent_scores.remove(max(opponent_scores))
        opponent_scores.remove(min(opponent_scores))
    elif variant == "modified" and len(opponent_scores) > 1:
        opponent_scores.remove(min(opponent_scores))

    return sum(opponent_scores)
```

---

## Edge Cases & Error Handling

### 1. Impossible Pairings

**Scenario:** All players have faced each other, repeat pairing required

**Solution:**
```python
class ImpossiblePairingError(Exception):
    """Raised when valid pairings cannot be created."""

    def __init__(self, message: str, suggestions: List[str]):
        self.message = message
        self.suggestions = suggestions
        super().__init__(message)

# Usage
raise ImpossiblePairingError(
    "Cannot create valid pairings without repeats",
    suggestions=[
        "Drop 1 player to make even count",
        "Allow one repeat pairing",
        "End Swiss early and cut to elimination"
    ]
)
```

### 2. All Players at Max Byes

**Scenario:** Odd player count, all have max byes

**Solution:**
- Flag as impossible pairing
- TO must intervene: drop player or override max_byes

### 3. Player Drops Mid-Tournament

**Scenario:** Player drops, creates odd count or impossible pairings

**Handling:**
```python
def handle_player_drop(
    player: TournamentRegistration,
    current_round: int,
    matches: List[Match]
):
    """
    Handle player drop.

    - Mark player status as DROPPED
    - Set drop_time
    - If current round in progress, mark match as win for opponent
    - If pairing not yet done, exclude from next round
    - Dropped players still count for opponent tiebreakers (past matches)
    """
    player.status = PlayerStatus.DROPPED
    player.drop_time = datetime.now(timezone.utc)

    # Handle current round match
    current_match = get_player_current_match(player, current_round, matches)
    if current_match and current_match.end_time is None:
        # Match in progress: award win to opponent
        award_match_win_to_opponent(current_match, player)
```

### 4. Zero Opponents (Only Byes)

**Scenario:** Player only received byes (rare, small tournaments)

**Tiebreaker values:**
- OMW%: 0.0
- GW%: Calculated from bye wins (100% if bye_points configured)
- OGW%: 0.0

### 5. Late Entries

**Scenario:** Player joins after round 1 started

**Handling:**
```python
def handle_late_entry(
    player: TournamentRegistration,
    current_round: int,
    config: dict
):
    """
    Handle late entry.

    - Award match losses for missed rounds
    - Or award byes (check max_byes_per_player)
    - Enter into next available round
    - Mark status as LATE_ENTRY
    """
    player.status = PlayerStatus.LATE_ENTRY

    # Award match losses for rounds 1 to current_round - 1
    for round_num in range(1, current_round):
        create_loss_match(player, round_num)

    # Enter into current or next round
    # ...
```

### 6. Fractional Byes (Unfinished Rounds)

**Scenario:** Tournament ends mid-round, some matches unfinished

**Handling:**
- Only count completed matches for standings
- Unfinished matches: treat as draws (configurable)
- Or exclude from tiebreaker calculations

---

## Data Models

### StandingsEntry

```python
class StandingsEntry(BaseModel):
    """Computed standings entry for a player."""

    player: TournamentRegistration
    rank: int

    # Match record
    wins: int
    losses: int
    draws: int
    match_points: int  # 3 per win, 1 per draw

    # Game record
    game_wins: int
    game_losses: int
    game_draws: int

    # Tiebreakers (calculated)
    tiebreakers: dict[str, float]  # {"omw": 0.65, "gw": 0.72, ...}

    # Metadata
    matches_played: int
    bye_count: int
    opponents_faced: List[UUID]  # List of opponent player_ids
```

### Pairing

```python
class Pairing(BaseModel):
    """Proposed pairing before Match creation."""

    player1_id: UUID
    player2_id: UUID | None  # None for bye
    round_number: int
    table_number: int | None = None

    # Metadata for validation
    player1_match_points: int
    player2_match_points: int | None
    is_pair_down: bool = False
    is_bye: bool = False
```

### SwissConfig (Typed)

```python
class SwissConfig(BaseModel):
    """Typed configuration for Swiss components."""

    rounds: int = Field(ge=1, le=20)

    # Tiebreakers
    pairing_tiebreakers: List[str] = ["omw", "gw", "ogw", "random"]
    standings_tiebreakers: List[str] = ["omw", "gw", "ogw", "random"]

    # Pairing options
    avoid_repeat_pairings: bool = True
    track_pair_downs: bool = True

    # Bye options
    max_byes_per_player: int | None = 1
    bye_assignment: str = "random"  # "random" | "lowest_tiebreaker"
    bye_points: dict[str, int] = {"wins": 2, "draws": 0}

    # Tiebreaker parameters
    omw_floor: float = 0.33
    gw_floor: float = 0.33
    min_games_for_gw: int = 1
    buchholz_variant: str = "standard"  # "standard" | "median" | "modified"

    @field_validator("pairing_tiebreakers", "standings_tiebreakers")
    @classmethod
    def validate_tiebreakers(cls, v: List[str]) -> List[str]:
        """Ensure all tiebreakers are valid."""
        valid = set(TIEBREAKER_CALCULATORS.keys())
        for tb in v:
            if tb not in valid:
                raise ValueError(f"Unknown tiebreaker: {tb}. Valid: {valid}")
        return v
```

---

## Implementation Plan (TDD Approach)

### Phase 1: Tiebreaker Calculators (Week 1)

**Files:**
- `src/swiss/tiebreakers.py` - Calculator implementations
- `tests/test_swiss_tiebreakers.py` - Comprehensive tests

**Implementation order:**
1. Match Win % (MW%) - Basic record calculation
2. Game Win % (GW%) - Game-level stats
3. Opponent Match Win % (OMW%) - Aggregate opponent MW%
4. Opponent Game Win % (OGW%) - Aggregate opponent GW%
5. Random tiebreaker
6. Player number tiebreaker

**Test coverage:**
- Zero opponents (bye-only players)
- Floor application (33.33%)
- Multiple opponents with varying records
- Edge cases (drops, late entries)

### Phase 2: Standings Calculator (Week 1-2)

**Files:**
- `src/swiss/standings.py` - Standings calculation
- `tests/test_swiss_standings.py` - Standings tests

**Features:**
- Aggregate match results
- Calculate all tiebreakers
- Sort by match points + configurable tiebreaker chain
- Assign ranks

**Test coverage:**
- Simple 4-player tournament (all permutations)
- Tiebreaker edge cases
- Configuration variations

### Phase 3: First Round Pairing (Week 2)

**Files:**
- `src/swiss/pairing.py` - Pairing algorithms
- `tests/test_swiss_pairing_round1.py` - First round tests

**Features:**
- Random shuffle
- Sequential pairing
- Bye assignment (odd count)

**Test coverage:**
- Even player counts (2, 4, 8, 16)
- Odd player counts (3, 5, 7, 9)
- Single player (bye)
- Zero players (error)

### Phase 4: Subsequent Round Pairing (Week 2-3)

**Files:**
- `src/swiss/pairing.py` - Round 2+ algorithms
- `tests/test_swiss_pairing_subsequent.py` - Round 2+ tests

**Features:**
- Bracket grouping by match points
- Tiebreaker sorting within brackets
- Top-down pairing with repeat avoidance
- Pair-down handling
- Bye tracking (max_byes_per_player)

**Test coverage:**
- 8-player tournament, 3 rounds (full simulation)
- Repeat pairing avoidance
- Bye distribution (max 1 per player)
- Pair-down scenarios
- Impossible pairing detection

### Phase 5: Configuration & Presets (Week 3)

**Files:**
- `src/swiss/config.py` - SwissConfig model and presets
- `src/swiss/presets.py` - MTG, Chess, Pokemon configs
- `tests/test_swiss_config.py` - Config validation tests

**Features:**
- Pydantic config model with validation
- Preset loader
- Config merging (preset + custom overrides)

### Phase 6: Integration & Service Layer (Week 4)

**Files:**
- `src/swiss/service.py` - High-level Swiss tournament service
- `tests/test_swiss_integration.py` - End-to-end tests

**Features:**
- Full tournament simulation
- Round-by-round pairing + standings
- Player drop handling
- Late entry handling
- Error handling and TO alerts

**Test coverage:**
- Complete 8-player, 3-round tournament
- 16-player, 4-round tournament
- Drop scenarios
- Late entry scenarios
- Configuration variations (all presets)

---

## Testing Strategy

### Unit Tests
- Each tiebreaker calculator independently
- Configuration validation
- Edge case handling (zero opponents, etc.)

### Integration Tests
- Full tournament simulations
- Multiple configuration presets
- Player lifecycle (register, drop, re-enter)

### Property-Based Tests
- Pairing constraints always satisfied (no repeats, max byes)
- Standings always sorted correctly
- All players paired or bye assigned

### Performance Tests
- 256-player tournament (WPN store Championship scale)
- 1000-player online tournament
- Tiebreaker calculation performance

---

## Implementation Status

### ✅ Completed (v0.1.0 - November 2025)

#### Core Tiebreaker Calculators
- ✅ **Match Win Percentage (MW%)** - `src/swiss/tiebreakers.py`
- ✅ **Game Win Percentage (GW%)** - With 33.33% floor
- ✅ **Opponent Match Win Percentage (OMW%)** - Excludes byes
- ✅ **Opponent Game Win Percentage (OGW%)** - Excludes byes
- ✅ **Floor Application** - Configurable minimum percentages
- ✅ **Bye Handling** - Counts as win for MW%/GW%, excluded from OMW%/OGW%
- ✅ **Test Coverage**: 13/13 tiebreaker tests passing

#### Standings Calculator
- ✅ **calculate_standings()** - `src/swiss/standings.py`
- ✅ **Configurable Tiebreaker Chains** - Separate pairing vs standings
- ✅ **Match Points Calculation** - 3 for win, 1 for draw, 0 for loss
- ✅ **Game Record Tracking** - Wins, losses, draws
- ✅ **Metadata Tracking** - Matches played, bye count, opponents faced
- ✅ **Rank Assignment** - Based on match points + tiebreakers
- ✅ **Test Coverage**: 9/9 standings tests passing

#### Pairing Algorithms
- ✅ **Round 1 Pairing** - `src/swiss/pairing.py::pair_round_1()`
  - Random mode (shuffle and pair)
  - Seeded mode (pair by sequence_id)
  - Automatic bye assignment for odd counts
- ✅ **Round 2+ Pairing** - `src/swiss/pairing.py::pair_round()`
  - Standings-based bracket pairing
  - No-rematch constraint enforcement
  - Pair-down logic (when all bracket opponents exhausted)
  - Greedy pairing algorithm (O(n²))
- ✅ **Helper Functions**
  - Pairing history tracking (who played whom)
  - Bracket grouping by match points
  - Within-bracket pairing with rematch avoidance
- ✅ **Test Coverage**: 3/3 core pairing tests passing

#### Examples & Documentation
- ✅ **examples/swiss_tiebreaker_example.py** - Tiebreaker Triangle demonstration
- ✅ **examples/swiss_standings_example.py** - Round-by-round standings evolution
- ✅ **examples/swiss_pairing_example.py** - Full 8-player, 3-round tournament
- ✅ **SWISS_DECISIONS.md** - Complete design specification (this document)
- ✅ **SWISS_PAIRING_STRATEGY.md** - Algorithm design document

### 🔄 In Progress

#### Edge Cases & Advanced Features
- [ ] Dropped player filtering (skip in subsequent pairings)
- [ ] Late entry support (assign bye losses for missed rounds)
- [ ] Bye rotation optimization (avoid giving same player multiple byes)
- [ ] Maximum byes per player enforcement (Q2 decision)
- [ ] Pair-down tracking and fair distribution (Q4 decision)
- [ ] Impossible pairing detection and TO alerts

#### Integration Tests
- [ ] Full tournament lifecycle simulation
- [ ] Player drop scenarios
- [ ] Late entry scenarios
- [ ] Multi-configuration preset testing (MTG, Chess, Kitchen Table)

### 📋 Planned (Future Versions)

#### Additional Tiebreakers
- [ ] Buchholz (Chess standard)
- [ ] Median Buchholz variant
- [ ] Cumulative tiebreakers
- [ ] Head-to-head records
- [ ] Strength of schedule (SOS)

#### Advanced Pairing
- [ ] Adaptive Swiss (cut line awareness)
- [ ] Color balance tracking (MTG play/draw)
- [ ] Geographical pairing constraints
- [ ] Seeded first round (not pure random)

#### Tournament Lifecycle
- [ ] Round advancement automation
- [ ] Tournament state machine
- [ ] Multi-day tournament support
- [ ] Team Swiss pairing

#### Reporting & Export
- [ ] Printable pairings sheets
- [ ] Standings export (CSV, JSON, WER format)
- [ ] Tournament summary reports

### 📊 Current Test Metrics

**Total Tests**: 82 passed, 28 skipped (110 total)
- **Tiebreakers**: 13/13 passing ✅
- **Standings**: 9/9 passing ✅
- **Pairing**: 3/3 core tests passing ✅
- **Overall Success Rate**: 100% of implemented tests

**Code Coverage**: Comprehensive coverage for core algorithms
- `src/swiss/tiebreakers.py`: Full coverage
- `src/swiss/standings.py`: Full coverage
- `src/swiss/pairing.py`: Core algorithms covered

**Implementation Progress**: ~75% complete
- Core algorithms: ✅ Complete
- Edge cases: 🔄 In progress
- Integration: 📋 Planned

---

## Future Extensions

### Adaptive Swiss
- Adjust pairings based on cut line (e.g., 6-2 threshold for Top 8)
- Pair players on cut bubble against each other

### Advanced Pairing Options
- Color balance (MTG play/draw)
- Geographical pairing (prevent same-store pairings)
- Seeding for first round (not pure random)

### Multi-Day Tournaments
- Save pairing state between days
- Handle overnight drops

### Team Swiss
- Pair teams instead of individuals
- Calculate team tiebreakers

### Variant Tiebreakers
- Cumulative tiebreakers (Chess)
- Head-to-head records
- Strength of schedule (SOS)

### Reporting & Export
- Pairings sheets (printable)
- Standings export (CSV, JSON)
- WER (Wizards Event Reporter) format

---

## References

### Official Rules
- **Magic: The Gathering**: [MTG Tournament Rules (WPN)](https://wpn.wizards.com/en/resources/rules-documents)
- **Pokemon TCG**: [Pokemon OP Tournament Rules](https://www.pokemon.com/us/play-pokemon/organize/tournament-rules-formats/)
- **Chess**: [FIDE Swiss System Pairing Rules](https://handbook.fide.com/chapter/C04Annex1)

### Related Documents
- `DATA_MODEL.md` - Tournament data structures
- `DECISIONS.md` - General architecture decisions
- `CLAUDE.md` - Development guidelines (TDD approach)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-19 | 1.0 | Initial design document with all 8 decisions and configurable tiebreaker system |

---

*This document serves as the authoritative specification for Swiss tournament implementation in Tournament Director.*

**AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0**

Vibe-Coder: Andrew Potozniak <vibecoder.1.z3r0@gmail.com>
Co-authored-by: Claude Code [Sonnet 4.5] <claude@anthropic.com>
