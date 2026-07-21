from __future__ import annotations

from backend.config import DEFAULT_LEADERBOARD_LIMIT, MAX_LEADERBOARD_LIMIT, MAX_NAME_LENGTH
from backend.supabase import SupabaseClient


def normalize_name(name: object) -> str:
    normalized = str(name or "").strip()
    if not normalized:
        raise ValueError("Player name is required.")
    return normalized[:MAX_NAME_LENGTH]


def normalize_country(country: object) -> str:
    normalized = str(country or "🌍").strip()
    return normalized or "🌍"


def normalize_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None

    if len(normalized) > 2000:
        raise ValueError(f"{field_name} is too long.")
    return normalized


def normalize_non_negative_int(value: object, field_name: str) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc

    if normalized < 0:
        raise ValueError(f"{field_name} must be non-negative.")
    return normalized


def parse_limit(raw_limit: str | None) -> int:
    if raw_limit is None:
        return DEFAULT_LEADERBOARD_LIMIT

    try:
        limit = int(raw_limit)
    except ValueError as exc:
        raise ValueError("limit must be an integer.") from exc

    if limit <= 0:
        raise ValueError("limit must be greater than 0.")

    return min(limit, MAX_LEADERBOARD_LIMIT)


class LeaderboardRepository:
    def __init__(self, client: SupabaseClient):
        self._client = client

    def fetch(self, *, limit: int = DEFAULT_LEADERBOARD_LIMIT) -> list[dict]:
        return self._client.get(
            params={
                "select": "id,name,country,score,streak,generation_icon_url,created_at",
                "order": "score.desc,streak.desc,id.asc",
                "limit": limit,
            }
        )

    def save(self, payload: dict, *, session_state: dict) -> dict:
        score = normalize_non_negative_int(session_state.get("score"), "score")
        if score == 0:
            raise ValueError("Score must be greater than 0 before saving to the leaderboard.")

        max_streak = normalize_non_negative_int(session_state.get("max_streak"), "streak")
        entry = {
            "name": normalize_name(payload.get("name")),
            "country": normalize_country(payload.get("country")),
            "score": score,
            "streak": max_streak,
            "generation_icon_url": normalize_optional_text(session_state.get("generation_icon_url"), "generation_icon_url"),
        }
        entry_id = session_state.get("leaderboard_entry_id")

        if entry_id:
            normalized_id = normalize_non_negative_int(entry_id, "id")
            if normalized_id == 0:
                raise ValueError("id must be greater than 0.")

            updated_rows = self._client.patch(
                params={"id": f"eq.{normalized_id}"},
                payload=entry,
            )
            if not updated_rows:
                raise RuntimeError("Supabase did not return the updated leaderboard row.")
            return updated_rows[0]

        created_rows = self._client.post(payload=entry)
        if not created_rows:
            raise RuntimeError("Supabase did not return the created leaderboard row.")
        return created_rows[0]
