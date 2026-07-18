"""Report API endpoints."""

from fastapi import APIRouter, HTTPException

from backend.storage.repository import get_market_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{trade_date}")
def get_report(trade_date: str):
    """Return markdown report by date."""
    report = get_market_report(trade_date)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="report not found",
        )

    return {
        "date": trade_date,
        "content": report.get("markdown_content"),
    }
