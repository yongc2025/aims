"""Validation helpers for AI collector outputs."""

from backend.schemas.market import MarketDailySchema


class DataValidator:
    """Validate AI generated market JSON before storage."""

    def validate(self, payload: dict) -> MarketDailySchema:
        return MarketDailySchema.model_validate(payload)
