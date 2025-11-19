# Tournament Director TUI

*AIA PAI Hin R Claude Code v1.0 // AIA Primarily AI, Human-initiated, Reviewed, Claude Code v1.0 // This work was primarily AI-generated. AI was prompted for its contributions, or AI assistance was enabled. AI-generated content was reviewed and approved. The following model(s) or application(s) were used: Claude Code.*

## Project Overview
A Terminal User Interface (TUI) application built with Python and Textual framework for tournament management and direction.

## AI Attribution
AIA PAI Hin R Claude Code v1.0 // AIA Primarily AI, Human-initiated, Reviewed, Claude Code v1.0 // This work was primarily AI-generated. AI was prompted for its contributions, or AI assistance was enabled. AI-generated content was reviewed and approved. The following model(s) or application(s) were used: Claude Code.

## Licensing
This project is dual-licensed under:
- **MIT License** - Primary license for legal certainty and broad compatibility
- **Vibe-Coder License (VCL-0.1-Experimental)** - Secondary license for those who serve the vibe

The VCL is a novelty license created for fun and cultural purposes with no legal bearing. The MIT license provides the legally binding terms.

## Development Team
- **Vibe Coder**: Andrew Potozniak <tyraziel@gmail.com>
- **AI Assistant**: Claude Code (Anthropic)

---

## Table of Contents

1. [Design Principles](#design-principles-based-on-mtga-mythic-tracker-tui)
2. [Project Structure](#project-structure-convention)
3. [Development Commands](#development-commands)
4. [Backend Architecture](#backend-architecture)
5. [Project Status](#project-status)
6. [AI Attribution (AIA) Requirements](#ai-attribution-aia-requirements)
7. [Test-Driven Development (TDD) Methodology](#test-driven-development-tdd-methodology)
8. [Code Coverage Standards](#code-coverage-standards)
9. [Refactoring Guidelines](#refactoring-guidelines)
10. [Code Quality Standards](#code-quality-standards)
11. [Project-Specific Conventions](#project-specific-conventions)
12. [Development Environment](#development-environment)
13. [Development Workflow](#development-workflow)

---

## Design Principles (Based on MTGA Mythic Tracker TUI)

### Architecture Philosophy
- **Modular Design**: Clear separation of concerns with dedicated modules
- **Type Safety**: Pydantic validation for all data models
- **Error Handling**: Comprehensive error handling for file I/O and parsing
- **Testing Strategy**: Each component has dedicated test files
- **Configuration Management**: JSON-based settings with validation

### TUI Framework Standards
- **Textual Framework**: Professional terminal user interface using Python Textual
- **Clean Layout**: Side-panel designs with clear information hierarchy
- **Keyboard Navigation**: Intuitive keybindings for all major actions
- **Real-time Updates**: Live data updates without screen flicker
- **Visual Indicators**: Clear status indicators and progress displays

### Code Quality Standards
- **Type Hints**: Type annotations throughout codebase
- **Documentation**: Comprehensive inline documentation
- **Import Organization**: Clean, organized imports
- **Consistent Naming**: Clear, descriptive variable and function names
- **No Unnecessary Comments**: Code should be self-documenting

### Project Structure Convention
```
project-root/
├── src/
│   ├── models/          # Data structures and business logic
│   ├── config/          # Configuration management
│   ├── core/            # Application state and management
│   ├── ui/              # TUI framework components
│   └── utils/           # Utility functions and helpers
├── tests/               # Test files (test_*.py format)
├── requirements.txt     # Python dependencies
├── main.py              # Main application entry point
├── CLAUDE.md            # Technical documentation
└── README.md            # User-facing documentation
```

### Development Practices
- **Virtual Environment**: Use dedicated venv for dependencies
- **Session Tracking**: Log development sessions in VIBE-CODING.md
- **Prompt Logging**: Track all AI interactions for context
- **Git Practices**: No automatic commits unless explicitly requested
- **Testing Focus**: Comprehensive test coverage with mock data
- **Vibe-Coder Principles**: Follow the Vibe-Coder Codex guidelines
  - "Serve the vibe" in all development decisions
  - Embrace collaborative AI development with proper attribution
  - Practice "trust but validate" with AI-generated code
  - Take Sacred Pauses when needed for alignment

### TUI Design Patterns
- **Panel-based Layout**: Multiple information panels with clear separation
- **Context Switching**: Tab navigation between different views
- **Status Bars**: Always-visible status and control information
- **Modal Dialogs**: For configuration and detailed input forms
- **Live Data**: Real-time updates for dynamic information

### Configuration Management
- **Default Paths**: Use `~/.config/app-name/` for user configuration
- **JSON Format**: Human-readable configuration files
- **Auto-detection**: Intelligent path detection where possible
- **Validation**: Pydantic models for configuration validation
- **CLI Override**: Command-line arguments override config files

### State Management
- **Persistence**: Automatic state saving for crash recovery
- **Session Management**: Track user sessions with start/stop/pause
- **Live State**: Maintain application state across restarts
- **Data Integrity**: Validation and error recovery for corrupted state

---

## Development Commands

### Setup
```bash
# Set up virtual environment
python3 -m venv ~/.venv-tui
source ~/.venv-tui/bin/activate
pip install -r requirements.txt
```

### Running
```bash
# Activate virtual environment first
source ~/.venv-tui/bin/activate

# Run main application
python3 main.py

# Show command line options
python3 main.py --help
```

### Testing
```bash
# Run all tests (activate venv first)
source ~/.venv-tui/bin/activate
python3 -m pytest tests/ -v

# Or run individual test files
python3 test_models.py
python3 test_config.py
```

## Git Policy
- **No Automatic Git Operations**: Never run git add, git commit, or git push unless explicitly requested by user
- **Manual Control**: All version control operations must be human-initiated
- **Branch Safety**: Never create or switch branches automatically

---

## Backend Architecture

The Tournament Director uses a **three-backend data layer architecture** for maximum flexibility:

### Backend Types
1. **Mock Backend** - In-memory storage for testing and development
2. **Local JSON Backend** - File-based persistence for standalone tournaments
3. **Database Backend** - PostgreSQL/SQLite for production (future implementation)

### Data Layer Interface
All backends implement the same abstract interface:
```python
from src.data import DataLayer

# Swap backends seamlessly
data_layer = MockDataLayer()           # For testing
data_layer = LocalDataLayer("./data")  # For file storage
data_layer = DatabaseDataLayer(db_url) # For production (future)

# Same API for all backends
players = await data_layer.players.list_all()
tournament = await data_layer.tournaments.get_by_id(tournament_id)
```

### Repository Pattern
Each entity has its own repository with full CRUD operations:
- `PlayerRepository` - Player management and lookups
- `TournamentRepository` - Tournament lifecycle and queries
- `RegistrationRepository` - Player registration and sequence IDs
- `MatchRepository` - Match results and tournament progress
- And more...

### Backend Selection Guide
- **Mock**: Unit testing, development, API prototyping
- **Local JSON**: Single-user tournaments, version control, backup/restore
- **Database**: Multi-user production, concurrent access, advanced queries

---

## Project Status

### Technical Stack
- **Language**: Python 3.7+
- **TUI Framework**: Textual
- **Validation**: Pydantic
- **Configuration**: JSON
- **Testing**: pytest
- **Development**: Claude Code AI assistance

### ✅ Completed
- Complete Pydantic data models with validation
- Abstract data layer interface design
- Mock backend (in-memory) implementation
- Local JSON backend with file persistence
- Comprehensive seed data generation
- Foreign key validation and data integrity
- Test coverage for all components
- **Swiss tiebreaker calculators** (MW%, GW%, OMW%, OGW%)
- **Swiss standings calculator** (with configurable tiebreaker chains)
- **Swiss pairing engine** (Round 1 + Round 2+ with no-rematch enforcement)
- **Swiss tournament examples** (tiebreakers, standings, full 3-round pairing demo)
- **Swiss edge case handling** (dropped players, late entries, bye rotation)
- **Tournament lifecycle management** (round completion detection, round advancement)
- **Comprehensive logging framework** (INFO/DEBUG levels, file rotation, structured logging)
- **Full tournament integration tests** (8-player, 7-player with byes, drops & late entries)
- **Impossible pairing detection** with Tournament Organizer guidance
- **Minimum tournament size validation** (2+ players)

### 🔄 In Progress
- FastAPI server with backend abstraction
- REST endpoints for all CRUD operations

### 📋 Planned
- Database backend (SQLAlchemy + PostgreSQL/SQLite)
- Textual TUI implementation
- Discord bot integration
- Elimination bracket pairing (single/double elimination)
- Tournament state machine (PENDING → IN_PROGRESS → COMPLETED)

### Next Steps
1. Complete FastAPI server implementation
2. Add authentication and authorization
3. Build TUI framework consuming API
4. Implement tournament state machine
5. Add Discord bot integration
6. Production deployment setup

---

# AI Development Guidelines

*AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0*

This section provides technical guidelines for AI-assisted development on the Tournament Director project. All AI assistants (Claude, Copilot, etc.) should follow these practices to maintain code quality, test coverage, and proper attribution.

---

## AI Attribution (AIA) Requirements

### Mandatory Attribution

All AI-generated or AI-assisted code MUST include proper attribution following the **AIA (AI Attribution) standard**.

### Attribution Format

**Tournament Director uses the following AIA attribution format:**

#### Short Form (for file headers and inline comments):
```
AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
```

Where:
- **AIA** = AI Attribution
- **EAI** = Entirely AI-generated
- **Hin** = Human-initiated
- **R** = Reviewed (by human)
- **Claude Code [Sonnet 4.5]** = The AI model/tool used
- **v1.0** = Version number

#### Long Form (for documentation and detailed attribution):
```
AIA Entirely AI, Human-initiated, Reviewed, Claude Code [Sonnet 4.5] v1.0

This work was entirely AI-generated. AI was prompted for its contributions, or
AI assistance was enabled. AI-generated content was reviewed and approved. The
following model(s) or application(s) were used: Claude Code [Sonnet 4.5].
```

**Official AIA Statement:**
https://aiattribution.github.io/statements/AIA-EAI-Hin-R-?model=Claude%20Code%20%5BSonnet%204.5%5D-v1.0

### Using Different AI Models

The examples in this document use **Claude Code [Sonnet 4.5]** as the primary AI assistant. If using a different AI model or tool, adjust the attribution accordingly:

**Claude Model Variants:**
- **Claude Sonnet 4.5** (current): `Claude Code [Sonnet 4.5]`
- **Claude Opus 4**: `Claude Code [Opus 4]`
- **Claude Haiku 4**: `Claude Code [Haiku 4]`

**Other AI Tools:**
- **GitHub Copilot**: `GitHub Copilot`
- **Cursor AI**: `Cursor AI`
- **Custom AI assistants**: Use the appropriate model name and version

**Co-authorship Examples:**

For Claude Opus:
```
Co-authored-by: Claude Code [Opus 4] <claude@anthropic.com>
```

For GitHub Copilot:
```
Co-authored-by: GitHub Copilot <copilot@github.com>
```

For Cursor AI:
```
Co-authored-by: Cursor AI <ai@cursor.sh>
```

**Important:** AI models should self-identify in their commit messages with accurate model information. Always verify the attribution matches the actual AI tool being used.

### File Headers

Every new file created with AI assistance must include:

```python
"""
Module description here.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""
```

**Example:**
```python
"""
Tournament pairing algorithms for Swiss-system tournaments.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""
```

For files with multiple AI contributions over time:
```python
"""
Tournament pairing algorithms for Swiss-system tournaments.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - 2025-01-15 - Initial implementation
AIA PAI Hin R Claude Code [Sonnet 4.5] v1.0 - 2025-01-16 - Refactored for async (Partial AI)
"""
```

#### Significant Code Changes

For substantial modifications (>50 lines or core logic changes), add inline attribution:

```python
# AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
def calculate_omw_percentage(player: Player, rounds: list[Round]) -> float:
    """Calculate Opponent Match Win Percentage for tiebreaker."""
    # Implementation here
```

Or with date and description for clarity:
```python
# AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - 2025-01-15 - OMW% tiebreaker implementation
def calculate_omw_percentage(player: Player, rounds: list[Round]) -> float:
    """Calculate Opponent Match Win Percentage for tiebreaker."""
    # Implementation here
```

#### Commit Messages

All commits with AI assistance must include attribution and co-authorship in the commit message:

**Short form (standard commits):**
```bash
git commit -m "Add Swiss pairing algorithm

- Implemented first round random pairing
- Added OMW% tiebreaker calculation
- Test coverage: 92%

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0

Vibe-Coder: Andrew Potozniak <vibecoder.1.z3r0@gmail.com>
Co-authored-by: Claude Code [Sonnet 4.5] <claude@anthropic.com>"
```

**Long form (detailed commits with full attribution):**
```bash
git commit -m "Add Swiss pairing algorithm

Implemented Swiss-system pairing algorithm with proper tiebreakers.

Features:
- First round random pairing
- Subsequent rounds paired by standings
- OMW%/GW%/OGW% tiebreaker support
- Comprehensive test coverage

AIA Entirely AI, Human-initiated, Reviewed, Claude Code [Sonnet 4.5] v1.0

This work was entirely AI-generated. AI was prompted for its contributions, or
AI assistance was enabled. AI-generated content was reviewed and approved. The
following model(s) or application(s) were used: Claude Code [Sonnet 4.5].

Vibe-Coder: Andrew Potozniak <vibecoder.1.z3r0@gmail.com>
Co-authored-by: Claude Code [Sonnet 4.5] <claude@anthropic.com>"
```

**Required commit trailer lines:**
- `Vibe-Coder: Andrew Potozniak <vibecoder.1.z3r0@gmail.com>` - Project lead attribution
- `Co-authored-by: Claude Code [Sonnet 4.5] <claude@anthropic.com>` - AI co-authorship

#### Session Tracking

Update `VIBE-CODING.md` with session details:
- Date and duration
- AI model and version
- Features/changes implemented
- Test coverage added
- Issues encountered and resolved

---

## Test-Driven Development (TDD) Methodology

### Core Principle: Red-Green-Refactor

Tournament Director follows **strict TDD practices**. All new features and bug fixes MUST follow the Red-Green-Refactor cycle:

```
🔴 RED → 🟢 GREEN → 🔵 REFACTOR
```

### The TDD Cycle

#### 1. 🔴 RED - Write a Failing Test

**ALWAYS write tests FIRST, before implementation.**

```python
# tests/test_pairing.py
def test_swiss_pairing_first_round_random():
    """Test that first round pairing is randomized."""
    # AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - Created test for first round pairing
    tournament = create_test_tournament(player_count=8)

    # This test WILL FAIL initially - that's expected!
    pairings = swiss_pair_first_round(tournament)

    assert len(pairings) == 4
    assert all(p.player1 != p.player2 for p in pairings)
    assert all_players_paired_once(pairings)
```

**Verify the test fails:**
```bash
pytest tests/test_pairing.py::test_swiss_pairing_first_round_random -v
# Expected: FAILED (because function doesn't exist yet)
```

#### 2. 🟢 GREEN - Write Minimal Implementation

Write **just enough code** to make the test pass:

```python
# src/pairing/swiss.py
def swiss_pair_first_round(tournament: Tournament) -> list[Pairing]:
    """Pair players randomly for first round of Swiss."""
    # AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - Minimal implementation for first round
    players = list(tournament.players)
    random.shuffle(players)

    pairings = []
    for i in range(0, len(players), 2):
        pairings.append(Pairing(player1=players[i], player2=players[i+1]))

    return pairings
```

**Verify the test passes:**
```bash
pytest tests/test_pairing.py::test_swiss_pairing_first_round_random -v
# Expected: PASSED
```

#### 3. 🔵 REFACTOR - Improve Without Breaking Tests

Now improve the code while keeping tests green:

```python
# src/pairing/swiss.py
def swiss_pair_first_round(tournament: Tournament) -> list[Pairing]:
    """
    Pair players randomly for first round of Swiss.

    AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - Refactored with validation and type safety
    """
    if len(tournament.players) % 2 != 0:
        raise ValueError("Tournament must have even number of players")

    players = list(tournament.players)
    random.shuffle(players)

    return [
        Pairing(player1=players[i], player2=players[i+1])
        for i in range(0, len(players), 2)
    ]
```

**Verify tests still pass after refactoring:**
```bash
pytest tests/test_pairing.py -v
# All tests must remain PASSED
```

### TDD Workflow Checklist

For EVERY new feature or bug fix:

- [ ] Write failing test(s) that define the desired behavior
- [ ] Run tests to verify they fail (🔴 RED)
- [ ] Write minimal implementation to pass tests
- [ ] Run tests to verify they pass (🟢 GREEN)
- [ ] Refactor code for quality and maintainability
- [ ] Run tests to verify they still pass (🔵 REFACTOR)
- [ ] Run full test suite to prevent regressions
- [ ] Check coverage to ensure new code is tested
- [ ] Update AIA attribution in code and commit message

### Testing Philosophy

> **"If it's not tested, it's broken."**

**Key principles:**

1. **Test behavior, not implementation** - Tests should validate what the code does, not how it does it
2. **One assertion per test** - Keep tests focused and maintainable (when practical)
3. **Arrange-Act-Assert (AAA)** - Structure tests clearly:
   ```python
   def test_player_registration():
       # ARRANGE - Set up test data
       tournament = create_test_tournament()
       player = create_test_player(name="Alice")

       # ACT - Execute the behavior
       registration = tournament.register_player(player)

       # ASSERT - Verify the outcome
       assert registration.player_id == player.id
       assert registration.sequence_id == 1
   ```
4. **Test edge cases** - Empty lists, None values, boundary conditions
5. **Test error cases** - Validate exceptions and error messages
6. **Async tests** - Use `pytest-asyncio` for async code:
   ```python
   @pytest.mark.asyncio
   async def test_async_save():
       data_layer = LocalDataLayer("./test_data")
       result = await data_layer.players.create(test_player)
       assert result.id == test_player.id
   ```

---

## Code Coverage Standards

### Minimum Coverage Requirements

Tournament Director enforces **strict coverage standards**:

| Component | Minimum Coverage | Target Coverage |
|-----------|-----------------|-----------------|
| **Models** (`src/models/`) | 95% | 100% |
| **Data Layer** (`src/data/`) | 90% | 95% |
| **Business Logic** | 85% | 90% |
| **UI/TUI** (`src/ui/`) | 70% | 80% |
| **Overall Project** | 85% | 90% |

### Configuring Coverage

Add `pytest-cov` to development dependencies:

```bash
pip install pytest-cov
```

**Run tests with coverage:**
```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=85
```

**Add to `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=85"
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

### Coverage Workflow

**Before submitting code:**

1. **Check current coverage:**
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

2. **Identify untested code:**
   Look for lines marked with `!` in the coverage report

3. **Write tests for uncovered code:**
   Follow TDD cycle for missing coverage

4. **Verify improvement:**
   ```bash
   pytest --cov=src --cov-report=html
   open htmlcov/index.html  # View detailed coverage report
   ```

5. **Add coverage badge** (future):
   Integrate with GitHub Actions to display coverage badge in README

---

## Refactoring Guidelines

### When to Refactor

Refactor code when you notice:

- Code duplication (DRY violation)
- Long functions (>50 lines)
- Complex conditionals (nested if/else)
- Poor naming or unclear intent
- Performance bottlenecks
- Type safety issues

### Refactoring Safety Rules

**NEVER refactor without tests!**

#### Pre-Refactoring Checklist

- [ ] Ensure comprehensive test coverage for the code to refactor (≥90%)
- [ ] All existing tests pass (🟢 GREEN)
- [ ] Understand the current behavior completely
- [ ] Have a clear refactoring goal in mind

#### Refactoring Workflow

1. **Verify Green State**
   ```bash
   pytest tests/ -v
   # All tests MUST pass before refactoring
   ```

2. **Make Small, Incremental Changes**
   - Refactor one thing at a time
   - Run tests after each change
   - Commit frequently

3. **Update Tests if Behavior Changes**
   ```python
   # BEFORE refactoring
   def test_old_behavior():
       result = old_function(input)
       assert result == expected_old_output

   # AFTER refactoring (if behavior changed intentionally)
   def test_new_behavior():
       result = new_function(input)
       assert result == expected_new_output
   ```

4. **Maintain or Improve Coverage**
   ```bash
   # Check coverage didn't decrease
   pytest --cov=src --cov-fail-under=85
   ```

5. **Update Documentation and Attribution**
   ```python
   """
   Refactored module for clarity and performance.

   AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - 2025-01-15 - Original implementation
   AIA PAI Hin R Claude Code [Sonnet 4.5] v1.0 - 2025-01-20 - Refactored for async/await pattern
   """
   ```

#### Test Maintenance During Refactoring

**Scenario 1: Internal Refactoring (No API Change)**
- Tests should NOT change
- If tests break, the refactoring changed behavior (likely a bug)

**Scenario 2: API Refactoring (Signature Changes)**
- Update test setup to use new API
- Verify same behavior with new interface
- Consider deprecation warnings for gradual migration

**Scenario 3: Behavior Change (Intentional)**
- Mark old tests with `@pytest.mark.skip(reason="Replaced by new behavior")`
- Write new tests for new behavior following TDD
- Document the change in DECISIONS.md

**Example - Safe Refactoring:**
```python
# BEFORE: Synchronous implementation
def save_player(player: Player) -> None:
    with open(f"players/{player.id}.json", "w") as f:
        json.dump(player.model_dump(), f)

# Test before refactoring
def test_save_player():
    player = Player(id=UUID4, name="Alice")
    save_player(player)
    assert Path(f"players/{player.id}.json").exists()

# AFTER: Async refactoring
async def save_player(player: Player) -> None:
    """Save player to JSON file asynchronously."""
    # AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - Refactored to async
    async with aiofiles.open(f"players/{player.id}.json", "w") as f:
        await f.write(json.dumps(player.model_dump()))

# Updated test (same behavior, different API)
@pytest.mark.asyncio
async def test_save_player():
    player = Player(id=UUID4, name="Alice")
    await save_player(player)  # Added await
    assert Path(f"players/{player.id}.json").exists()
```

---

## Code Quality Standards

### Type Safety (MyPy)

**All code must pass strict type checking.**

```bash
mypy src/ --strict
```

**Type hints are mandatory:**
```python
# ✅ GOOD
def calculate_tiebreaker(
    player: Player,
    rounds: list[Round],
    method: TiebreakerMethod = TiebreakerMethod.OMW
) -> float:
    """Calculate tiebreaker score for player."""
    ...

# ❌ BAD - Missing type hints
def calculate_tiebreaker(player, rounds, method="OMW"):
    ...
```

**Use Pydantic for validation:**
```python
from pydantic import BaseModel, Field, field_validator

class TournamentConfig(BaseModel):
    """Tournament configuration with validation."""
    name: str = Field(..., min_length=1, max_length=100)
    player_count: int = Field(..., ge=2, le=128)
    rounds: int = Field(..., ge=1)

    @field_validator("rounds")
    @classmethod
    def validate_rounds(cls, v: int, values: dict) -> int:
        """Ensure rounds is appropriate for player count."""
        player_count = values.get("player_count", 0)
        max_rounds = math.ceil(math.log2(player_count))
        if v > max_rounds:
            raise ValueError(f"Too many rounds for {player_count} players")
        return v
```

### Linting (Ruff)

**All code must pass Ruff checks.**

```bash
ruff check src/ tests/
ruff format src/ tests/
```

**Configuration** (from `pyproject.toml`):
- Line length: 100 characters
- Follow PEP 8, plus additional safety and complexity rules
- No unused imports or variables
- No print statements in production code (tests/CLI OK)

### Code Style Guidelines

**Naming Conventions:**
- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Descriptive names over abbreviations

**Function Length:**
- Keep functions under 50 lines
- Extract complex logic into helper functions
- Use meaningful function names that describe intent

**Complexity:**
- Avoid deeply nested conditionals (max 3 levels)
- Use early returns to reduce nesting
- Extract complex conditions into named functions

**Example:**
```python
# ❌ BAD - Nested complexity
def process_match_result(match: Match, result: MatchResult) -> None:
    if match.status == MatchStatus.IN_PROGRESS:
        if result.winner is not None:
            if result.winner in [match.player1, match.player2]:
                match.winner = result.winner
                match.status = MatchStatus.COMPLETED
            else:
                raise ValueError("Winner not in match")
        else:
            if result.is_draw:
                match.status = MatchStatus.DRAW
    else:
        raise ValueError("Match not in progress")

# ✅ GOOD - Early returns and validation
def process_match_result(match: Match, result: MatchResult) -> None:
    """Process and validate match result."""
    # AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - Refactored for clarity

    if match.status != MatchStatus.IN_PROGRESS:
        raise ValueError("Match not in progress")

    if result.is_draw:
        match.status = MatchStatus.DRAW
        return

    if result.winner not in [match.player1, match.player2]:
        raise ValueError("Winner not in match")

    match.winner = result.winner
    match.status = MatchStatus.COMPLETED
```

---

## Project-Specific Conventions

### Repository Pattern

**Always use the repository interfaces from `src/data/interface.py`:**

```python
# ✅ GOOD - Repository pattern
async def get_player_tournaments(player_id: UUID, repo: TournamentRepository) -> list[Tournament]:
    """
    Get all tournaments for a player.

    AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
    """
    registrations = await repo.registrations.find_by_player(player_id)
    return [await repo.get(reg.tournament_id) for reg in registrations]

# ❌ BAD - Direct data access
async def get_player_tournaments(player_id: UUID) -> list[Tournament]:
    """Get all tournaments for a player."""
    with open("tournaments.json") as f:
        tournaments = json.load(f)
    return [t for t in tournaments if player_id in t["players"]]
```

### Pydantic Models

**All data models must inherit from Pydantic BaseModel:**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class Player(BaseModel):
    """Player model with validation."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    discord_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = False  # Allow modification
        validate_assignment = True  # Validate on field assignment
```

### Async/Await Pattern

**Data layer operations are async:**

```python
# ✅ GOOD - Async data operations
@pytest.mark.asyncio
async def test_create_tournament():
    data_layer = LocalDataLayer("./test_data")
    tournament = Tournament(name="Kitchen Table Pauper", game_system=GameSystem.MTG)

    created = await data_layer.tournaments.create(tournament)

    assert created.id == tournament.id
    assert created.name == "Kitchen Table Pauper"

# ❌ BAD - Blocking I/O in async context
async def save_tournament(tournament: Tournament):
    with open("tournament.json", "w") as f:  # Blocks!
        json.dump(tournament.model_dump(), f)
```

### Error Handling

**Use custom exceptions from `src/data/exceptions.py`:**

```python
from src.data.exceptions import NotFoundError, DuplicateError, IntegrityError

async def get_tournament_or_404(tournament_id: UUID, repo: TournamentRepository) -> Tournament:
    """Get tournament by ID or raise NotFoundError."""
    try:
        return await repo.get(tournament_id)
    except NotFoundError:
        logger.error(f"Tournament {tournament_id} not found")
        raise

async def register_player_safely(
    tournament_id: UUID,
    player_id: UUID,
    repo: RegistrationRepository
) -> Registration:
    """Register player with duplicate detection."""
    try:
        return await repo.create(tournament_id, player_id)
    except DuplicateError:
        logger.warning(f"Player {player_id} already registered")
        raise
```

---

## Development Environment

### Database Setup

Tournament Director supports multiple database backends for testing and development. The environment provides both **SQLite** and **PostgreSQL**.

#### SQLite (Always Available)

**Built-in Python support** - no server required:

```python
import sqlite3

# File-based (persistent)
conn = sqlite3.connect('tournament.db')

# In-memory (testing)
conn = sqlite3.connect(':memory:')
```

**For async usage with SQLAlchemy:**
```bash
pip install aiosqlite
```

**Connection strings:**
```python
# File-based
"sqlite+aiosqlite:///tournament.db"

# In-memory (tests)
"sqlite+aiosqlite:///:memory:"
```

#### PostgreSQL (Requires Setup)

PostgreSQL 16.10 is installed but **requires initialization**:

**1. Initialize PostgreSQL cluster:**
```bash
# Create data directory
mkdir -p /tmp/pgdata /tmp/pg_socket
chown postgres:postgres /tmp/pgdata /tmp/pg_socket

# Initialize database
su - postgres -c "/usr/lib/postgresql/16/bin/initdb -D /tmp/pgdata"

# Configure socket directory
echo "unix_socket_directories = '/tmp/pg_socket'" >> /tmp/pgdata/postgresql.conf
```

**2. Start PostgreSQL server:**
```bash
su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata -l /tmp/pgdata/logfile start"

# Verify it's running
su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata status"
```

**3. Create database:**
```bash
su - postgres -c "psql -h /tmp/pg_socket -c 'CREATE DATABASE tournament_director;'"
```

**4. Install Python async PostgreSQL driver:**
```bash
pip install asyncpg
```

**Connection string:**
```python
"postgresql+asyncpg://postgres@/tournament_director?host=/tmp/pg_socket"
```

#### Required Python Database Libraries

Add to `requirements.txt`:
```txt
# SQLite async support
aiosqlite==0.20.0

# PostgreSQL async driver
asyncpg==0.29.0

# ORM and migrations
sqlalchemy[asyncio]==2.0.23
alembic==1.13.1
```

#### Backend Selection

The data layer abstraction allows seamless switching:

```python
from src.data.mock import MockDataLayer
from src.data.local import LocalDataLayer
# from src.data.database import DatabaseDataLayer  # Future implementation

# Testing - in-memory
data_layer = MockDataLayer()

# Local development - JSON files
data_layer = LocalDataLayer("./data")

# Future: SQLite
data_layer = DatabaseDataLayer("sqlite+aiosqlite:///tournament.db")

# Future: PostgreSQL
data_layer = DatabaseDataLayer("postgresql+asyncpg://postgres@/tournament_director?host=/tmp/pg_socket")
```

### Testing with Different Backends

Run the same test suite across all backends:

```python
import pytest
from src.data.mock import MockDataLayer
from src.data.local import LocalDataLayer

@pytest.fixture(params=["mock", "local"])
async def data_layer(request, tmp_path):
    """Parameterized fixture for testing all backends."""
    if request.param == "mock":
        return MockDataLayer()
    elif request.param == "local":
        return LocalDataLayer(str(tmp_path))
    # Add database backends when implemented

@pytest.mark.asyncio
async def test_player_creation(data_layer):
    """Test runs against ALL backends."""
    player = Player(name="Alice")
    created = await data_layer.players.create(player)
    assert created.name == "Alice"
```

### Environment Quick Check

Verify database availability:

```bash
# Check SQLite
python3 -c "import sqlite3; print('✅ SQLite:', sqlite3.version)"

# Check PostgreSQL
su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata status" 2>&1 | grep "server is running" && echo "✅ PostgreSQL running" || echo "❌ PostgreSQL not running"

# Check Python libraries
python3 -c "
try:
    import aiosqlite
    print('✅ aiosqlite installed')
except ImportError:
    print('❌ aiosqlite not installed')

try:
    import asyncpg
    print('✅ asyncpg installed')
except ImportError:
    print('❌ asyncpg not installed')
"
```

**See `AI_ENVIRONMENT.md` for detailed setup instructions and troubleshooting.**

---

## Development Workflow

### Daily Development Cycle

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/swiss-pairing
   ```

3. **Write failing tests (🔴 RED)**
   ```bash
   pytest tests/test_pairing.py -v
   # Verify tests fail
   ```

4. **Implement feature (🟢 GREEN)**
   ```bash
   # Write minimal implementation
   pytest tests/test_pairing.py -v
   # Verify tests pass
   ```

5. **Refactor and polish (🔵 REFACTOR)**
   ```bash
   # Improve code quality
   pytest tests/ -v  # All tests still pass
   ruff check src/ tests/
   mypy src/ --strict
   ```

6. **Check coverage**
   ```bash
   pytest --cov=src --cov-report=term-missing
   # Ensure coverage ≥85%
   ```

7. **Run full test suite**
   ```bash
   tox -e py311,lint,type
   ```

8. **Commit with attribution**
   ```bash
   git add .
   git commit -m "Add Swiss pairing algorithm

   - Implemented first round random pairing
   - Added OMW% tiebreaker calculation
   - Test coverage: 92%

   AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0

   Vibe-Coder: Andrew Potozniak <vibecoder.1.z3r0@gmail.com>
   Co-authored-by: Claude Code [Sonnet 4.5] <claude@anthropic.com>"
   ```

9. **Push and create PR**
   ```bash
   git push origin feature/swiss-pairing
   gh pr create --title "Add Swiss pairing algorithm" --body "..."
   ```

### Pre-Commit Checklist

Before committing code, verify:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Linting passes: `ruff check src/ tests/`
- [ ] Type checking passes: `mypy src/ --strict`
- [ ] Coverage maintained: `pytest --cov=src --cov-fail-under=85`
- [ ] AIA attribution added to new/modified files
- [ ] Commit message includes AIA attribution
- [ ] VIBE-CODING.md updated with session details

### CI/CD Integration

**GitHub Actions runs on every push:**

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests with coverage
        run: pytest --cov=src --cov-fail-under=85
      - name: Lint
        run: ruff check src/ tests/
      - name: Type check
        run: mypy src/ --strict
```

---

## Quick Reference

### TDD Command Cheatsheet

```bash
# Write failing test
pytest tests/test_feature.py::test_new_feature -v  # Should FAIL

# Implement feature
pytest tests/test_feature.py::test_new_feature -v  # Should PASS

# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run quality checks
ruff check src/ tests/
mypy src/ --strict

# Run full validation
tox -e all
```

### AIA Attribution Templates

**File header (short form):**
```python
"""
Module description.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""
```

**File header (with dates for multiple contributions):**
```python
"""
Module description.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0 - 2025-01-15 - Initial implementation
AIA PAI Hin R Claude Code [Sonnet 4.5] v1.0 - 2025-01-16 - Partial refactor
"""
```

**Inline comment:**
```python
# AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
```

**Commit message (short form):**
```
Subject line

Body describing changes.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0

Vibe-Coder: Andrew Potozniak <vibecoder.1.z3r0@gmail.com>
Co-authored-by: Claude Code [Sonnet 4.5] <claude@anthropic.com>
```

**Commit message (long form with full attribution):**
```
Subject line

Body describing changes.

AIA Entirely AI, Human-initiated, Reviewed, Claude Code [Sonnet 4.5] v1.0

This work was entirely AI-generated. AI was prompted for its contributions, or
AI assistance was enabled. AI-generated content was reviewed and approved. The
following model(s) or application(s) were used: Claude Code [Sonnet 4.5].

Vibe-Coder: Andrew Potozniak <vibecoder.1.z3r0@gmail.com>
Co-authored-by: Claude Code [Sonnet 4.5] <claude@anthropic.com>
```

---

## Philosophy

> **"Trust but validate"** - AI can generate code quickly, but humans must verify quality, correctness, and test coverage.

> **"Serve the vibe"** - Code should be clean, tested, and maintainable. No shortcuts on quality.

> **"Red-Green-Refactor"** - Tests first, implementation second, quality always.

---

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Ruff Documentation**: https://docs.astral.sh/ruff/
- **MyPy Documentation**: https://mypy.readthedocs.io/
- **TDD Best Practices**: https://testdriven.io/test-driven-development/
- **AIA Standard**: https://aiattribution.github.io/
- **Tournament Director AIA Statement**: https://aiattribution.github.io/statements/AIA-EAI-Hin-R-?model=Claude%20Code%20%5BSonnet%204.5%5D-v1.0

---

*This document serves as the source of truth for AI-assisted development on Tournament Director. All AI assistants must follow these guidelines to maintain code quality and proper attribution.*

**Last Updated:** 2025-01-15
**Maintained By:** Vibe-Coder Team
**Version:** 1.0.0
