from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

TABLE_NAME = "leaderboard_scores"
GENERATION_ICONS_TABLE_NAME = "pokemon_generation_icons"
MAX_NAME_LENGTH = 10
DEFAULT_LEADERBOARD_LIMIT = 5
MAX_LEADERBOARD_LIMIT = 25


@dataclass(frozen=True)
class AppConfig:
    supabase_url: str
    supabase_secret_key: str
    supabase_rest_url: str
    flask_secret_key: str

    def rest_url_for(self, table_name: str) -> str:
        return f"{self.supabase_url}/rest/v1/{table_name}"


def load_config() -> AppConfig:
    load_dotenv(ENV_PATH)

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_secret_key = os.getenv("SUPABASE_SECRET_KEY", "")

    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not supabase_secret_key:
        missing.append("SUPABASE_SECRET_KEY")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return AppConfig(
        supabase_url=supabase_url,
        supabase_secret_key=supabase_secret_key,
        supabase_rest_url=f"{supabase_url}/rest/v1/{TABLE_NAME}",
        flask_secret_key=os.getenv("FLASK_SECRET_KEY", "whos-that-pokemon-dev-secret"),
    )
