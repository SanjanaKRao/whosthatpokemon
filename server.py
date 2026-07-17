#!/usr/bin/env python3
import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest

from backend.config import DEFAULT_LEADERBOARD_LIMIT, GENERATION_ICONS_TABLE_NAME, ROOT_DIR, load_config
from backend.errors import SupabaseRequestError
from backend.game_session import get_next_pokemon_for_session, start_generation_session
from backend.generation_catalog import GenerationIconRepository
from backend.leaderboard import LeaderboardRepository, parse_limit
from backend.supabase import SupabaseClient

app = Flask(__name__)
config = load_config()
app.secret_key = config.flask_secret_key
leaderboard_repository = LeaderboardRepository(SupabaseClient(config))
generation_icon_repository = GenerationIconRepository(
    SupabaseClient(config, table_name=GENERATION_ICONS_TABLE_NAME)
)


def resolve_generation_icon_url(generation_key: str, requested_icon_url: object) -> str | None:
    normalized_requested = str(requested_icon_url or "").strip()
    if normalized_requested:
        return normalized_requested

    options = generation_icon_repository.fetch_options()
    for option in options:
        if str(option.get("key") or "").strip().lower() == generation_key:
            normalized_option_icon = str(option.get("icon_url") or "").strip()
            return normalized_option_icon or None

    return None


def supabase_error_response(error: SupabaseRequestError) -> tuple:
    payload = {"error": str(error)}
    if error.details:
        payload["details"] = error.details
    return jsonify(payload), 502


@app.get("/api/leaderboard")
def get_leaderboard() -> tuple:
    try:
        limit = parse_limit(request.args.get("limit"))
        return jsonify({"entries": leaderboard_repository.fetch(limit=limit)}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except SupabaseRequestError as exc:
        return supabase_error_response(exc)


@app.post("/api/leaderboard")
def post_leaderboard() -> tuple:
    try:
        payload = request.get_json(silent=False)
        if payload is None:
            payload = {}

        saved_entry = leaderboard_repository.save(payload)
        response = {
            "entry": saved_entry,
            "entries": leaderboard_repository.fetch(limit=DEFAULT_LEADERBOARD_LIMIT),
        }
        return jsonify(response), 201
    except BadRequest:
        return jsonify({"error": "Request body must be valid JSON."}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except SupabaseRequestError as exc:
        return supabase_error_response(exc)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502


@app.get("/api/generations")
def get_generations() -> tuple:
    return jsonify({"options": generation_icon_repository.fetch_options()}), 200


@app.post("/api/game/session")
def post_game_session() -> tuple:
    try:
        payload = request.get_json(silent=False)
        if payload is None:
            payload = {}

        generation_key = str(payload.get("generation") or "").strip().lower()
        generation_icon_url = resolve_generation_icon_url(generation_key, payload.get("generationIconUrl"))
        session_state = start_generation_session(generation_key, generation_icon_url)
        return jsonify(session_state), 200
    except BadRequest:
        return jsonify({"error": "Request body must be valid JSON."}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/game/pokemon")
def get_game_pokemon() -> tuple:
    try:
        return jsonify(get_next_pokemon_for_session()), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/")
def serve_index():
    return send_from_directory(ROOT_DIR, "index.html")


@app.get("/<path:path>")
def serve_static(path: str):
    return send_from_directory(ROOT_DIR, path)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    port = int(os.getenv("PORT", str(port)))
    app.run(host=host, port=port)


if __name__ == "__main__":
    run()
