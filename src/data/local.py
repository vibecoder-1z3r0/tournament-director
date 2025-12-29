"""Local backend implementation using JSON file storage.

AIA PAI Hin R Claude Code v1.0
"""

import json
from pathlib import Path
from typing import Any, Generic, TypeVar
from uuid import UUID

import aiofiles
from pydantic import BaseModel

from src.models.auth import APIKey
from src.models.format import Format
from src.models.match import Component, Match, Round
from src.models.player import Player
from src.models.tournament import Tournament, TournamentRegistration
from src.models.venue import Venue

from .exceptions import DuplicateError, NotFoundError
from .interface import (
    APIKeyRepository,
    ComponentRepository,
    DataLayer,
    FormatRepository,
    MatchRepository,
    PlayerRepository,
    RegistrationRepository,
    RoundRepository,
    TournamentRepository,
    VenueRepository,
)

T = TypeVar("T", bound=BaseModel)


class LocalJSONRepository(Generic[T]):
    """Base class for JSON file-based repositories."""

    def __init__(self, data_dir: Path, entity_name: str, model_class: type[T]) -> None:
        self.data_dir = data_dir
        self.entity_name = entity_name
        self.model_class = model_class
        self.file_path = data_dir / f"{entity_name}.json"
        self._data: dict[str, dict] = {}
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        """Ensure data is loaded from file."""
        if self._loaded:
            return

        await self._load_from_file()
        self._loaded = True

    async def _load_from_file(self) -> None:
        """Load data from JSON file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self._data = {}
            return

        try:
            async with aiofiles.open(self.file_path) as f:
                content = await f.read()
                if content.strip():
                    file_data = json.loads(content)
                    # Convert string keys back to UUIDs for internal storage
                    self._data = dict(file_data.items())
                else:
                    self._data = {}
        except (json.JSONDecodeError, FileNotFoundError):
            self._data = {}

    async def _save_to_file(self) -> None:
        """Save data to JSON file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Convert UUID keys to strings for JSON serialization
        json_data = {}
        for k, v in self._data.items():
            # Ensure all datetime objects are properly serialized
            if hasattr(v, "items"):  # It's a dict
                serialized = {}
                for field_k, field_v in v.items():
                    if hasattr(field_v, "isoformat"):  # datetime object
                        serialized[field_k] = field_v.isoformat()
                    else:
                        serialized[field_k] = field_v
                json_data[str(k)] = serialized
            else:
                json_data[str(k)] = v

        async with aiofiles.open(self.file_path, "w") as f:
            await f.write(json.dumps(json_data, indent=2, default=str))

    async def _get_by_id(self, entity_id: UUID) -> T:
        """Get entity by ID, returning Pydantic model."""
        await self._ensure_loaded()

        entity_key = str(entity_id)
        if entity_key not in self._data:
            raise NotFoundError(self.entity_name, entity_id)

        # Convert back to Pydantic model
        return self.model_class.model_validate(self._data[entity_key])

    async def _list_all(self, limit: int | None = None, offset: int = 0) -> list[T]:
        """List all entities, returning Pydantic models."""
        await self._ensure_loaded()

        entities: list[T] = []
        for entity_data in self._data.values():
            entities.append(self.model_class.model_validate(entity_data))

        # Apply pagination
        if offset >= len(entities):
            return []

        end_idx = offset + limit if limit else len(entities)
        return entities[offset:end_idx]

    async def _create(self, entity: T) -> T:
        """Create new entity."""
        await self._ensure_loaded()

        entity_key = str(entity.id)
        if entity_key in self._data:
            raise DuplicateError(self.entity_name, "id", entity.id)

        # Store as dict for JSON serialization
        self._data[entity_key] = entity.model_dump()
        await self._save_to_file()
        return entity

    async def _update(self, entity: T) -> T:
        """Update existing entity."""
        await self._ensure_loaded()

        entity_key = str(entity.id)
        if entity_key not in self._data:
            raise NotFoundError(self.entity_name, entity.id)

        self._data[entity_key] = entity.model_dump()
        await self._save_to_file()
        return entity

    async def _delete(self, entity_id: UUID) -> None:
        """Delete entity."""
        await self._ensure_loaded()

        entity_key = str(entity_id)
        if entity_key not in self._data:
            raise NotFoundError(self.entity_name, entity_id)

        del self._data[entity_key]
        await self._save_to_file()

    async def _clear_all(self) -> None:
        """Clear all data."""
        self._data = {}
        await self._save_to_file()


class LocalPlayerRepository(LocalJSONRepository, PlayerRepository):
    """Local JSON implementation of PlayerRepository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, "players", Player)

    async def create(self, player: Player) -> Player:
        await self._ensure_loaded()

        # Check for duplicate name
        for existing_data in self._data.values():
            if existing_data.get("name") == player.name:
                raise DuplicateError("Player", "name", player.name)

        return await self._create(player)  # type: ignore[no-any-return]

    async def get_by_id(self, player_id: UUID) -> Player:
        return await self._get_by_id(player_id)  # type: ignore[no-any-return]

    async def get_by_name(self, name: str) -> Player | None:
        await self._ensure_loaded()

        for entity_data in self._data.values():
            if entity_data.get("name") == name:
                return Player.model_validate(entity_data)
        return None

    async def get_by_discord_id(self, discord_id: str) -> Player | None:
        await self._ensure_loaded()

        for entity_data in self._data.values():
            if entity_data.get("discord_id") == discord_id:
                return Player.model_validate(entity_data)
        return None

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Player]:
        entities = await self._list_all(limit, offset)
        entities.sort(key=lambda p: p.created_at)
        return entities

    async def update(self, player: Player) -> Player:
        await self._ensure_loaded()

        # Check for duplicate name (excluding self)
        for entity_id, existing_data in self._data.items():
            if entity_id != str(player.id) and existing_data.get("name") == player.name:
                raise DuplicateError("Player", "name", player.name)

        return await self._update(player)  # type: ignore[no-any-return]

    async def delete(self, player_id: UUID) -> None:
        await self._delete(player_id)


class LocalAPIKeyRepository(LocalJSONRepository, APIKeyRepository):
    """Local JSON implementation of APIKeyRepository.

    AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
    """

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, "api_keys", APIKey)

    async def create(self, api_key: APIKey) -> APIKey:
        await self._ensure_loaded()

        # Check for duplicate token
        for existing_data in self._data.values():
            if existing_data.get("token") == api_key.token:
                raise DuplicateError("APIKey", "token", api_key.token)

        return await self._create(api_key)  # type: ignore[no-any-return]

    async def get_by_id(self, api_key_id: UUID) -> APIKey:
        return await self._get_by_id(api_key_id)  # type: ignore[no-any-return]

    async def get_by_token(self, token: str) -> APIKey | None:
        await self._ensure_loaded()

        for entity_data in self._data.values():
            if entity_data.get("token") == token:
                return APIKey.model_validate(entity_data)
        return None

    async def list_by_owner(self, player_id: UUID) -> list[APIKey]:
        await self._ensure_loaded()

        player_id_str = str(player_id)
        api_keys = []
        for entity_data in self._data.values():
            if entity_data.get("created_by") == player_id_str:
                api_keys.append(APIKey.model_validate(entity_data))

        # Sort by created_at descending (newest first)
        api_keys.sort(key=lambda k: k.created_at, reverse=True)
        return api_keys

    async def update(self, api_key: APIKey) -> APIKey:
        await self._ensure_loaded()

        # Check for duplicate token (excluding self)
        for entity_id, existing_data in self._data.items():
            if entity_id != str(api_key.id) and existing_data.get("token") == api_key.token:
                raise DuplicateError("APIKey", "token", api_key.token)

        return await self._update(api_key)  # type: ignore[no-any-return]

    async def delete(self, api_key_id: UUID) -> None:
        await self._delete(api_key_id)


class LocalVenueRepository(LocalJSONRepository, VenueRepository):
    """Local JSON implementation of VenueRepository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, "venues", Venue)

    async def create(self, venue: Venue) -> Venue:
        return await self._create(venue)  # type: ignore[no-any-return]

    async def get_by_id(self, venue_id: UUID) -> Venue:
        return await self._get_by_id(venue_id)  # type: ignore[no-any-return]

    async def get_by_name(self, name: str) -> Venue | None:
        await self._ensure_loaded()

        for entity_data in self._data.values():
            if entity_data.get("name") == name:
                return Venue.model_validate(entity_data)
        return None

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Venue]:
        entities = await self._list_all(limit, offset)
        entities.sort(key=lambda v: v.name)
        return entities

    async def update(self, venue: Venue) -> Venue:
        return await self._update(venue)  # type: ignore[no-any-return]

    async def delete(self, venue_id: UUID) -> None:
        await self._delete(venue_id)


class LocalFormatRepository(LocalJSONRepository, FormatRepository):
    """Local JSON implementation of FormatRepository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, "formats", Format)

    async def create(self, format_obj: Format) -> Format:
        await self._ensure_loaded()

        # Check for duplicate name within game system
        for existing_data in self._data.values():
            if (
                existing_data.get("name") == format_obj.name
                and existing_data.get("game_system") == format_obj.game_system
            ):
                raise DuplicateError(
                    "Format", "name+game_system", f"{format_obj.name}+{format_obj.game_system}"
                )

        return await self._create(format_obj)  # type: ignore[no-any-return]

    async def get_by_id(self, format_id: UUID) -> Format:
        return await self._get_by_id(format_id)  # type: ignore[no-any-return]

    async def get_by_name(self, name: str, game_system: str | None = None) -> Format | None:
        await self._ensure_loaded()

        for entity_data in self._data.values():
            if entity_data.get("name") == name and (
                game_system is None or entity_data.get("game_system") == game_system
            ):
                return Format.model_validate(entity_data)
        return None

    async def list_by_game_system(self, game_system: str) -> list[Format]:
        await self._ensure_loaded()

        formats = []
        for entity_data in self._data.values():
            if entity_data.get("game_system") == game_system:
                formats.append(Format.model_validate(entity_data))

        formats.sort(key=lambda f: f.name)
        return formats

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Format]:
        entities = await self._list_all(limit, offset)
        entities.sort(key=lambda f: (f.game_system.value, f.name))
        return entities

    async def update(self, format_obj: Format) -> Format:
        await self._ensure_loaded()

        # Check for duplicate name within game system (excluding self)
        for entity_id, existing_data in self._data.items():
            if (
                entity_id != str(format_obj.id)
                and existing_data.get("name") == format_obj.name
                and existing_data.get("game_system") == format_obj.game_system
            ):
                raise DuplicateError(
                    "Format", "name+game_system", f"{format_obj.name}+{format_obj.game_system}"
                )

        return await self._update(format_obj)  # type: ignore[no-any-return]

    async def delete(self, format_id: UUID) -> None:
        await self._delete(format_id)


class LocalTournamentRepository(LocalJSONRepository, TournamentRepository):
    """Local JSON implementation of TournamentRepository."""

    def __init__(
        self,
        data_dir: Path,
        player_repo: LocalPlayerRepository,
        venue_repo: LocalVenueRepository,
        format_repo: LocalFormatRepository,
    ):
        super().__init__(data_dir, "tournaments", Tournament)
        self._player_repo = player_repo
        self._venue_repo = venue_repo
        self._format_repo = format_repo

    async def create(self, tournament: Tournament) -> Tournament:
        # Validate foreign keys
        # Will raise NotFoundError if invalid
        await self._player_repo.get_by_id(tournament.created_by)
        await self._venue_repo.get_by_id(tournament.venue_id)
        await self._format_repo.get_by_id(tournament.format_id)

        return await self._create(tournament)  # type: ignore[no-any-return]

    async def get_by_id(self, tournament_id: UUID) -> Tournament:
        return await self._get_by_id(tournament_id)  # type: ignore[no-any-return]

    async def list_by_status(self, status: str) -> list[Tournament]:
        await self._ensure_loaded()

        tournaments = []
        for entity_data in self._data.values():
            if entity_data.get("status") == status:
                tournaments.append(Tournament.model_validate(entity_data))

        tournaments.sort(key=lambda t: t.created_at, reverse=True)
        return tournaments

    async def list_by_venue(self, venue_id: UUID) -> list[Tournament]:
        await self._ensure_loaded()

        tournaments = []
        venue_id_str = str(venue_id)
        for entity_data in self._data.values():
            if entity_data.get("venue_id") == venue_id_str:
                tournaments.append(Tournament.model_validate(entity_data))

        tournaments.sort(key=lambda t: t.created_at, reverse=True)
        return tournaments

    async def list_by_format(self, format_id: UUID) -> list[Tournament]:
        await self._ensure_loaded()

        tournaments = []
        format_id_str = str(format_id)
        for entity_data in self._data.values():
            if entity_data.get("format_id") == format_id_str:
                tournaments.append(Tournament.model_validate(entity_data))

        tournaments.sort(key=lambda t: t.created_at, reverse=True)
        return tournaments

    async def list_by_organizer(self, organizer_id: UUID) -> list[Tournament]:
        await self._ensure_loaded()

        tournaments = []
        organizer_id_str = str(organizer_id)
        for entity_data in self._data.values():
            if entity_data.get("created_by") == organizer_id_str:
                tournaments.append(Tournament.model_validate(entity_data))

        tournaments.sort(key=lambda t: t.created_at, reverse=True)
        return tournaments

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Tournament]:
        entities = await self._list_all(limit, offset)
        entities.sort(key=lambda t: t.created_at, reverse=True)
        return entities

    async def update(self, tournament: Tournament) -> Tournament:
        # Validate foreign keys
        await self._player_repo.get_by_id(tournament.created_by)
        await self._venue_repo.get_by_id(tournament.venue_id)
        await self._format_repo.get_by_id(tournament.format_id)

        return await self._update(tournament)  # type: ignore[no-any-return]

    async def delete(self, tournament_id: UUID) -> None:
        await self._delete(tournament_id)


class LocalRegistrationRepository(LocalJSONRepository, RegistrationRepository):
    """Local JSON implementation of RegistrationRepository."""

    def __init__(
        self,
        data_dir: Path,
        tournament_repo: LocalTournamentRepository,
        player_repo: LocalPlayerRepository,
    ):
        super().__init__(data_dir, "registrations", TournamentRegistration)
        self._tournament_repo = tournament_repo
        self._player_repo = player_repo

    async def create(self, registration: TournamentRegistration) -> TournamentRegistration:
        await self._ensure_loaded()

        # Validate foreign keys
        await self._tournament_repo.get_by_id(registration.tournament_id)
        await self._player_repo.get_by_id(registration.player_id)

        # Check for duplicate registration
        tournament_id_str = str(registration.tournament_id)
        player_id_str = str(registration.player_id)

        for existing_data in self._data.values():
            if (
                existing_data.get("tournament_id") == tournament_id_str
                and existing_data.get("player_id") == player_id_str
            ):
                raise DuplicateError(
                    "TournamentRegistration",
                    "tournament+player",
                    f"{registration.tournament_id}+{registration.player_id}",
                )

        # Check for duplicate sequence ID
        for existing_data in self._data.values():
            if (
                existing_data.get("tournament_id") == tournament_id_str
                and existing_data.get("sequence_id") == registration.sequence_id
            ):
                raise DuplicateError(
                    "TournamentRegistration",
                    "tournament+sequence_id",
                    f"{registration.tournament_id}+{registration.sequence_id}",
                )

        return await self._create(registration)  # type: ignore[no-any-return]

    async def get_by_id(self, registration_id: UUID) -> TournamentRegistration:
        return await self._get_by_id(registration_id)  # type: ignore[no-any-return]

    async def get_by_tournament_and_player(
        self, tournament_id: UUID, player_id: UUID
    ) -> TournamentRegistration | None:
        await self._ensure_loaded()

        tournament_id_str = str(tournament_id)
        player_id_str = str(player_id)

        for entity_data in self._data.values():
            if (
                entity_data.get("tournament_id") == tournament_id_str
                and entity_data.get("player_id") == player_id_str
            ):
                return TournamentRegistration.model_validate(entity_data)
        return None

    async def get_by_tournament_and_sequence_id(
        self, tournament_id: UUID, sequence_id: int
    ) -> TournamentRegistration | None:
        await self._ensure_loaded()

        tournament_id_str = str(tournament_id)

        for entity_data in self._data.values():
            if (
                entity_data.get("tournament_id") == tournament_id_str
                and entity_data.get("sequence_id") == sequence_id
            ):
                return TournamentRegistration.model_validate(entity_data)
        return None

    async def list_by_tournament(
        self, tournament_id: UUID, status: str | None = None
    ) -> list[TournamentRegistration]:
        await self._ensure_loaded()

        tournament_id_str = str(tournament_id)
        registrations = []

        for entity_data in self._data.values():
            if entity_data.get("tournament_id") == tournament_id_str and (
                status is None or entity_data.get("status") == status
            ):
                registrations.append(TournamentRegistration.model_validate(entity_data))

        registrations.sort(key=lambda r: r.sequence_id)
        return registrations

    async def list_by_player(
        self, player_id: UUID, status: str | None = None
    ) -> list[TournamentRegistration]:
        await self._ensure_loaded()

        player_id_str = str(player_id)
        registrations = []

        for entity_data in self._data.values():
            if entity_data.get("player_id") == player_id_str and (
                status is None or entity_data.get("status") == status
            ):
                registrations.append(TournamentRegistration.model_validate(entity_data))

        registrations.sort(key=lambda r: r.registration_time, reverse=True)
        return registrations

    async def get_next_sequence_id(self, tournament_id: UUID) -> int:
        await self._ensure_loaded()

        tournament_id_str = str(tournament_id)
        max_sequence_id = 0

        for entity_data in self._data.values():
            if (
                entity_data.get("tournament_id") == tournament_id_str
                and entity_data.get("sequence_id", 0) > max_sequence_id
            ):
                max_sequence_id = entity_data.get("sequence_id", 0)

        return max_sequence_id + 1

    async def update(self, registration: TournamentRegistration) -> TournamentRegistration:
        await self._ensure_loaded()

        # Validate foreign keys
        await self._tournament_repo.get_by_id(registration.tournament_id)
        await self._player_repo.get_by_id(registration.player_id)

        # Check for duplicate sequence ID (excluding self)
        tournament_id_str = str(registration.tournament_id)
        registration_id_str = str(registration.id)

        for entity_id, existing_data in self._data.items():
            if (
                entity_id != registration_id_str
                and existing_data.get("tournament_id") == tournament_id_str
                and existing_data.get("sequence_id") == registration.sequence_id
            ):
                raise DuplicateError(
                    "TournamentRegistration",
                    "tournament+sequence_id",
                    f"{registration.tournament_id}+{registration.sequence_id}",
                )

        return await self._update(registration)  # type: ignore[no-any-return]

    async def delete(self, registration_id: UUID) -> None:
        await self._delete(registration_id)


# Simplified implementations for other repositories
class LocalComponentRepository(LocalJSONRepository, ComponentRepository):
    def __init__(self, data_dir: Path, tournament_repo: LocalTournamentRepository):
        super().__init__(data_dir, "components", Component)
        self._tournament_repo = tournament_repo

    async def create(self, component: Component) -> Component:
        await self._tournament_repo.get_by_id(component.tournament_id)  # Validate FK
        return await self._create(component)  # type: ignore[no-any-return]

    async def get_by_id(self, component_id: UUID) -> Component:
        return await self._get_by_id(component_id)  # type: ignore[no-any-return]

    async def list_by_tournament(self, tournament_id: UUID) -> list[Component]:
        await self._ensure_loaded()
        tournament_id_str = str(tournament_id)

        components = []
        for entity_data in self._data.values():
            if entity_data.get("tournament_id") == tournament_id_str:
                components.append(Component.model_validate(entity_data))

        components.sort(key=lambda c: c.sequence_order)
        return components

    async def get_by_tournament_and_sequence(
        self, tournament_id: UUID, sequence_order: int
    ) -> Component | None:
        await self._ensure_loaded()
        tournament_id_str = str(tournament_id)

        for entity_data in self._data.values():
            if (
                entity_data.get("tournament_id") == tournament_id_str
                and entity_data.get("sequence_order") == sequence_order
            ):
                return Component.model_validate(entity_data)
        return None

    async def update(self, component: Component) -> Component:
        return await self._update(component)  # type: ignore[no-any-return]

    async def delete(self, component_id: UUID) -> None:
        await self._delete(component_id)


class LocalRoundRepository(LocalJSONRepository, RoundRepository):
    def __init__(
        self,
        data_dir: Path,
        tournament_repo: LocalTournamentRepository,
        component_repo: LocalComponentRepository,
    ):
        super().__init__(data_dir, "rounds", Round)
        self._tournament_repo = tournament_repo
        self._component_repo = component_repo

    async def create(self, round_obj: Round) -> Round:
        await self._tournament_repo.get_by_id(round_obj.tournament_id)  # Validate FK
        await self._component_repo.get_by_id(round_obj.component_id)  # Validate FK
        return await self._create(round_obj)  # type: ignore[no-any-return]

    async def get_by_id(self, round_id: UUID) -> Round:
        return await self._get_by_id(round_id)  # type: ignore[no-any-return]

    async def list_by_tournament(self, tournament_id: UUID) -> list[Round]:
        await self._ensure_loaded()
        tournament_id_str = str(tournament_id)

        rounds = []
        for entity_data in self._data.values():
            if entity_data.get("tournament_id") == tournament_id_str:
                rounds.append(Round.model_validate(entity_data))

        rounds.sort(key=lambda r: r.round_number)
        return rounds

    async def list_by_component(self, component_id: UUID) -> list[Round]:
        await self._ensure_loaded()
        component_id_str = str(component_id)

        rounds = []
        for entity_data in self._data.values():
            if entity_data.get("component_id") == component_id_str:
                rounds.append(Round.model_validate(entity_data))

        rounds.sort(key=lambda r: r.round_number)
        return rounds

    async def get_by_component_and_round_number(
        self, component_id: UUID, round_number: int
    ) -> Round | None:
        await self._ensure_loaded()
        component_id_str = str(component_id)

        for entity_data in self._data.values():
            if (
                entity_data.get("component_id") == component_id_str
                and entity_data.get("round_number") == round_number
            ):
                return Round.model_validate(entity_data)
        return None

    async def update(self, round_obj: Round) -> Round:
        return await self._update(round_obj)  # type: ignore[no-any-return]

    async def delete(self, round_id: UUID) -> None:
        await self._delete(round_id)


class LocalMatchRepository(LocalJSONRepository, MatchRepository):
    def __init__(
        self,
        data_dir: Path,
        tournament_repo: LocalTournamentRepository,
        component_repo: LocalComponentRepository,
        round_repo: LocalRoundRepository,
        player_repo: LocalPlayerRepository,
    ):
        super().__init__(data_dir, "matches", Match)
        self._tournament_repo = tournament_repo
        self._component_repo = component_repo
        self._round_repo = round_repo
        self._player_repo = player_repo

    async def create(self, match: Match) -> Match:
        # Validate foreign keys
        await self._tournament_repo.get_by_id(match.tournament_id)
        await self._component_repo.get_by_id(match.component_id)
        await self._round_repo.get_by_id(match.round_id)
        await self._player_repo.get_by_id(match.player1_id)
        if match.player2_id:  # Can be None for bye
            await self._player_repo.get_by_id(match.player2_id)

        return await self._create(match)  # type: ignore[no-any-return]

    async def get_by_id(self, match_id: UUID) -> Match:
        return await self._get_by_id(match_id)  # type: ignore[no-any-return]

    async def list_by_tournament(self, tournament_id: UUID) -> list[Match]:
        await self._ensure_loaded()
        tournament_id_str = str(tournament_id)

        matches = []
        for entity_data in self._data.values():
            if entity_data.get("tournament_id") == tournament_id_str:
                matches.append(Match.model_validate(entity_data))

        matches.sort(key=lambda m: (m.round_number, m.table_number or 0))
        return matches

    async def list_by_round(self, round_id: UUID) -> list[Match]:
        await self._ensure_loaded()
        round_id_str = str(round_id)

        matches = []
        for entity_data in self._data.values():
            if entity_data.get("round_id") == round_id_str:
                matches.append(Match.model_validate(entity_data))

        matches.sort(key=lambda m: m.table_number or 0)
        return matches

    async def list_by_component(self, component_id: UUID) -> list[Match]:
        await self._ensure_loaded()
        component_id_str = str(component_id)

        matches = []
        for entity_data in self._data.values():
            if entity_data.get("component_id") == component_id_str:
                matches.append(Match.model_validate(entity_data))

        matches.sort(key=lambda m: (m.round_number, m.table_number or 0))
        return matches

    async def list_by_player(
        self, player_id: UUID, tournament_id: UUID | None = None
    ) -> list[Match]:
        await self._ensure_loaded()
        player_id_str = str(player_id)
        tournament_id_str = str(tournament_id) if tournament_id else None

        matches = []
        for entity_data in self._data.values():
            if (
                entity_data.get("player1_id") == player_id_str
                or entity_data.get("player2_id") == player_id_str
            ) and (
                tournament_id_str is None or entity_data.get("tournament_id") == tournament_id_str
            ):
                matches.append(Match.model_validate(entity_data))

        matches.sort(key=lambda m: (m.round_number, m.table_number or 0))
        return matches

    async def update(self, match: Match) -> Match:
        return await self._update(match)  # type: ignore[no-any-return]

    async def delete(self, match_id: UUID) -> None:
        await self._delete(match_id)


class LocalDataLayer(DataLayer):
    """Local JSON file-based implementation of the complete data layer."""

    def __init__(self, data_dir: str = "./tournament_data"):
        self.data_dir = Path(data_dir)

        # Initialize repositories in dependency order
        self._player_repo = LocalPlayerRepository(self.data_dir)
        self._api_key_repo = LocalAPIKeyRepository(self.data_dir)
        self._venue_repo = LocalVenueRepository(self.data_dir)
        self._format_repo = LocalFormatRepository(self.data_dir)
        self._tournament_repo = LocalTournamentRepository(
            self.data_dir, self._player_repo, self._venue_repo, self._format_repo
        )
        self._registration_repo = LocalRegistrationRepository(
            self.data_dir, self._tournament_repo, self._player_repo
        )
        self._component_repo = LocalComponentRepository(self.data_dir, self._tournament_repo)
        self._round_repo = LocalRoundRepository(
            self.data_dir, self._tournament_repo, self._component_repo
        )
        self._match_repo = LocalMatchRepository(
            self.data_dir,
            self._tournament_repo,
            self._component_repo,
            self._round_repo,
            self._player_repo,
        )

    @property
    def players(self) -> PlayerRepository:
        return self._player_repo

    @property
    def api_keys(self) -> APIKeyRepository:
        return self._api_key_repo

    @property
    def venues(self) -> VenueRepository:
        return self._venue_repo

    @property
    def formats(self) -> FormatRepository:
        return self._format_repo

    @property
    def tournaments(self) -> TournamentRepository:
        return self._tournament_repo

    @property
    def registrations(self) -> RegistrationRepository:
        return self._registration_repo

    @property
    def components(self) -> ComponentRepository:
        return self._component_repo

    @property
    def rounds(self) -> RoundRepository:
        return self._round_repo

    @property
    def matches(self) -> MatchRepository:
        return self._match_repo

    async def seed_data(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Seed the data layer with test/demo data."""
        # Clear existing data first
        await self.clear_all_data()

        # Import data in dependency order
        model_classes = {
            "players": Player,
            "api_keys": APIKey,
            "venues": Venue,
            "formats": Format,
            "tournaments": Tournament,
            "registrations": TournamentRegistration,
            "components": Component,
            "rounds": Round,
            "matches": Match,
        }

        repositories = {
            "players": self.players,
            "api_keys": self.api_keys,
            "venues": self.venues,
            "formats": self.formats,
            "tournaments": self.tournaments,
            "registrations": self.registrations,
            "components": self.components,
            "rounds": self.rounds,
            "matches": self.matches,
        }

        for entity_type, entity_list in data.items():
            if entity_type in model_classes and entity_list:
                model_class = model_classes[entity_type]
                repository = repositories[entity_type]

                for entity_data in entity_list:
                    # Convert dict to Pydantic model
                    entity = model_class.model_validate(entity_data)
                    await repository.create(entity)

    async def clear_all_data(self) -> None:
        """Clear all data from the data layer."""
        # Clear in reverse dependency order
        await self._match_repo._clear_all()
        await self._round_repo._clear_all()
        await self._component_repo._clear_all()
        await self._registration_repo._clear_all()
        await self._tournament_repo._clear_all()
        await self._format_repo._clear_all()
        await self._venue_repo._clear_all()
        await self._api_key_repo._clear_all()
        await self._player_repo._clear_all()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check and return status information."""
        # Force load all repositories to get accurate counts
        await self._player_repo._ensure_loaded()
        await self._api_key_repo._ensure_loaded()
        await self._venue_repo._ensure_loaded()
        await self._format_repo._ensure_loaded()
        await self._tournament_repo._ensure_loaded()
        await self._registration_repo._ensure_loaded()
        await self._component_repo._ensure_loaded()
        await self._round_repo._ensure_loaded()
        await self._match_repo._ensure_loaded()

        return {
            "backend_type": "local_json",
            "status": "healthy",
            "data_directory": str(self.data_dir.absolute()),
            "entities": {
                "players": len(self._player_repo._data),
                "api_keys": len(self._api_key_repo._data),
                "venues": len(self._venue_repo._data),
                "formats": len(self._format_repo._data),
                "tournaments": len(self._tournament_repo._data),
                "registrations": len(self._registration_repo._data),
                "components": len(self._component_repo._data),
                "rounds": len(self._round_repo._data),
                "matches": len(self._match_repo._data),
            },
        }
