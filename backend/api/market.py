"""Market data API endpoints."""

from datetime import date

from fastapi import APIRouter

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/{trade_date}")
def get_market(trade_date: date):
    """Get market data by trade date.

    Storage integration will be connected in the next stage.
    """
    return {
        "date": trade_date.isoformat(),
        "status": "pending_storage_integration",
    }
