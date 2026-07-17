#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import GENERATION_ICONS_TABLE_NAME, load_config
from backend.generation_catalog import generation_icon_seed_rows, get_generation_definition
from backend.supabase import SupabaseClient


POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/pokemon"


def fetch_pokemon_icon(pokemon_id: int) -> dict[str, Any]:
    response = requests.get(f"{POKEAPI_BASE_URL}/{pokemon_id}", timeout=10)
    response.raise_for_status()
    payload = response.json()

    icon_url = (
        payload.get("sprites", {})
        .get("other", {})
        .get("official-artwork", {})
        .get("front_default")
    ) or payload.get("sprites", {}).get("front_default")

    sprite_url = payload.get("sprites", {}).get("front_default")
    if not icon_url:
        raise RuntimeError(f"No icon image found for Pokemon {pokemon_id}.")

    return {
        "pokemon_name": payload["name"],
        "icon_url": icon_url,
        "sprite_url": sprite_url,
    }


def build_seed_payload() -> list[dict[str, Any]]:
    rows = []
    for row in generation_icon_seed_rows():
        definition = get_generation_definition(str(row["generation_key"]))
        pokemon_icon = fetch_pokemon_icon(int(row["pokemon_id"]))
        icon_url = definition.icon_url_override or pokemon_icon["icon_url"]
        sprite_url = pokemon_icon["sprite_url"]
        rows.append(
            {
                **row,
                "pokemon_name": pokemon_icon["pokemon_name"],
                "icon_url": icon_url,
                "sprite_url": sprite_url,
            }
        )
    return rows


def main() -> None:
    config = load_config()
    client = SupabaseClient(config, table_name=GENERATION_ICONS_TABLE_NAME)
    payload = build_seed_payload()
    saved_rows = client.upsert_many(payload=payload, on_conflict="generation_key")
    for row in saved_rows:
        print(
            f"seeded {row['generation_key']}: "
            f"{row['pokemon_name']} ({row['pokemon_id']}) -> {row['icon_url']}"
        )


if __name__ == "__main__":
    main()
