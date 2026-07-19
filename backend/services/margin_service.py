"""Margin balance trend service."""

from backend.storage.analysis_repository import get_margin_trend as query_margin_trend


def get_margin_trend():
    """Return margin balance trend from storage."""
    return query_margin_trend()
