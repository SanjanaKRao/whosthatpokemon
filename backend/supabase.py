from __future__ import annotations

from typing import Any

import requests

from backend.config import AppConfig, TABLE_NAME
from backend.errors import SupabaseRequestError


class SupabaseClient:
    def __init__(self, config: AppConfig, *, table_name: str = TABLE_NAME):
        self._rest_url = config.rest_url_for(table_name)
        self._secret_key = config.supabase_secret_key

    def headers(
        self,
        *,
        prefer_representation: bool = False,
        merge_duplicates: bool = False,
    ) -> dict[str, str]:
        headers = {
            "apikey": self._secret_key,
            "Authorization": f"Bearer {self._secret_key}",
            "Content-Type": "application/json",
        }
        prefer_parts = []
        if merge_duplicates:
            prefer_parts.append("resolution=merge-duplicates")
        if prefer_representation:
            prefer_parts.append("return=representation")
        if prefer_parts:
            headers["Prefer"] = ",".join(prefer_parts)
        return headers

    def get(self, *, params: dict[str, Any]) -> list[dict]:
        try:
            response = requests.get(
                self._rest_url,
                headers=self.headers(),
                params=params,
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SupabaseRequestError("Supabase request failed.", str(exc)) from exc
        return self._parse_json_response(response)

    def post(self, *, payload: dict[str, Any]) -> list[dict]:
        try:
            response = requests.post(
                self._rest_url,
                headers=self.headers(prefer_representation=True),
                json=payload,
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SupabaseRequestError("Supabase request failed.", str(exc)) from exc
        return self._parse_json_response(response)

    def upsert_many(self, *, payload: list[dict[str, Any]], on_conflict: str) -> list[dict]:
        try:
            response = requests.post(
                self._rest_url,
                headers=self.headers(prefer_representation=True, merge_duplicates=True),
                params={"on_conflict": on_conflict},
                json=payload,
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SupabaseRequestError("Supabase request failed.", str(exc)) from exc
        return self._parse_json_response(response)

    def patch(self, *, params: dict[str, Any], payload: dict[str, Any]) -> list[dict]:
        try:
            response = requests.patch(
                self._rest_url,
                headers=self.headers(prefer_representation=True),
                params=params,
                json=payload,
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SupabaseRequestError("Supabase request failed.", str(exc)) from exc
        return self._parse_json_response(response)

    @staticmethod
    def _parse_json_response(response: requests.Response) -> list[dict]:
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            details: object | None = None
            if exc.response is not None:
                try:
                    details = exc.response.json()
                except ValueError:
                    details = exc.response.text
            raise SupabaseRequestError("Supabase request failed.", details) from exc

        return response.json()
