"""Daily A-share market data collection task."""

from datetime import date

from backend.agents.run_akshare_collector import build_summary, collect_market_data


def run_daily_collection(
    trade_date: date,
    *,
    preserve_realtime_snapshot: bool = False,
) -> dict:
    """Execute the daily collection workflow."""
    data = collect_market_data(
        trade_date.isoformat(),
        preserve_realtime_snapshot=preserve_realtime_snapshot,
    )
    return build_summary(data)
