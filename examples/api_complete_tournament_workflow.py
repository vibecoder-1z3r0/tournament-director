"""
Comprehensive REST API End-to-End Example: Complete Tournament Workflow

This example demonstrates a complete tournament from setup through completion,
showing all request/response payloads and the proper sequence of API calls.

Workflow:
1. Create venue, format, and tournament organizer
2. Create tournament
3. Register 8 players
4. Start tournament (creates Round 1 pairings)
5. Submit match results for Round 1
6. View standings after Round 1
7. Pair Round 2
8. Submit match results for Round 2
9. View final standings
10. Complete tournament

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import asyncio
import json
from uuid import uuid4

import httpx


class TournamentDirectorAPIExample:
    """Comprehensive REST API example demonstrating full tournament workflow."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize with API base URL."""
        self.base_url = base_url
        self.client: httpx.AsyncClient | None = None

        # Store IDs for later use
        self.venue_id: str | None = None
        self.format_id: str | None = None
        self.to_player_id: str | None = None
        self.tournament_id: str | None = None
        self.player_ids: list[str] = []
        self.round1_match_ids: list[str] = []
        self.round2_match_ids: list[str] = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    def print_section(self, title: str):
        """Print section header."""
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")

    def print_request(self, method: str, endpoint: str, data: dict | None = None):
        """Print request details."""
        print(f"📤 REQUEST: {method} {endpoint}")
        if data:
            print(f"   Body: {json.dumps(data, indent=2)}")

    def print_response(self, response: httpx.Response):
        """Print response details."""
        status_icon = "✅" if response.status_code < 400 else "❌"
        print(f"{status_icon} RESPONSE: {response.status_code}")
        try:
            data = response.json()
            print(f"   Body: {json.dumps(data, indent=2)}")
        except Exception:
            print(f"   Body: {response.text}")

    async def step_1_create_venue(self):
        """Step 1: Create a venue for the tournament."""
        self.print_section("STEP 1: Create Venue")

        data = {
            "name": "Dragon's Lair Game Store",
            "address": "123 Main Street, Austin, TX 78701",
            "description": "Premier TCG venue in downtown Austin",
        }

        self.print_request("POST", "/venues/", data)
        response = await self.client.post("/venues/", json=data)
        self.print_response(response)

        assert response.status_code == 201, f"Failed to create venue: {response.text}"
        self.venue_id = response.json()["id"]
        print(f"\n💾 Saved venue_id: {self.venue_id}")

    async def step_2_create_format(self):
        """Step 2: Create tournament format."""
        self.print_section("STEP 2: Create Format")

        data = {
            "name": "Pauper",
            "game_system": "magic_the_gathering",
            "base_format": "constructed",
            "card_pool": "Common cards only",
            "description": "60-card constructed deck with only common rarity cards",
        }

        self.print_request("POST", "/formats/", data)
        response = await self.client.post("/formats/", json=data)
        self.print_response(response)

        assert response.status_code == 201, f"Failed to create format: {response.text}"
        self.format_id = response.json()["id"]
        print(f"\n💾 Saved format_id: {self.format_id}")

    async def step_3_create_tournament_organizer(self):
        """Step 3: Create tournament organizer player."""
        self.print_section("STEP 3: Create Tournament Organizer")

        data = {
            "name": "Jane Smith (TO)",
            "email": "jane.smith@dragonslair.com",
            "discord_id": "JaneTO#1234",
        }

        self.print_request("POST", "/players/", data)
        response = await self.client.post("/players/", json=data)
        self.print_response(response)

        assert response.status_code == 201, f"Failed to create TO: {response.text}"
        self.to_player_id = response.json()["id"]
        print(f"\n💾 Saved TO player_id: {self.to_player_id}")

    async def step_4_create_tournament(self):
        """Step 4: Create tournament."""
        self.print_section("STEP 4: Create Tournament")

        data = {
            "name": "Friday Night Pauper - Week 1",
            "format_id": self.format_id,
            "venue_id": self.venue_id,
            "created_by": self.to_player_id,
            "description": "Weekly Pauper tournament with prize support",
            "max_players": 32,
            "max_rounds": 3,
        }

        self.print_request("POST", "/tournaments/", data)
        response = await self.client.post("/tournaments/", json=data)
        self.print_response(response)

        assert response.status_code == 201, f"Failed to create tournament: {response.text}"
        self.tournament_id = response.json()["id"]
        print(f"\n💾 Saved tournament_id: {self.tournament_id}")
        print(f"   Status: {response.json()['status']}")  # Should be DRAFT

    async def step_5_register_players(self):
        """Step 5: Register 8 players for the tournament."""
        self.print_section("STEP 5: Register 8 Players")

        player_names = [
            "Alice Anderson",
            "Bob Brown",
            "Charlie Chen",
            "Diana Davis",
            "Eve Evans",
            "Frank Foster",
            "Grace Garcia",
            "Henry Harris",
        ]

        for i, name in enumerate(player_names, 1):
            # Create player
            player_data = {
                "name": name,
                "email": f"{name.lower().replace(' ', '.')}@example.com",
                "discord_id": f"{name.split()[0]}#{1000 + i}",
            }

            print(f"\n--- Player {i}/8: {name} ---")
            self.print_request("POST", "/players/", player_data)
            player_response = await self.client.post("/players/", json=player_data)
            self.print_response(player_response)
            assert player_response.status_code == 201

            player_id = player_response.json()["id"]
            self.player_ids.append(player_id)

            # Register player in tournament
            reg_data = {
                "player_id": player_id,
                "tournament_id": self.tournament_id,
            }

            self.print_request("POST", "/registrations/", reg_data)
            reg_response = await self.client.post("/registrations/", json=reg_data)
            self.print_response(reg_response)
            assert reg_response.status_code == 201

            print(f"   ✅ Registered {name} (Sequence #{reg_response.json()['sequence_id']})")

        print(f"\n✅ Total players registered: {len(self.player_ids)}")

    async def step_6_start_tournament(self):
        """Step 6: Start tournament (creates Round 1 pairings)."""
        self.print_section("STEP 6: Start Tournament")

        endpoint = f"/tournaments/{self.tournament_id}/start"
        self.print_request("POST", endpoint)
        response = await self.client.post(endpoint)
        self.print_response(response)

        assert response.status_code == 200, f"Failed to start tournament: {response.text}"

        data = response.json()
        print(f"\n✅ Tournament started!")
        print(f"   Status: {data['tournament']['status']}")  # Should be IN_PROGRESS
        print(f"   Round 1 created with ID: {data['round']['id']}")
        print(f"   Number of matches: {len(data['matches'])}")

        # Show pairings
        print(f"\n📋 Round 1 Pairings:")
        for i, match in enumerate(data["matches"], 1):
            p1_name = match.get("player1_name", "BYE")
            p2_name = match.get("player2_name", "BYE")
            print(f"   Match {i}: {p1_name} vs {p2_name}")
            self.round1_match_ids.append(match["id"])

    async def step_7_submit_round1_results(self):
        """Step 7: Submit match results for Round 1."""
        self.print_section("STEP 7: Submit Round 1 Match Results")

        # Get matches for round 1
        endpoint = f"/tournaments/{self.tournament_id}/matches?round=1"
        print(f"📤 GET {endpoint}")
        response = await self.client.get(endpoint)
        matches = response.json()

        print(f"\n📝 Submitting results for {len(matches)} matches...\n")

        # Submit results (alternate wins and some draws)
        results = [
            {"winner_id": matches[0]["player1_id"], "player1_wins": 2, "player2_wins": 0},
            {"winner_id": matches[1]["player2_id"], "player1_wins": 1, "player2_wins": 2},
        ]

        if len(matches) > 2:
            results.append(
                {"winner_id": None, "player1_wins": 1, "player2_wins": 1, "is_draw": True}
            )
        if len(matches) > 3:
            results.append(
                {"winner_id": matches[3]["player1_id"], "player1_wins": 2, "player2_wins": 1}
            )

        for i, (match, result) in enumerate(zip(matches, results), 1):
            endpoint = f"/matches/{match['id']}/result"
            print(f"--- Match {i} ---")
            self.print_request("POST", endpoint, result)
            response = await self.client.post(endpoint, json=result)
            self.print_response(response)
            assert response.status_code == 200

        print(f"\n✅ All Round 1 results submitted!")

    async def step_8_view_standings_after_round1(self):
        """Step 8: View standings after Round 1."""
        self.print_section("STEP 8: View Standings After Round 1")

        endpoint = f"/tournaments/{self.tournament_id}/standings"
        self.print_request("GET", endpoint)
        response = await self.client.get(endpoint)
        self.print_response(response)

        assert response.status_code == 200
        standings = response.json()

        print(f"\n📊 Standings after Round 1:")
        print(f"{'Rank':<6} {'Player':<25} {'Points':<8} {'MW%':<8} {'GW%':<8}")
        print("-" * 60)

        for entry in standings[:8]:  # Top 8
            print(
                f"{entry['rank']:<6} "
                f"{entry.get('player_name', 'Unknown'):<25} "
                f"{entry['points']:<8} "
                f"{entry['match_win_percentage']:.1%}  "
                f"{entry['game_win_percentage']:.1%}"
            )

    async def step_9_pair_round2(self):
        """Step 9: Pair Round 2."""
        self.print_section("STEP 9: Pair Round 2")

        endpoint = f"/tournaments/{self.tournament_id}/rounds/2/pair"
        self.print_request("POST", endpoint)
        response = await self.client.post(endpoint)
        self.print_response(response)

        assert response.status_code == 200, f"Failed to pair round 2: {response.text}"

        data = response.json()
        print(f"\n✅ Round 2 paired!")
        print(f"   Round ID: {data['id']}")

        # Get matches
        matches_response = await self.client.get(
            f"/tournaments/{self.tournament_id}/matches?round=2"
        )
        matches = matches_response.json()

        print(f"\n📋 Round 2 Pairings (by standings):")
        for i, match in enumerate(matches, 1):
            p1_name = match.get("player1_name", "BYE")
            p2_name = match.get("player2_name", "BYE")
            print(f"   Match {i}: {p1_name} vs {p2_name}")
            self.round2_match_ids.append(match["id"])

    async def step_10_submit_round2_results(self):
        """Step 10: Submit match results for Round 2."""
        self.print_section("STEP 10: Submit Round 2 Match Results")

        endpoint = f"/tournaments/{self.tournament_id}/matches?round=2"
        response = await self.client.get(endpoint)
        matches = response.json()

        print(f"\n📝 Submitting results for {len(matches)} matches...\n")

        # Submit varied results
        for i, match in enumerate(matches, 1):
            # Alternate winners
            winner_id = match["player1_id"] if i % 2 == 0 else match["player2_id"]
            result = {
                "winner_id": winner_id,
                "player1_wins": 2 if i % 2 == 0 else 1,
                "player2_wins": 1 if i % 2 == 0 else 2,
            }

            endpoint = f"/matches/{match['id']}/result"
            print(f"--- Match {i} ---")
            self.print_request("POST", endpoint, result)
            response = await self.client.post(endpoint, json=result)
            self.print_response(response)
            assert response.status_code == 200

        print(f"\n✅ All Round 2 results submitted!")

    async def step_11_view_final_standings(self):
        """Step 11: View final standings."""
        self.print_section("STEP 11: View Final Standings")

        endpoint = f"/tournaments/{self.tournament_id}/standings"
        self.print_request("GET", endpoint)
        response = await self.client.get(endpoint)
        self.print_response(response)

        assert response.status_code == 200
        standings = response.json()

        print(f"\n🏆 FINAL STANDINGS:")
        print(
            f"{'Rank':<6} {'Player':<25} {'Points':<8} {'MW%':<8} {'GW%':<8} "
            f"{'OMW%':<8} {'OGW%':<8}"
        )
        print("-" * 85)

        for entry in standings:
            print(
                f"{entry['rank']:<6} "
                f"{entry.get('player_name', 'Unknown'):<25} "
                f"{entry['points']:<8} "
                f"{entry['match_win_percentage']:.1%}  "
                f"{entry['game_win_percentage']:.1%}  "
                f"{entry['opponent_match_win_percentage']:.1%}  "
                f"{entry['opponent_game_win_percentage']:.1%}"
            )

        winner = standings[0]
        print(f"\n👑 WINNER: {winner.get('player_name', 'Unknown')} ({winner['points']} points)")

    async def step_12_complete_tournament(self):
        """Step 12: Complete/finish the tournament."""
        self.print_section("STEP 12: Complete Tournament")

        endpoint = f"/tournaments/{self.tournament_id}/complete"
        self.print_request("POST", endpoint)
        response = await self.client.post(endpoint)
        self.print_response(response)

        assert response.status_code == 200, f"Failed to complete tournament: {response.text}"

        data = response.json()
        print(f"\n✅ Tournament completed!")
        print(f"   Final status: {data['status']}")  # Should be COMPLETED

    async def run_full_workflow(self):
        """Execute complete tournament workflow."""
        print("\n" + "=" * 80)
        print("  Tournament Director REST API - Complete Workflow Example")
        print("  Demonstrates a full tournament from creation to completion")
        print("=" * 80)

        try:
            await self.step_1_create_venue()
            await self.step_2_create_format()
            await self.step_3_create_tournament_organizer()
            await self.step_4_create_tournament()
            await self.step_5_register_players()
            await self.step_6_start_tournament()
            await self.step_7_submit_round1_results()
            await self.step_8_view_standings_after_round1()
            await self.step_9_pair_round2()
            await self.step_10_submit_round2_results()
            await self.step_11_view_final_standings()
            await self.step_12_complete_tournament()

            print("\n" + "=" * 80)
            print("  ✅ COMPLETE WORKFLOW FINISHED SUCCESSFULLY!")
            print("=" * 80)

            print("\n📋 Summary:")
            print(f"   • Venue ID: {self.venue_id}")
            print(f"   • Format ID: {self.format_id}")
            print(f"   • Tournament ID: {self.tournament_id}")
            print(f"   • Players registered: {len(self.player_ids)}")
            print(f"   • Rounds completed: 2")
            print(f"   • Total matches: {len(self.round1_match_ids) + len(self.round2_match_ids)}")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback

            traceback.print_exc()
            raise


async def main():
    """Run the comprehensive example."""
    # Make sure API server is running first!
    print("\n⚠️  NOTE: Ensure the API server is running:")
    print("   uvicorn src.api.main:app --reload")
    print("\nStarting in 3 seconds...\n")
    await asyncio.sleep(3)

    async with TournamentDirectorAPIExample() as example:
        await example.run_full_workflow()


if __name__ == "__main__":
    asyncio.run(main())
