from __future__ import annotations


class SupabaseRequestError(RuntimeError):
    def __init__(self, message: str, details: object | None = None):
        super().__init__(message)
        self.details = details
