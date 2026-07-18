"""Market data API endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException

from backend.api.market_service import query_market_by_date

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/{trade_date}")
def get_market(trade_date: date):
    """Get stored market data by trade date."""
    result = query_market_by_date(trade_date.isoformat())

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="market data not found",
        )

    return result
