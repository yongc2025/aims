"""Report API endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{trade_date}")
def get_report(trade_date: str):
    """Return markdown report by date.

    Storage integration will be connected later.
    """
    return {
        "date": trade_date,
        "content": "report pending storage integration",
    }
