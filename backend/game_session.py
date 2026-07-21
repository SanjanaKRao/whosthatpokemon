from __future__ import annotations

from functools import lru_cache
from random import choice

import requests
from flask import session

from backend.generation_catalog import get_generation_definition

SESSION_KEY = "pokemon_game_session"
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/pokemon"
DEFAULT_GUESSES_PER_ROUND = 3


def get_active_game_session() -> dict:
    state = session.get(SESSION_KEY)
    if not state:
        raise ValueError("No active generation selected.")
    return state


@lru_cache(maxsize=2048)
def fetch_pokemon_name(pokemon_id: int) -> str:
    try:
        response = requests.get(f"{POKEAPI_BASE_URL}/{pokemon_id}", timeout=10)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("Pokemon lookup failed.") from exc

    name = str(payload.get("name") or "").strip().lower()
    if not name:
        raise RuntimeError("Pokemon lookup failed.")
    return name


def persist_game_session(state: dict) -> None:
    session[SESSION_KEY] = state
    session.modified = True


def build_game_session_state(definition, generation_icon_url: str | None) -> dict:
    return {
        "generation_key": definition.key,
        "generation_icon_url": normalize_session_icon_url(generation_icon_url),
        "shown_ids": [],
        "current_pokemon_id": None,
        "current_pokemon_name": None,
        "guesses_remaining": 0,
        "round_resolved": True,
        "score": 0,
        "streak": 0,
        "max_streak": 0,
        "leaderboard_entry_id": None,
    }


def start_generation_session(generation_key: str, generation_icon_url: str | None = None) -> dict:
    definition = get_generation_definition(generation_key)
    state = build_game_session_state(definition, generation_icon_url)
    persist_game_session(state)
    return serialize_generation_state(
        definition,
        state=state,
        completed=False,
        generation_icon_url=state["generation_icon_url"],
    )


def get_next_pokemon_for_session() -> dict:
    state = get_active_game_session()
    definition = get_generation_definition(state["generation_key"])
    shown_ids = [int(pokemon_id) for pokemon_id in state.get("shown_ids", [])]
    current_pokemon_id = state.get("current_pokemon_id")

    if current_pokemon_id and not bool(state.get("round_resolved", True)):
        return {
            **serialize_generation_state(
                definition,
                state=state,
                completed=False,
                generation_icon_url=state.get("generation_icon_url"),
            ),
            "pokemon_id": int(current_pokemon_id),
        }

    shown_ids_set = set(shown_ids)
    available_ids = [pokemon_id for pokemon_id in definition.pokemon_ids if pokemon_id not in shown_ids_set]

    if not available_ids:
        state["current_pokemon_id"] = None
        state["current_pokemon_name"] = None
        state["guesses_remaining"] = 0
        state["round_resolved"] = True
        persist_game_session(state)
        return {
            **serialize_generation_state(
                definition,
                state=state,
                completed=True,
                generation_icon_url=state.get("generation_icon_url"),
            ),
            "pokemon_id": None,
        }

    pokemon_id = choice(available_ids)
    pokemon_name = fetch_pokemon_name(pokemon_id)
    shown_ids.append(pokemon_id)
    state["shown_ids"] = shown_ids
    state["current_pokemon_id"] = pokemon_id
    state["current_pokemon_name"] = pokemon_name
    state["guesses_remaining"] = DEFAULT_GUESSES_PER_ROUND
    state["round_resolved"] = False
    persist_game_session(state)

    return {
        **serialize_generation_state(
            definition,
            state=state,
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


def normalize_guess(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        raise ValueError("Guess is required.")
    return normalized


def ensure_active_round(state: dict) -> tuple:
    current_pokemon_id = state.get("current_pokemon_id")
    if not current_pokemon_id:
        raise ValueError("No active Pokemon round.")
    if bool(state.get("round_resolved", True)):
        raise ValueError("Current Pokemon round is already resolved.")
    guesses_remaining = int(state.get("guesses_remaining") or 0)
    if guesses_remaining <= 0:
        raise ValueError("No guesses remain for the current Pokemon.")
    return int(current_pokemon_id), guesses_remaining


def submit_guess_for_session(guess: object) -> dict:
    state = get_active_game_session()
    definition = get_generation_definition(state["generation_key"])
    current_pokemon_id, guesses_remaining = ensure_active_round(state)
    normalized_guess = normalize_guess(guess)
    current_pokemon_name = str(state.get("current_pokemon_name") or "").strip().lower() or fetch_pokemon_name(current_pokemon_id)
    state["current_pokemon_name"] = current_pokemon_name
    attempt_number = DEFAULT_GUESSES_PER_ROUND - guesses_remaining + 1

    if normalized_guess == current_pokemon_name:
        points_earned = guesses_remaining
        updated_streak = int(state.get("streak") or 0) + 1
        state["score"] = int(state.get("score") or 0) + points_earned
        state["streak"] = updated_streak
        state["max_streak"] = max(int(state.get("max_streak") or 0), updated_streak)
        state["guesses_remaining"] = 0
        state["round_resolved"] = True
        persist_game_session(state)
        return {
            **serialize_generation_state(
                definition,
                state=state,
                completed=False,
                generation_icon_url=state.get("generation_icon_url"),
            ),
            "result": "correct",
            "pokemon_id": current_pokemon_id,
            "pokemon_name": current_pokemon_name,
            "attempt_number": attempt_number,
            "points_earned": points_earned,
            "streak_broken": False,
        }

    guesses_remaining -= 1
    state["guesses_remaining"] = guesses_remaining
    if guesses_remaining > 0:
        persist_game_session(state)
        return {
            **serialize_generation_state(
                definition,
                state=state,
                completed=False,
                generation_icon_url=state.get("generation_icon_url"),
            ),
            "result": "incorrect",
            "pokemon_id": current_pokemon_id,
            "attempt_number": attempt_number,
            "streak_broken": False,
        }

    previous_streak = int(state.get("streak") or 0)
    state["streak"] = 0
    state["guesses_remaining"] = 0
    state["round_resolved"] = True
    persist_game_session(state)
    return {
        **serialize_generation_state(
            definition,
            state=state,
            completed=False,
            generation_icon_url=state.get("generation_icon_url"),
        ),
        "result": "missed",
        "pokemon_id": current_pokemon_id,
        "pokemon_name": current_pokemon_name,
        "attempt_number": attempt_number,
        "attempts_used": DEFAULT_GUESSES_PER_ROUND,
        "streak_broken": previous_streak > 0,
        "previous_streak": previous_streak,
    }


def skip_current_pokemon_for_session() -> dict:
    state = get_active_game_session()
    definition = get_generation_definition(state["generation_key"])
    current_pokemon_id, guesses_remaining = ensure_active_round(state)
    current_pokemon_name = str(state.get("current_pokemon_name") or "").strip().lower() or fetch_pokemon_name(current_pokemon_id)
    state["current_pokemon_name"] = current_pokemon_name
    previous_streak = int(state.get("streak") or 0)
    attempts_used = DEFAULT_GUESSES_PER_ROUND - guesses_remaining
    state["streak"] = 0
    state["guesses_remaining"] = 0
    state["round_resolved"] = True
    persist_game_session(state)
    return {
        **serialize_generation_state(
            definition,
            state=state,
            completed=False,
            generation_icon_url=state.get("generation_icon_url"),
        ),
        "result": "skipped",
        "pokemon_id": current_pokemon_id,
        "pokemon_name": current_pokemon_name,
        "attempts_used": attempts_used,
        "streak_broken": previous_streak > 0,
        "previous_streak": previous_streak,
    }


def store_leaderboard_entry_id(entry_id: int) -> None:
    state = get_active_game_session()
    state["leaderboard_entry_id"] = int(entry_id)
    persist_game_session(state)


def serialize_generation_state(
    definition,
    *,
    state: dict,
    completed: bool,
    generation_icon_url: str | None,
) -> dict:
    shown_ids = [int(pokemon_id) for pokemon_id in state.get("shown_ids", [])]
    return {
        "generation": {
            "key": definition.key,
            "label": definition.label,
            "icon": definition.fallback_icon,
            "icon_url": generation_icon_url,
            "display_label": definition.label,
        },
        "seen_count": len(shown_ids),
        "total_count": definition.total_count,
        "completed": completed,
        "score": int(state.get("score") or 0),
        "streak": int(state.get("streak") or 0),
        "max_streak": int(state.get("max_streak") or 0),
        "guesses_remaining": int(state.get("guesses_remaining") or 0),
    }
