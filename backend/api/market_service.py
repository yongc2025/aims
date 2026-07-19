"""Market data service layer."""

from backend.services.trade_calendar import is_trade_day
from backend.storage.repository import get_market_report, get_recent_market_reports


def query_market_by_date(trade_date: str):
    """Query stored market data by trade date."""
    if not is_trade_day(trade_date):
        return None

    return get_market_report(trade_date)


def query_latest_market():
    """Query the latest stored market data."""
    for report in get_recent_market_reports():
        if is_trade_day(report["date"]):
            return report
    return None
