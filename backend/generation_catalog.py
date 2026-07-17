from __future__ import annotations

from dataclasses import dataclass

from backend.config import GENERATION_ICONS_TABLE_NAME
from backend.errors import SupabaseRequestError
from backend.supabase import SupabaseClient

POKEBALL_ICON_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png"


@dataclass(frozen=True)
class GenerationDefinition:
    key: str
    label: str
    start_id: int
    end_id: int
    fallback_icon: str
    seed_pokemon_id: int
    seed_pokemon_name: str
    icon_url_override: str | None = None

    @property
    def total_count(self) -> int:
        return self.end_id - self.start_id + 1

    @property
    def pokemon_ids(self) -> list[int]:
        return list(range(self.start_id, self.end_id + 1))


GENERATION_DEFINITIONS = (
    GenerationDefinition("gen1", "Gen 1", 1, 151, "⚡", 25, "pikachu"),
    GenerationDefinition("gen2", "Gen 2", 152, 251, "🥚", 197, "umbreon"),
    GenerationDefinition("gen3", "Gen 3", 252, 386, "💎", 384, "rayquaza"),
    GenerationDefinition("gen4", "Gen 4", 387, 493, "⛰️", 448, "lucario"),
    GenerationDefinition("gen5", "Gen 5", 494, 649, "⚔️", 609, "chandelure"),
    GenerationDefinition("gen6", "Gen 6", 650, 721, "✨", 658, "greninja"),
    GenerationDefinition("gen7", "Gen 7", 722, 809, "🌙", 778, "mimikyu"),
    GenerationDefinition("gen8", "Gen 8", 810, 905, "👑", 823, "corviknight"),
    GenerationDefinition("gen9", "Gen 9", 906, 1025, "🧭", 959, "tinkaton"),
    GenerationDefinition("all", "All", 1, 1025, "🌐", 25, "pikachu", POKEBALL_ICON_URL),
)

GENERATION_DEFINITION_BY_KEY = {definition.key: definition for definition in GENERATION_DEFINITIONS}


def get_generation_definition(generation_key: str) -> GenerationDefinition:
    definition = GENERATION_DEFINITION_BY_KEY.get(generation_key)
    if definition is None:
        raise ValueError("Invalid generation selection.")
    return definition


def build_generation_option(
    definition: GenerationDefinition,
    icon_row: dict | None = None,
) -> dict:
    icon_row = icon_row or {}
    return {
        "key": definition.key,
        "label": definition.label,
        "display_label": definition.label,
        "total_count": definition.total_count,
        "start_id": definition.start_id,
        "end_id": definition.end_id,
        "id_range": f"{definition.start_id}-{definition.end_id}",
        "fallback_icon": definition.fallback_icon,
        "icon_url": icon_row.get("icon_url") or definition.icon_url_override,
        "sprite_url": icon_row.get("sprite_url"),
        "icon_pokemon_id": icon_row.get("pokemon_id") or definition.seed_pokemon_id,
        "icon_pokemon_name": icon_row.get("pokemon_name") or definition.seed_pokemon_name,
    }


def build_generation_options(icon_rows: list[dict] | None = None) -> list[dict]:
    rows_by_key = {
        str(row.get("generation_key") or "").strip().lower(): row
        for row in (icon_rows or [])
    }
    return [build_generation_option(definition, rows_by_key.get(definition.key)) for definition in GENERATION_DEFINITIONS]


class GenerationIconRepository:
    def __init__(self, client: SupabaseClient):
        self._client = client

    def fetch_options(self) -> list[dict]:
        try:
            rows = self._client.get(
                params={
                    "select": "generation_key,generation_label,pokemon_id,pokemon_name,icon_url,sprite_url",
                    "order": "sort_order.asc,generation_key.asc",
                }
            )
        except SupabaseRequestError:
            rows = []
        return build_generation_options(rows)


def generation_icon_seed_rows() -> list[dict]:
    return [
        {
            "generation_key": definition.key,
            "generation_label": definition.label,
            "sort_order": index,
            "pokemon_id": definition.seed_pokemon_id,
            "pokemon_name": definition.seed_pokemon_name,
        }
        for index, definition in enumerate(GENERATION_DEFINITIONS, start=1)
    ]


__all__ = [
    "GENERATION_DEFINITIONS",
    "GENERATION_ICONS_TABLE_NAME",
    "GenerationDefinition",
    "GenerationIconRepository",
    "build_generation_option",
    "build_generation_options",
    "generation_icon_seed_rows",
    "get_generation_definition",
]
