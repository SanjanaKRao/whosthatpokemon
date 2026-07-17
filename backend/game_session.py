from __future__ import annotations

from random import choice

from flask import session

from backend.generation_catalog import get_generation_definition

SESSION_KEY = "pokemon_game_session"


def start_generation_session(generation_key: str, generation_icon_url: str | None = None) -> dict:
    definition = get_generation_definition(generation_key)
    session[SESSION_KEY] = {
        "generation_key": definition.key,
        "generation_icon_url": normalize_session_icon_url(generation_icon_url),
        "shown_ids": [],
    }
    session.modified = True
    return serialize_generation_state(
        definition,
        seen_count=0,
        completed=False,
        generation_icon_url=session[SESSION_KEY]["generation_icon_url"],
    )


def get_next_pokemon_for_session() -> dict:
    state = session.get(SESSION_KEY)
    if not state:
        raise ValueError("No active generation selected.")

    definition = get_generation_definition(state["generation_key"])
    shown_ids = [int(pokemon_id) for pokemon_id in state.get("shown_ids", [])]
    shown_ids_set = set(shown_ids)
    available_ids = [pokemon_id for pokemon_id in definition.pokemon_ids if pokemon_id not in shown_ids_set]

    if not available_ids:
        return {
            **serialize_generation_state(
                definition,
                seen_count=len(shown_ids),
                completed=True,
                generation_icon_url=state.get("generation_icon_url"),
            ),
            "pokemon_id": None,
        }

    pokemon_id = choice(available_ids)
    shown_ids.append(pokemon_id)
    state["shown_ids"] = shown_ids
    session[SESSION_KEY] = state
    session.modified = True

    return {
        **serialize_generation_state(
            definition,
            seen_count=len(shown_ids),
            completed=False,
            generation_icon_url=state.get("generation_icon_url"),
        ),
        "pokemon_id": pokemon_id,
    }


def normalize_session_icon_url(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized[:2000]


def serialize_generation_state(
    definition,
    *,
    seen_count: int,
    completed: bool,
    generation_icon_url: str | None,
) -> dict:
    return {
        "generation": {
            "key": definition.key,
            "label": definition.label,
            "icon": definition.fallback_icon,
            "icon_url": generation_icon_url,
            "display_label": definition.label,
        },
        "seen_count": seen_count,
        "total_count": definition.total_count,
        "completed": completed,
    }
