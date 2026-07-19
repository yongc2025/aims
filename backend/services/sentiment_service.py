"""Market sentiment trend service."""

from backend.storage.analysis_repository import get_sentiment_trend as query_sentiment_trend


def get_sentiment_trend():
    """Return market sentiment time series from storage."""
    return query_sentiment_trend()
