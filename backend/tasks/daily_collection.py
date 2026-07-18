"""Daily A-share market data collection task."""

from datetime import date


def run_daily_collection(trade_date: date):
    """Execute daily collection workflow.

    Workflow placeholder:
    1. Run collector agent
    2. Validate output
    3. Save JSON
    4. Generate markdown
    """
    return {
        "date": trade_date.isoformat(),
        "status": "pending_agent_execution",
    }
