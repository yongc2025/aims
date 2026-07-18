"""Market data service layer."""

from backend.storage.repository import get_market_report


def query_market_by_date(trade_date: str):
    """Query stored market data by trade date."""
    return get_market_report(trade_date)
