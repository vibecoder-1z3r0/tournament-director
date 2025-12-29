"""
End-to-end tournament workflow integration test.

Tests a complete tournament from creation through completion with full
request/response validation at each step.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app
import src.api.dependencies as deps


@pytest_asyncio.fixture
async def client():
    """Create async test client with fresh data layer for each test."""
    # Reset the global data layer singleton to ensure test isolation
    deps._data_layer = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # Clean up after test
    deps._data_layer = None


@pytest.mark.asyncio
async def test_complete_tournament_workflow_8_players_2_rounds(client: AsyncClient):
    """
    Test complete tournament workflow with 8 players and 2 rounds.

    Workflow:
    1. Create venue, format, and TO
    2. Create tournament (DRAFT status)
    3. Register 8 players
    4. Start tournament → creates Round 1 with 4 matches (IN_PROGRESS status)
    5. Submit all Round 1 results (2-0, 1-2, 1-1 draw, 2-1)
    6. Get standings after Round 1
    7. Pair Round 2 (based on standings)
    8. Submit all Round 2 results
    9. Get final standings
    10. Complete tournament (COMPLETED status)

    Validates:
    - Proper status transitions
    - Match pairing logic
    - Results submission and standing calculation
    - Tiebreaker calculations (MW%, GW%, OMW%, OGW%)
    - Complete request/response payloads
    """

    # STEP 1: Create supporting entities
    # -----------------
    # Create venue
    venue_response = await client.post(
        "/venues/",
        json={
            "name": "Test Game Store",
            "address": "123 Test St",
            "description": "Test venue for integration testing",
        },
    )
    assert venue_response.status_code == 201
    venue = venue_response.json()
    assert venue["name"] == "Test Game Store"
    venue_id = venue["id"]

    # Create format
    format_response = await client.post(
        "/formats/",
        json={
            "name": "Pauper Test",
            "game_system": "magic_the_gathering",
            "base_format": "constructed",
            "card_pool": "Commons only",
        },
    )
    assert format_response.status_code == 201
    format_data = format_response.json()
    assert format_data["name"] == "Pauper Test"
    format_id = format_data["id"]

    # Create Tournament Organizer
    to_response = await client.post(
        "/players/",
        json={"name": "Test TO", "email": "to@test.com"},
    )
    assert to_response.status_code == 201
    to_player = to_response.json()
    to_id = to_player["id"]

    # STEP 2: Create tournament
    # -----------------
    tournament_response = await client.post(
        "/tournaments/",
        json={
            "name": "Integration Test Tournament",
            "format_id": format_id,
            "venue_id": venue_id,
            "created_by": to_id,
            "max_players": 16,
            "max_rounds": 3,
        },
    )
    assert tournament_response.status_code == 201
    tournament = tournament_response.json()
    assert tournament["status"] == "draft"  # Should start in DRAFT
    assert tournament["name"] == "Integration Test Tournament"
    tournament_id = tournament["id"]

    # STEP 3: Register 8 players
    # -----------------
    player_names = [
        "Alice",
        "Bob",
        "Charlie",
        "Diana",
        "Eve",
        "Frank",
        "Grace",
        "Henry",
    ]
    player_ids = []

    for name in player_names:
        # Create player
        player_response = await client.post(
            "/players/",
            json={"name": name, "email": f"{name.lower()}@test.com"},
        )
        assert player_response.status_code == 201
        player_id = player_response.json()["id"]
        player_ids.append(player_id)

        # Register player
        reg_response = await client.post(
            f"/tournaments/{tournament_id}/register",
            json={"player_id": player_id},
        )
        assert reg_response.status_code == 201
        reg = reg_response.json()
        assert reg["tournament_id"] == tournament_id
        assert reg["player_id"] == player_id
        assert reg["status"] == "active"
        # Sequence ID should match registration order
        assert reg["sequence_id"] == len(player_ids)

    # Verify all registrations
    reg_list_response = await client.get(f"/tournaments/{tournament_id}/registrations")
    assert reg_list_response.status_code == 200
    registrations = reg_list_response.json()
    assert len(registrations) == 8

    # STEP 4: Start tournament
    # -----------------
    start_response = await client.post(f"/tournaments/{tournament_id}/start")
    assert start_response.status_code == 200
    tournament_started = start_response.json()

    # Validate tournament status changed to in_progress
    assert tournament_started["status"] == "in_progress"

    # STEP 5: Pair Round 1
    # -----------------
    pair_round1_response = await client.post(f"/tournaments/{tournament_id}/rounds/1/pair")
    assert pair_round1_response.status_code == 201
    round1 = pair_round1_response.json()
    assert round1["round_number"] == 1
    assert round1["status"] == "active"

    # Get Round 1 matches
    matches_response = await client.get(f"/tournaments/{tournament_id}/matches?round_number=1")
    assert matches_response.status_code == 200
    matches_round1 = matches_response.json()

    # Validate matches were created (4 matches for 8 players)
    assert len(matches_round1) == 4
    for match in matches_round1:
        assert match["round_number"] == 1
        assert match["player1_id"] in player_ids
        if match["player2_id"] is not None:  # Not a bye
            assert match["player2_id"] in player_ids
            assert match["player1_id"] != match["player2_id"]

    # STEP 6: Submit Round 1 results
    # -----------------
    matches = matches_round1

    # Submit varied results
    # Match 1: Player 1 wins 2-0
    result1 = await client.put(
        f"/matches/{matches[0]['id']}/result",
        json={
            "winner_id": matches[0]["player1_id"],
            "player1_wins": 2,
            "player2_wins": 0,
        },
    )
    assert result1.status_code == 200

    # Match 2: Player 2 wins 2-1
    result2 = await client.put(
        f"/matches/{matches[1]['id']}/result",
        json={
            "winner_id": matches[1]["player2_id"],
            "player1_wins": 1,
            "player2_wins": 2,
        },
    )
    assert result2.status_code == 200

    # Match 3: Draw 1-1
    result3 = await client.put(
        f"/matches/{matches[2]['id']}/result",
        json={
            "winner_id": None,
            "player1_wins": 1,
            "player2_wins": 1,
            "draws": 1,
        },
    )
    assert result3.status_code == 200

    # Match 4: Player 1 wins 2-1
    result4 = await client.put(
        f"/matches/{matches[3]['id']}/result",
        json={
            "winner_id": matches[3]["player1_id"],
            "player1_wins": 2,
            "player2_wins": 1,
        },
    )
    assert result4.status_code == 200

    # STEP 7: Get standings after Round 1
    # -----------------
    standings1_response = await client.get(f"/tournaments/{tournament_id}/standings")
    assert standings1_response.status_code == 200
    standings1 = standings1_response.json()

    assert len(standings1) == 8  # All players should have standings

    # Validate standings structure
    for entry in standings1:
        assert "rank" in entry
        assert "player_id" in entry
        assert "match_points" in entry
        assert "game_points" in entry
        assert "match_win_percentage" in entry
        assert "game_win_percentage" in entry
        assert "opponent_match_win_percentage" in entry  # OMW%
        assert "opponent_game_win_percentage" in entry  # OGW%

    # Top player should have 3 match points (1 win = 3 points)
    top_players = [s for s in standings1 if s["match_points"] == 3]
    assert len(top_players) == 3  # 3 winners

    # Players with draw should have 1 match point
    draw_players = [s for s in standings1 if s["match_points"] == 1]
    assert len(draw_players) == 2  # 2 players from the draw

    # Losers should have 0 match points
    losing_players = [s for s in standings1 if s["match_points"] == 0]
    assert len(losing_players) == 3  # 3 losers

    # STEP 8: Pair Round 2
    # -----------------
    pair_round2_response = await client.post(f"/tournaments/{tournament_id}/rounds/2/pair")
    assert pair_round2_response.status_code == 201  # 201 Created for new round
    round2 = pair_round2_response.json()
    assert round2["round_number"] == 2

    # Get Round 2 matches
    matches2_response = await client.get(f"/tournaments/{tournament_id}/matches?round_number=2")
    assert matches2_response.status_code == 200
    matches_round2 = matches2_response.json()
    assert len(matches_round2) == 4

    # Validate Swiss pairing (players paired by standings)
    # Top players should be paired against each other
    # Note: We can't predict exact pairings due to random seeding in Round 1,
    # but we can validate structure
    for match in matches_round2:
        assert match["round_number"] == 2

    # STEP 9: Submit Round 2 results
    # -----------------
    for i, match in enumerate(matches_round2):
        # Alternate winners
        winner_id = match["player1_id"] if i % 2 == 0 else match["player2_id"]
        result = await client.put(
            f"/matches/{match['id']}/result",
            json={
                "winner_id": winner_id,
                "player1_wins": 2,
                "player2_wins": 1,
            },
        )
        assert result.status_code == 200

    # STEP 10: Get final standings
    # -----------------
    final_standings_response = await client.get(f"/tournaments/{tournament_id}/standings")
    assert final_standings_response.status_code == 200
    final_standings = final_standings_response.json()

    assert len(final_standings) == 8

    # Validate ranking
    for i, entry in enumerate(final_standings):
        assert entry["rank"] == i + 1  # Rankings should be sequential

    # Winner should be at rank 1
    winner = final_standings[0]
    assert winner["rank"] == 1
    assert winner["match_points"] >= 3  # At least one win

    # Validate tiebreaker calculations exist
    for entry in final_standings:
        assert 0.0 <= entry["match_win_percentage"] <= 1.0
        assert 0.0 <= entry["game_win_percentage"] <= 1.0
        # OMW% and OGW% can be 0 if opponents performed poorly
        assert entry["opponent_match_win_percentage"] >= 0.0
        assert entry["opponent_game_win_percentage"] >= 0.0

    # STEP 11: Complete tournament
    # -----------------
    complete_response = await client.post(f"/tournaments/{tournament_id}/complete")
    assert complete_response.status_code == 200
    completed_tournament = complete_response.json()
    assert completed_tournament["status"] == "completed"
    assert completed_tournament["id"] == tournament_id

    # Verify tournament is in COMPLETED state
    get_tournament_response = await client.get(f"/tournaments/{tournament_id}")
    assert get_tournament_response.status_code == 200
    final_tournament = get_tournament_response.json()
    assert final_tournament["status"] == "completed"

    # Verify we can still get standings after completion
    final_check_response = await client.get(f"/tournaments/{tournament_id}/standings")
    assert final_check_response.status_code == 200
    final_check = final_check_response.json()
    assert len(final_check) == 8

    print(f"\n✅ Complete tournament workflow test passed!")
    print(f"   Tournament ID: {tournament_id}")
    print(f"   Players: {len(player_ids)}")
    print(f"   Rounds: 2")
    print(f"   Winner: {winner.get('player_name', 'Unknown')} ({winner['match_points']} match points)")


